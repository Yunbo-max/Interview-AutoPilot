#!/usr/bin/env python3
"""Voice-first, local-only interview UI. PDF never written to disk; candidate code never executed."""
from __future__ import annotations
import argparse
from http.server import ThreadingHTTPServer
import importlib.util
import json
import os
from pathlib import Path
import secrets
import sys
import threading
from urllib.parse import urlsplit, parse_qs, urlencode
import xml.etree.ElementTree as ET
import webbrowser

from mic_stt import Handler as LocalHandler, AppState, MAX_AUDIO_BYTES
from voicestudio_adapter import VoiceStudioAdapter
from interview_core import InterviewSession, read_resume_pdf, MAX_CV_BYTES
from interview_curriculum import ROLE_PLANS, ROLE_LABELS
from interview_models import ModelRouter, PROVIDERS
from career import (CareerWorkspace, briefing_for_role, memory_brief, topic_review_due, ROLE_TAGS,
    get_public_bytes, arxiv_search_url, parse_arxiv_feed, parse_hf_daily, HF_BASE, utcnow)

ROOT = Path(__file__).resolve().parent
VERSION = '0.7.0'


class StudioState(AppState):
    def __init__(self, router=None, speech=None, token=None, workspace=None, voicestudio=None):
        super().__init__(speech, Path.home()/'.cache/ai-interview/studio-unused',
                         token=token or secrets.token_urlsafe(32), model_name='optional local Whisper')
        self.router = router or ModelRouter()
        self.speech = speech
        self.interview = InterviewSession(self.router)
        self.workspace = workspace if workspace is not None else CareerWorkspace()
        self.research_lock = threading.Lock()
        self.memory_save_lock = threading.Lock()
        self.memory_saved = None
        self.voicestudio = voicestudio
        self.voicestudio_relay = None  # Optional, bounded localhost WebSocket relay


class StudioHandler(LocalHandler):
    server_version = 'AIInterviewStudio/0.5'

    def send_bytes(self, status:int, body:bytes, content_type:str) -> None:
        """Only our verified local relay port may receive browser WS audio."""
        relay = getattr(self.state, 'voicestudio_relay', None)
        connect_src = "'self'"
        if relay and getattr(relay,'url',None):
            from urllib.parse import urlsplit as _split
            endpoint = _split(relay.url)
            if endpoint.hostname == '127.0.0.1' and endpoint.scheme == 'ws':
                connect_src += f' ws://127.0.0.1:{endpoint.port}'
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length',str(len(body)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','no-referrer')
        self.send_header('Permissions-Policy','microphone=(self), camera=(), display-capture=()')
        self.send_header('Content-Security-Policy',
             f"default-src 'self'; script-src 'self'; style-src 'self'; connect-src {connect_src}; "
             "media-src 'self' blob:; object-src 'none'; frame-ancestors 'none'; base-uri 'none'")
        self.end_headers()
        try:self.wfile.write(body)
        except (BrokenPipeError,ConnectionResetError):pass
    def do_GET(self):
        path=urlsplit(self.path).path
        if not self.authorized(path.startswith('/api/')):return
        if path=='/api/voicestudio/status':
            if self.state.voicestudio is None:
                self.json(200,{'available':False,'streaming':False,'voices':[],
                    'detail':'VoiceStudio adapter disabled; select --voicestudio to enable.'});return
            data=self.state.voicestudio.status().copy()
            if not self.state.voicestudio_relay:
                data['streaming']=False
                data['relay_url']=None
                data['note']='Streaming relay unavailable; batch STT and TTS may still work.'
            else:
                data['relay_url']=self.state.voicestudio_relay.url
            self.json(200,data);return
        if path=='/api/health':
            self.json(200,{'version':VERSION,'speech_ready':self.state.speech is not None,'audio_limit':MAX_AUDIO_BYTES,
                           'note':'Local-only HTTP server; model providers may send confirmed text externally'})
            return
        if path=='/api/evidence-summary':
            requested=parse_qs(urlsplit(self.path).query).get('role',[''])[0]
            if requested not in ROLE_TAGS:
                self.json(400,{'error':'Choose a supported role'});return
            brief=briefing_for_role(self.state.workspace,requested)
            memory=self.state.workspace.memory()
            self.json(200,{'role':requested,'recent_papers':brief.count('\nsource: '),
                 'memory_topics':len(topic_review_due(memory)),
                 'note':'Cached-only: no live internet fetch. Age of evidence is not forgetting.'})
            return
        if path=='/api/jobs':
            jobs=[{k:j.get(k) for k in ('id','title','company','location','source')} for j in self.state.workspace.jobs()[-100:]]
            self.json(200,{'jobs':jobs});return
        if path=='/api/providers':
            self.json(200,{'roles':[{'id':r,'label':ROLE_LABELS[r],'phases':p} for r,p in ROLE_PLANS.items()],
                           'providers':self.state.router.availability()})
            return
        if path=='/api/state':
            self.json(200,self.state.interview.public_state());return
        assets={'/':('index.html','text/html; charset=utf-8'),
                '/app.js':('app.js','application/javascript; charset=utf-8'),
                '/style.css':('style.css','text/css; charset=utf-8')}
        if path not in assets:self.json(404,{'error':'Not found'});return
        name,content_type=assets[path]
        self.send_bytes(200,(ROOT/'studio_web'/name).read_bytes(),content_type)

    def do_POST(self):
        if not self.authorized(True):return
        path=urlsplit(self.path).path
        if path=='/api/shutdown':
            # Private one-click launcher stops only its own authenticated localhost service.
            # Never accept a remote address or kill a PID supplied by a file.
            self.json(200,{'status':'stopping'})
            threading.Thread(target=self.server.shutdown,daemon=True).start()
            return
        if path=='/api/resume':
            if self.headers.get('Content-Type','').split(';')[0].strip().lower()!='application/pdf':
                self.json(415,{'error':'Upload a PDF file (application/pdf)'});return
            body=self.read_body(MAX_CV_BYTES)
            if body is None:return
            try:
                text=read_resume_pdf(body)
                result=self.state.interview.set_resume_text(text)
                self.json(200,result)
            except ValueError as exc:self.json(400,{'error':str(exc)})
            except RuntimeError as exc:self.json(503,{'error':str(exc)})
            return
        if path=='/api/voicestudio/speak':
            if self.state.voicestudio is None:
                self.json(503, {'error':'VoiceStudio is not enabled for this session.'});return
            if self.headers.get('Content-Type','').split(';')[0].strip().lower()!='application/json':
                self.json(415,{'error':'JSON content required'});return
            body=self.read_body(14_000)
            if body is None:return
            try:
                data=json.loads(body)
                if not isinstance(data,dict):raise ValueError('Expected JSON object')
                question_id=data.get('question_id')
                with self.state.interview.lock:
                    current=self.state.interview.current_question
                    if (self.state.interview.status!='active' or not current or
                            current.get('kind')=='code' or current.get('id')!=question_id or
                            current.get('question')!=data.get('text')):
                        raise ValueError('Only the active spoken interview question can be synthesized.')
                voice=data.get('voice','default')
                audio=self.state.voicestudio.speak(data['text'],voice)
                with self.state.interview.lock:
                    current=self.state.interview.current_question
                    if (self.state.interview.status!='active' or not current or
                            current.get('id')!=question_id):
                        raise ValueError('Question changed while voice was generating; audio discarded.')
                self.send_bytes(200,audio,'audio/wav')
            except (ValueError,TypeError,KeyError,json.JSONDecodeError) as e:
                self.json(409,{'error':str(e)})
            except (RuntimeError,OSError) as e:
                self.json(502,{'error':str(e)})
            return
        if path=='/api/transcribe':
            selected=parse_qs(urlsplit(self.path).query).get('backend',['builtin'])[0]
            if selected not in ('builtin','voicestudio'):
                self.json(400,{'error':'Unknown speech backend'});return
            if selected=='builtin' and self.state.speech is None:
                self.json(503,{'error':'Local Whisper not loaded; type your answer or enable VoiceStudio'});return
            if selected=='voicestudio' and self.state.voicestudio is None:
                self.json(503,{'error':'VoiceStudio is not enabled'});return
            mime=self.headers.get('Content-Type','').lower()
            if not mime.startswith(('audio/','video/webm','video/mp4','application/octet-stream')):
                self.json(415,{'error':'Audio content required'});return
            if not self.state.transcription_lock.acquire(blocking=False):
                self.json(409,{'error':'Another audio clip is being transcribed'});return
            hold_token=None
            try:
                body=self.read_body(MAX_AUDIO_BYTES)
                if body is None:return
                if not body: self.json(400,{'error':'Empty recording'});return
                # Modern clients bind ASR to the active question. Untrusted old/stale
                # audio cannot freeze the clock or overwrite another turn's draft.
                question_id=parse_qs(urlsplit(self.path).query).get('question_id',[None])[0]
                if question_id is not None:
                    hold_token=self.state.interview.begin_host_wait(question_id,'stt')
                    if hold_token is None:
                        self.json(409,{'error':'Speech request is not for the active question'});return
                if selected=='voicestudio':
                    text=self.state.voicestudio.transcribe(body,mime)
                    result={'raw_text':text, 'backend':'voicestudio', 'final':True}
                else:
                    decoded=self.state.speech.transcribe(body,None)
                    result={'raw_text':decoded.get('raw_text',''),
                            'duration_seconds':decoded.get('duration_seconds'), 'backend':'builtin', 'final':True}
                self.json(200,result)
            except Exception as exc:
                self.json(422,{'error':f'Speech recognition failed ({type(exc).__name__}); you may type your answer'})
            finally:
                self.state.interview.end_host_wait(hold_token)
                self.state.transcription_lock.release()
            return
        if path not in ('/api/start','/api/answer','/api/skip','/api/extend-question','/api/pause','/api/resume-session','/api/finish','/api/trends-refresh','/api/save-memory'):
            self.json(404,{'error':'Not found'});return
        if self.headers.get('Content-Type','').split(';')[0].strip().lower()!='application/json':
            self.json(415,{'error':'JSON content required'});return
        body=self.read_body(60_000)
        if body is None:return
        try:
            data=json.loads(body)
            if not isinstance(data,dict):raise ValueError('Expected a JSON object')
            interview=self.state.interview
            if path=='/api/save-memory':
                if data.get('confirm') is not True:
                    raise ValueError('Confirm saving a private memory summary')
                if interview.status!='completed' or interview.finished_review is None:
                    raise ValueError('Finish the interview before saving the summary')
                with self.state.memory_save_lock:
                    if self.state.memory_saved is None:
                        self.state.memory_saved=self.state.workspace.record_session(interview.finished_review)
                    result={'status':'saved','session_summary':self.state.memory_saved,
                            'note':'Only coverage and counts saved, not your raw transcript or CV.'}
            elif path=='/api/trends-refresh':
                role=data.get('role');source=data.get('source','arxiv')
                if role not in ROLE_TAGS or source not in ('arxiv','hf'):
                    raise ValueError('Unsupported role or research source')
                if interview.status != 'setup':
                    raise ValueError('Research refresh is only available before starting the interview')
                if not self.state.research_lock.acquire(blocking=False):
                    raise ValueError('Research refresh already in progress')
                try:
                    if source == 'arxiv':
                        url=arxiv_search_url(role,max_results=18)
                        papers=parse_arxiv_feed(get_public_bytes(url),role)
                    else:
                        url=HF_BASE+'?'+urlencode({'date':utcnow().strftime('%Y-%m-%d'),'limit':18})
                        papers=parse_hf_daily(json.loads(get_public_bytes(url)),role)
                    if not papers:
                        raise RuntimeError('No dated papers were returned. Research cache was not refreshed.')
                    count=self.state.workspace.write_papers(papers)
                    result={'status':'retrieved','source':source,'count':count,
                            'source_url':url,'retrieved_at':utcnow().isoformat(),
                            'notice':'Paper abstracts and dates only; not verified paper results.'}
                finally:
                    self.state.research_lock.release()
            elif path=='/api/start':
                role=data.get('role')
                chosen_job=''
                job_id=data.get('job_id')
                if job_id:
                    found=next((j for j in self.state.workspace.jobs() if j.get('id')==job_id),None)
                    if found is None:raise ValueError('Selected job not found in the private workspace')
                    chosen_job=f"Company: {found['company']}. Role: {found['title']}. URL: {found['url']}\n"+found['description'][:3300]
                trend=briefing_for_role(self.state.workspace,role) if data.get('use_trends') is True and role in ROLE_TAGS else ''
                history=memory_brief(self.state.workspace) if data.get('use_memory') is True else ''
                result=interview.start(role,data.get('provider'),data.get('consent') is True,
                      data.get('focus',''),data.get('language','zh'),trend_brief=trend,memory_brief=history,job_brief=chosen_job)
            elif path=='/api/answer':
                result=interview.submit(data.get('question_id'),data.get('text'),data.get('kind'),data.get('submission_id'))
            elif path=='/api/skip':
                result=interview.skip(data.get('question_id'),data.get('submission_id'))
            elif path=='/api/extend-question':
                seconds=interview.extend_question(data.get('question_id'))
                result={'status':'extended','additional_seconds':seconds,
                        'timekeeper':interview.public_state()['timekeeper']}
            elif path=='/api/pause':interview.pause();result=interview.public_state()
            elif path=='/api/resume-session':interview.resume();result=interview.public_state()
            else:result=interview.finish()
            self.json(200,result)
        except (ValueError,KeyError,TypeError) as exc:
            self.json(409,{'error':str(exc)})
        except (RuntimeError,OSError,UnicodeError,ET.ParseError) as exc:
            self.json(502,{'error':str(exc)})


class InterviewServer(ThreadingHTTPServer):
    """Run the deterministic timekeeper on the local server's service loop.

    It never calls a model; pulse is nonblocking when a turn is in flight.
    """
    def service_actions(self):
        self.state.interview.pulse()


def make_server(state:StudioState,port=0):
    server=InterviewServer(('127.0.0.1',port),StudioHandler)
    server.daemon_threads=True
    server.state=state
    state.host=f'127.0.0.1:{server.server_address[1]}'
    state.origin='http://'+state.host
    return server


def main(argv=None):
    parser=argparse.ArgumentParser(description='Local AI interview studio; requires explicit microphone permission')
    sub=parser.add_subparsers(dest='action',required=True)
    d=sub.add_parser('doctor')
    d.add_argument('--voicestudio', action='store_true', help='Check optional local VoiceStudio service')
    d.add_argument('--voicestudio-url',default='http://127.0.0.1:3900')
    p=sub.add_parser('download-model');p.add_argument('--allow-download',action='store_true');p.add_argument('--model',default='base')
    p=sub.add_parser('serve');p.add_argument('--port',type=int,default=0)
    p.add_argument('--model',default='base');p.add_argument('--without-stt',action='store_true')
    p.add_argument('--voicestudio',action='store_true',help='Enable optional external local VoiceStudio service (never installs it)')
    p.add_argument('--voicestudio-url',default='http://127.0.0.1:3900',help='Only http://127.0.0.1:<port> permitted')
    p.add_argument('--no-browser',action='store_true');p.add_argument('--compute-type',choices=('int8','float32'),default='int8')
    args=parser.parse_args(argv)
    if args.action=='doctor':
        data={'python':sys.version.split()[0],'pypdf_installed':importlib.util.find_spec('pypdf') is not None,
            'faster_whisper_installed':importlib.util.find_spec('faster_whisper') is not None,
            'providers':ModelRouter().availability(),'microphone_tested':False}
        if args.voicestudio:
            data['voicestudio']=VoiceStudioAdapter(args.voicestudio_url).status()
            data['voicestudio_websockets_installed']=importlib.util.find_spec('websockets') is not None
        print(json.dumps(data,ensure_ascii=False,indent=2))
        return 0
    if args.action=='download-model':
        if not args.allow_download:
            print('Explicit --allow-download required for model weights',file=sys.stderr);return 1
        from speech_backend import download
        print(download(args.model));return 0
    if not 0<=args.port<=65535:parser.error('port must be 0-65535')
    speech=None
    if not args.without_stt:
        try:
            from speech_backend import LocalWhisper
            speech=LocalWhisper(args.model,compute_type=args.compute_type)
        except (RuntimeError,ImportError,ValueError,OSError) as exc:
            print('Speech model unavailable; typed answers remain available. Use doctor/download-model. '+str(type(exc).__name__),file=sys.stderr)
    voicestudio=VoiceStudioAdapter(args.voicestudio_url) if args.voicestudio else None
    state=StudioState(speech=speech,voicestudio=voicestudio)
    server=make_server(state,args.port)
    if voicestudio is not None:
        speech_status=voicestudio.status()
        if speech_status['available'] and speech_status['streaming']:
            try:
                from voicestudio_relay import VoiceStudioRelay
                relay=VoiceStudioRelay(state,voicestudio)
                relay.start()
                state.voicestudio_relay=relay
                print('VoiceStudio streaming relay ready on loopback.', file=sys.stderr)
            except (ImportError,RuntimeError,OSError) as exc:
                print('Streaming relay unavailable; VoiceStudio batch STT/TTS can still work. '
                      +type(exc).__name__,file=sys.stderr)
        elif not speech_status['available']:
            print('VoiceStudio not reachable. Start its backend, then restart AI-Interview to enable it.',file=sys.stderr)
    url=state.origin+'/#token='+state.token
    print('Local private studio URL (never publish): '+url,flush=True)
    print('PDF and interview content stay in process memory; model calls send confirmed text to the selected provider after consent.',flush=True)
    if not args.no_browser:webbrowser.open(url)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:
        server.server_close()
        if state.voicestudio_relay:state.voicestudio_relay.stop()
    return 0

if __name__=='__main__':raise SystemExit(main())
