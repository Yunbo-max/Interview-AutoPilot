"""Installable skill and explicit /profile /scrape /rank /interview /memory /trends commands."""
from pathlib import Path
import json
import unittest
ROOT=Path(__file__).resolve().parents[1]
SKILL=ROOT/'skills/ai-interview'
class PackagingTests(unittest.TestCase):
    def test_version_and_entrypoints(self):
        self.assertEqual((ROOT/'VERSION').read_text().strip(),'0.4.0')
        self.assertTrue((SKILL/'scripts/career.py').is_file())
        self.assertTrue((SKILL/'references/career-workflow.md').is_file())
        self.assertIn('career-workflow.md',(SKILL/'SKILL.md').read_text())
        for name in ('profile','scrape','rank','interview','memory','trends'):
            self.assertTrue((ROOT/'.claude/commands'/f'{name}.md').is_file(),name)
        self.assertFalse((ROOT/'.claude/commands/apply.md').exists())
    def test_private_workspace_is_gitignored(self):
        text=(ROOT/'.gitignore').read_text()
        for name in ('profile.json','jobs.json','memory.json','papers.json'):
            self.assertIn(name,text)
    def test_cross_host_contract_is_honest(self):
        readme=(ROOT/'README.md').read_text()
        self.assertIn('LinkedIn',readme)
        self.assertIn('Greenhouse',readme)
        self.assertIn('Lever',readme)
        self.assertIn('arXiv',readme)
        self.assertIn('no automatic applications',readme.lower())
if __name__=='__main__':unittest.main()
