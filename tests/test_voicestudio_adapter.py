"""VoiceStudio adapter contract tests with an isolated fake local VoiceStudio service."""
import base64
import http.server
import json
import os
import sys
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'skills' / 'ai-interview' / 'scripts'
sys.path.insert(0, str(SCRIPTS))

class FakeVoiceHandler(http.server.BaseHTTPRequestHandler):
    calls = []
    def log_message(self, *args): pass
    def do_GET(self):
        if self.path == '/health':
            payload={'status':'ok'}
        elif self.path == '/.well-known/voicestudio-speech':
            payload={'protocol':'voicestudio.speech.v1','service':'VoiceStudio',
                'endpoints':{'streaming_transcription':{'path':'/v1/audio/transcriptions/stream','transport':'websocket'},
                             'batch_transcription':{'path':'/v1/audio/transcriptions','transport':'http'}},
                'features':{'streaming_transcription':True},'stream_input':{'default_format':'audio/webm;codecs=opus'}}
        elif self.path == '/v1/audio/voices':
            payload={'data':[{'id':'default'},{'id':'voice-example'}]}
        else:
            self.send_error(404); return
        encoded=json.dumps(payload).encode();self.send_response(200)
        self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(encoded)))
        self.end_headers();self.wfile.write(encoded)
    def do_POST(self):
        body=self.rfile.read(int(self.headers['Content-Length']))
        self.calls.append((self.path,body,self.headers.get('Content-Type')))
        if self.path == '/v1/audio/speech':
            response=b'RIFF'+b'\x00'*24
            kind='audio/wav'
        elif self.path == '/v1/audio/transcriptions':
            response=b'{"text":"VoiceStudio recognized answer"}'
            kind='application/json'
        else:
            self.send_error(404);return
        self.send_response(200);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(response)));self.end_headers();self.wfile.write(response)

class VoiceStudioAdapterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from voicestudio_adapter import VoiceStudioAdapter
        cls.VoiceStudioAdapter=VoiceStudioAdapter
        cls.httpd=http.server.ThreadingHTTPServer(('127.0.0.1',0),FakeVoiceHandler)
        cls.thread=threading.Thread(target=cls.httpd.serve_forever,daemon=True)
        cls.thread.start()
        cls.url=f'http://127.0.0.1:{cls.httpd.server_address[1]}'
    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown();cls.httpd.server_close();cls.thread.join(2)
    def setUp(self): FakeVoiceHandler.calls.clear()
    def test_accepts_only_loopback_and_fixed_transport(self):
        for url in ('https://example.com','http://example.com','http://127.0.0.1:3900/path',
                    'http://user@127.0.0.1:3900','file:///etc/passwd','http://localhost:3900@evil.com'):
            with self.subTest(url=url), self.assertRaises(ValueError):self.VoiceStudioAdapter(url)
        self.assertEqual(self.VoiceStudioAdapter(self.url).url,self.url)
    def test_discovers_server_capabilities_and_voices(self):
        client=self.VoiceStudioAdapter(self.url)
        status=client.status()
        self.assertTrue(status['available'])
        self.assertTrue(status['streaming'])
        self.assertEqual(status['voices'],['default','voice-example'])
        self.assertEqual(client.websocket_upstream,f'ws://127.0.0.1:{self.httpd.server_address[1]}/v1/audio/transcriptions/stream')
    def test_rejects_wrong_capability_protocol(self):
        client=self.VoiceStudioAdapter(self.url)
        with patch.object(client,'_json_get',return_value={'protocol':'other','service':'bad'}):
            with self.assertRaises(ValueError):client.capabilities()
    def test_generates_wav_only_from_bounded_text(self):
        client=self.VoiceStudioAdapter(self.url)
        blob=client.speak('Explain your KV cache design','default')
        self.assertTrue(blob.startswith(b'RIFF'))
        self.assertEqual(FakeVoiceHandler.calls[-1][0],'/v1/audio/speech')
        payload=json.loads(FakeVoiceHandler.calls[-1][1]);self.assertEqual(payload['voice'],'default')
        self.assertEqual(payload['response_format'],'wav')
        for bad in ('',' '*6,'x'*4097):
            with self.assertRaises(ValueError):client.speak(bad)
    def test_batch_stt_uses_multipart_only_on_explicit_recording(self):
        client=self.VoiceStudioAdapter(self.url)
        self.assertEqual(client.transcribe(b'webm-sample', 'audio/webm'), 'VoiceStudio recognized answer')
        p,body,ctype=FakeVoiceHandler.calls[-1]
        self.assertEqual(p,'/v1/audio/transcriptions');self.assertIn('multipart/form-data',ctype)
        self.assertIn(b'webm-sample',body)
        with self.assertRaises(ValueError):client.transcribe(b'')
        with self.assertRaises(ValueError):client.transcribe(b'x'*20_971_521)
    def test_unavailable_returns_safe_status_not_a_success(self):
        client=self.VoiceStudioAdapter('http://127.0.0.1:1')
        status=client.status()
        self.assertFalse(status['available']);self.assertFalse(status['streaming'])
        self.assertNotIn('Traceback',status.get('detail',''))

class StudioBridgeHttpTests(unittest.TestCase):
    def setUp(self):
        import interview_studio
        self.module=interview_studio
        class R:
            def availability(self):return []
            def generate(self,prompt,provider):return {'question':'Explain cache','assessment':''}
        self.state=interview_studio.StudioState(R(),speech=None,token='local-test')
        self.state.voicestudio=type('Fake',(),{'status':lambda s:{'available':True,'streaming':True,'voices':['default']},
             'speak':lambda s,text,voice=b'default':b'RIFF'+b'\x00'*24,
             'transcribe':lambda s,raw,kind:'hello from voicestudio'})()
        self.server=interview_studio.make_server(self.state,0)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True,kwargs={'poll_interval':.02});self.thread.start()
        self.url=f'127.0.0.1:{self.server.server_address[1]}'
    def tearDown(self):self.server.shutdown();self.server.server_close();self.thread.join(2)
    def call(self,method,path,payload=None,content_type='application/json'):
        import http.client
        c=http.client.HTTPConnection('127.0.0.1',self.server.server_address[1],timeout=4)
        headers={'Authorization':'Bearer local-test','Origin':'http://'+self.url,'Content-Type':content_type}
        c.request(method,path,body=payload,headers=headers);r=c.getresponse();body=r.read();status=r.status;ctype=r.getheader('Content-Type');c.close()
        try:body=json.loads(body)
        except Exception:pass
        return status,body,ctype
    def test_status_endpoint_is_private_and_side_effect_free(self):
        s,data,_=self.call('GET','/api/voicestudio/status')
        self.assertEqual(s,200);self.assertTrue(data['available']);self.assertFalse(data['streaming'])
        self.assertIsNone(data['relay_url'])
    def test_tts_rejects_unsanctioned_text_and_wrong_turn(self):
        payload=json.dumps({'question_id':'q999','text':'malicious TTS'}).encode()
        self.assertEqual(self.call('POST','/api/voicestudio/speak',payload)[0],409)
    def test_tts_speaks_only_matching_active_spoken_question(self):
        self.state.interview.status='active'
        self.state.interview.current_question={'id':'q123','kind':'voice','question':'Explain KV compression'}
        payload=json.dumps({'question_id':'q123','text':'Explain KV compression','voice':'default'}).encode()
        status,voice,mime=self.call('POST','/api/voicestudio/speak',payload)
        self.assertEqual(status,200);self.assertEqual(mime,'audio/wav')
        self.assertTrue(voice.startswith(b'RIFF'))
        self.state.interview.current_question['kind']='code'
        self.assertEqual(self.call('POST','/api/voicestudio/speak',payload)[0],409)

    def test_relay_csp_allows_only_verified_loopback_port(self):
        self.state.voicestudio_relay=type('FakeRelay',(),{'url':'ws://127.0.0.1:43219/stream'})()
        import http.client
        c=http.client.HTTPConnection('127.0.0.1',self.server.server_address[1],timeout=4)
        c.request('GET','/',headers={'Authorization':'Bearer local-test','Origin':'http://'+self.url})
        response=c.getresponse();csp=response.getheader('Content-Security-Policy');response.read();c.close()
        self.assertEqual(response.status,200)
        self.assertIn("connect-src 'self' ws://127.0.0.1:43219",csp)
        self.assertNotIn('ws://0.0.0.0',csp)

    def test_batch_voice_backend_optin_does_not_require_local_whisper(self):
        status,data,_=self.call('POST','/api/transcribe?backend=voicestudio',b'FAKE_WEBM','audio/webm')
        self.assertEqual(status,200);self.assertEqual(data['raw_text'],'hello from voicestudio')

if __name__=='__main__':unittest.main()

class SpeechRelayTests(unittest.TestCase):
    """Fake upstream VoiceStudio WS stream; no real mic, no app installation."""
    def test_stream_session_requires_private_token_and_question(self):
        import asyncio
        from websockets.asyncio.client import connect
        from voicestudio_relay import VoiceStudioRelay
        from interview_studio import StudioState, make_server
        class Backend:
            websocket_upstream='ws://127.0.0.1:1/v1/audio/transcriptions/stream'
        class Router:
            def availability(self):return []
            def generate(self,prompt,provider):return {'question':'Explain attention','assessment':''}
        state=StudioState(Router(),token='test-relay-token',voicestudio=Backend())
        server=make_server(state,0)
        relay=VoiceStudioRelay(state,Backend())
        relay.start()
        async def probe():
            # Cross-origin WS clients are rejected before any bearer token is accepted.
            from websockets.exceptions import InvalidStatus
            with self.assertRaises(InvalidStatus):
                async with connect(relay.url,origin='https://attacker.invalid',proxy=None) as ws:pass
            async with connect(relay.url,origin=state.origin,proxy=None) as ws:
                await ws.send(json.dumps({'type':'start','token':'wrong','question_id':'q001'}))
                response=json.loads(await ws.recv())
                self.assertEqual(response['type'],'error')
            async with connect(relay.url,origin=state.origin,proxy=None) as ws:
                await ws.send(json.dumps({'type':'start','token':'test-relay-token','question_id':'q001'}))
                response=json.loads(await ws.recv())
                self.assertEqual(response['type'],'error','no active question may record')
        try:asyncio.run(probe())
        finally:relay.stop();server.server_close()

    def test_stream_proxy_reports_partials_only_final_summary(self):
        import asyncio
        from websockets.asyncio.server import serve
        from websockets.asyncio.client import connect
        from voicestudio_relay import VoiceStudioRelay
        from interview_studio import StudioState, make_server
        class Router:
            def availability(self):return []
            def generate(self,prompt,provider):return {'question':'Explain attention','assessment':''}
        state=StudioState(Router(),token='rel-token')
        state.interview.status='active'
        state.interview.current_question={'id':'q999','kind':'voice','question':'Describe causal attention.'}
        server=make_server(state,0)
        async def scenario():
            data=[]
            async def fake_vs(ws):
                await ws.send(json.dumps({'type':'session.started','session_id':'vs-1'}))
                while True:
                    message=await ws.recv()
                    if isinstance(message, bytes):
                        data.append(message)
                        await ws.send(json.dumps({'type':'partial','text':'prefix','session_id':'vs-1'}))
                        await ws.send(json.dumps({'type':'final','final_kind':'utterance','text':'partial utterance','session_id':'vs-1'}))
                    elif json.loads(message).get('type')=='input_audio.end':
                        await ws.send(json.dumps({'type':'final','final_kind':'summary','text':'FINAL VERIFIED IN FIXTURE','session_id':'vs-1'}))
                        break
            async with serve(fake_vs,'127.0.0.1',0) as upstream:
                port=upstream.sockets[0].getsockname()[1]
                class Backend: websocket_upstream=f'ws://127.0.0.1:{port}/v1/audio/transcriptions/stream'
                relay=VoiceStudioRelay(state,Backend())
                relay.start()
                try:
                    async with connect(relay.url,origin=state.origin,proxy=None) as ws:
                        await ws.send(json.dumps({'type':'start','token':'rel-token','question_id':'q999'}))
                        self.assertEqual(json.loads(await ws.recv())['type'],'ready')
                        # A second local tab cannot start a parallel candidate stream.
                        async with connect(relay.url,origin=state.origin,proxy=None) as duplicate:
                            await duplicate.send(json.dumps({'type':'start','token':'rel-token','question_id':'q999'}))
                            duplicate_reply=json.loads(await asyncio.wait_for(duplicate.recv(),3))
                            self.assertEqual(duplicate_reply['type'],'error')
                        await ws.send(b'WEBM CHUNK')
                        found=[]
                        for _ in range(3):
                            found.append(json.loads(await asyncio.wait_for(ws.recv(),3)))
                            if found[-1]['type']=='final' and found[-1].get('final_kind')=='utterance':break
                        self.assertTrue(any(x['type']=='partial' for x in found))
                        self.assertTrue(any(x.get('final_kind')=='utterance' for x in found))
                        await ws.send(json.dumps({'type':'input_audio.end'}))
                        completed=json.loads(await asyncio.wait_for(ws.recv(),3))
                        self.assertEqual(completed['final_kind'],'summary')
                        self.assertEqual(completed['text'],'FINAL VERIFIED IN FIXTURE')
                finally:relay.stop()
            self.assertEqual(data,[b'WEBM CHUNK'])
        try:asyncio.run(scenario())
        finally:server.server_close()
