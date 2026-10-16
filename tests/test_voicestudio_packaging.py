"""Portable Skill includes only our MIT interoperability code, not upstream AGPL assets."""
import json
import sys
from pathlib import Path
import subprocess
import tempfile
import shutil
import unittest
ROOT=Path(__file__).resolve().parents[1]
SKILL=ROOT/'skills/ai-interview'

class VoiceStudioPackagingTests(unittest.TestCase):
    def test_versions_match_with_optional_adapter(self):
        for p in (ROOT/'VERSION',SKILL/'VERSION'):
            self.assertEqual(p.read_text(encoding='utf-8').strip(),'0.5.0')
        for p in (ROOT/'plugin.json',ROOT/'.codex-plugin/plugin.json'):
            self.assertEqual(json.loads(p.read_text(encoding='utf-8'))['version'],'0.5.0')
    def test_self_contained_skill_installs_without_upstream(self):
        for name in ('scripts/voicestudio_adapter.py','scripts/voicestudio_relay.py',
                     'scripts/requirements-voicestudio.txt',
                     'references/voicestudio-backend.md'):
            self.assertTrue((SKILL/name).is_file(),name)
        self.assertIn('voicestudio-backend.md',(SKILL/'SKILL.md').read_text(encoding='utf-8'))
        with tempfile.TemporaryDirectory() as td:
            target=Path(td)/'Portable Interview Skill'
            shutil.copytree(SKILL,target,ignore=shutil.ignore_patterns('__pycache__'))
            program=target/'scripts/interview_studio.py'
            r=subprocess.run([sys.executable,str(program),'doctor','--voicestudio','--voicestudio-url','http://127.0.0.1:1'],
                 capture_output=True,text=True,timeout=15,cwd=td)
            self.assertEqual(r.returncode,0,r.stderr)
            data=json.loads(r.stdout)
            self.assertFalse(data['voicestudio']['available'])
    def test_docs_include_no_auto_download_and_privacy_boundaries(self):
        docs=(SKILL/'references/voicestudio-backend.md').read_text(encoding='utf-8')
        for term in ('AGPL-3.0','/v1/audio/speech','/v1/audio/transcriptions/stream',
                     'releases/latest','--voicestudio','no automatic install','remote'):
            self.assertIn(term.lower(),docs.lower())
        self.assertTrue((ROOT/'docs/VOICESTUDIO-INTEGRATION.md').is_file())
        self.assertTrue((ROOT/'docs/VOICESTUDIO-VERIFICATION.md').is_file())
        self.assertFalse((ROOT/'.github/workflows').exists())
    def test_no_third_party_source_bundled(self):
        self.assertFalse((SKILL/'voicestudio').exists())
        self.assertFalse((ROOT/'voicestudio').exists())
        self.assertFalse(list(SKILL.glob('**/*.safetensors')))
if __name__=='__main__':unittest.main()
