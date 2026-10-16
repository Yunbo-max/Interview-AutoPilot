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
from urllib.parse import urlsplit
import webbrowser

from mic_stt import Handler as LocalHandler, AppState, MAX_AUDIO_BYTES
from interview_core import InterviewSession, read_resume_pdf, MAX_CV_BYTES
from interview_curriculum import ROLE_PLANS, ROLE_LABELS
from interview_models import ModelRouter, PROVIDERS

ROOT = Path(__file__).resolve().parent
VERSION = '0.3.0'


class StudioState(AppState):
    def __init__(self, router=None, speech=None, token=None):
        super().__init__(speech, Path.home()/'.cache/ai-interview/studio-unused',
                         token=token or secrets.token_urlsafe(32), model_name='optional local Whisper')
        self.router = router or ModelRouter()
        self.speech = speech
        self.interview = InterviewSession(self.router)


class StudioHandler(LocalHandler):
    server_version = 'AIInterviewStudio/0.3'
    def do_GET(self):
        path=urlsplit(self.path).path
        if not self.authorized(path.startswith('/api/')):return
        if path=='/api/health':
            self.json(200,{'version':VERSION,'speech_ready':self.state.speech is not None,'audio_limit':MAX_AUDIO_BYTES,
                           'note':'Local-only HTTP server; model providers may send confirmed text externally'})
            return
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
        if path=='/api/transcribe':
            if self.state.speech is None:
                self.json(503,{'error':'Speech model not loaded; type your answer or install local faster-whisper'});return
            if not self.headers.get('Content-Type','').lower().startswith(('audio/','video/webm','video/mp4','application/octet-stream')):
                self.json(415,{'error':'Audio content required'});return
            if not self.state.transcription_lock.acquire(blocking=False):
                self.json(409,{'error':'Another audio clip is being transcribed'});return
            try:
                body=self.read_body(MAX_AUDIO_BYTES)
                if body is None:return
                if not body: self.json(400,{'error':'Empty recording'});return
                result=self.state.speech.transcribe(body,None)
                self.json(200,{'raw_text':result.get('raw_text',''),'duration_seconds':result.get('duration_seconds')})
            except Exception as exc:
                self.json(422,{'error':f'Local audio decoding failed ({type(exc).__name__}); you may type your answer'})
            finally:self.state.transcription_lock.release()
            return
        if path not in ('/api/start','/api/answer','/api/pause','/api/resume-session','/api/finish'):
            self.json(404,{'error':'Not found'});return
        if self.headers.get('Content-Type','').split(';')[0].strip().lower()!='application/json':
            self.json(415,{'error':'JSON content required'});return
        body=self.read_body(60_000)
        if body is None:return
        try:
            data=json.loads(body)
            if not isinstance(data,dict):raise ValueError('Expected a JSON object')
            interview=self.state.interview
            if path=='/api/start':
                result=interview.start(data.get('role'),data.get('provider'),data.get('consent') is True,data.get('focus',''),data.get('language','zh'))
            elif path=='/api/answer':
                result=interview.submit(data.get('question_id'),data.get('text'),data.get('kind'),data.get('submission_id'))
            elif path=='/api/pause':interview.pause();result=interview.public_state()
            elif path=='/api/resume-session':interview.resume();result=interview.public_state()
            else:result=interview.finish()
            self.json(200,result)
        except (ValueError,KeyError,TypeError) as exc:
            self.json(409,{'error':str(exc)})
        except RuntimeError as exc:
            self.json(502,{'error':str(exc)})


def make_server(state:StudioState,port=0):
    server=ThreadingHTTPServer(('127.0.0.1',port),StudioHandler)
    server.daemon_threads=True
    server.state=state
    state.host=f'127.0.0.1:{server.server_address[1]}'
    state.origin='http://'+state.host
    return server


def main(argv=None):
    parser=argparse.ArgumentParser(description='Local AI interview studio; requires explicit microphone permission')
    sub=parser.add_subparsers(dest='action',required=True)
    sub.add_parser('doctor')
    p=sub.add_parser('download-model');p.add_argument('--allow-download',action='store_true');p.add_argument('--model',default='base')
    p=sub.add_parser('serve');p.add_argument('--port',type=int,default=0)
    p.add_argument('--model',default='base');p.add_argument('--without-stt',action='store_true')
    p.add_argument('--no-browser',action='store_true');p.add_argument('--compute-type',choices=('int8','float32'),default='int8')
    args=parser.parse_args(argv)
    if args.action=='doctor':
        print(json.dumps({'python':sys.version.split()[0],'pypdf_installed':importlib.util.find_spec('pypdf') is not None,
            'faster_whisper_installed':importlib.util.find_spec('faster_whisper') is not None,
            'providers':ModelRouter().availability(),'microphone_tested':False},ensure_ascii=False,indent=2))
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
    state=StudioState(speech=speech)
    server=make_server(state,args.port)
    url=state.origin+'/#token='+state.token
    print('Local private studio URL (never publish): '+url,flush=True)
    print('PDF and interview content stay in process memory; model calls send confirmed text to the selected provider after consent.',flush=True)
    if not args.no_browser:webbrowser.open(url)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
    return 0

if __name__=='__main__':raise SystemExit(main())
