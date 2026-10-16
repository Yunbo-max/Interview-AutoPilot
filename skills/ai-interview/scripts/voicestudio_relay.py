"""Private local WebSocket relay for VoiceStudio streaming speech recognition.

VoiceStudio correctly refuses a browser WebSocket whose Origin is another
local application's port. This independent relay validates the studio Origin,
private bearer token, and exact active question before connecting as a native
loopback WS client (with no browser Origin). It cannot capture a microphone.
"""
from __future__ import annotations

import asyncio
import json
import secrets
import threading
import time

MAX_TOTAL_AUDIO = 20 * 1024 * 1024
MAX_STREAM_SECONDS = 190
MAX_TRANSCRIPT = 20_000


class VoiceStudioRelay:
    def __init__(self, state, backend):
        self.state = state
        self.backend = backend
        self.url = None
        self._thread = None
        self._loop = None
        self._done = None
        self._started = threading.Event()
        self._failure = None
        self._active_lock = threading.Lock()

    def start(self):
        if self._thread:
            raise RuntimeError('VoiceStudio WebSocket relay is already running')
        self._thread = threading.Thread(target=self._run, daemon=True,
                                       name='ai-interview-voicestudio-relay')
        self._thread.start()
        if not self._started.wait(timeout=8) or self._failure or not self.url:
            raise RuntimeError('Could not start local VoiceStudio stream relay')
        return self.url

    def _run(self):
        async def serve_ws():
            from websockets.asyncio.server import serve
            self._loop = asyncio.get_running_loop()
            self._done = asyncio.Event()
            async with serve(self._handle, '127.0.0.1', 0, origins=[self.state.origin],
                             compression=None, max_size=1024 * 1024,
                             max_queue=8, ping_interval=20, close_timeout=2) as server:
                port = server.sockets[0].getsockname()[1]
                self.url = f'ws://127.0.0.1:{port}/stream'
                self._started.set()
                await self._done.wait()
        try:
            asyncio.run(serve_ws())
        except Exception as e:
            self._failure = e
            self._started.set()

    def stop(self):
        if self._loop and self._done and self._thread and self._thread.is_alive():
            self._loop.call_soon_threadsafe(self._done.set)
            self._thread.join(timeout=5)
        self._loop = None

    def _valid_question(self, qid):
        with self.state.interview.lock:
            question = self.state.interview.current_question
            return (self.state.interview.status == 'active' and question is not None
                    and question.get('id') == qid and question.get('kind') == 'voice')

    async def _handle(self, client):
        from websockets.asyncio.client import connect
        if client.request.path != '/stream':
            await client.close(code=1008, reason='Invalid voice relay path');return
        try:
            raw = await asyncio.wait_for(client.recv(), timeout=5)
            if not isinstance(raw, str) or len(raw) > 2048:
                raise ValueError('Invalid voice session handshake')
            request = json.loads(raw)
            token = request.get('token') if isinstance(request, dict) else None
            qid = request.get('question_id') if isinstance(request, dict) else None
            if (not isinstance(token, str) or not isinstance(qid, str)
                    or not secrets.compare_digest(token, self.state.token)
                    or request.get('type') != 'start'):
                raise ValueError('Unauthorized voice session')
            if not self._valid_question(qid):
                raise ValueError('Not the active spoken question')
        except (ValueError, TypeError, json.JSONDecodeError, asyncio.TimeoutError) as e:
            await client.send(json.dumps({'type':'error','message':str(e)[:150]}))
            await client.close(code=1008);return
        if not self._active_lock.acquire(blocking=False):
            await client.send(json.dumps({'type':'error','message':'Another candidate recording is already active.'}))
            await client.close(code=1008)
            return
        hold_token=None
        try:
            # proxy=None prevents proxy settings from redirecting local mic audio.
            async with connect(self.backend.websocket_upstream, proxy=None,
                               origin=None, compression=None, max_size=128*1024,
                               open_timeout=5, close_timeout=2) as upstream:
                await client.send(json.dumps({'type':'ready','question_id':qid}))
                created = time.monotonic()

                async def input_forward():
                    nonlocal hold_token
                    total = 0
                    async for msg in client:
                        if not self._valid_question(qid):
                            raise ValueError('Question changed; audio discarded')
                        if time.monotonic()-created > MAX_STREAM_SECONDS:
                            raise ValueError('Recording exceeded session limit')
                        if isinstance(msg, bytes):
                            total += len(msg)
                            if total > MAX_TOTAL_AUDIO:
                                raise ValueError('Recording exceeded 20 MiB')
                            await upstream.send(msg)
                        else:
                            command=json.loads(msg)
                            if command == {'type':'input_audio.end'}:
                                # Stop candidate time while waiting for the final ASR summary.
                                # This operation cannot initiate a microphone recording.
                                hold_token=self.state.interview.begin_host_wait(qid,'stt_stream')
                                if hold_token is None:
                                    raise ValueError('Stale spoken question while finalizing the transcript')
                                await upstream.send(msg)
                                # Wait for the upstream summary; never turn a partial into final.
                                await asyncio.Event().wait()
                            if command == {'type':'cancel'}:
                                return
                            raise ValueError('Unsupported microphone control')

                async def output_forward():
                    nonlocal hold_token
                    async for msg in upstream:
                        if not self._valid_question(qid):
                            raise ValueError('Question changed during transcription')
                        if not isinstance(msg,str) or len(msg)>130_000:
                            raise ValueError('Invalid upstream speech event')
                        data=json.loads(msg)
                        kind=data.get('type')
                        if kind not in ('partial','final','status','error','session.started'):
                            continue
                        safe={'type':kind}
                        if kind in ('partial','final'):
                            text=data.get('text','')
                            if not isinstance(text,str): raise ValueError('Invalid upstream transcription')
                            safe['text']=text[:MAX_TRANSCRIPT]
                        if kind=='final':
                            safe['final_kind']=data.get('final_kind','summary') if data.get('final_kind') in ('utterance','summary') else 'utterance'
                        if kind=='error':
                            safe['message']='VoiceStudio reported a transcription error; retry or use batch input.'
                        if kind=='final' and safe.get('final_kind')=='summary':
                            # The client may submit immediately on receiving the summary.
                            # Release the processing hold before handing it over; the outer
                            # finally still releases on errors or disconnects.
                            self.state.interview.end_host_wait(hold_token)
                            hold_token=None
                        await client.send(json.dumps(safe,ensure_ascii=False))
                        if kind=='final' and safe['final_kind']=='summary':return
                        if kind=='error':return
                    raise RuntimeError('VoiceStudio speech stream closed without a final summary')

                tasks=[asyncio.create_task(input_forward()),asyncio.create_task(output_forward())]
                done,pending=await asyncio.wait(tasks,timeout=MAX_STREAM_SECONDS + 5,
                                                return_when=asyncio.FIRST_COMPLETED)
                for task in pending: task.cancel()
                await asyncio.gather(*pending,return_exceptions=True)
                if not done:
                    raise TimeoutError('VoiceStudio speech session timed out')
                for task in done:
                    if not task.cancelled():
                        ex=task.exception()
                        if ex: raise ex
        except Exception as e:
            try:
                await client.send(json.dumps({'type':'error',
                    'message':'VoiceStudio stream interrupted. You may retry or switch to batch transcription.'}))
            except Exception:pass
        finally:
            self.state.interview.end_host_wait(hold_token)
            self._active_lock.release()
            try:await client.close()
            except Exception:pass
