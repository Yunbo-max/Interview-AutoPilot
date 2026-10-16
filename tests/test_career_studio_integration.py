"""Optional candidate-consented current papers and evidence reach the interview engine."""
import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch
import sys
import tempfile
import threading
import unittest
import http.client
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'skills/ai-interview/scripts'))
from career import CareerWorkspace
from interview_core import InterviewSession

NOW=datetime(2026,10,16,tzinfo=timezone.utc)
PAPER={'id':'2610.01234','title':'Agent harness and tool use','summary':'Planning tool use and execution',
       'url':'https://arxiv.org/abs/2610.01234','role':'agent_engineer','source':'arxiv',
       'retrieved_at':NOW.isoformat(),'published_at':NOW.isoformat()}

class Model:
    def __init__(self):self.calls=[]
    def availability(self):return [{'id':'codex','kind':'cli','configured':True}]
    def generate(self,prompt,provider):
        self.calls.append(prompt)
        return {'question':'Explain your contribution','assessment':'Please justify it'}

class BriefTests(unittest.TestCase):
    def test_briefing_only_non_hr_phase_and_never_diagnoses_forgetting(self):
        model=Model(); s=InterviewSession(model)
        s.set_resume_text('Agent harness engineering experiments')
        q=s.start('agent_engineer','codex',True,trend_brief='source: arxiv | Agent harness 2610.01234',
                  memory_brief='Agent harness: last observed 200 days ago; review due, not lost ability')
        self.assertNotIn('2610.01234',model.calls[0])
        s._clock.elapsed=lambda:46*60
        s.submit(q['id'],'A factual explanation','voice','trial1')
        self.assertIn('2610.01234',model.calls[-1])
        self.assertIn('not evidence of forgetting',model.calls[-1])

class StudioEvidenceTests(unittest.TestCase):
    def setUp(self):
        from interview_studio import StudioState,make_server
        self.tmp=tempfile.TemporaryDirectory()
        self.ws=CareerWorkspace(Path(self.tmp.name)/'private')
        self.ws.write_papers([PAPER])
        self.ws.remember_topic('Agent harness','needs_practice','candidate_confirmed',today=NOW)
        self.model=Model()
        self.state=StudioState(self.model,speech=None,token='this-test-token',workspace=self.ws)
        self.server=make_server(self.state,port=0)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True,kwargs={'poll_interval':.02})
        self.thread.start()
        self.state.interview.set_resume_text('Agent engineer research project')
    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join(2);self.tmp.cleanup()
    def request(self,method,path,payload=None):
        conn=http.client.HTTPConnection('127.0.0.1',self.server.server_address[1],timeout=5)
        headers={'Authorization':'Bearer this-test-token','Origin':self.state.origin}
        if payload is not None:payload=json.dumps(payload).encode();headers['Content-Type']='application/json'
        conn.request(method,path,payload,headers);r=conn.getresponse();d=json.loads(r.read());status=r.status;conn.close()
        return status,d
    def test_review_memory_write_requires_explicit_user_request(self):
        self.assertEqual(self.ws.memory()['sessions'],[])
        self.state.interview.start('agent_engineer','codex',True)
        self.state.interview.finish()
        self.assertEqual(self.ws.memory()['sessions'],[])
        status,response=self.request('POST','/api/save-memory',{'confirm':True})
        self.assertEqual(status,200,response)
        self.assertEqual(response['status'],'saved')
        self.assertEqual(self.ws.memory()['sessions'][0]['role'],'agent_engineer')
        self.assertEqual(self.ws.memory()['sessions'][0]['source'],'model_unverified')
        self.assertFalse(any('answer' in x for x in self.ws.memory()['sessions']))

    def test_memory_export_rejected_while_not_completed(self):
        status,response=self.request('POST','/api/save-memory',{'confirm':True})
        self.assertEqual(status,409,response)
        self.assertEqual(self.ws.memory()['sessions'],[])

    def test_selected_ranked_job_shapes_hr_questions_without_fabrication(self):
        job=self.ws.add_job('Agent Engineer','Example Research','https://jobs.example.org/agent',
            'Agent harness evaluation, production observability, Python and tool calling')
        status,data=self.request('GET','/api/jobs')
        self.assertEqual(status,200)
        self.assertEqual(len(data['jobs']),1)
        self.assertNotIn('description',data['jobs'][0], 'do not expose full JD list unless selected')
        status,result=self.request('POST','/api/start',{
            'role':'agent_engineer','provider':'codex','consent':True,'job_id':job['id']})
        self.assertEqual(status,200,result)
        self.assertIn('production observability',self.model.calls[0])
        self.assertEqual(result['phase'],'hr')

    def test_unknown_job_selection_rejected(self):
        status,result=self.request('POST','/api/start',{
            'role':'agent_engineer','provider':'codex','consent':True,'job_id':'nonexistent'})
        self.assertEqual(status,409,result)
        self.assertEqual(self.state.interview.status,'setup')

    def test_studio_evidence_status_no_remote_fetch(self):
        code,data=self.request('GET','/api/evidence-summary?role=agent_engineer')
        self.assertEqual(code,200)
        self.assertEqual(data['recent_papers'],1)
        self.assertEqual(data['memory_topics'],1)
    def test_invalid_paper_feed_fails_cleanly_without_fake_freshness(self):
        with patch('interview_studio.get_public_bytes',return_value=b'<not-xml'):
            status,result=self.request('POST','/api/trends-refresh',{'role':'agent_engineer','source':'arxiv'})
        self.assertEqual(status,502,result)
        self.assertIn('error',result)

    def test_research_refresh_requires_explicit_click_and_uses_fixed_host(self):
        feed=('<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom">'
              '<entry><id>https://arxiv.org/abs/2610.06789</id><title>Reliable agent tools</title>'
              '<published>2026-10-15T00:00:00Z</published>'
              '<summary>Tool use planning and model execution.</summary></entry></feed>').encode()
        with patch('interview_studio.get_public_bytes',return_value=feed) as fetch:
            code,data=self.request('POST','/api/trends-refresh',{'role':'agent_engineer','source':'arxiv'})
        self.assertEqual(code,200,data)
        self.assertEqual(data['count'],1)
        self.assertIn('export.arxiv.org',fetch.call_args.args[0])
        self.assertTrue(any(p.get('id')=='2610.06789' for p in self.ws.papers()))
        self.assertEqual(self.request('POST','/api/trends-refresh',{'role':'invalid','source':'arxiv'})[0],409)

    def test_explicit_flags_attach_only_cached_briefing(self):
        code,data=self.request('POST','/api/start',{'role':'agent_engineer','provider':'codex','consent':True,
            'use_trends':True,'use_memory':True})
        self.assertEqual(code,200)
        self.assertEqual(data['phase'],'hr')
        self.assertTrue(self.state.interview.trend_brief)
        self.assertTrue(self.state.interview.memory_brief)
        self.assertNotIn('arxiv',self.model.calls[0])

if __name__=='__main__':unittest.main()
