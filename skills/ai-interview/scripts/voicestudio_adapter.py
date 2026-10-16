"""Optional loopback-only VoiceStudio speech service adapter.

Uses publicly documented HTTP /v1/audio routes and capability discovery. This
file is independently written MIT project code; VoiceStudio AGPL code/weights
are neither imported, copied nor redistributed. No microphone access here.
"""
from __future__ import annotations

import json
import os
import secrets
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

MAX_TTS_TEXT = 4000
MAX_AUDIO_BYTES = 20 * 1024 * 1024
MAX_SPEECH_BYTES = 24 * 1024 * 1024
MAX_JSON_BYTES = 1024 * 1024
PROTOCOL = 'voicestudio.speech.v1'


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class VoiceStudioAdapter:
    """Talk only to an explicitly configured loopback VoiceStudio instance."""

    def __init__(self, url: str = 'http://127.0.0.1:3900'):
        if not isinstance(url, str):
            raise ValueError('VoiceStudio URL must be text')
        parsed = urlsplit(url)
        if (parsed.scheme != 'http' or parsed.hostname != '127.0.0.1'
                or parsed.username or parsed.password or parsed.path not in ('', '/')
                or parsed.query or parsed.fragment or not parsed.port):
            raise ValueError('VoiceStudio URL must be http://127.0.0.1:<port> with no path or credentials')
        self.url = f'http://127.0.0.1:{parsed.port}'
        self.websocket_upstream = f'ws://127.0.0.1:{parsed.port}/v1/audio/transcriptions/stream'
        self._opener = build_opener(ProxyHandler({}), _NoRedirect())

    def _get(self, path: str, *, payload: bytes | None = None,
             content_type: str | None = None, limit: int = MAX_JSON_BYTES,
             timeout: float = 3.0) -> tuple[bytes, str]:
        if path not in ('/health', '/.well-known/voicestudio-speech',
                        '/v1/audio/voices', '/v1/audio/speech',
                        '/v1/audio/transcriptions'):
            raise ValueError('VoiceStudio endpoint not allowed')
        headers = {'Accept': 'application/json' if payload is None else '*/*'}
        if content_type:
            headers['Content-Type'] = content_type
        request = Request(self.url + path, data=payload, headers=headers,
                          method='GET' if payload is None else 'POST')
        try:
            with self._opener.open(request, timeout=timeout) as response:
                media_type = response.headers.get('Content-Type', '').lower().split(';')[0].strip()
                data = response.read(limit + 1)
                if len(data) > limit:
                    raise ValueError('VoiceStudio response exceeded the allowed size')
                return data, media_type
        except HTTPError as e:
            # Do not expose arbitrary backend response bodies or sensitive headers.
            raise RuntimeError(f'VoiceStudio HTTP {e.code}; check installed model and the VoiceStudio window') from None
        except (URLError, TimeoutError, ConnectionError, OSError) as e:
            raise RuntimeError('VoiceStudio is unavailable at the configured local address') from None

    def _json_get(self, path: str) -> dict:
        body, media_type = self._get(path)
        if media_type != 'application/json':
            raise ValueError('VoiceStudio sent a non-JSON capability response')
        response = json.loads(body)
        if not isinstance(response, dict):
            raise ValueError('Invalid VoiceStudio JSON shape')
        return response

    def capabilities(self) -> dict:
        result = self._json_get('/.well-known/voicestudio-speech')
        if result.get('protocol') != PROTOCOL or result.get('service') != 'VoiceStudio':
            raise ValueError('VoiceStudio speech protocol does not match version v1')
        endpoints = result.get('endpoints') or {}
        stream = endpoints.get('streaming_transcription') or {}
        if stream.get('path') != '/v1/audio/transcriptions/stream' or stream.get('transport') != 'websocket':
            raise ValueError('VoiceStudio did not advertise the supported streaming endpoint')
        return result

    def status(self) -> dict:
        try:
            caps = self.capabilities()
        except (RuntimeError, ValueError, OSError, json.JSONDecodeError) as e:
            return {'available': False, 'streaming': False, 'voices': [],
                    'detail': str(e)[:250], 'url': self.url}
        voices = []
        try:
            records = self._json_get('/v1/audio/voices')
            values = records.get('data', [])
            if isinstance(values, list):
                voices = [item['id'] for item in values if isinstance(item, dict)
                          and isinstance(item.get('id'), str) and len(item['id']) <= 100][:30]
        except (RuntimeError, ValueError, json.JSONDecodeError):
            # Discovering installed voice profiles is optional; default can still work.
            pass
        return {'available': True, 'streaming':bool(caps.get('features',{}).get('streaming_transcription')),
                'voices': voices, 'protocol': PROTOCOL, 'url':self.url,
                'note': 'VoiceStudio is an independently installed local service; readiness does not certify a loaded model.'}

    def speak(self, text: str, voice: str = 'default') -> bytes:
        if not isinstance(text, str) or not text.strip() or len(text) > MAX_TTS_TEXT or '\x00' in text:
            raise ValueError('Speech text must be 1–4000 printable characters')
        if not isinstance(voice, str) or not voice or len(voice) > 100 or '\x00' in voice:
            raise ValueError('Invalid VoiceStudio voice profile')
        payload = json.dumps({'model':'tts-1', 'voice':voice, 'input':text,
                              'response_format':'wav'}, ensure_ascii=False).encode('utf-8')
        audio, media_type = self._get('/v1/audio/speech', payload=payload,
                                      content_type='application/json',limit=MAX_SPEECH_BYTES,timeout=120)
        if media_type not in ('audio/wav', 'audio/x-wav', 'audio/wave', 'application/octet-stream') or not audio.startswith(b'RIFF'):
            raise RuntimeError('VoiceStudio returned an unexpected audio format; audio was discarded')
        return audio

    def transcribe(self, audio: bytes, content_type: str = 'audio/webm') -> str:
        if not isinstance(audio, bytes) or not 0 < len(audio) <= MAX_AUDIO_BYTES:
            raise ValueError('VoiceStudio transcription audio is empty or too large')
        kind = content_type.split(';')[0].strip().lower()
        if kind not in ('audio/webm','video/webm','audio/mp4','video/mp4','audio/ogg','application/octet-stream'):
            raise ValueError('Unsupported audio type')
        boundary = 'AIInterview' + secrets.token_hex(12)
        ext = '.mp4' if 'mp4' in kind else '.ogg' if 'ogg' in kind else '.webm'
        prefix = (f'--{boundary}\r\nContent-Disposition: form-data; name="model"\r\n\r\nwhisper-1\r\n'
                  f'--{boundary}\r\nContent-Disposition: form-data; name="response_format"\r\n\r\njson\r\n'
                  f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="answer{ext}"\r\n'
                  f'Content-Type: {kind}\r\n\r\n').encode('ascii')
        payload = prefix + audio + f'\r\n--{boundary}--\r\n'.encode('ascii')
        body, media_type = self._get('/v1/audio/transcriptions', payload=payload,
                        content_type=f'multipart/form-data; boundary={boundary}', timeout=120)
        if media_type != 'application/json':
            raise RuntimeError('VoiceStudio transcription returned an unexpected data format')
        result = json.loads(body)
        if not isinstance(result,dict) or not isinstance(result.get('text'),str):
            raise RuntimeError('VoiceStudio transcription returned no text field')
        return result['text'][:20_000]
