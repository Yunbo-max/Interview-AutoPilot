"""Tests use a fake speech backend; they are not an ASR accuracy benchmark."""
import http.client
import importlib
import importlib.util
import json
from pathlib import Path
import tempfile
import threading
import unittest
import sys

ROOT = Path(__file__).resolve().parents[1] / 'skills/ai-interview/scripts'
sys.path.insert(0, str(ROOT))

class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue((ROOT / 'mic_stt.py').exists(), 'Microphone adapter not implemented yet')
        self.app = importlib.import_module('mic_stt')
        self.temp = tempfile.TemporaryDirectory()
        self.out = Path(self.temp.name) / 'private-inbox'
        class FakeBackend:
            def transcribe(self, audio, language):
                if audio == b'bad':
                    raise ValueError('Invalid audio fixture')
                return {'raw_text': '我使用了 Agent 和 KV cache。', 'language': language or 'zh',
                        'duration_seconds': 2.0, 'segments': [{'start': 0.0, 'end': 2.0, 'text': '我使用了 Agent 和 KV cache。'}]}
        self.state = self.app.AppState(FakeBackend(), self.out, token='test-token', model_name='fake-test-only')
        self.server = self.app.make_server(self.state, port=0)
        self.port = self.server.server_address[1]
        self.origin = f'http://127.0.0.1:{self.port}'
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval":0.02}, daemon=True)
        self.thread.start()

    def tearDown(self):
        if hasattr(self, 'server'):
            self.server.shutdown()
            self.server.server_close()
            self.thread.join(timeout=2)
        if hasattr(self, 'temp'):
            self.temp.cleanup()

    def call(self, method, path, body=None, headers=None):
        h = {'Authorization': 'Bearer test-token', 'Origin': self.origin}
        if headers:
            h.update(headers)
        c = http.client.HTTPConnection('127.0.0.1', self.port, timeout=5)
        c.request(method, path, body=body, headers=h)
        r = c.getresponse()
        data = r.read()
        status = r.status
        c.close()
        try: data = json.loads(data)
        except (ValueError, UnicodeDecodeError): pass
        return status, data

    def draft(self):
        status, data = self.call('POST', '/api/transcribe?language=zh', b'fixture', {'Content-Type': 'audio/webm'})
        self.assertEqual(status, 200)
        return data

    def test_health(self):
        status, data = self.call('GET', '/api/health')
        self.assertEqual(status, 200)
        self.assertEqual(data['mode'], 'local-only')

    def test_bad_token(self):
        self.assertEqual(self.call('GET', '/api/health', headers={'Authorization': 'Bearer bad'})[0], 403)

    def test_foreign_origin(self):
        self.assertEqual(self.call('GET', '/api/health', headers={'Origin': 'https://evil.invalid'})[0], 403)

    def test_foreign_host(self):
        self.assertEqual(self.call('GET', '/', headers={'Host': 'evil.invalid'})[0], 403)

    def test_no_save_on_transcribe(self):
        self.draft()
        self.assertFalse(self.out.exists())

    def test_save_preserves_raw_and_confirmed(self):
        draft = self.draft()
        payload = json.dumps({'draft_id': draft['draft_id'], 'text': '我使用了 ReAct 与 KV cache。'}, ensure_ascii=False).encode()
        status, data = self.call('POST', '/api/save', payload, {'Content-Type':'application/json'})
        self.assertEqual(status, 200)
        self.assertEqual((self.out / 'latest.txt').read_text(), '我使用了 ReAct 与 KV cache。\n')
        saved = json.loads(Path(data['json_path']).read_text())
        self.assertEqual(saved['raw_text'], draft['raw_text'])
        self.assertEqual(saved['confirmed_text'], '我使用了 ReAct 与 KV cache。')
        self.assertFalse(any(p.suffix in {'.wav', '.webm', '.mp3'} for p in self.out.iterdir()))

    def test_save_unknown_draft_denied(self):
        status, _ = self.call('POST','/api/save', b'{"draft_id":"missing","text":"hi"}', {'Content-Type':'application/json'})
        self.assertEqual(status, 409)
        self.assertFalse(self.out.exists())

    def test_empty_text_denied(self):
        d = self.draft()
        payload = json.dumps({'draft_id':d['draft_id'], 'text':'   '}).encode()
        self.assertEqual(self.call('POST','/api/save', payload, {'Content-Type':'application/json'})[0], 400)

    def test_bad_audio_reports_error(self):
        self.assertEqual(self.call('POST','/api/transcribe', b'bad', {'Content-Type':'audio/webm'})[0], 422)

    def test_empty_audio_denied(self):
        self.assertEqual(self.call('POST','/api/transcribe', b'', {'Content-Type':'audio/webm'})[0], 400)

    def test_unsupported_language_denied(self):
        self.assertEqual(self.call('POST','/api/transcribe?language=invalid', b'a', {'Content-Type':'audio/webm'})[0], 400)

    def test_wrong_content_type_denied(self):
        self.assertEqual(self.call('POST','/api/transcribe', b'a', {'Content-Type':'text/plain'})[0], 415)

    def test_invalid_json_denied(self):
        self.assertEqual(self.call('POST','/api/save', b'{', {'Content-Type':'application/json'})[0], 400)

    def test_static_routes_are_allowlisted(self):
        self.assertEqual(self.call('GET','/../../etc/passwd')[0], 404)

    def test_lock_rejects_parallel_transcription(self):
        with self.state.transcription_lock:
            self.assertEqual(self.call('POST','/api/transcribe', b'a', {'Content-Type':'audio/webm'})[0], 409)

    def test_repeated_identical_save_is_idempotent(self):
        d = self.draft()
        payload = json.dumps({'draft_id':d['draft_id'], 'text':d['raw_text']}).encode()
        _, a = self.call('POST','/api/save', payload, {'Content-Type':'application/json'})
        _, b = self.call('POST','/api/save', payload, {'Content-Type':'application/json'})
        self.assertEqual(a['json_path'], b['json_path'])
        self.assertEqual(len(list(self.out.glob('turn-*.json'))), 1)

    def test_token_not_served_in_html(self):
        status, html = self.call('GET','/')
        self.assertEqual(status, 200)
        self.assertNotIn(b'test-token', html)

if __name__ == '__main__':
    unittest.main()
