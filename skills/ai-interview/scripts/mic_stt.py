#!/usr/bin/env python3
"""Consent-first local microphone transcription; not a Codex auto-submitter.

python mic_stt.py download --model base
python mic_stt.py serve --model base --output-dir ~/Interview-Workspace/voice-inbox
"""
from __future__ import annotations

import argparse
from collections import OrderedDict
from datetime import datetime, timezone
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
import socket
import sys
import tempfile
import threading
import time
from typing import Any
from urllib.parse import parse_qs, urlsplit
import uuid
import webbrowser

VERSION = '0.2.0'
ROOT = Path(__file__).resolve().parent
MAX_AUDIO_BYTES = 20 * 1024 * 1024
MAX_JSON_BYTES = 256 * 1024
MAX_TEXT = 100_000
MAX_DRAFTS = 12
MAX_DRAFT_AGE = 30 * 60


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def atomic_write(path: Path, text: str) -> None:
    """Write without following an existing file symlink; restrictive POSIX mode."""
    fd, tmp = tempfile.mkstemp(prefix='.stt-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


class AppState:
    def __init__(self, backend: Any, output_dir: Path, token: str | None = None,
                 model_name: str = 'base'):
        self.backend = backend
        self.output_dir = output_dir.expanduser().resolve()
        self.token = token or secrets.token_urlsafe(32)
        self.model_name = model_name
        self.transcription_lock = threading.Lock()
        self.state_lock = threading.Lock()
        self.drafts: OrderedDict[str, dict[str, Any]] = OrderedDict()
        self.origin = ''
        self.host = ''

    def add_draft(self, result: dict[str, Any]) -> dict[str, Any]:
        with self.state_lock:
            draft = {**result, 'draft_id':uuid.uuid4().hex, 'created_at':now()}
            self.drafts[draft['draft_id']] = {
                'result':draft, 'created':time.monotonic(), 'saved':{}}
            while len(self.drafts) > MAX_DRAFTS:
                self.drafts.popitem(last=False)
            return draft

    def save(self, payload: Any) -> dict[str, str]:
        if not isinstance(payload, dict):
            raise ValueError('保存请求必须是 JSON 对象。')
        draft_id, text = payload.get('draft_id'), payload.get('text')
        if not isinstance(draft_id, str) or not isinstance(text, str):
            raise ValueError('缺少有效的 draft_id 或 text。')
        text = text.strip()
        if not text or len(text) > MAX_TEXT or '\x00' in text:
            raise ValueError('确认文本为空、过长或含不支持字符。')
        with self.state_lock:
            entry = self.drafts.get(draft_id)
            if entry is None or time.monotonic() - entry['created'] > MAX_DRAFT_AGE:
                raise KeyError('转写草稿已过期；请复制文字或重新转写后再保存。')
            digest = hashlib.sha256(text.encode()).hexdigest()
            if digest in entry['saved']:
                return entry['saved'][digest]
            # Only the explicit Save action creates the output directory.
            self.output_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
            suffix = uuid.uuid4().hex
            stem = f'turn-{datetime.now(timezone.utc):%Y%m%dT%H%M%SZ}-{suffix}'
            txt_path, json_path = self.output_dir / (stem+'.txt'), self.output_dir / (stem+'.json')
            record = {**entry['result'], 'confirmed_text':text, 'confirmed_at':now(),
                      'confirmed_by':'user', 'record_type':'mic-stt-export-v1',
                      'model':self.model_name, 'audio_persisted_by_app':False,
                      'raw_transcript_is_unverified':True,
                      'timing_note':'Segment times are ASR estimates, not speaking-style measurements.'}
            atomic_write(txt_path, text+'\n')
            atomic_write(json_path, json.dumps(record, ensure_ascii=False, indent=2)+'\n')
            atomic_write(self.output_dir / 'latest.txt', text+'\n')
            receipt = {'text_path':str(txt_path), 'json_path':str(json_path),
                       'latest_path':str(self.output_dir / 'latest.txt')}
            entry['saved'][digest] = receipt
            return receipt


class Handler(BaseHTTPRequestHandler):
    server_version = 'LocalMicSTT/0.2'
    def log_message(self, *args):
        # Do not put transcript content, access tokens or URLs in access logs.
        pass

    @property
    def state(self) -> AppState:
        return self.server.state

    def send_bytes(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Permissions-Policy', 'microphone=(self), camera=(), display-capture=()')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; media-src 'self' blob:; object-src 'none'; frame-ancestors 'none'; base-uri 'none'")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def json(self, status: int, value: Any) -> None:
        self.send_bytes(status, json.dumps(value, ensure_ascii=False, allow_nan=False).encode(), 'application/json; charset=utf-8')

    def authorized(self, api: bool) -> bool:
        if self.headers.get('Host') != self.state.host:
            self.json(403, {'error':'Host 不匹配；请打开终端打印的本机地址。'})
            return False
        origin = self.headers.get('Origin')
        if origin is not None and origin != self.state.origin:
            self.json(403, {'error':'拒绝跨站请求。'})
            return False
        if api:
            token = self.headers.get('Authorization', '')
            if not secrets.compare_digest(token, 'Bearer '+self.state.token):
                self.json(403, {'error':'访问令牌无效；请重新打开终端打印的完整链接。'})
                return False
        return True

    def do_GET(self):
        path = urlsplit(self.path).path
        if not self.authorized(path.startswith('/api/')):
            return
        if path == '/api/health':
            self.json(200, {'version':VERSION, 'mode':'local-only', 'model':self.state.model_name,
                            'max_seconds':180, 'max_audio_bytes':MAX_AUDIO_BYTES,
                            'output_dir':str(self.state.output_dir)})
            return
        static = {'/':('index.html','text/html; charset=utf-8'),
                  '/app.js':('app.js','application/javascript; charset=utf-8'),
                  '/style.css':('style.css','text/css; charset=utf-8')}
        if path not in static:
            self.json(404, {'error':'Not found'})
            return
        filename, kind = static[path]
        self.send_bytes(200, (ROOT / 'web' / filename).read_bytes(), kind)

    def do_OPTIONS(self):
        self.json(403, {'error':'Cross-origin access is disabled.'})

    def read_body(self, limit: int) -> bytes | None:
        if self.headers.get('Transfer-Encoding'):
            self.json(400, {'error':'分块请求不受支持。'})
            return None
        try:
            length = int(self.headers.get('Content-Length', '-1'))
        except ValueError:
            length = -1
        if length < 0:
            self.json(411, {'error':'需要 Content-Length。'})
            return None
        if length > limit:
            self.close_connection = True
            self.json(413, {'error':'请求过大；请缩短录音。'})
            return None
        self.connection.settimeout(30)
        try:
            body = self.rfile.read(length)
        except (TimeoutError, socket.timeout):
            self.json(408, {'error':'读取请求超时。'})
            return None
        if len(body) != length:
            self.json(400, {'error':'请求不完整。'})
            return None
        return body

    def do_POST(self):
        if not self.authorized(True):
            return
        parsed = urlsplit(self.path)
        if parsed.path == '/api/transcribe':
            if not self.headers.get('Content-Type','').lower().startswith(('audio/', 'video/webm', 'video/mp4', 'application/octet-stream')):
                self.json(415, {'error':'需要浏览器录制的音频。'})
                return
            language = parse_qs(parsed.query).get('language', ['auto'])[0]
            if language not in ('auto', 'zh', 'en'):
                self.json(400, {'error':'语言选项须为 auto、zh 或 en。'})
                return
            if not self.state.transcription_lock.acquire(blocking=False):
                self.json(409, {'error':'已有转写进行中，请稍后重试。'})
                return
            try:
                body = self.read_body(MAX_AUDIO_BYTES)
                if body is None:
                    return
                if not body:
                    self.json(400, {'error':'录音为空。'})
                    return
                result = self.state.backend.transcribe(body, None if language == 'auto' else language)
                self.json(200, self.state.add_draft(result))
            except Exception as e:
                self.json(422, {'error':f'本地转写失败（{type(e).__name__}）：请检查音频或终端环境。可重试、重新录音或复制已有文字。'})
            finally:
                self.state.transcription_lock.release()
        elif parsed.path == '/api/save':
            if not self.headers.get('Content-Type','').startswith('application/json'):
                self.json(415, {'error':'需要 JSON。'})
                return
            body = self.read_body(MAX_JSON_BYTES)
            if body is None:
                return
            try:
                result = self.state.save(json.loads(body))
                self.json(200, result)
            except KeyError as e:
                self.json(409, {'error':str(e)})
            except (ValueError, UnicodeDecodeError) as e:
                self.json(400, {'error':str(e)})
            except OSError:
                self.json(500, {'error':'无法保存文件。请检查输出目录权限；页面文字仍可复制。'})
        else:
            self.json(404, {'error':'Not found'})


def make_server(state: AppState, port: int = 8765) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    server.daemon_threads = True
    server.state = state
    state.host = f'127.0.0.1:{server.server_address[1]}'
    state.origin = 'http://'+state.host
    return server


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Local microphone → Whisper → reviewed text. No cloud speech API.')
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('download', help='Explicitly download a model; no microphone is opened.')
    p.add_argument('--model', default='base')
    for command in ('serve', 'transcribe'):
        p = sub.add_parser(command)
        p.add_argument('--model', default='base', help='Cached multilingual model name or local directory')
        p.add_argument('--threads', type=int, default=4)
        p.add_argument('--compute-type', choices=('int8','float32'), default='int8')
        if command == 'serve':
            p.add_argument('--port', type=int, default=8765, help='0 chooses an available local port')
            p.add_argument('--output-dir', type=Path, default=Path.home()/'Interview-Workspace'/'voice-inbox')
            p.add_argument('--no-browser', action='store_true')
        else:
            p.add_argument('file', type=Path)
            p.add_argument('--language', choices=('auto','zh','en'), default='auto')
    args = parser.parse_args(argv)
    try:
        from speech_backend import LocalWhisper, download
        if args.command == 'download':
            print('This command downloads model weights only; it does not record/upload audio.')
            print(download(args.model))
            return 0
        if args.threads < 1:
            raise ValueError('--threads must be positive')
        print('Loading a local-only speech model. No microphone is open.', file=sys.stderr)
        backend = LocalWhisper(args.model, args.threads, args.compute_type)
        if args.command == 'transcribe':
            if args.file.stat().st_size > MAX_AUDIO_BYTES:
                raise ValueError('Audio exceeds 20 MiB')
            result = backend.transcribe(args.file.read_bytes(), None if args.language=='auto' else args.language)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
        if not 0 <= args.port <= 65535:
            raise ValueError('--port must be between 0 and 65535')
        state = AppState(backend, args.output_dir, model_name=args.model)
        server = make_server(state, args.port)
        url = state.origin+'/#token='+state.token
        print('\nOpen this private local link (do not share it):\n'+url, flush=True)
        print('Only clicking Record opens the microphone. Ctrl+C stops the server.', flush=True)
        if not args.no_browser:
            webbrowser.open(url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print('\nServer stopped. Close the recording tab as well.')
        finally:
            server.server_close()
        return 0
    except (ImportError, OSError, RuntimeError, ValueError) as e:
        print(f'ERROR [{type(e).__name__}]: {e}', file=sys.stderr)
        print('Install requirements-voice.txt; then run: python mic_stt.py download --model base\n'
              'Use a cached model or local --model directory; check --port/permissions.\n'
              'If int8 is unsupported on your CPU, try --compute-type float32.', file=sys.stderr)
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
