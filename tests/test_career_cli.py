"""CLI boundaries and no-apply workflow integration; no external network requests."""
from pathlib import Path
from io import StringIO
import contextlib
import json
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'skills/ai-interview/scripts'))
import career

class CareerCLITests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.workspace=self.root/'private'
    def tearDown(self):self.temp.cleanup()
    def invoke(self,*args):
        output=StringIO()
        with contextlib.redirect_stdout(output):
            rc=career.main(['--workspace',str(self.workspace),*args])
        return rc,json.loads(output.getvalue())

    def test_profile_scrape_rank_memory_round_trip(self):
        cv=self.root/'resume.txt';cv.write_text('ML Engineer. Python PyTorch deployment and MLOps.',encoding='utf-8')
        rc,o=self.invoke('profile','--resume',str(cv),'--role','ml_engineer')
        self.assertEqual(rc,0,o);self.assertTrue(Path(o['private_cv_draft']).exists())
        jd=self.root/'job.txt';jd.write_text('PyTorch Python inference engineer',encoding='utf-8')
        rc,o=self.invoke('scrape','--import-description',str(jd),'--title','ML Engineer',
                         '--company','Example','--url','https://jobs.example.org/example')
        self.assertEqual(rc,0,o)
        rc,o=self.invoke('rank')
        self.assertEqual(rc,0,o);self.assertEqual(len(o['jobs']),1)
        rc,o=self.invoke('memory','--topic','Transformer Attention','--status','demonstrated')
        self.assertEqual(rc,0,o)
        rc,o=self.invoke('memory','--show')
        self.assertEqual(rc,0,o);self.assertEqual(o['topics'][0]['status'],'demonstrated')
        self.assertNotIn('source_text',json.dumps(o))

    def test_linkedin_is_link_generation_not_a_scraper(self):
        with patch('career.get_public_bytes',side_effect=AssertionError('unexpected network request')):
            rc,o=self.invoke('scrape','--linkedin','Agent Engineer','--location','London')
        self.assertEqual(rc,0);self.assertEqual(o['status'],'browser_link')
        self.assertIn('linkedin.com/jobs/search',o['url'])

    def test_profile_external_polish_requires_separate_permission(self):
        cv=self.root/'resume.txt';cv.write_text('I designed models and compared experiments.',encoding='utf-8')
        rc,o=self.invoke('profile','--resume',str(cv),'--role','ai_researcher','--polish-with','codex')
        self.assertEqual(rc,1)
        self.assertIn('--allow-model-transfer',o['error'])
        self.assertFalse((self.workspace/'profile.json').exists(), 'lack of transfer consent must fail before changing personal state')

    def test_arxiv_refresh_records_real_source_metadata_fixture(self):
        feed='''<feed xmlns="http://www.w3.org/2005/Atom"><entry>
            <id>https://arxiv.org/abs/2610.01999</id><title>Transformer architecture improvements</title>
            <published>2026-10-15T00:00:00Z</published><summary>Attention alternatives and architecture tradeoffs.</summary>
            </entry></feed>'''.encode()
        with patch('career.get_public_bytes',return_value=feed) as call:
            rc,o=self.invoke('trends','--role','ai_researcher','--source','arxiv')
        self.assertEqual(rc,0,o);self.assertEqual(o['count'],1)
        self.assertIn('export.arxiv.org',call.call_args.args[0])
        self.assertEqual(career.CareerWorkspace(self.workspace).papers()[0]['source'],'arxiv')

    def test_trend_fetch_failure_never_claims_freshness(self):
        with patch('career.get_public_bytes',side_effect=RuntimeError('source timeout')):
            rc,o=self.invoke('trends','--role','ai_researcher')
        self.assertEqual(rc,1)
        self.assertEqual(o['status'],'error')
        self.assertFalse((self.workspace/'papers.json').exists())

    def test_no_apply_command_and_no_auto_application(self):
        out=StringIO();err=StringIO()
        with contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):
            with self.assertRaises(SystemExit):
                career.main(['--workspace',str(self.workspace),'apply'])
        self.assertIn('invalid choice',err.getvalue())
        self.assertFalse(self.workspace.exists())

if __name__=='__main__':unittest.main()
