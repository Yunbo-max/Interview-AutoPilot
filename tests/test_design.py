"""Offline design checks, not LLM behavior or live-runtime certification."""
import copy
import itertools
import json
import re
import unittest
from fractions import Fraction
from pathlib import Path

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills' / 'ai-interview'
REFS = ['start-and-contract', 'session-and-clock', 'adversarial-engine',
        'multimodal', 'speech-assessment', 'coding', 'mathematics',
        'research-and-resume', 'evaluation-and-report', 'tool-contracts',
        'privacy-and-security', 'host-adapters', 'failure-recovery']


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def schema_validator():
    return jsonschema.Draft202012Validator(load(SKILL / 'assets' / 'contracts.schema.json'))


class DesignTests(unittest.TestCase):
    def test_required_files(self):
        required = ['README.md', 'README.zh-CN.md', 'AGENTS.md', 'plugin.json',
                    '.codex-plugin/plugin.json', '.gitignore', 'VERSION',
                    'docs/DESIGN.md', 'docs/ACCEPTANCE.md', 'docs/SOURCES.md',
                    'skills/ai-interview/SKILL.md', 'skills/ai-interview/agents/openai.yaml',
                    'skills/ai-interview/assets/contracts.schema.json',
                    'skills/ai-interview/assets/session.example.json',
                    'skills/ai-interview/assets/question-coding.example.json',
                    'skills/ai-interview/assets/question-math.example.json',
                    'skills/ai-interview/assets/judgment.example.json',
                    'skills/ai-interview/assets/event.example.json',
                    'skills/ai-interview/assets/speech.example.json',
                    'skills/ai-interview/examples/cross-examination.md',
                    'tests/scenarios.json']
        required += [f'skills/ai-interview/references/{r}.md' for r in REFS]
        self.assertEqual([p for p in required if not (ROOT / p).is_file()], [], 'Missing design files')

    def test_skill_metadata_and_size(self):
        p = SKILL / 'SKILL.md'
        self.assertTrue(p.is_file(), 'Missing SKILL.md')
        parts = p.read_text(encoding='utf-8').split('---', 2)
        self.assertEqual(parts[0].strip(), '')
        meta = yaml.safe_load(parts[1])
        self.assertEqual(meta['name'], SKILL.name)
        self.assertTrue(meta['description'].startswith('Use when'))
        self.assertLessEqual(len(meta['description']), 1024)
        self.assertLessEqual(len(parts[1]), 1024)
        self.assertLessEqual(len(parts[2].split()), 650)

    def test_local_markdown_links(self):
        broken = []
        for p in ROOT.rglob('*.md'):
            text = re.sub(r'```.*?```', '', p.read_text(encoding='utf-8'), flags=re.S)
            for link in re.findall(r'\]\(([^)]+)\)', text):
                if re.match(r'^[a-zA-Z]+:', link) or link.startswith('#'):
                    continue
                target = (p.parent / link.split('#')[0]).resolve()
                if not target.exists():
                    broken.append((str(p.relative_to(ROOT)), link))
        self.assertEqual(broken, [])

    def test_skill_links_stay_self_contained(self):
        self.assertTrue(SKILL.is_dir(), 'Missing skill directory')
        for p in SKILL.rglob('*.md'):
            text = re.sub(r'```.*?```', '', p.read_text(encoding='utf-8'), flags=re.S)
            for link in re.findall(r'\]\(([^)]+)\)', text):
                if re.match(r'^[a-zA-Z]+:', link) or link.startswith('#'):
                    continue
                target = (p.parent / link.split('#')[0]).resolve()
                self.assertTrue(target.is_relative_to(SKILL.resolve()), (p, link))
                self.assertTrue(target.exists(), (p, link))

    def test_version_consistency(self):
        self.assertTrue((ROOT / 'VERSION').is_file(), 'Missing VERSION')
        version = (ROOT / 'VERSION').read_text().strip()
        self.assertEqual(load(ROOT / 'plugin.json')['version'], version)
        legacy = load(ROOT / '.codex-plugin/plugin.json')
        self.assertEqual(legacy['version'], version)
        self.assertEqual(legacy['skills'], './skills/')
        self.assertNotIn('mcpServers', legacy)

    def test_contract_schema(self):
        p = SKILL / 'assets/contracts.schema.json'
        self.assertTrue(p.is_file(), 'Missing schema')
        jsonschema.Draft202012Validator.check_schema(load(p))
        validator = schema_validator()
        examples = list((SKILL / 'assets').glob('*.example.json'))
        self.assertEqual(len(examples), 9)
        for p in examples:
            with self.subTest(example=p.name):
                validator.validate(load(p))

    def test_default_clock_and_consent(self):
        p = SKILL / 'assets/session.example.json'
        self.assertTrue(p.is_file(), 'Missing session fixture')
        data = load(p)
        self.assertEqual(data['duration_seconds'], 3600)
        self.assertEqual(sum(x['budget_seconds'] for x in data['phases']), 3600)
        self.assertEqual(len({x['id'] for x in data['phases']}), len(data['phases']))
        self.assertEqual(data['clock_mode'], 'user_managed')
        self.assertFalse(any(data['consent'].values()))
        self.assertFalse(any(data['capabilities'].values()))

    def test_invalid_contracts_rejected(self):
        p = SKILL / 'assets/session.example.json'
        self.assertTrue(p.is_file(), 'Missing session fixture')
        data = load(p)
        validator = schema_validator()
        for patch in [{'duration_seconds': -1}, {'clock_mode': 'imagined'},
                      {'mode': 'covert-live-exam'}, {'secret_upload': True},
                      {'clock_mode': 'host_monotonic'}]:
            invalid = copy.deepcopy(data)
            invalid.update(patch)
            with self.subTest(patch=patch):
                self.assertFalse(validator.is_valid(invalid))

    def test_speech_without_audio_rejected(self):
        p = SKILL / 'assets/speech.example.json'
        self.assertTrue(p.is_file(), 'Missing speech fixture')
        data = load(p)
        data.update(audio_available=True, audio_source_id='fictional-audio',
                    metrics=[{'name': 'pitch_p95_hz', 'value': 100, 'unit': 'Hz'}])
        self.assertTrue(schema_validator().is_valid(data))
        data.update(audio_available=False, audio_source_id=None)
        self.assertFalse(schema_validator().is_valid(data))

    def test_scenarios_are_not_fabricated_runs(self):
        p = ROOT / 'tests/scenarios.json'
        self.assertTrue(p.is_file(), 'Missing scenarios')
        cases = load(p)
        self.assertEqual(len(cases), 32)
        self.assertEqual(len({x['id'] for x in cases}), len(cases))
        for case in cases:
            self.assertEqual(case['execution_status'], 'not_run')
            self.assertTrue(case['prompt'] and case['pass_condition'] and case['fail_condition'])

    def test_coding_reference_exhaustive(self):
        p = SKILL / 'assets/question-coding.example.json'
        self.assertTrue(p.is_file(), 'Missing coding fixture')
        data = load(p)
        # Execute ONLY the repository-owned, manually reviewed reference function.
        # This is not a candidate-code runner and is not a security sandbox.
        namespace = {}
        exec(data['reference_answer'], namespace)
        solve = namespace['solve']
        for length in range(8):
            for chars in itertools.product('abc', repeat=length):
                s = ''.join(chars)
                expected = max([0] + [j-i for i in range(len(s)) for j in range(i+1, len(s)+1)
                                      if len(set(s[i:j])) == j-i])
                self.assertEqual(solve(s), expected, s)
        for case in data['tests']:
            self.assertEqual(solve(case['input']), case['expected'])

    def test_coding_mutant_is_detected(self):
        # Deliberately flawed: the left boundary can move backwards.
        def wrong(s):
            left = best = 0
            seen = {}
            for right, char in enumerate(s):
                if char in seen:
                    left = seen[char] + 1
                seen[char] = right
                best = max(best, right-left+1)
            return best
        self.assertNotEqual(wrong('abba'), 2)

    def test_sample_variance_finite_distribution_sanity(self):
        # Exact finite examples support a sanity check, not a general proof.
        distributions = [
            [(Fraction(-1), Fraction(1, 3)), (Fraction(2), Fraction(2, 3))],
            [(Fraction(0), Fraction(1, 2)), (Fraction(4), Fraction(1, 2))],
            [(Fraction(5), Fraction(1))]
        ]
        for dist in distributions:
            mu = sum(x*p for x, p in dist)
            variance = sum(p*(x-mu)**2 for x, p in dist)
            for n in range(2, 5):
                expectation = Fraction(0)
                for draw in itertools.product(dist, repeat=n):
                    xs = [x for x, p in draw]
                    probability = Fraction(1)
                    for x, p in draw:
                        probability *= p
                    average = sum(xs)/n
                    estimator = sum((x-average)**2 for x in xs)/(n-1)
                    expectation += probability*estimator
                self.assertEqual(expectation, variance)

    def test_role_boundary(self):
        p = ROOT / 'AGENTS.md'
        self.assertTrue(p.is_file(), 'Missing maintainer rules')
        self.assertIn('Do not start an interview', p.read_text())
        self.assertIn('not_run', (ROOT / 'docs/ACCEPTANCE.md').read_text())


if __name__ == '__main__':
    unittest.main(verbosity=2)
