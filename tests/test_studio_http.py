import http.client, io, json,sys,threading,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'skills/ai-interview/scripts'))
from pypdf import PdfWriter

class HttpTests(unittest.TestCase):
    def setUp(self):
        from interview_studio import StudioState,make_server
        class Router:
            def availability(self):return [{'id':'codex','configured':True,'kind':'cli'}]
            def generate(self,prompt,provider):return {'question':'Explain a claim from your resume','assessment':'Evidence still needed'}
        self.state=StudioState(Router(),speech=None,token='secret-test')
        self.server=make_server(self.state,0)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True,kwargs={'poll_interval':.02})
        self.thread.start()
        self.origin=self.state.origin
        writer=PdfWriter();page=writer.add_blank_page(400,400)
        # pypdf cannot create text without extra deps, patch text parser for the HTTP flow.
        out=io.BytesIO();writer.write(out)
        self.pdf=out.getvalue()

    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join(3)

    def req(self,method,path,body=None,headers=None,auth=True):
        h={'Origin':self.origin}
        if auth:h['Authorization']='Bearer secret-test'
        if headers:h.update(headers)
        c=http.client.HTTPConnection('127.0.0.1',self.server.server_address[1],timeout=5)
        c.request(method,path,body,headers=h)
        r=c.getresponse();status=r.status;raw=r.read();c.close()
        try:data=json.loads(raw)
        except Exception:data=raw
        return status,data

    def test_no_upload_or_session_automatically(self):
        status,data=self.req('GET','/api/state')
        self.assertEqual(status,200);self.assertFalse(data['resume_loaded']);self.assertEqual(data['status'],'setup')
        self.assertEqual(self.req('GET','/api/providers')[0],200)

    def test_denies_foreign_origin_bad_token(self):
        self.assertEqual(self.req('GET','/api/state',auth=False)[0],403)
        self.assertEqual(self.req('GET','/api/state',headers={'Origin':'https://attacker.invalid'})[0],403)

    def test_pdf_then_start_then_voice_answer(self):
        with patch('interview_studio.read_resume_pdf',return_value='My project uses transformers and RAG'):
            status,preview=self.req('POST','/api/resume',self.pdf,{'Content-Type':'application/pdf'})
        self.assertEqual(status,200);self.assertIn('project',preview['preview'])
        req={'role':'agent_engineer','provider':'codex','consent':True}
        status,data=self.req('POST','/api/start',json.dumps(req).encode(),{'Content-Type':'application/json'})
        self.assertEqual(status,200);self.assertEqual(data['kind'],'voice')
        status,result=self.req('POST','/api/answer',json.dumps({'question_id':data['id'],'text':'It is an agent harness.','kind':'voice','submission_id':'once'}).encode(),{'Content-Type':'application/json'})
        self.assertEqual(status,200);self.assertNotEqual(result['id'],data['id'])
        self.assertEqual(self.req('GET','/api/state')[1]['history'][0]['answer_kind'],'voice')
        status,_=self.req('POST','/api/answer',json.dumps({'question_id':data['id'],'text':'other','kind':'voice','submission_id':'twice'}).encode(),{'Content-Type':'application/json'})
        self.assertEqual(status,409)

    def test_upload_rejects_other_content(self):
        self.assertEqual(self.req('POST','/api/resume',b'hello',{'Content-Type':'application/pdf'})[0],400)
        self.assertEqual(self.req('POST','/api/resume',b'hello',{'Content-Type':'text/plain'})[0],415)
        self.assertEqual(self.req('GET','/../secret.txt')[0],404)

    def test_without_speech_falls_back_to_typing(self):
        self.assertEqual(self.req('POST','/api/transcribe',b'fake',{'Content-Type':'audio/webm'})[0],503)
        status,html=self.req('GET','/')
        self.assertEqual(status,200)
        self.assertIn(b'upload',html)

if __name__=='__main__':unittest.main()
