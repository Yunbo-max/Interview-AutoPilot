import json,os,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'skills/ai-interview/scripts'))

class ModelTests(unittest.TestCase):
    def test_supported_providers_and_missing_keys(self):
        from interview_models import ModelRouter, PROVIDERS
        self.assertEqual(set(PROVIDERS),{'codex','claude','gemini','qwen','deepseek','glm','kimi'})
        r=ModelRouter(environ={},which=lambda x:None)
        with self.assertRaisesRegex(RuntimeError,'API key'):
            r.generate('q','qwen')
        with self.assertRaisesRegex(RuntimeError,'installed'):
            r.generate('q','claude')
        with self.assertRaises(ValueError):r.generate('q','malicious')

    def test_json_extraction_rejects_prose(self):
        from interview_models import parse_model_json
        self.assertEqual(parse_model_json('```json\n{"question":"Test?","assessment":""}\n```')['question'],'Test?')
        with self.assertRaisesRegex(RuntimeError,'JSON'):
            parse_model_json('The answer is X')
        with self.assertRaises(RuntimeError):parse_model_json('{"assessment":"x"}')

    def test_all_four_api_transports_fixed_endpoints(self):
        from interview_models import ModelRouter
        seen=[]
        env={'DASHSCOPE_API_KEY':'QKEY','DEEPSEEK_API_KEY':'DKEY','ZAI_API_KEY':'GKEY','MOONSHOT_API_KEY':'KKEY'}
        def fake(url,key,body):
            seen.append((url,key,body))
            return {'choices':[{'message':{'content':'{"question":"Why?","assessment":""}'}}]}
        r=ModelRouter(environ=env,http_post=fake)
        for provider in ('qwen','deepseek','glm','kimi'):
            self.assertEqual(r.generate('resume context',provider)['question'],'Why?')
        self.assertTrue(all(url.startswith('https://') and url.endswith('/chat/completions') for url,_,_ in seen))
        self.assertEqual(len(set(x[0] for x in seen)),4)
        self.assertNotIn('DKEY',str(seen[1][2]))

    def test_cli_invokes_argument_array_not_shell(self):
        from interview_models import ModelRouter
        calls=[]
        def fake(argv,stdin,timeout):
            calls.append((argv,stdin,timeout))
            return '{"question":"Next","assessment":""}'
        r=ModelRouter(run_cli=fake,which=lambda x:'/usr/bin/'+x)
        for p in ('codex','claude','gemini'):
            self.assertEqual(r.generate('Candidate says `rm -rf /`',p)['question'],'Next')
        for args,stdin,timeout in calls:
            self.assertIsInstance(args,list)
            self.assertIn('rm -rf /',stdin)
            self.assertGreater(timeout,0)
            self.assertNotIn('danger-full-access',args)

    def test_excessive_prompt_or_invalid_response(self):
        from interview_models import ModelRouter
        r=ModelRouter(environ={'DEEPSEEK_API_KEY':'key'},http_post=lambda *_:{'choices':[]})
        with self.assertRaises(RuntimeError):r.generate('hi','deepseek')
        with self.assertRaises(ValueError):r.generate('x'*100000,'deepseek')

if __name__=='__main__':unittest.main()
