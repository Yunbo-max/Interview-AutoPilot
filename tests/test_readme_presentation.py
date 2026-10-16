"""Documentation-only regression checks for the bilingual visual README.

This validates files and honest labels, not live UI rendering or provider behavior.
"""
from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
MEDIA = ('docs/assets/hero.svg', 'docs/assets/studio-preview.svg', 'docs/assets/workflow.svg')
DOCS = ('README.md', 'README.zh-CN.md')


class ReadmePresentationTests(unittest.TestCase):
    def test_bilingual_readmes_reference_committed_images(self):
        for name in DOCS:
            source = (ROOT / name).read_text(encoding='utf-8')
            with self.subTest(readme=name):
                for asset in MEDIA:
                    self.assertIn(f'src="{asset}"', source)
                    self.assertTrue((ROOT / asset).is_file(), asset)
                self.assertIn('DeepInterview', source)
                self.assertIn('ai-job-search', source)
                self.assertIn('VoiceStudio', source)
                self.assertIn('arXiv', source)
                self.assertIn('0.6.0', source)
                self.assertIn('MIT', source)

    def test_svg_images_are_portable_and_have_no_executable_content(self):
        ns = '{http://www.w3.org/2000/svg}'
        for name in MEDIA:
            with self.subTest(asset=name):
                path = ROOT / name
                tree = ET.parse(path)
                root = tree.getroot()
                self.assertEqual(root.tag, ns + 'svg')
                self.assertIn('viewBox', root.attrib)
                self.assertTrue(root.attrib.get('aria-label'))
                self.assertLess(path.stat().st_size, 90_000)
                for elem in tree.iter():
                    self.assertNotIn(elem.tag.split('}')[-1], ('script', 'foreignObject', 'image'))
                    self.assertFalse(any(key.lower().startswith('on') for key in elem.attrib))
                    self.assertFalse(any('http://' in value or 'https://' in value for key, value in elem.attrib.items() if key not in ('xmlns',)))

    def test_relative_html_navigation_and_visual_paths_exist(self):
        for name in DOCS:
            path = ROOT / name
            body = path.read_text(encoding='utf-8')
            links = re.findall(r'(?:href|src)="([^"]+)"', body)
            for uri in links:
                if '://' in uri or uri.startswith('#'):
                    continue
                local = uri.split('#', 1)[0].split('?', 1)[0]
                with self.subTest(readme=name, link=local):
                    self.assertTrue((path.parent / local).is_file())

    def test_competitor_comparison_is_labeled_not_a_trending_rank(self):
        en = (ROOT / 'README.md').read_text(encoding='utf-8')
        cn = (ROOT / 'README.zh-CN.md').read_text(encoding='utf-8')
        self.assertIn('not** an official GitHub Trending ranking', en)
        self.assertIn('不是 GitHub Trending 排名', cn)
        self.assertIn('Candidate code is **not executed**', en)
        self.assertIn('代码编辑器**不执行提交的代码**', cn)
        self.assertIn('not full-duplex', en)
        self.assertIn('不是真正全双工', cn)


if __name__ == '__main__':
    unittest.main()
