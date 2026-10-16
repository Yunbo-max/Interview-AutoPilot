import io
import os
from pathlib import Path
import sys
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'skills/ai-interview/scripts'))
from pypdf import PdfWriter

class CoreTests(unittest.TestCase):
    def test_curriculum_roles_and_minute_totals(self):
        from interview_curriculum import ROLE_PLANS, choose_phase
        self.assertEqual(len(ROLE_PLANS), 6)
        for role, phases in ROLE_PLANS.items():
            self.assertEqual(sum(p['minutes'] for p in phases), 60, role)
            self.assertEqual(phases[0]['id'], 'hr')
            self.assertEqual(choose_phase(role, 0)['id'], 'hr')
            self.assertEqual(choose_phase(role, 59*60)['id'], phases[-1]['id'])
        self.assertIn('math', [p['id'] for p in ROLE_PLANS['quant_research']])
        self.assertIn('coding', [p['id'] for p in ROLE_PLANS['ml_engineer']])
        self.assertIn('generation', [p['id'] for p in ROLE_PLANS['generative_researcher']])

    def test_pdf_extract_valid_and_reject_invalid(self):
        from interview_core import read_resume_pdf
        w=PdfWriter();w.add_blank_page(width=200,height=100)
        out=io.BytesIO();w.write(out)
        with self.assertRaisesRegex(ValueError, 'text'):
            read_resume_pdf(out.getvalue())
        with self.assertRaises(ValueError): read_resume_pdf(b'garbage')
        with self.assertRaises(ValueError): read_resume_pdf(b'%PDF'+b'x'*(9*1024*1024))

    def test_clock_pause_hold_does_not_advance(self):
        from interview_core import SessionClock
        now=[10.0]
        clock=SessionClock(lambda: now[0]);clock.start()
        now[0]=40.0
        self.assertEqual(clock.elapsed(), 30)
        clock.pause();now[0]=400
        self.assertEqual(clock.elapsed(),30)
        clock.resume();now[0]=421
        self.assertEqual(clock.elapsed(),51)

    def test_engine_consented_start_adaptive_and_code(self):
        from interview_core import InterviewSession
        class Fake:
            def __init__(self):self.calls=[]
            def generate(self,prompt,provider):
                self.calls.append(prompt)
                return {'question':'Please justify your baseline.', 'kind':'voice', 'assessment':'Your claim needs a baseline.'}
        fake=Fake();s=InterviewSession(fake)
        s.set_resume_text('I designed an agent runtime and evaluated baselines. ' * 10)
        with self.assertRaisesRegex(ValueError,'consent'):
            s.start('quant_research','qwen',consent=False)
        q=s.start('quant_research','qwen',consent=True)
        self.assertEqual(q['phase'],'hr')
        out=s.submit(q['id'],'Spending twice as many tokens may explain the difference','voice','turn-a')
        self.assertIn('baseline',s.history[0]['assessment'].lower())
        self.assertEqual(s.public_state()['history'][0]['answer_kind'],'voice')
        self.assertEqual(s.submit(q['id'],'Spending twice as many tokens may explain the difference','voice','turn-a')['id'],out['id'])
        with self.assertRaises(ValueError):s.submit(q['id'],'more','voice','turn-b')
        s._clock.elapsed=lambda: 18*60
        q=s.current_question
        self.assertEqual(s.phase()['id'],'math')

    def test_language_and_review_instructions(self):
        from interview_core import InterviewSession
        class Fake:
            def __init__(self):self.prompts=[]
            def generate(self,prompt,provider):
                self.prompts.append(prompt)
                return {'question':'请说明个人贡献','assessment':'Reference: explanation with assumptions'}
        fake=Fake();s=InterviewSession(fake)
        s.set_resume_text('I worked on a quant project with real empirical validation.')
        s.start('quant_research','qwen',True,language='zh')
        self.assertIn('Chinese',fake.prompts[0])
        s.submit(s.current_question['id'],'我负责方法设计','voice','q-answer')
        review=s.finish()
        self.assertIn('reference_solutions',review)
        self.assertIn('review',fake.prompts[-1].lower())

    def test_deadline_does_not_trigger_new_model_call(self):
        from interview_core import InterviewSession
        class Fake:
            def __init__(self): self.count=0
            def generate(self,prompt,provider): self.count+=1;return {'question':'Q','assessment':''}
        f=Fake();s=InterviewSession(f);s.set_resume_text('Resume text')
        q=s.start('quant_developer','codex',True)
        s._clock.elapsed=lambda:3601
        result=s.submit(q['id'],'final answer','voice','s')
        self.assertEqual(result['status'],'completed')
        self.assertEqual(f.count,1)

    def test_failed_model_submission_is_retryable(self):
        from interview_core import InterviewSession
        class Fault:
            def __init__(self):self.count=0
            def generate(self,prompt,provider):
                self.count+=1
                if self.count==2: raise RuntimeError('provider down')
                return {'question':'Explain your contribution','kind':'voice','assessment':'Not checked'}
        m=Fault();s=InterviewSession(m)
        s.set_resume_text('A real CV excerpt')
        q=s.start('ai_researcher','codex',True)
        with self.assertRaises(RuntimeError):s.submit(q['id'],'My contribution','voice','abc')
        self.assertEqual(s.current_question['id'],q['id'])
        self.assertEqual(s.public_state()['history'],[])
        self.assertEqual(s.submit(q['id'],'My contribution','voice','abc')['phase'],'hr')

    def test_completed_review_survives_page_refresh_in_memory(self):
        from interview_core import InterviewSession
        class Fake:
            def generate(self,prompt,provider):
                return {'question':'Q','kind':'voice','assessment':'Assumptions discussed'}
        s=InterviewSession(Fake())
        s.set_resume_text('Resume demonstrates experiments, baselines, coding and research.')
        q=s.start('ai_researcher','codex',True)
        s.submit(q['id'],'I changed the architecture','voice','refresh-test')
        expected=s.finish()
        refreshed=s.public_state()
        self.assertEqual(refreshed['status'],'completed')
        self.assertEqual(refreshed['review']['reference_solutions'],expected['reference_solutions'])
        self.assertEqual(refreshed['review']['history'],expected['history'])

    def test_code_submission_is_not_executed(self):
        from interview_core import InterviewSession
        class Fake:
            def generate(self,prompt,provider):return {'question':'Write a solution','kind':'code','assessment':'Review only'}
        s=InterviewSession(Fake());s.set_resume_text('Projects')
        q=s.start('ml_engineer','gemini',True)
        self.assertEqual(q['kind'],'voice') # HR enforces voice first
        s._clock.elapsed=lambda: 16*60
        nextq=s.submit(q['id'],'My project detail','voice','id1')
        self.assertEqual(nextq['kind'],'code')
        s.submit(nextq['id'],'import os;os.system("touch /tmp/evil")','code','id2')
        self.assertFalse(Path('/tmp/evil').exists())

if __name__=='__main__':unittest.main()
