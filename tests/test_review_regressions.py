"""Final review regressions. Fake ASR; actual local HTTP for auth behavior."""
import contextlib
import http.client
import io
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / 'skills/ai-interview/scripts'
sys.path.insert(0, str(SCRIPTS))
import voice


class ReviewRegressions(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.state = voice.BridgeState(None, self.root / 'answers', token='review-fixture-token')
        self.state.set_question({'question_id':'q1', 'text':'Question fixture'})

    def tearDown(self):
        self.tmp.cleanup()

    def test_replayed_confirmation_does_not_undo_correction(self):
        draft = self.state.add_draft({'question_id':'q1', 'raw_text':'unverified fixture'})
        a = {'draft_id':draft['draft_id'], 'text':'original confirmed fixture'}
        b = {**a, 'text':'corrected fixture'}
        first = self.state.save(a)
        second = self.state.save(b)
        replay = self.state.save(a)
        self.assertEqual(replay, first, 'same confirmation replay must retain its original receipt')
        self.assertEqual(self.state.get_answer('q1', 0)['answer']['revision'], second['revision'])
        self.assertEqual(self.state.get_answer('q1', 0)['answer']['confirmed_text'], b['text'])
        self.assertEqual(len(list((self.root/'answers').glob('*.json'))), 2)

    def test_new_submission_can_deliberately_restore_earlier_text(self):
        draft = self.state.add_draft({'question_id':'q1', 'raw_text':'fixture'})
        base = {'draft_id':draft['draft_id'], 'text':'first answer'}
        self.state.save({**base, 'submission_id':'s1', 'expected_revision':0})
        self.state.save({**base, 'text':'second answer', 'submission_id':'s2', 'expected_revision':1})
        third = self.state.save({**base, 'submission_id':'s3', 'expected_revision':2})
        self.assertEqual(third['revision'], 3)
        self.assertEqual(self.state.get_answer('q1', 0)['answer']['confirmed_text'], 'first answer')

    def test_submission_id_is_immutable(self):
        draft = self.state.add_draft({'question_id':'q1', 'raw_text':'fixture'})
        payload = {'draft_id':draft['draft_id'], 'text':'first answer', 'submission_id':'s1'}
        self.state.save(payload)
        with self.assertRaises(ValueError):
            self.state.save({**payload, 'text':'different answer'})

    def test_stale_new_submission_cannot_overwrite_a_correction(self):
        draft = self.state.add_draft({'question_id':'q1', 'raw_text':'fixture'})
        payload = {'draft_id':draft['draft_id'], 'text':'first answer', 'submission_id':'s1', 'expected_revision':0}
        receipt = self.state.save(payload)
        self.assertEqual(self.state.save(payload), receipt, 'identical retry is idempotent')
        with self.assertRaises(ValueError):
            self.state.save({**payload, 'text':'outdated tab answer', 'submission_id':'s2'})
        self.assertEqual(self.state.get_answer('q1', 0)['answer']['confirmed_text'], 'first answer')

    def test_invalid_submission_metadata_is_rejected(self):
        draft = self.state.add_draft({'question_id':'q1', 'raw_text':'fixture'})
        for patch in ({'submission_id':''}, {'submission_id':'../bad'}, {'expected_revision':True}, {'expected_revision':-1}):
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                self.state.save({'draft_id':draft['draft_id'], 'text':'answer', **patch})

    def test_malformed_connection_is_a_clear_validation_error(self):
        cases = [None, [], {'origin':42}, {'origin':'http://127.0.0.1:1234','token':'bad\nheader'},
                 {'origin':'http://127.0.0.1:1234','token':'nonascii-é'}]
        for data in cases:
            with self.subTest(data=data):
                (self.root/'connection.json').write_text(json.dumps(data), encoding='utf-8')
                try:
                    voice.read_connection(self.root)
                except ValueError:
                    continue
                except Exception as exc:
                    self.fail('Malformed metadata escaped as '+type(exc).__name__)
                self.fail('Malformed metadata was accepted')

    def test_nonascii_authorization_is_rejected_without_handler_crash(self):
        server = voice.make_bridge_server(self.state, 0)
        thread = threading.Thread(target=server.serve_forever, kwargs={'poll_interval':.02}, daemon=True)
        thread.start()
        errors = io.StringIO()
        try:
            with contextlib.redirect_stderr(errors):
                conn = http.client.HTTPConnection('127.0.0.1', server.server_address[1], timeout=3)
                try:
                    conn.request('GET', '/api/health', headers={'Authorization':'Bearer é'})
                    response = conn.getresponse(); code = response.status; response.read()
                except http.client.RemoteDisconnected:
                    code = None
                finally:
                    conn.close()
            self.assertEqual(code, 403, 'invalid auth must receive a controlled HTTP rejection')
            self.assertNotIn('Traceback', errors.getvalue())
        finally:
            server.shutdown(); server.server_close(); thread.join(2)

    def test_stopped_session_never_delivers_ready_answer(self):
        draft = self.state.add_draft({'question_id':'q1', 'raw_text':'fixture'})
        self.state.save({'draft_id':draft['draft_id'], 'text':'confirmed fixture'})
        self.state.stopped = True
        reply = self.state.get_answer('q1', 0)
        self.assertEqual(reply['status'], 'stopped')
        self.assertNotIn('answer', reply)


if __name__ == '__main__':
    unittest.main()
