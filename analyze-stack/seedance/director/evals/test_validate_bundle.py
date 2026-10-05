"""Unit tests of the package checker, not the prompt-writing agent or Seedance."""
from pathlib import Path
import importlib.util
import json
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('bundle_validator', ROOT / 'scripts/validate_bundle.py')
assert spec is not None and spec.loader is not None
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


class BundleChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'seedance-2-5-director'
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))

    def assert_problem(self, text):
        self.assertTrue(any(text in e for e in validator.validate(self.root)), text)

    def test_valid_bundle(self):
        self.assertEqual(validator.validate(self.root), [])

    def test_missing_required_file(self):
        (self.root / 'assets/context-handoff.md').unlink()
        self.assert_problem('Missing required file')

    def test_broken_local_link(self):
        with (self.root / 'README.md').open('a') as f:
            f.write('\n[missing](missing.md)\n')
        self.assert_problem('Broken local link')

    def test_broken_anchor(self):
        with (self.root / 'README.md').open('a') as f:
            f.write('\n[bad](SKILL.md#anchor-that-does-not-exist)\n')
        self.assert_problem('Broken anchor')

    def test_link_escape(self):
        with (self.root / 'README.md').open('a') as f:
            f.write('\n[escape](../../outside.txt)\n')
        self.assert_problem('Link escapes package')

    def test_malformed_json(self):
        (self.root / 'evals/evals.json').write_text('{broken', encoding='utf-8')
        self.assert_problem('Invalid evaluation JSON')

    def test_duplicate_case(self):
        p = self.root / 'evals/evals.json'
        data = json.loads(p.read_text())
        data['cases'].append(data['cases'][0])
        p.write_text(json.dumps(data), encoding='utf-8')
        self.assert_problem('duplicate case ID')

    def test_second_skill(self):
        sub = self.root / 'nested'
        sub.mkdir()
        (sub / 'SKILL.md').write_text('# Unexpected second skill\n', encoding='utf-8')
        self.assert_problem('exactly one root SKILL.md')

    def test_unclosed_fence(self):
        with (self.root / 'README.md').open('a') as f:
            f.write('\n```text\nunclosed example\n')
        self.assert_problem('Unclosed code fence')

    def test_hash_integrity_detects_tampering(self):
        (self.root / 'manifest.json').write_text(json.dumps({'files': validator.inventory(self.root)}), encoding='utf-8')
        self.assertEqual(validator.validate(self.root, True), [])
        with (self.root / 'assets/context-handoff.md').open('a') as f:
            f.write('\nUnauthorized modification.\n')
        self.assertTrue(any('Integrity mismatch' in e for e in validator.validate(self.root, True)))


if __name__ == '__main__':
    unittest.main()
