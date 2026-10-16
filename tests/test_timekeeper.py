"""Deterministic timekeeper: fake monotonic time, never wall-clock sleep."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'skills/ai-interview/scripts'))

class TimekeeperPolicyTests(unittest.TestCase):
    def test_voice_warns_at_one_two_and_five_minutes_once(self):
        from interview_timekeeper import TimekeeperAgent
        t=TimekeeperAgent()
        t.begin({'id':'q1','phase':'hr','kind':'voice'}, 0)
        self.assertEqual(t.snapshot(59,True)['reminders'],[])
        t.observe(60,True)
        self.assertEqual([e['at_seconds'] for e in t.snapshot(61,True)['reminders']],[60])
        t.observe(120,True);t.observe(120,True)
        self.assertEqual([e['level'] for e in t.snapshot(120,True)['reminders']],['gentle','progress'])
        t.observe(301,True)
        info=t.snapshot(301,True,language='zh')
        self.assertEqual(len(info['reminders']),3)
        self.assertEqual(info['recommended_seconds'],300)
        self.assertIn('未提交',info['reminders'][-1]['message'])
        self.assertNotIn('答错',info['reminders'][-1]['message'])
        t.close(302,'answered')
        self.assertEqual(t.report()['turns'][0]['active_seconds'],302)
        self.assertEqual(t.report()['turns'][0]['outcome'],'answered')

    def test_coding_and_math_receive_longer_windows(self):
        from interview_timekeeper import TimekeeperAgent
        for phase,kind,expected in [('coding','code',[300,600,900]),('math','voice',[120,240,360]),('transformer','voice',[90,180,300])]:
            with self.subTest(phase=phase):
                t=TimekeeperAgent();t.begin({'id':'q','phase':phase,'kind':kind},10)
                self.assertEqual(t.snapshot(10,True)['thresholds_seconds'],expected)
                t.observe(10+expected[0]-1,True)
                self.assertEqual(t.snapshot(10+expected[0]-1,True)['reminders'],[])
                t.observe(10+expected[0],True)
                self.assertEqual(len(t.snapshot(10+expected[0],True)['reminders']),1)

    def test_pause_never_produces_reminders_and_extension_is_bounded(self):
        from interview_timekeeper import TimekeeperAgent
        t=TimekeeperAgent();t.begin({'id':'q1','phase':'hr','kind':'voice'},0)
        t.observe(45,False)
        self.assertEqual(t.snapshot(45,False)['reminders'],[])
        self.assertEqual(t.extend('q1'),60)
        self.assertEqual(t.extend('q1'),120)
        with self.assertRaisesRegex(ValueError,'limit'):
            t.extend('q1')
        with self.assertRaisesRegex(ValueError,'Stale'):
            t.extend('wrong')
        self.assertEqual(t.snapshot(46,True)['thresholds_seconds'],[60,120,420])
        t.observe(301,True)
        self.assertEqual(len(t.snapshot(301,True)['reminders']),2)
        t.close(301,'skipped')
        self.assertEqual(t.report()['skipped_count'],1)
        self.assertEqual(t.snapshot(301,True)['reminders'],[])

    def test_late_poll_crosses_all_thresholds_and_session_warning_once(self):
        from interview_timekeeper import TimekeeperAgent
        t=TimekeeperAgent();t.begin({'id':'q1','phase':'hr','kind':'voice'},0)
        t.observe(3310,True)
        snap=t.snapshot(3310,True)
        self.assertEqual(len(snap['reminders']),3)
        self.assertEqual([e['at_seconds'] for e in snap['session_reminders']],[3300])
        t.observe(3599,True);t.observe(3599,True)
        self.assertEqual([e['at_seconds'] for e in t.snapshot(3599,True)['session_reminders']],[3300,3540])

class InterviewTimingTests(unittest.TestCase):
    class FakeBackend:
        def __init__(self, callback=None):self.prompts=[];self.callback=callback
        def generate(self,prompt,provider):
            self.prompts.append(prompt)
            if self.callback:self.callback(len(self.prompts))
            return {'question':f'Q{len(self.prompts)}','kind':'voice','assessment':'Model note'}

    def session(self,backend=None):
        from interview_core import InterviewSession
        clock=[0.0]
        b=backend or self.FakeBackend()
        s=InterviewSession(b)
        s._clock.source=lambda:clock[0]
        s.set_resume_text('Candidate published a model evaluation and built a research harness.')
        q=s.start('ai_researcher','codex',True)
        return s,q,clock,b

    def test_pause_freezes_question_time_and_new_question_resets(self):
        s,q,clock,b=self.session()
        clock[0]=50;s.pause();clock[0]=1000
        self.assertEqual(s.public_state()['timekeeper']['elapsed_seconds'],50)
        s.resume();clock[0]=1040
        st=s.public_state()
        self.assertEqual(st['timekeeper']['elapsed_seconds'],90)
        self.assertEqual(len(st['timekeeper']['reminders']),1)
        result=s.submit(q['id'],'Evidence about the method','voice','turn001')
        self.assertEqual(s.history[0]['answer_elapsed_seconds'],90)
        self.assertEqual(s.public_state()['timekeeper']['elapsed_seconds'],0)
        self.assertEqual(s.public_state()['timekeeper']['question_id'],result['id'])

    def test_model_wait_is_not_counted_for_next_question(self):
        clock=[0.]
        def hook(count):
            if count==2:clock[0]+=180
        b=self.FakeBackend(hook)
        from interview_core import InterviewSession
        s=InterviewSession(b);s._clock.source=lambda:clock[0]
        s.set_resume_text('Legitimate resume text');q=s.start('agent_engineer','codex',True)
        clock[0]=100
        out=s.submit(q['id'],'I measured agent search costs','voice','a1')
        self.assertEqual(s.history[-1]['answer_elapsed_seconds'],100)
        self.assertEqual(s.public_state()['elapsed_seconds'],100)
        self.assertEqual(s.public_state()['timekeeper']['elapsed_seconds'],0)
        self.assertEqual(s.public_state()['timekeeper']['question_id'],out['id'])

    def test_speech_decoding_wait_excluded_even_across_manual_pause(self):
        s,q,clock,b=self.session()
        clock[0]=75
        token=s.begin_host_wait(q['id'],'stt')
        self.assertIsNotNone(token)
        clock[0]=300
        self.assertEqual(s.public_state()['timekeeper']['elapsed_seconds'],75)
        with self.assertRaisesRegex(ValueError,'speech processing'):
            s.submit(q['id'],'Pending unconfirmed transcript','voice','no-early-grading')
        s.pause()
        s.end_host_wait(token)
        clock[0]=500
        self.assertEqual(s.public_state()['timekeeper']['elapsed_seconds'],75)
        s.resume();clock[0]=525
        self.assertEqual(s.public_state()['timekeeper']['elapsed_seconds'],100)
        s.submit(q['id'],'Confirmed candidate text','voice','after-stt')
        self.assertEqual(s.history[-1]['answer_elapsed_seconds'],100)

    def test_failed_skip_model_keeps_question_ungraded_and_retryable(self):
        def fail_second(call):
            if call==2:raise RuntimeError('provider down')
        s,q,clock,b=self.session(self.FakeBackend(fail_second));clock[0]=150
        with self.assertRaises(RuntimeError):s.skip(q['id'],'skip-retry')
        self.assertEqual(s.current_question['id'],q['id'])
        self.assertEqual(s.history,[])
        self.assertEqual(s.timekeeper.snapshot(s._clock.elapsed(),True)['elapsed_seconds'],150)
        self.assertTrue(s._clock.running)
        s.skip(q['id'],'skip-retry')
        self.assertEqual(s.timekeeper.report()['skipped_count'],1)

    def test_skip_is_explicit_ungraded_idempotent_and_stale_rejected(self):
        s,q,clock,b=self.session();clock[0]=301;s.pulse()
        self.assertEqual(len(b.prompts),1,'a passive timeout must not invoke the LLM')
        result=s.skip(q['id'],'skip-a')
        self.assertEqual(s.history[-1]['response_status'],'skipped')
        self.assertEqual(s.history[-1]['answer'],'')
        self.assertEqual(s.history[-1]['assessment'],'Not assessed (explicit skip)')
        self.assertEqual(s.history[-1]['answer_elapsed_seconds'],301)
        self.assertEqual(s.skip(q['id'],'skip-a'),result)
        with self.assertRaisesRegex(ValueError,'Stale'):
            s.skip(q['id'],'skip-b')
        self.assertEqual(s.public_state()['timekeeper']['question_id'],result['id'])
        self.assertEqual(s.timekeeper.report()['skipped_count'],1)
        self.assertIn('not a wrong answer',b.prompts[1].lower())

    def test_extension_on_active_question_only(self):
        s,q,clock,b=self.session();self.assertEqual(s.extend_question(q['id']),60)
        s.pause()
        with self.assertRaisesRegex(ValueError,'active'):
            s.extend_question(q['id'])
        s.resume()
        with self.assertRaisesRegex(ValueError,'Stale'):
            s.extend_question('another')

    def test_deadline_expires_without_new_llm_or_wrong_answer(self):
        s,q,clock,b=self.session();clock[0]=3601;s.pulse()
        st=s.public_state()
        self.assertEqual(st['status'],'completed')
        self.assertEqual(len(b.prompts),1)
        self.assertIsNone(st['question'])
        self.assertEqual(s.timekeeper.report()['turns'][0]['outcome'],'time_limit')
        self.assertEqual(s.timekeeper.report()['turns'][0]['active_seconds'],3601)
        rev=s.finish()
        self.assertIn('timing',rev)
        self.assertEqual(rev['timing']['turns'][0]['outcome'],'time_limit')
        self.assertEqual(rev['history'],[])

    def test_finish_preserves_unanswered_duration_without_scoring(self):
        s,q,clock,b=self.session();clock[0]=135
        review=s.finish()
        self.assertEqual(review['timing']['turns'][0]['outcome'],'unfinished')
        self.assertEqual(review['timing']['turns'][0]['active_seconds'],135)
        self.assertEqual(review['history'],[])

if __name__=='__main__':unittest.main()
