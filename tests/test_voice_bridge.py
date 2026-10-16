"""Real loopback/CLI tests with a fake decoder, not microphone or model tests."""
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'skills/ai-interview/scripts'

class VoiceTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue((SCRIPTS / 'voice.py').is_file(), 'Missing Codex-callable voice bridge')
        sys.path.insert(0, str(SCRIPTS))
        self.voice = importlib.import_module('voice')
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        class Decoder:
            def transcribe(self, audio, language):
                return {'raw_text':'原始识别', 'segments':[], 'language':'zh', 'duration_seconds':1}
        self.state = self.voice.BridgeState(Decoder(), self.directory / 'answers', token='test-secret', model_name='FAKE')
        self.server = self.voice.make_bridge_server(self.state, 0)
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval":0.02}, daemon=True)
        self.thread.start()
        self.connection = self.voice.write_connection(self.directory, self.state, os.getpid())

    def tearDown(self):
        if hasattr(self, 'server'):
            self.server.shutdown(); self.server.server_close(); self.thread.join(2)
        if hasattr(self, 'temp'): self.temp.cleanup()

    def call(self, method, path, payload=None):
        return self.voice.request(self.directory, method, path, payload)

    def ask(self, q='q1', text='为什么选这个算法？'):
        return self.call('POST', '/api/question', {'question_id':q, 'text':text})

    def confirm(self, q='q1', text='这是我核对后的答案'):
        d = self.state.add_draft({'raw_text':'原始识别', 'segments':[], 'language':'zh', 'duration_seconds':1, 'question_id':q})
        return self.call('POST', '/api/save', {'draft_id':d['draft_id'], 'text':text})

    def cli(self, *args):
        # Most argument/JSON tests call the real CLI entry in-process for speed.
        # Separate round-trip/lifecycle tests below launch real CLI processes.
        import contextlib
        import io
        output=io.StringIO()
        with contextlib.redirect_stdout(output):
            code=self.voice.main([*args,'--session-dir',str(self.directory)])
        proc=subprocess.CompletedProcess(args,code,output.getvalue(),'')
        return proc,json.loads(proc.stdout)

    def test_no_answer_until_confirmed(self):
        self.ask()
        self.state.add_draft({'raw_text':'秘密草稿', 'question_id':'q1'})
        self.assertEqual(self.call('GET','/api/answer?question_id=q1&after_revision=0')['status'], 'waiting')
        self.assertFalse((self.directory/'answers').exists())

    def test_exact_question_revision_and_idempotency(self):
        self.ask()
        first = self.confirm()
        got = self.call('GET','/api/answer?question_id=q1&after_revision=0')
        self.assertEqual(got['status'],'ready')
        self.assertEqual(got['answer']['confirmed_text'],'这是我核对后的答案')
        self.assertEqual(got['answer']['revision'],1)
        self.assertEqual(got['answer']['question_id'],'q1')
        self.assertEqual(got['answer']['raw_text'],'原始识别')
        self.assertEqual(self.call('GET','/api/answer?question_id=q1&after_revision=1')['status'],'waiting')
        receipt = self.call('POST','/api/save',{'draft_id':got['answer']['draft_id'],'text':'这是我核对后的答案'})
        self.assertEqual(receipt['revision'],first['revision'])

    def test_correction_is_new_revision(self):
        self.ask(); first=self.confirm()
        self.call('POST','/api/save',{'draft_id':first['draft_id'],'text':'修正：不是线性，是平方复杂度'})
        answer=self.call('GET','/api/answer?question_id=q1&after_revision=1')['answer']
        self.assertEqual(answer['revision'],2)

    def test_same_question_is_idempotent_but_not_mutable(self):
        self.ask(); self.ask()
        with self.assertRaises(RuntimeError): self.ask(text='偷偷更换题目')

    def test_pending_question_cannot_be_silently_replaced(self):
        self.ask()
        with self.assertRaises(RuntimeError): self.ask('q2')

    def test_new_question_does_not_return_previous_answer(self):
        self.ask(); self.confirm(); self.ask('q2')
        self.assertEqual(self.call('GET','/api/answer?question_id=q2&after_revision=0')['status'],'waiting')

    def test_stale_draft_cannot_be_submitted_to_next_question(self):
        self.ask()
        old=self.state.add_draft({'raw_text':'old', 'question_id':'q1'})
        self.confirm(); self.ask('q2')
        with self.assertRaises(RuntimeError):
            self.call('POST','/api/save',{'draft_id':old['draft_id'],'text':'late'})

    def test_wait_cli_returns_data_not_shell_instructions(self):
        self.ask(); self.confirm(text='$(do not execute)；这是答题文本')
        p=subprocess.run([sys.executable,str(SCRIPTS/'voice.py'),'wait','--session-dir',str(self.directory),'--question-id','q1','--timeout','0'],capture_output=True,text=True,timeout=15)
        d=json.loads(p.stdout)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertEqual(d['status'],'ready')
        self.assertEqual(d['answer']['confirmed_text'],'$(do not execute)；这是答题文本')
        self.assertNotIn('test-secret',p.stdout)

    def test_wait_timeout_is_not_empty_answer(self):
        self.ask()
        p,d=self.cli('wait','--question-id','q1','--timeout','0')
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertEqual(d['status'],'waiting')
        self.assertNotIn('answer',d)

    def test_invalid_wait_limits_are_rejected(self):
        self.ask()
        for value in ('-1','nan','inf','301'):
            p,d=self.cli('wait','--question-id','q1','--timeout',value)
            self.assertNotEqual(p.returncode,0)
            self.assertEqual(d['status'],'error')

    def test_metadata_cannot_redirect_local_tokens(self):
        path=self.directory/'connection.json'
        data=json.loads(path.read_text()); data['origin']='https://example.com'
        path.write_text(json.dumps(data))
        with self.assertRaises(ValueError): self.voice.request(self.directory,'GET','/api/health')

    def test_start_refuses_existing_session(self):
        p,d=self.cli('start','--no-browser')
        self.assertNotEqual(p.returncode,0)
        self.assertEqual(d['status'],'error')

    def test_question_id_validation(self):
        for q in ('../q','', 'q/../../key','x'*100):
            with self.assertRaises(RuntimeError): self.ask(q)

    def test_browser_question_endpoint(self):
        self.ask(text='请说明你的个人贡献。')
        got=self.call('GET','/api/question')
        self.assertEqual(got['question']['text'],'请说明你的个人贡献。')
        self.assertEqual(self.call('GET','/api/health')['agent_mode'],True)

    def test_stop_marks_state_and_shuts_down(self):
        p,d=self.cli('stop')
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertEqual(d['status'],'stopped')
        self.thread.join(3)
        self.assertFalse(self.thread.is_alive())

    def test_cli_ask_and_http_transcribe_confirm_round_trip(self):
        import http.client
        proc,result=self.cli('ask','--question-id','q1','--text','请解释边界条件')
        self.assertEqual(proc.returncode,0,proc.stderr)
        self.assertEqual(result['question']['question_id'],'q1')
        c=http.client.HTTPConnection('127.0.0.1',self.server.server_address[1],timeout=5)
        c.request('POST','/api/transcribe?language=zh',body=b'FAKE AUDIO ONLY',headers={
            'Authorization':'Bearer test-secret','Content-Type':'audio/webm','X-Question-ID':'q1'})
        response=c.getresponse(); status=response.status; draft=json.loads(response.read()); c.close()
        self.assertEqual(status,200)
        self.assertEqual(draft['question_id'],'q1')
        self.assertEqual(self.call('GET','/api/answer?question_id=q1')['status'],'waiting')
        self.call('POST','/api/save',{'draft_id':draft['draft_id'],'text':'确认后的边界条件'})
        proc,result=self.cli('wait','--question-id','q1','--timeout','0')
        self.assertEqual(result['answer']['confirmed_text'],'确认后的边界条件')

    def test_stale_recording_header_rejected(self):
        import http.client
        self.ask()
        c=http.client.HTTPConnection('127.0.0.1',self.server.server_address[1],timeout=5)
        c.request('POST','/api/transcribe',body=b'FAKE',headers={'Authorization':'Bearer test-secret','Content-Type':'audio/webm','X-Question-ID':'q-old'})
        response=c.getresponse(); response.read(); c.close()
        self.assertEqual(response.status,409)
        self.assertEqual(len(self.state.drafts),0)

    def test_round_trip_confirmed_record_on_disk(self):
        self.ask(); receipt=self.confirm()
        data=json.loads(Path(receipt['json_path']).read_text())
        self.assertEqual(data['question_id'],'q1')
        self.assertEqual(data['revision'],1)
        self.assertFalse(data['audio_persisted_by_app'])
        self.assertTrue(data['raw_transcript_is_unverified'])
        self.assertFalse(any(p.suffix in ('.wav','.webm','.mp3') for p in (self.directory/'answers').iterdir()))

class PackageVoiceTests(unittest.TestCase):
    def test_self_contained_runtime_files(self):
        for p in ('voice.py','mic_stt.py','speech_backend.py','requirements-voice.txt','web/app.js','web/index.html','web/style.css'):
            self.assertTrue((SCRIPTS/p).is_file(),p)
    def test_no_workflow_files(self):
        self.assertFalse(list((ROOT/'.github/workflows').glob('*')))
    def test_skill_routes_to_real_commands(self):
        text=(ROOT/'skills/ai-interview/SKILL.md').read_text()
        self.assertIn('references/local-voice.md',text)
        ref=ROOT/'skills/ai-interview/references/local-voice.md'
        self.assertTrue(ref.is_file())
        text=ref.read_text()
        for word in ('doctor','setup','start','ask','wait','stop','confirmed_text','after-revision'):
            self.assertIn(word,text)


class PortableVoiceTests(unittest.TestCase):
    def test_copied_skill_runs_outside_repo(self):
        import shutil
        with tempfile.TemporaryDirectory() as td:
            target=Path(td)/'installed skill'
            shutil.copytree(ROOT/'skills/ai-interview',target,ignore=shutil.ignore_patterns('__pycache__'))
            p=subprocess.run([sys.executable,str(target/'scripts/voice.py'),'doctor'],cwd=td,capture_output=True,text=True,timeout=15)
            self.assertEqual(p.returncode,0,p.stderr)
            data=json.loads(p.stdout)
            self.assertEqual(data['status'],'checked')
            self.assertFalse(data['microphone_tested'])
    def test_setup_requires_download_permission(self):
        p=subprocess.run([sys.executable,str(SCRIPTS/'voice.py'),'setup'],capture_output=True,text=True,timeout=5)
        self.assertEqual(p.returncode,1)
        self.assertIn('--allow-download',json.loads(p.stdout)['error'])

    def test_real_start_stop_lifecycle_with_fake_model(self):
        import shutil
        with tempfile.TemporaryDirectory() as td:
            target=Path(td)/'runtime with spaces'
            shutil.copytree(SCRIPTS,target,ignore=shutil.ignore_patterns('__pycache__'))
            # Reviewed fixture: tests process lifecycle, NOT actual Whisper.
            (target/'speech_backend.py').write_text("class LocalWhisper:\n    def __init__(self,*args,**kwargs): pass\n",encoding='utf-8')
            session=Path(td)/'private-session'
            env={**os.environ,'AI_INTERVIEW_VOICE_HOME':str(Path(td)/'isolated-runtime')}
            command=[sys.executable,str(target/'voice.py')]
            started=False
            try:
                p=subprocess.run(command+['start','--session-dir',str(session),'--no-browser'],env=env,capture_output=True,text=True,timeout=15)
                self.assertEqual(p.returncode,0,p.stdout+p.stderr)
                data=json.loads(p.stdout); started=True
                self.assertEqual(data['status'],'started')
                self.assertFalse(data['microphone_opened'])
                self.assertTrue(data['url'].startswith('http://127.0.0.1:'))
                metadata=json.loads((session/'connection.json').read_text())
                self.assertNotIn(metadata['token'],(session/'server.log').read_text())
                if os.name!='nt':
                    self.assertEqual((session/'connection.json').stat().st_mode & 0o777,0o600)
                p=subprocess.run(command+['status','--session-dir',str(session)],env=env,capture_output=True,text=True,timeout=5)
                self.assertEqual(json.loads(p.stdout)['status'],'running')
            finally:
                if started:
                    p=subprocess.run(command+['stop','--session-dir',str(session)],env=env,capture_output=True,text=True,timeout=5)
                    self.assertEqual(json.loads(p.stdout)['status'],'stopped')

if __name__=='__main__': unittest.main()
