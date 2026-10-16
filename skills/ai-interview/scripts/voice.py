#!/usr/bin/env python3
"""Codex-callable local speech bridge. No API keys, automatic recording or shell eval."""
from __future__ import annotations

import argparse
from collections import OrderedDict
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlsplit
from urllib.request import Request, ProxyHandler, HTTPRedirectHandler, build_opener
import uuid
import webbrowser

from mic_stt import AppState, Handler, ThreadingHTTPServer, atomic_write, now, MAX_TEXT, MAX_JSON_BYTES, MAX_AUDIO_BYTES, MAX_DRAFT_AGE

VERSION = '0.2.0'
ROOT = Path(__file__).resolve().parent
ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}\Z')


class BridgeState(AppState):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state_lock = threading.RLock()
        self.session_id = uuid.uuid4().hex
        self.question = None
        self.questions = OrderedDict()
        self.answers: dict[str, dict[str, Any]] = {}
        self.stopped = False

    def set_question(self, payload):
        if not isinstance(payload, dict):
            raise ValueError('Question must be a JSON object.')
        qid, text = payload.get('question_id'), payload.get('text')
        if not isinstance(qid, str) or not ID.fullmatch(qid):
            raise ValueError('question_id must be 1-80 ASCII letters, digits, hyphens or underscores.')
        if not isinstance(text, str) or not text.strip() or len(text) > 20_000 or '\x00' in text:
            raise ValueError('Question text is empty or too long.')
        with self.state_lock:
            if self.stopped:
                raise ValueError('Session is stopped.')
            if qid in self.questions:
                if self.question['question_id'] == qid and self.question['text'] == text:
                    return {'status':'asking', 'question':self.question}
                raise ValueError('Do not reuse or silently edit a question ID; use a new ID.')
            if len(self.questions) >= 1000:
                raise ValueError('Session question limit reached; stop this session.')
            if self.question and self.question['question_id'] not in self.answers and payload.get('replace_pending') is not True:
                raise ValueError('Current question is unanswered. Replacement requires an explicit skip.')
            self.question = {'question_id':qid, 'text':text, 'created_at':now()}
            self.questions[qid] = self.question
            return {'status':'asking', 'question':self.question}

    def save(self, payload):
        if not isinstance(payload, dict):
            raise ValueError('Expected a JSON object.')
        did, text = payload.get('draft_id'), payload.get('text')
        if not isinstance(did, str) or not isinstance(text, str):
            raise ValueError('Missing draft_id or confirmed text.')
        text = text.strip()
        if not text or len(text) > MAX_TEXT or '\x00' in text:
            raise ValueError('Confirmed text is empty, too long or invalid.')
        with self.state_lock:
            entry = self.drafts.get(did)
            if not entry or time.monotonic() - entry['created'] > MAX_DRAFT_AGE:
                raise KeyError('Draft expired. Record again or copy your text.')
            qid = entry['result'].get('question_id')
            if self.stopped or not self.question or qid != self.question['question_id']:
                raise KeyError('This draft belongs to an older question; it cannot answer the current one.')
            previous = self.answers.get(qid)
            if previous and previous['draft_id'] == did and previous['confirmed_text'] == text:
                return previous['receipt']
            revision = (previous['revision'] if previous else 0) + 1
            # Text files are created only following the candidate's Confirm action.
            self.output_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
            stem = f'{qid}-r{revision}-{uuid.uuid4().hex}'
            txt, js = self.output_dir/(stem+'.txt'), self.output_dir/(stem+'.json')
            receipt = {'text_path':str(txt), 'json_path':str(js),
                       'latest_path':str(self.output_dir/'latest.txt'),
                       'question_id':qid, 'draft_id':did, 'revision':revision}
            record = {**entry['result'], 'record_type':'ai-interview-voice-answer-v1',
                      'session_id':self.session_id, 'question_id':qid, 'revision':revision,
                      'confirmed_text':text, 'confirmed_at':now(), 'confirmed_by':'user',
                      'raw_transcript_is_unverified':True, 'audio_persisted_by_app':False,
                      'model':self.model_name, 'receipt':receipt}
            atomic_write(txt, text+'\n')
            atomic_write(js, json.dumps(record, ensure_ascii=False, indent=2)+'\n')
            atomic_write(self.output_dir/'latest.txt', text+'\n')
            self.answers[qid] = record
            return receipt

    def get_answer(self, qid, after):
        if not isinstance(qid, str) or not ID.fullmatch(qid) or after < 0:
            raise ValueError('Invalid question_id or revision.')
        with self.state_lock:
            if qid not in self.questions:
                raise ValueError('Unknown question ID.')
            answer = self.answers.get(qid)
            if answer and answer['revision'] > after:
                return {'status':'ready', 'answer':answer}
            return {'status':'waiting', 'question_id':qid, 'after_revision':after}


class BridgeHandler(Handler):
    def do_GET(self):
        parsed = urlsplit(self.path)
        if parsed.path not in ('/api/question','/api/answer','/api/health'):
            return super().do_GET()
        if not self.authorized(True):
            return
        try:
            if parsed.path == '/api/question':
                with self.state.state_lock:
                    self.json(200, {'question':self.state.question, 'stopped':self.state.stopped})
            elif parsed.path == '/api/health':
                self.json(200, {'version':VERSION, 'mode':'local-only', 'agent_mode':True,
                    'session_id':self.state.session_id, 'model':self.state.model_name,
                    'max_seconds':180, 'max_audio_bytes':MAX_AUDIO_BYTES,
                    'output_dir':str(self.state.output_dir)})
            else:
                qs = parse_qs(parsed.query)
                self.json(200, self.state.get_answer(qs.get('question_id',[''])[0], int(qs.get('after_revision',['0'])[0])))
        except (ValueError, TypeError) as e:
            self.json(400, {'error':str(e)})

    def do_POST(self):
        parsed = urlsplit(self.path)
        if parsed.path not in ('/api/question','/api/shutdown','/api/transcribe'):
            return super().do_POST()
        if not self.authorized(True):
            return
        if parsed.path == '/api/shutdown':
            self.state.stopped = True
            self.json(200, {'status':'stopped', 'note':'Close the browser tab to release any active microphone immediately.'})
            threading.Thread(target=self.server.shutdown, daemon=True).start()
            return
        if parsed.path == '/api/question':
            if not self.headers.get('Content-Type','').startswith('application/json'):
                self.json(415, {'error':'Expected JSON.'}); return
            body = self.read_body(MAX_JSON_BYTES)
            if body is None: return
            try:
                self.json(200, self.state.set_question(json.loads(body)))
            except (ValueError, UnicodeDecodeError) as e:
                self.json(409, {'error':str(e)})
            return
        qid = self.headers.get('X-Question-ID', '')
        with self.state.state_lock:
            if not self.state.question or qid != self.state.question['question_id']:
                self.json(409, {'error':'Question changed or missing. Reload the current question before recording.'}); return
        if not self.headers.get('Content-Type','').lower().startswith(('audio/', 'video/webm', 'video/mp4', 'application/octet-stream')):
            self.json(415, {'error':'Expected recorded audio.'}); return
        language = parse_qs(parsed.query).get('language',['auto'])[0]
        if language not in ('auto','zh','en'):
            self.json(400, {'error':'Invalid language.'}); return
        if not self.state.transcription_lock.acquire(blocking=False):
            self.json(409, {'error':'Transcription is already running.'}); return
        try:
            body = self.read_body(MAX_AUDIO_BYTES)
            if body is None: return
            if not body: raise ValueError('Empty audio')
            result = self.state.backend.transcribe(body, None if language == 'auto' else language)
            with self.state.state_lock:
                if self.state.stopped or qid != self.state.question['question_id']:
                    self.json(409, {'error':'Question changed during transcription; result not submitted.'}); return
                self.json(200, self.state.add_draft({**result, 'question_id':qid}))
        except Exception as e:
            self.json(422, {'error':f'Local transcription failed ({type(e).__name__}); retry or use text.'})
        finally:
            self.state.transcription_lock.release()


def make_bridge_server(state, port=0):
    server = ThreadingHTTPServer(('127.0.0.1',port), BridgeHandler)
    server.daemon_threads = True
    server.state = state
    state.host = f'127.0.0.1:{server.server_address[1]}'
    state.origin = 'http://'+state.host
    return server


def write_connection(directory: Path, state: BridgeState, pid: int):
    directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    data = {'version':VERSION, 'pid':pid, 'origin':state.origin, 'token':state.token,
            'session_id':state.session_id, 'created_at':now()}
    atomic_write(directory/'connection.json', json.dumps(data)+'\n')
    return data


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError('Local bridge redirects are not allowed.')


def read_connection(directory):
    data = json.loads((Path(directory)/'connection.json').read_text(encoding='utf-8'))
    url = urlsplit(data['origin'])
    if url.scheme != 'http' or url.hostname != '127.0.0.1' or not url.port or url.username or url.password or url.path or url.query or url.fragment:
        raise ValueError('Refusing a non-loopback or malformed bridge address.')
    if not isinstance(data.get('token'),str) or not data['token']:
        raise ValueError('Missing local bridge token.')
    return data


def request(directory, method, path, payload=None):
    conn = read_connection(directory)
    if not path.startswith('/api/') or '\n' in path or '\r' in path:
        raise ValueError('Invalid bridge endpoint.')
    body = None if payload is None else json.dumps(payload, ensure_ascii=False, allow_nan=False).encode()
    req = Request(conn['origin']+path, data=body, method=method,
                  headers={'Authorization':'Bearer '+conn['token'], 'Content-Type':'application/json'})
    try:
        # Do not pass loopback requests through user/system proxy configuration.
        with build_opener(ProxyHandler({}), NoRedirect()).open(req, timeout=5) as response:
            raw = response.read(2*1024*1024+1)
            if len(raw)>2*1024*1024: raise ValueError('Oversized bridge reply.')
            return json.loads(raw)
    except HTTPError as e:
        message = json.loads(e.read(4096)).get('error','Request rejected')
        raise RuntimeError(message) from None
    except URLError:
        raise RuntimeError('Local speech service is unavailable. Do not grade silence; check status or restart in a new session directory.') from None


def runtime_home():
    return Path(os.environ.get('AI_INTERVIEW_VOICE_HOME', str(Path.home()/'.cache/ai-interview-voice'))).expanduser()


def runtime_python():
    p = runtime_home()/'venv'/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    return str(p) if p.is_file() else sys.executable


def doctor():
    exe=runtime_python()
    probe=subprocess.run([exe,'-c',"import importlib.util,json,sys; print(json.dumps({'python':sys.version.split()[0],'faster_whisper_installed':importlib.util.find_spec('faster_whisper') is not None}))"], capture_output=True,text=True,timeout=10)
    if probe.returncode: raise RuntimeError('Python runtime is not usable.')
    return {'status':'checked','python_executable':exe,'runtime_home':str(runtime_home()),
            **json.loads(probe.stdout), 'microphone_tested':False,'model_inference_tested':False,
            'note':'Dependency discovery only; start verifies local model loading. Browser permission is still required.'}


def setup(args):
    if not args.allow_download:
        raise ValueError('Setup downloads Python dependencies and model weights. Explicit --allow-download consent is required.')
    home=runtime_home(); home.mkdir(parents=True,exist_ok=True,mode=0o700)
    venv=home/'venv'
    if not venv.exists():
        subprocess.run([sys.executable,'-m','venv',str(venv)],check=True,stdout=sys.stderr)
    exe=runtime_python()
    subprocess.run([exe,'-m','pip','install','-r',str(ROOT/'requirements-voice.txt')],check=True,stdout=sys.stderr)
    subprocess.run([exe,str(ROOT/'mic_stt.py'),'download','--model',args.model],check=True,stdout=sys.stderr)
    return {'status':'installed','python_executable':exe,'model':args.model,'microphone_opened':False}


def start(args):
    directory=args.session_dir.expanduser().resolve()
    if directory.exists() and any(directory.iterdir()):
        raise ValueError('Session directory is not empty. Use status for a live session, or a NEW directory after a crash; do not overwrite records.')
    directory.mkdir(parents=True,exist_ok=True,mode=0o700)
    lock=directory/'start.lock'
    with lock.open('x') as f: f.write('owned startup\n')
    cmd=[runtime_python(),str(Path(__file__).resolve()),'_serve','--session-dir',str(directory),
         '--model',args.model,'--compute-type',args.compute_type]
    opts={'start_new_session':True} if os.name!='nt' else {'creationflags':subprocess.CREATE_NEW_PROCESS_GROUP}
    ready=False
    with (directory/'server.log').open('a',encoding='utf-8') as log:
        process=subprocess.Popen(cmd,stdin=subprocess.DEVNULL,stdout=log,stderr=log,**opts)
    try:
        end=time.monotonic()+60
        while time.monotonic()<end:
            if process.poll() is not None:
                raise RuntimeError('Local model service failed to start. Read session server.log; run doctor/setup or use --compute-type float32. No microphone was opened.')
            if (directory/'connection.json').is_file():
                request(directory,'GET','/api/health'); ready=True; break
            time.sleep(.2)
        if not ready: raise RuntimeError('Model startup timeout. Inspect server.log; this attempt was stopped.')
        conn=read_connection(directory)
        url=conn['origin']+'/#token='+conn['token']
        opened=False if args.no_browser else bool(webbrowser.open(url))
        return {'status':'started','session_dir':str(directory),'url':url,'browser_opened':opened,
                'microphone_opened':False,'note':'Open the private link locally. Record only after the candidate clicks Record. Never publish this URL.'}
    finally:
        if not ready and process.poll() is None:
            process.terminate()
            try: process.wait(5)
            except subprocess.TimeoutExpired: process.kill(); process.wait(5)


def serve(args):
    from speech_backend import LocalWhisper
    backend=LocalWhisper(args.model,compute_type=args.compute_type)
    state=BridgeState(backend,args.session_dir/'answers',model_name=args.model)
    server=make_bridge_server(state)
    write_connection(args.session_dir,state,os.getpid())
    # A lease bounds an accidentally abandoned local process. This is not the interview clock.
    lease=threading.Timer(4*60*60,server.shutdown); lease.daemon=True; lease.start()
    try: server.serve_forever()
    finally: lease.cancel(); state.stopped=True; server.server_close()
    return {'status':'stopped'}


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('doctor',help='Check local runtime without opening a microphone.')
    p=sub.add_parser('setup',help='Install speech dependencies and explicitly download model weights.')
    p.add_argument('--allow-download',action='store_true'); p.add_argument('--model',default='base')
    for command in ('start','_serve','status','ask','wait','stop'):
        p=sub.add_parser(command)
        p.add_argument('--session-dir',type=Path,required=True)
        if command in ('start','_serve'):
            p.add_argument('--model',default='base')
            p.add_argument('--compute-type',choices=('int8','float32'),default='int8')
            p.add_argument('--no-browser',action='store_true')
        if command=='ask':
            p.add_argument('--question-id',required=True)
            g=p.add_mutually_exclusive_group(required=True)
            g.add_argument('--text'); g.add_argument('--text-file',type=Path)
            p.add_argument('--replace-pending',action='store_true',help='Only after an explicit candidate skip.')
        if command=='wait':
            p.add_argument('--question-id',required=True)
            p.add_argument('--after-revision',type=int,default=0)
            p.add_argument('--timeout',type=float,default=20)
    args=parser.parse_args(argv)
    try:
        if args.command=='doctor': result=doctor()
        elif args.command=='setup': result=setup(args)
        elif args.command=='start': result=start(args)
        elif args.command=='_serve': result=serve(args)
        elif args.command=='status': result={'status':'running',**request(args.session_dir,'GET','/api/health')}
        elif args.command=='stop': result=request(args.session_dir,'POST','/api/shutdown',{})
        elif args.command=='ask':
            text=args.text if args.text is not None else args.text_file.read_text(encoding='utf-8')
            result=request(args.session_dir,'POST','/api/question',{'question_id':args.question_id,'text':text,'replace_pending':args.replace_pending})
        else:
            if not math.isfinite(args.timeout) or not 0 <= args.timeout <= 300 or args.after_revision < 0:
                raise ValueError('timeout must be finite and between 0 and 300 seconds; revision must be nonnegative.')
            query=urlencode({'question_id':args.question_id,'after_revision':args.after_revision})
            end=time.monotonic()+args.timeout
            while True:
                result=request(args.session_dir,'GET','/api/answer?'+query)
                if result['status']=='ready' or time.monotonic()>=end: break
                time.sleep(min(.25,max(0,end-time.monotonic())))
        print(json.dumps(result,ensure_ascii=False,allow_nan=False)); return 0
    except (OSError,RuntimeError,ValueError,KeyError,subprocess.SubprocessError) as e:
        print(json.dumps({'status':'error','error':str(e)},ensure_ascii=False)); return 1
    except KeyboardInterrupt:
        print(json.dumps({'status':'cancelled'})); return 130

if __name__=='__main__': raise SystemExit(main())
