import base64
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('recovery', ROOT / 'skills/source-recovery/scripts/recover.py')
recovery = importlib.util.module_from_spec(spec)
spec.loader.exec_module(recovery)


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.target = self.root / 'app'
        self.target.mkdir()
        self.out = self.root / 'recovered'

    def run_recovery(self, budget=4096):
        return recovery.recover(self.target, self.out, budget)

    def test_exact_bytes_and_no_execution(self):
        content = b'\xef\xbb\xbfraise RuntimeError("must never execute")\r\n'
        (self.target / 'script.py').write_bytes(content)
        result = self.run_recovery()
        row = result['records'][0]
        self.assertEqual((self.out / row['output']).read_bytes(), content)
        self.assertEqual(row['sha256'], recovery.digest(content))
        self.assertEqual((self.target / 'script.py').read_bytes(), content)

    def test_map_paths_cannot_escape_output_and_missing_content_reported(self):
        obj = {'version': 3, 'sources': ['../../escape.ts', '/absolute.ts', 'missing.ts'],
               'sourcesContent': ['const a = 1;', 'const b = 2;', None]}
        (self.target / 'bundle.js.map').write_text(json.dumps(obj))
        result = self.run_recovery()
        self.assertEqual(len(result['records']), 2)
        self.assertEqual(len(result['skipped']), 1)
        self.assertFalse((self.root / 'escape.ts').exists())
        for row in result['records']:
            self.assertIn(self.out, (self.out / row['output']).resolve().parents)

    def test_inline_and_indexed_maps(self):
        obj = {'version': 3, 'sections': [{'offset': {'line': 0, 'column': 0},
                 'map': {'version': 3, 'sources': ['hello.ts'], 'sourcesContent': ['let hello = 1;']}},
                 {'url': 'https://invalid.test/no-fetch.map'}]}
        encoded = base64.b64encode(json.dumps(obj).encode()).decode()
        (self.target / 'bundle.js').write_text('//# sourceMappingURL=data:application/json;base64,' + encoded)
        result = self.run_recovery()
        self.assertEqual([r['category'] for r in result['records']], ['shipped-source', 'source-map-content'])
        self.assertEqual((self.out / result['records'][1]['output']).read_text(), 'let hello = 1;')
        self.assertTrue(any('not fetched' in s['reason'] for s in result['skipped']))

    def test_invalid_binary_oversized_and_malformed_map(self):
        (self.target / 'binary.js').write_bytes(b'\x00\xff')
        (self.target / 'big.js').write_bytes(b'x' * 200)
        (self.target / 'bad.map').write_text('{')
        result = self.run_recovery(100)
        self.assertEqual(result['records'], [])
        self.assertEqual(len(result['skipped']), 3)

    def test_refuses_existing_and_inside_target_output(self):
        self.out.mkdir()
        (self.out / 'keep').write_text('keep')
        with self.assertRaises(FileExistsError):
            self.run_recovery()
        with self.assertRaises(ValueError):
            recovery.recover(self.target, self.target / 'output')
        self.assertEqual((self.out / 'keep').read_text(), 'keep')

    def test_symlink_not_read(self):
        secret = self.root / 'outside.js'
        secret.write_text('private')
        try:
            (self.target / 'link.js').symlink_to(secret)
        except OSError:
            self.skipTest('Symlinks unavailable')
        result = self.run_recovery()
        self.assertEqual(result['records'], [])
        self.assertEqual(len(result['skipped']), 1)

    def test_source_recovery_installs_for_all_clients(self):
        installer_spec = importlib.util.spec_from_file_location('installer', ROOT / 'scripts/install.py')
        installer = importlib.util.module_from_spec(installer_spec)
        installer_spec.loader.exec_module(installer)
        destinations = installer.install('all', self.target, skill='source-recovery')
        self.assertEqual(len(destinations), 2)
        for destination in destinations:
            self.assertTrue((destination / 'scripts/recover.py').is_file())
            self.assertFalse((destination / 'scripts/__pycache__').exists())


if __name__ == '__main__':
    unittest.main()
