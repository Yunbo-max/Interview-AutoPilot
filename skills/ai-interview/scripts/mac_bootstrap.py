#!/usr/bin/env python3
"""Consent-aware one-command Mac launcher for the self-contained AI Interview Skill.

This module NEVER executes downloaded shell scripts. It downloads only the
independent, official VoiceStudio DMG and SHA256SUMS, verifies the exact asset,
and copies the app into ~/Applications. First-run models, macOS Gatekeeper,
and microphone permission remain controlled by the user.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import plistlib
import re
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener

VOICE_REPO = 'debpalash/VoiceStudio'
RELEASE_API = f'https://api.github.com/repos/{VOICE_REPO}/releases/latest'
RELEASE_ROOT = f'https://github.com/{VOICE_REPO}/releases/download/'
MAX_RELEASE_JSON = 1024 * 1024
MAX_CHECKSUM_TEXT = 256 * 1024
MAX_DMG_BYTES = 900 * 1024 * 1024
MIN_VOICESTUDIO_DISK = 10 * 1000 * 1000 * 1000
MIN_PYTHON = (3, 10)
# Hold intentionally detached child handles until the short-lived launcher exits.
_DETACHED_PROCESSES: list[subprocess.Popen] = []


class BootstrapError(RuntimeError):
    """Recoverable setup failure; never treated as an interview failure."""


@dataclass(frozen=True)
class VoiceRelease:
    version: str
    dmg_filename: str
    dmg_url: str
    checksum_url: str
    size: int


def locate_skill_dir(script: Path) -> Path | None:
    """Support standalone Skill copies even when their parent folder is renamed."""
    script = Path(script).resolve()
    folder = script.parent.parent
    entry = folder / 'SKILL.md'
    if not entry.is_file():
        return None
    try:
        header = entry.read_text(encoding='utf-8')[:1024]
    except (OSError,UnicodeError):
        return None
    return folder if re.search(r'(?m)^name:\s*ai-interview\s*$',header) else None


def voice_platform_recommendation(system: str, machine: str) -> str:
    if system != 'Darwin':
        return 'not_macos'
    return 'supported_apple_silicon' if machine == 'arm64' else 'unsupported_intel_mac'


def macos_version_supports_voice(version: str) -> bool:
    """Upstream VoiceStudio packaged Mac runtime requires macOS 13.3+."""
    if not isinstance(version,str):
        return False
    match = re.fullmatch(r'(\d+)\.(\d+)(?:\.\d+)?',version)
    if not match:
        return False
    return (int(match.group(1)),int(match.group(2))) >= (13,3)


def select_release(data: dict) -> VoiceRelease:
    if not isinstance(data, dict) or data.get('prerelease') or data.get('draft'):
        raise ValueError('VoiceStudio latest GitHub release is missing or not stable.')
    tag = data.get('tag_name')
    if not isinstance(tag, str) or not re.fullmatch(r'v[0-9]+\.[0-9]+\.[0-9]+', tag):
        raise ValueError('Unrecognized VoiceStudio release tag; no installer will run.')
    name = f'VoiceStudio-Electron-{tag[1:]}-mac-arm64.dmg'
    prefix = f'{RELEASE_ROOT}{tag}/'
    assets = data.get('assets')
    if not isinstance(assets, list):
        raise ValueError('VoiceStudio release has no usable assets')
    dmgs = [a for a in assets if isinstance(a, dict) and a.get('name') == name]
    checks = [a for a in assets if isinstance(a, dict) and a.get('name') == 'SHA256SUMS.txt']
    if len(dmgs) != 1 or len(checks) != 1:
        raise ValueError('Required official ARM64 DMG or SHA256SUMS.txt was not published')
    dmg, checksum = dmgs[0], checks[0]
    if dmg.get('browser_download_url') != prefix + name or checksum.get('browser_download_url') != prefix + 'SHA256SUMS.txt':
        raise ValueError('Release asset URL differs from the approved official GitHub path')
    size = dmg.get('size')
    if not isinstance(size, int) or not 20 * 1024 * 1024 <= size <= MAX_DMG_BYTES:
        raise ValueError('Release DMG has an unexpected size')
    return VoiceRelease(version=tag, dmg_filename=name,
                        dmg_url=prefix + name, checksum_url=prefix + 'SHA256SUMS.txt', size=size)


def checksum_for(manifest: str, filename: str) -> str:
    if not isinstance(manifest, str) or len(manifest) > MAX_CHECKSUM_TEXT:
        raise ValueError('Invalid SHA256SUMS file')
    found = []
    for line in manifest.splitlines():
        match = re.fullmatch(r'([0-9a-fA-F]{64})\s+\*?([^\r\n]+)', line.strip())
        if match and match.group(2) == filename:
            found.append(match.group(1).lower())
    if len(found) != 1:
        raise ValueError('Missing or ambiguous exact DMG hash in SHA256SUMS.txt')
    return found[0]


def verify_download(filename: Path, expected_sha256: str, expected_size: int) -> None:
    if filename.stat().st_size != expected_size:
        raise ValueError('Downloaded VoiceStudio DMG size did not match the release manifest')
    digest = hashlib.sha256()
    with filename.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    if digest.hexdigest() != expected_sha256:
        raise ValueError('VoiceStudio DMG SHA256 verification failed; refusing to mount')


class HTTPSOnlyRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urlsplit(newurl)
        if parsed.scheme != 'https' or parsed.hostname not in (
            'github.com', 'api.github.com', 'release-assets.githubusercontent.com',
            'objects.githubusercontent.com', 'github-releases.githubusercontent.com',
        ):
            raise ValueError('Unexpected or insecure release download redirect')
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _urlopen(url: str, limit: int, timeout: float = 40.0):
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or parsed.hostname not in ('api.github.com', 'github.com'):
        raise ValueError('Only official GitHub HTTPS endpoints are permitted')
    req = Request(url, headers={'User-Agent': 'AI-Interview-mac-bootstrap/0.6',
                                'Accept': 'application/vnd.github+json' if parsed.hostname == 'api.github.com' else '*/*'})
    opener = build_opener(HTTPSOnlyRedirect())
    response = opener.open(req, timeout=timeout)
    if response.status != 200:
        response.close()
        raise BootstrapError(f'Official download returned HTTP {response.status}')
    return response


def fetch_small_json(url: str, max_bytes: int = MAX_RELEASE_JSON) -> dict:
    with _urlopen(url, max_bytes) as response:
        data = response.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise BootstrapError('GitHub release metadata exceeds limit')
    obj = json.loads(data)
    if not isinstance(obj, dict):
        raise BootstrapError('Unexpected GitHub release metadata shape')
    return obj


def fetch_checksum(url: str) -> str:
    with _urlopen(url, MAX_CHECKSUM_TEXT) as response:
        content = response.read(MAX_CHECKSUM_TEXT + 1)
    if len(content) > MAX_CHECKSUM_TEXT:
        raise BootstrapError('Checksum manifest too large')
    return content.decode('utf-8', 'strict')


def download_release(spec: VoiceRelease, dest: Path) -> None:
    size = 0
    with _urlopen(spec.dmg_url, MAX_DMG_BYTES, timeout=60) as response, dest.open('xb') as out:
        for chunk in iter(lambda: response.read(1024 * 1024), b''):
            size += len(chunk)
            if size > MAX_DMG_BYTES or size > spec.size:
                raise BootstrapError('Downloaded VoiceStudio DMG exceeded the approved size')
            out.write(chunk)
    if size != spec.size:
        raise BootstrapError('VoiceStudio DMG download was truncated')


def voice_app_path(home: Path) -> Path | None:
    for target in (home / 'Applications/VoiceStudio.app', Path('/Applications/VoiceStudio.app')):
        if target.is_dir() and (target / 'Contents/Info.plist').is_file():
            return target
    return None


def install_voicestudio_app(home: Path, *, release_data: dict | None = None,
                            manifest: str | None = None) -> Path:
    """Install a separate third-party app without sudo, executing no fetched code."""
    current = voice_app_path(home)
    if current:
        return current
    if voice_platform_recommendation(platform.system(), platform.machine()) != 'supported_apple_silicon':
        raise BootstrapError('Local VoiceStudio installation requires Apple Silicon macOS')
    if not macos_version_supports_voice(platform.mac_ver()[0]):
        raise BootstrapError('VoiceStudio requires macOS 13.3 or newer; use Whisper fallback until macOS is upgraded')
    if shutil.disk_usage(home).free < MIN_VOICESTUDIO_DISK:
        raise BootstrapError('VoiceStudio recommends at least 10 GB free disk before first-run models')
    metadata = release_data if release_data is not None else fetch_small_json(RELEASE_API)
    spec = select_release(metadata)
    checksum = checksum_for(manifest if manifest is not None else fetch_checksum(spec.checksum_url), spec.dmg_filename)
    print(f'[VoiceStudio] Downloading the official {spec.version} ARM64 DMG ({spec.size // 1_000_000} MB); verifying SHA256…', flush=True)
    with tempfile.TemporaryDirectory(prefix='ai-interview-vs-') as td:
        t = Path(td)
        dmg = t / spec.dmg_filename
        download_release(spec, dmg)
        verify_download(dmg, checksum, spec.size)
        mounts = t / 'mounts'
        mounts.mkdir()
        proc = subprocess.run(['hdiutil', 'attach', str(dmg), '-readonly', '-nobrowse',
                               '-plist', '-mountroot', str(mounts)],
                              capture_output=True, check=True, timeout=120)
        mounted = []
        try:
            data = plistlib.loads(proc.stdout)
            for ent in data.get('system-entities', []):
                if isinstance(ent, dict) and isinstance(ent.get('mount-point'), str):
                    mount = Path(ent['mount-point'])
                    if mount.resolve().is_relative_to(mounts.resolve()):
                        mounted.append(mount)
            packages = [m / 'VoiceStudio.app' for m in mounted if (m / 'VoiceStudio.app/Contents/Info.plist').is_file()]
            if len(packages) != 1 or packages[0].is_symlink():
                raise BootstrapError('Verified DMG had no unique VoiceStudio.app; refusing to install')
            dest = home / 'Applications' / 'VoiceStudio.app'
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.exists():
                raise FileExistsError('An app appeared at ~/Applications/VoiceStudio.app during installation; not overwriting')
            partial = dest.with_name('.VoiceStudio.app.partial-' + uuid.uuid4().hex)
            try:
                subprocess.run(['ditto', '--rsrc', '--extattr', str(packages[0]), str(partial)],
                               check=True, timeout=180)
                if not (partial / 'Contents/Info.plist').is_file():
                    raise BootstrapError('Copied VoiceStudio app bundle failed post-copy validation')
                if dest.exists():
                    raise FileExistsError('Installation target changed; not overwriting')
                partial.rename(dest)
            finally:
                if partial.exists():
                    shutil.rmtree(partial)
            return dest
        finally:
            for mount in reversed(mounted):
                subprocess.run(['hdiutil', 'detach', str(mount), '-quiet'],
                               capture_output=True, check=False, timeout=30)


def install_skill_link(source: Path, dest: Path, home: Path, *, allow_backup: bool) -> str:
    source = source.resolve()
    dest = dest.expanduser()
    if dest == source or (dest.is_symlink() and dest.resolve() == source):
        return 'already_installed'
    if dest.exists() or dest.is_symlink():
        if not allow_backup:
            raise FileExistsError(f'Existing skill at {dest}; use --replace-skills to back it up safely')
        backup_dir = home / '.local/share/ai-interview/skill-backups'
        backup_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        dest.rename(backup_dir / f'ai-interview-{stamp}-{uuid.uuid4().hex[:8]}')
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.symlink_to(source, target_is_directory=True)
    return 'installed'


def dry_run_plan(skill_dir: Path, home: Path, *, mac_machine: str) -> dict:
    return {
        'status': 'dry_run_no_changes',
        'platform': platform.system() + ' ' + mac_machine,
        'python': 'Python >=3.10; create isolated venv, pip install studio/voice/WS requirements',
        'optional_third_party': 'VoiceStudio independently installed from official ARM64 DMG with SHA256 verification, if compatible',
        'local_speech_fallback': 'Download multilingual base Whisper model for local CPU speech recognition',
        'skill_links': [str(home / '.agents/skills/ai-interview'), str(home / '.claude/skills/ai-interview')],
        'launch': 'Open VoiceStudio (if present), then start private AI Interview localhost web studio',
        'skill_source': str(skill_dir),
        'privacy': 'Never open mic or send CV automatically; provider login and VoiceStudio model licenses require user action',
    }


def say(msg: str) -> None:
    print('[AI Interview] ' + msg, flush=True)


def consent(question: str, *, yes: bool) -> bool:
    if yes:
        say(question + ' (authorized with --yes)')
        return True
    if not sys.stdin.isatty():
        raise BootstrapError('Interactive approval required. Run from a terminal or explicitly add --yes')
    answer = input(question + ' [y/N]: ').strip().lower()
    return answer in ('y', 'yes')


def runtime_home(home: Path) -> Path:
    return home / '.local/share/ai-interview/runtime'


def runtime_python(home: Path) -> Path:
    return runtime_home(home) / '.venv/bin/python'


def requirements_digest(skill_dir: Path, *, with_voice: bool, with_ws: bool) -> tuple[str, list[Path]]:
    scripts = skill_dir / 'scripts'
    paths = [scripts / 'requirements-studio.txt']
    if with_ws:
        paths.append(scripts / 'requirements-voicestudio.txt')
    if with_voice:
        paths.append(scripts / 'requirements-voice.txt')
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    digest.update(str(sys.version_info[:2]).encode())
    return digest.hexdigest(), paths


def install_dependencies(home: Path, skill_dir: Path, *, with_voice: bool, with_ws: bool,
                         repair: bool = False) -> Path:
    runtime = runtime_home(home)
    runtime.mkdir(parents=True, exist_ok=True, mode=0o700)
    venv = runtime / '.venv'
    py = runtime_python(home)
    if not py.is_file():
        say('Creating an isolated Python environment…')
        subprocess.run([sys.executable, '-m', 'venv', str(venv)], check=True)
    digest, requirements = requirements_digest(skill_dir, with_voice=with_voice, with_ws=with_ws)
    marker = runtime / 'installed.json'
    if not repair and marker.is_file():
        try:
            record = json.loads(marker.read_text('utf-8'))
            if record.get('digest') == digest and record.get('python') == str(py):
                say('Python dependencies already installed; skipping repeated downloads.')
                return py
        except (ValueError, OSError, TypeError):
            pass
    for req in requirements:
        say(f'Installing {req.name} into the private virtual environment…')
        subprocess.run([str(py), '-m', 'pip', 'install', '--disable-pip-version-check', '-r', str(req)],
                       check=True, timeout=1800)
    marker.write_text(json.dumps({'digest': digest, 'python': str(py),
                                  'requirements': [r.name for r in requirements]}, indent=2) + '\n', encoding='utf-8')
    return py


def local_whisper_ready(home: Path) -> bool:
    marker = runtime_home(home) / 'whisper-base.ready'
    return marker.is_file() and runtime_python(home).is_file()


def install_whisper_model(py: Path, skill_dir: Path, home: Path) -> bool:
    marker = runtime_home(home) / 'whisper-base.ready'
    if marker.is_file():
        say('Multilingual Whisper base model was previously downloaded.')
        return True
    say('Downloading multilingual Whisper base model for offline microphone fallback…')
    cmd = [str(py), str(skill_dir / 'scripts/interview_studio.py'),
           'download-model', '--allow-download', '--model', 'base']
    subprocess.run(cmd, check=True, timeout=1800)
    marker.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    marker.write_text('Whisper base downloaded by AI Interview one-click setup\n', encoding='utf-8')
    return True


def voice_backend_available(skill_dir: Path) -> bool:
    try:
        sys.path.insert(0, str(skill_dir / 'scripts'))
        from voicestudio_adapter import VoiceStudioAdapter
        return VoiceStudioAdapter().status().get('available') is True
    except (OSError, RuntimeError, ValueError, ImportError):
        return False


def validate_private_url(url: str) -> str:
    if not isinstance(url, str) or not 35 <= len(url) <= 380 or '\n' in url or '\r' in url:
        raise ValueError('Invalid local interview URL')
    parsed = urlsplit(url)
    if (parsed.scheme != 'http' or parsed.hostname != '127.0.0.1' or
        not parsed.port or parsed.username or parsed.password or
        parsed.netloc != f'127.0.0.1:{parsed.port}' or parsed.path != '/' or parsed.query or
        not re.fullmatch(r'token=[A-Za-z0-9_-]{1,200}', parsed.fragment)):
        raise ValueError('Refusing an unexpected interview server URL')
    return url


def session_file(home: Path) -> Path:
    return runtime_home(home) / 'studio-session.json'


def _authorized_local_request(url: str, method: str = 'GET') -> dict:
    url = validate_private_url(url)
    parsed = urlsplit(url)
    token = parsed.fragment.removeprefix('token=')
    endpoint = f'http://127.0.0.1:{parsed.port}/api/health' if method == 'GET' else f'http://127.0.0.1:{parsed.port}/api/shutdown'
    req = Request(endpoint, method=method, data=b'' if method == 'POST' else None,
                  headers={'Authorization': 'Bearer ' + token})
    class RefuseRedirect(HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None
    with build_opener(ProxyHandler({}), RefuseRedirect()).open(req, timeout=2) as response:
        body=response.read(4096)
    result=json.loads(body)
    if not isinstance(result, dict):
        raise ValueError('Unexpected local studio JSON')
    return result


def check_interview_health(url: str) -> bool:
    try:
        data=_authorized_local_request(url)
        return isinstance(data.get('version'), str) and 'speech_ready' in data
    except (OSError, ValueError, KeyError, HTTPError, URLError, TimeoutError):
        return False


def get_running_session(home: Path) -> dict | None:
    metadata = session_file(home)
    try:
        if not metadata.is_file() or metadata.stat().st_size > 2048:
            return None
        record = json.loads(metadata.read_text(encoding='utf-8'))
        if (not isinstance(record, dict) or not isinstance(record.get('pid'), int) or
            record['pid'] <= 0):
            return None
        url = validate_private_url(record.get('url', ''))
        return record if check_interview_health(url) else None
    except (OSError, ValueError, TypeError):
        return None


def _write_private_json(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    temp = path.parent / ('.session-' + uuid.uuid4().hex)
    try:
        descriptor = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
            json.dump(record, stream, ensure_ascii=False)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def stop_interview(home: Path) -> int:
    running = get_running_session(home)
    if not running:
        say('No active local interview server is registered.')
        return 0
    try:
        reply = _authorized_local_request(running['url'], method='POST')
        if reply.get('status') != 'stopping':
            raise BootstrapError('Local server did not acknowledge shutdown')
    except (OSError, HTTPError, URLError, ValueError, TimeoutError) as exc:
        raise BootstrapError('Authenticated shutdown failed; no PID was killed') from exc
    session_file(home).unlink(missing_ok=True)
    say('Interview studio shutdown requested. Close the browser tab to release any open microphone.')
    return 0


def launch_interview(home: Path, skill_dir: Path, *, try_voicestudio: bool, verbose: bool = True) -> int:
    py = runtime_python(home)
    if not py.is_file():
        raise BootstrapError('AI Interview has not been installed; run one-click setup first')
    running = get_running_session(home)
    if running:
        say('Reusing your already-running private interview, not starting a duplicate server.')
        import webbrowser
        if not webbrowser.open(running['url']):
            say('Browser did not open. Copy this PRIVATE local link only onto your own Mac: ' + running['url'])
        return 0
    app = voice_app_path(home) if try_voicestudio else None
    if app:
        say('Opening separately installed VoiceStudio (microphone still off)…')
        proc = subprocess.run(['open', str(app)], check=False, timeout=20)
        if proc.returncode:
            say('VoiceStudio did not open automatically. Check macOS Gatekeeper or start it manually.')
    ready=False
    if try_voicestudio:
        for _ in range(12 if app else 1):
            if voice_backend_available(skill_dir):
                ready=True
                break
            if app:
                time.sleep(1)
        say('VoiceStudio local speech API detected.' if ready else
            'VoiceStudio is not ready. Complete its first-run model wizard, then re-run launcher for streaming subtitles.')
    cli = [name for name in ('codex', 'claude', 'gemini') if shutil.which(name)]
    if cli:
        say('Available interviewer CLIs: ' + ', '.join(cli) + ' (login status still needs checking).')
    else:
        say('No local Codex/Claude/Gemini CLI detected. You may configure a supported API key in the same terminal environment.')
    command = [str(py), str(skill_dir / 'scripts/career.py'), 'interview', '--no-browser']
    if try_voicestudio:
        command.append('--voicestudio')
    # Do not load VoiceStudio and a second Whisper recognizer on a tight-memory Mac.
    if ready or not local_whisper_ready(home):
        command.append('--without-stt')
    private_dir = runtime_home(home)
    private_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    log = private_dir / 'studio.log'
    log_fd = os.open(log, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    os.fchmod(log_fd, 0o600)  # The logfile may predate this version; keep bearer URLs private.
    say('Starting a private localhost studio. This returns control to your CLI Agent.')
    with os.fdopen(log_fd, 'w', encoding='utf-8') as output:
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=output,
                                   stderr=subprocess.STDOUT, start_new_session=True,
                                   cwd=str(home))
    url = None
    for _ in range(120):
        if process.poll() is not None:
            break
        try:
            for line in log.read_text(encoding='utf-8').splitlines():
                prefix = 'Local private studio URL (never publish): '
                if line.startswith(prefix):
                    candidate = line[len(prefix):].strip()
                    url = validate_private_url(candidate)
                    break
        except (OSError, UnicodeDecodeError):
            pass
        if url and check_interview_health(url):
            break
        time.sleep(.25)
    if not url or not check_interview_health(url):
        # This process is newly created and still owned by this launch attempt.
        if process.poll() is None:
            process.terminate()
        raise BootstrapError('Studio failed to start; inspect your private runtime/studio.log (no CV/recordings stored there)')
    _write_private_json(session_file(home), {'pid': process.pid, 'url':url,
                        'created_at':datetime.now(timezone.utc).isoformat()})
    _DETACHED_PROCESSES.append(process)
    say('Interview studio is running on 127.0.0.1. It requires an explicit browser microphone click.')
    import webbrowser
    if not webbrowser.open(url):
        say('Browser did not open automatically. Open this private link on your own Mac: '+url)
    say('To stop the local service, run the same launcher with --stop.')
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description='One-command installer/launcher for AI Interview on macOS')
    parser.add_argument('--yes', action='store_true', help='Explicitly authorize package, model and official VoiceStudio downloads')
    parser.add_argument('--dry-run', action='store_true', help='Show the plan without network, disk changes, or launch')
    parser.add_argument('--doctor', action='store_true', help='Report local readiness without changes')
    parser.add_argument('--stop', action='store_true', help='Stop the previously launched studio through its authenticated localhost API')
    parser.add_argument('--no-voicestudio', action='store_true', help='Use browser TTS and local Whisper instead')
    parser.add_argument('--skip-whisper', action='store_true', help='Do not download/install built-in Whisper fallback')
    parser.add_argument('--no-skills', action='store_true', help='Do not link Skill into Codex/Claude skill directories')
    parser.add_argument('--replace-skills', action='store_true', help='Back up any existing installation before replacing a Skill link')
    parser.add_argument('--no-launch', action='store_true', help='Install everything, but do not start the interview')
    parser.add_argument('--launch-only', action='store_true', help='Skip setup and start using the existing installation')
    parser.add_argument('--repair', action='store_true', help='Re-install dependencies even if previously installed')
    args = parser.parse_args(argv)
    skill = locate_skill_dir(Path(__file__))
    if skill is None:
        parser.error('mac_bootstrap.py must remain inside the complete ai-interview Skill folder')
    home = Path.home()
    system, machine = platform.system(), platform.machine()
    if args.dry_run:
        print(json.dumps(dry_run_plan(skill, home, mac_machine=machine), indent=2, ensure_ascii=False))
        return 0
    if args.doctor:
        data = {'platform':system,'chip':machine,'python':sys.version.split()[0],
                'skill':str(skill), 'installed_venv':runtime_python(home).is_file(),
                'whisper_model_downloaded_by_installer':local_whisper_ready(home),
                'voicestudio_app':str(voice_app_path(home) or ''),
                'voicestudio_api_ready':voice_backend_available(skill),
                'installed_interviewer_clis':[n for n in ('codex','claude','gemini') if shutil.which(n)],
                'studio_running':bool(get_running_session(home))}
        print(json.dumps(data, indent=2,ensure_ascii=False))
        return 0
    if args.stop:
        return stop_interview(home)
    if system != 'Darwin':
        raise BootstrapError('This one-click installer targets macOS only; use the README manual commands on Linux/Windows')
    if sys.version_info < MIN_PYTHON:
        raise BootstrapError('Python 3.10+ required. The accompanying one-click-mac.sh selects or installs a modern interpreter.')
    if args.launch_only:
        return launch_interview(home,skill,try_voicestudio=not args.no_voicestudio)

    say(f'Using macOS {machine}. Install location: {runtime_home(home)}')
    say('Local packages and speech models need an Internet download. Interview LLM login and mic permission are NOT automatic.')
    if not consent('Install AI Interview dependencies and the multilingual Whisper base model?', yes=args.yes):
        raise BootstrapError('Package download not authorized. Nothing has been installed by this command.')
    py = install_dependencies(home,skill,with_voice=not args.skip_whisper,
                              with_ws=not args.no_voicestudio,repair=args.repair)
    if not args.skip_whisper:
        try:
            install_whisper_model(py,skill,home)
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError, RuntimeError) as exc:
            say(f'Whisper fallback download failed: {type(exc).__name__}. VoiceStudio or typed answers can still work.')

    if not args.no_skills:
        for dest in (home / '.agents/skills/ai-interview', home / '.claude/skills/ai-interview'):
            replace = args.yes or args.replace_skills
            if (dest.exists() or dest.is_symlink()) and not replace and dest.resolve()!=skill.resolve():
                replace = consent(f'Back up the existing {dest} and point it at this Skill?',yes=False)
            try:
                result=install_skill_link(skill,dest,home,allow_backup=replace)
                say(f'Skill at {dest}: {result}')
            except (OSError, FileExistsError) as exc:
                say(f'Skill link not updated: {exc}')
    if not args.no_voicestudio:
        kind=voice_platform_recommendation(system,machine)
        if kind == 'unsupported_intel_mac':
            say('Intel Mac: upstream VoiceStudio does not support a local Python backend. Keeping Whisper/browser voice.')
        elif voice_app_path(home):
            say('VoiceStudio is already installed; not replacing or upgrading it.')
        elif not macos_version_supports_voice(platform.mac_ver()[0]):
            say('VoiceStudio needs macOS 13.3+. Keeping Whisper/browser speech until the system is upgraded.')
        elif consent('Install separate VoiceStudio AGPL-3.0 macOS ARM64 app from official SHA256-verified release? (model licenses still require approval in its UI)', yes=args.yes):
            try:
                app=install_voicestudio_app(home)
                say('VoiceStudio installed in '+str(app)+'. macOS may require a manual first Open approval.')
            except (BootstrapError, ValueError, HTTPError, URLError, OSError, subprocess.SubprocessError, plistlib.InvalidFileException) as exc:
                say('VoiceStudio installation was not completed: '+type(exc).__name__+': '+str(exc)[:240])
                say('You can still use the built-in Whisper fallback. Do not bypass macOS Gatekeeper silently.')
    if args.no_launch:
        say('Installation step finished; to open the interview later use --launch-only.')
        return 0
    return launch_interview(home,skill,try_voicestudio=not args.no_voicestudio)


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (BootstrapError, FileNotFoundError, PermissionError, subprocess.SubprocessError) as exc:
        print('[AI Interview] SETUP ERROR: '+str(exc), file=sys.stderr)
        raise SystemExit(2)
