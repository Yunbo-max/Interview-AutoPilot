"""Offline contract tests: never install packages, touch a real Mac, or download apps."""
from __future__ import annotations

import importlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'skills' / 'ai-interview' / 'scripts'
sys.path.insert(0, str(SCRIPTS))


class OneClickTests(unittest.TestCase):
    def setUp(self):
        self.mod = importlib.import_module('mac_bootstrap')
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)

    @staticmethod
    def fixture_release(name='VoiceStudio-Electron-0.5.6-mac-arm64.dmg'):
        base = 'https://github.com/debpalash/VoiceStudio/releases/download/v0.5.6/'
        return {'tag_name': 'v0.5.6', 'prerelease': False,
                'assets': [{'name': name, 'browser_download_url': base + name, 'size': 267000000},
                           {'name': 'SHA256SUMS.txt', 'browser_download_url': base+'SHA256SUMS.txt', 'size': 1885}]}

    def test_release_metadata_allowlist(self):
        spec = self.mod.select_release(self.fixture_release())
        self.assertEqual(spec.version, 'v0.5.6')
        self.assertTrue(spec.dmg_url.startswith('https://github.com/debpalash/VoiceStudio/releases/download/'))
        self.assertEqual(spec.dmg_filename, 'VoiceStudio-Electron-0.5.6-mac-arm64.dmg')
        self.assertEqual(spec.size, 267000000)

    def test_rejects_untrusted_asset_and_unstable_tag(self):
        for change in ('domain', 'filename', 'prerelease', 'tag'):
            with self.subTest(change=change):
                metadata=self.fixture_release()
                if change == 'domain': metadata['assets'][0]['browser_download_url'] = 'https://evil.example/VoiceStudio.dmg'
                if change == 'filename': metadata['assets'][0]['name'] = 'unsigned-package.dmg'
                if change == 'prerelease': metadata['prerelease'] = True
                if change == 'tag': metadata['tag_name'] = 'v0.5.6; echo BAD'
                with self.assertRaises(ValueError): self.mod.select_release(metadata)

    def test_checksum_parser_accepts_only_exact_filename(self):
        filename='VoiceStudio-Electron-0.5.6-mac-arm64.dmg'
        sha='a'*64
        data=f'{sha}  {filename}\n'+'b'*64+'  other.dmg\n'
        self.assertEqual(self.mod.checksum_for(data, filename),sha)
        with self.assertRaises(ValueError):self.mod.checksum_for(data, 'missing.dmg')
        with self.assertRaises(ValueError):self.mod.checksum_for(data+('b'*64)+f'  {filename}\n', filename)

    def test_simulated_official_dmg_install_is_checksummed_and_no_sudo(self):
        import hashlib
        import plistlib
        import shutil
        import subprocess
        filename='VoiceStudio-Electron-0.5.6-mac-arm64.dmg'
        fake_payload=b'A'*(20*1024*1024)
        meta=self.fixture_release()
        meta['assets'][0]['size']=len(fake_payload)
        sha=hashlib.sha256(fake_payload).hexdigest()
        actions=[]
        def fake_download(spec, dest):
            dest.write_bytes(fake_payload)
        def fake_run(argv, **kwargs):
            actions.append(argv)
            if argv[:2]==['hdiutil','attach']:
                root=Path(argv[argv.index('-mountroot')+1]);mount=root/'VoiceStudio'
                (mount/'VoiceStudio.app/Contents').mkdir(parents=True)
                (mount/'VoiceStudio.app/Contents/Info.plist').write_text('fixture')
                return subprocess.CompletedProcess(argv,0,plistlib.dumps({'system-entities':[{'mount-point':str(mount)}]}),b'')
            if argv[0]=='ditto':
                shutil.copytree(argv[-2],argv[-1])
            return subprocess.CompletedProcess(argv,0,b'',b'')
        with mock.patch('platform.system',return_value='Darwin'),mock.patch('platform.machine',return_value='arm64'):
            with mock.patch('platform.mac_ver',return_value=('14.5',('', '', ''),'arm64')):
                with mock.patch.object(self.mod,'download_release',side_effect=fake_download):
                    with mock.patch('subprocess.run',side_effect=fake_run):
                        app=self.mod.install_voicestudio_app(self.home,release_data=meta,manifest=f'{sha}  {filename}\n')
        self.assertEqual(app,self.home/'Applications/VoiceStudio.app')
        self.assertTrue((app/'Contents/Info.plist').is_file())
        self.assertEqual(actions[0][0:2],['hdiutil','attach'])
        self.assertIn('-readonly',actions[0])
        self.assertEqual(actions[1][0],'ditto')
        self.assertEqual(actions[-1][0:2],['hdiutil','detach'])
        self.assertFalse(any('sudo' in str(arg) for a in actions for arg in a))

    def test_portable_skill_can_dry_run_without_repository(self):
        import shutil
        import subprocess
        with tempfile.TemporaryDirectory() as td:
            target=Path(td)/'installed Skill with spaces'
            shutil.copytree(ROOT/'skills/ai-interview',target,ignore=shutil.ignore_patterns('__pycache__'))
            run=subprocess.run([sys.executable,str(target/'scripts/mac_bootstrap.py'),'--dry-run'],
                               cwd=td,capture_output=True,text=True,timeout=8)
            self.assertEqual(run.returncode,0,run.stderr)
            self.assertEqual(json.loads(run.stdout)['status'],'dry_run_no_changes')

    def test_checksum_verification_rejects_wrong_file(self):
        p=self.home/'voice.dmg'
        p.write_bytes(b'fake image bytes')
        import hashlib
        valid=hashlib.sha256(b'fake image bytes').hexdigest()
        self.mod.verify_download(p,valid,expected_size=len(b'fake image bytes'))
        with self.assertRaises(ValueError):self.mod.verify_download(p,'0'*64,expected_size=len(b'fake image bytes'))
        with self.assertRaises(ValueError):self.mod.verify_download(p,valid,expected_size=44)

    def test_skill_links_never_overwrite_without_optin(self):
        src=ROOT/'skills/ai-interview'
        dest=self.home/'.agents/skills/ai-interview'
        dest.parent.mkdir(parents=True)
        dest.mkdir()
        (dest/'SKILL.md').write_text('old user installation')
        with self.assertRaises(FileExistsError):self.mod.install_skill_link(src,dest,self.home,allow_backup=False)
        self.assertEqual((dest/'SKILL.md').read_text(),'old user installation')
        result=self.mod.install_skill_link(src,dest,self.home,allow_backup=True)
        self.assertEqual(result,'installed')
        self.assertTrue(dest.is_symlink())
        self.assertEqual(dest.resolve(),src.resolve())
        self.assertTrue(list((self.home/'.local/share/ai-interview/skill-backups').glob('ai-interview-*')))
        self.assertEqual(self.mod.install_skill_link(src,dest,self.home,allow_backup=False),'already_installed')

    def test_standalone_skill_path_detection(self):
        source=self.mod.locate_skill_dir(Path(__file__).resolve())
        self.assertIsNone(source)  # not anywhere inside skill
        source=self.mod.locate_skill_dir(SCRIPTS/'mac_bootstrap.py')
        self.assertEqual(source,ROOT/'skills/ai-interview')

    def test_dry_run_has_no_writes_or_external_calls(self):
        with mock.patch.object(self.mod,'download_release',side_effect=AssertionError('downloaded')):
            with mock.patch.object(self.mod,'install_dependencies',side_effect=AssertionError('pip executed')):
                summary=self.mod.dry_run_plan(ROOT/'skills/ai-interview',self.home,mac_machine='arm64')
        self.assertIn('VoiceStudio',summary['optional_third_party'])
        self.assertIn('whisper',summary['local_speech_fallback'].lower())
        self.assertFalse((self.home/'.agents').exists())

    def test_minimum_voice_studio_macos_version(self):
        self.assertFalse(self.mod.macos_version_supports_voice('12.7.9'))
        self.assertFalse(self.mod.macos_version_supports_voice('13.2'))
        self.assertFalse(self.mod.macos_version_supports_voice(''))
        self.assertTrue(self.mod.macos_version_supports_voice('13.3'))
        self.assertTrue(self.mod.macos_version_supports_voice('15.2.1'))

    def test_intel_cannot_install_voicestudio_locally(self):
        self.assertEqual(self.mod.voice_platform_recommendation('Darwin','x86_64'), 'unsupported_intel_mac')
        self.assertEqual(self.mod.voice_platform_recommendation('Darwin','arm64'), 'supported_apple_silicon')
        self.assertEqual(self.mod.voice_platform_recommendation('Linux','x86_64'), 'not_macos')

    def test_bash_invocation_of_finder_command_reaches_platform_gate(self):
        import subprocess
        result=subprocess.run(['bash',str(ROOT/'AI-Interview.command'),'--dry-run'],capture_output=True,text=True,timeout=6)
        self.assertEqual(result.returncode,2)
        self.assertIn('macOS',result.stderr)
        self.assertNotIn('unbound variable',result.stderr)

    def test_mac_wrapper_and_agent_instructions_exist(self):
        self.assertTrue((ROOT/'AI-Interview.command').is_file())
        self.assertTrue((SCRIPTS/'one-click-mac.sh').is_file())
        self.assertTrue((ROOT/'skills/ai-interview/references/one-click-mac.md').is_file())
        self.assertIn('one-click-mac', (ROOT/'AGENTS.md').read_text())
        self.assertIn('one-click-mac.md', (ROOT/'skills/ai-interview/SKILL.md').read_text())

    def test_official_urls_not_remote_shell_execution(self):
        text=(SCRIPTS/'mac_bootstrap.py').read_text()
        self.assertNotIn('curl | sh',text)
        self.assertNotIn('shell=True',text)
        self.assertIn('SHA256', (ROOT/'skills/ai-interview/references/one-click-mac.md').read_text())


class DaemonContractTests(unittest.TestCase):
    def setUp(self):
        self.mod=importlib.import_module('mac_bootstrap')

    def test_accepts_only_our_local_url_and_token(self):
        url='http://127.0.0.1:12345/#token=MySecretToken-123'
        self.assertEqual(self.mod.validate_private_url(url),url)
        for hostile in ('http://evil.example/#token=x', 'https://127.0.0.1:12345/#token=x',
                        'http://localhost:12345/#token=x',
                        'http://127.0.0.1:12345/#token=x&next=http://bad.example',
                        'http://127.0.0.1:12345/api/delete#token=x',
                        'http://127.0.0.1:12345/#token=',
                        'http://127.0.0.1:12345/#token=x\nBAD'):
            with self.subTest(hostile=hostile):
                with self.assertRaises(ValueError):self.mod.validate_private_url(hostile)

    def test_reuses_valid_server_without_launching_duplicate(self):
        with tempfile.TemporaryDirectory() as td:
            home=Path(td)
            meta=self.mod.runtime_home(home)/'studio-session.json'
            meta.parent.mkdir(parents=True)
            meta.write_text(json.dumps({'url':'http://127.0.0.1:12345/#token=abc123', 'pid':123}))
            with mock.patch.object(self.mod,'check_interview_health',return_value=True):
                with mock.patch('subprocess.Popen',side_effect=AssertionError('unwanted duplicate process')):
                    result=self.mod.get_running_session(home)
            self.assertEqual(result['pid'],123)

    def test_refuses_invalid_session_metadata(self):
        with tempfile.TemporaryDirectory() as td:
            home=Path(td)
            meta=self.mod.runtime_home(home)/'studio-session.json'
            meta.parent.mkdir(parents=True)
            meta.write_text(json.dumps({'url':'http://example.com/#token=leak', 'pid':44}))
            with mock.patch.object(self.mod,'check_interview_health',side_effect=AssertionError('attempted untrusted fetch')):
                self.assertIsNone(self.mod.get_running_session(home))

    def test_graceful_shutdown_endpoint_and_authenticated_session(self):
        # Inspects the reviewed controller; full HTTP behavior is checked in test_studio_http.
        src=(ROOT/'skills/ai-interview/scripts/interview_studio.py').read_text()
        self.assertIn('/api/shutdown',src)
        self.assertIn('self.server.shutdown',src)

    def test_script_agents_return_after_launch(self):
        src=(SCRIPTS/'mac_bootstrap.py').read_text()
        self.assertIn('start_new_session=True',src)
        self.assertIn("'--no-browser'",src)
        self.assertIn('studio-session.json',src)
        self.assertNotIn('shell=True',src)

class RunningLocalStudioTests(unittest.TestCase):
    def setUp(self):
        self.mod=importlib.import_module('mac_bootstrap')
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home=Path(self.temp.name)

    def test_authenticated_shutdown_round_trip_via_real_local_http(self):
        from interview_studio import StudioState, make_server
        state=StudioState(token='local-test-secret')
        server=make_server(state,0)
        thread=__import__('threading').Thread(target=server.serve_forever,daemon=True)
        thread.start()
        try:
            port=server.server_address[1]
            link=f'http://127.0.0.1:{port}/#token=local-test-secret'
            self.assertTrue(self.mod.check_interview_health(link))
            self.mod._write_private_json(self.mod.session_file(self.home),{'pid':os.getpid(),'url':link})
            self.assertEqual(self.mod.get_running_session(self.home)['pid'],os.getpid())
            with mock.patch('http.client.HTTPSConnection',side_effect=AssertionError('external net')):
                self.assertEqual(self.mod.stop_interview(self.home),0)
            thread.join(2)
            self.assertFalse(thread.is_alive())
            self.assertFalse(self.mod.session_file(self.home).exists())
        finally:
            server.shutdown()
            server.server_close()
            thread.join(2)

    def test_agent_launch_returns_without_waiting_for_the_interview(self):
        # Actual local web-server process, typed-only (no models or microphone).
        runtime=self.mod.runtime_home(self.home)
        (runtime/'.venv/bin').mkdir(parents=True)
        (runtime/'.venv/bin/python').symlink_to(sys.executable)
        skill=ROOT/'skills/ai-interview'
        with mock.patch('webbrowser.open',return_value=True):
            try:
                code=self.mod.launch_interview(self.home,skill,try_voicestudio=False)
                self.assertEqual(code,0)
                session=self.mod.get_running_session(self.home)
                self.assertIsNotNone(session)
                with mock.patch('subprocess.Popen',side_effect=AssertionError('duplicate service')):
                    self.mod.launch_interview(self.home,skill,try_voicestudio=False)
            finally:
                self.mod.stop_interview(self.home)

if __name__=="__main__": unittest.main()
