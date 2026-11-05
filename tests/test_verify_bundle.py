import copy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / 'skills/source-recovery/scripts'


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


collector = load('collect_bundle')
verifier = load('verify_bundle')


class VerifyBundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.source = self.root / 'source'
        self.source.mkdir()
        (self.source / 'clip.bin').write_bytes(b'\x00\xffhello')
        self.bundle = self.root / 'bundle'
        self.manifest = collector.collect(self.source, self.bundle)
        self.payload = self.bundle / 'bundle-files/clip.bin'

    def write_manifest(self, manifest):
        (self.bundle / 'bundle-manifest.json').write_text(json.dumps(manifest), encoding='utf-8')

    def cli(self):
        run = subprocess.run([sys.executable, str(SCRIPTS / 'verify_bundle.py'),
                              '--bundle', str(self.bundle)], capture_output=True, text=True)
        return run, json.loads(run.stdout)

    def test_round_trip_cli_is_read_only_and_does_not_need_source(self):
        before = {p.relative_to(self.bundle): p.read_bytes() for p in self.bundle.rglob('*') if p.is_file()}
        (self.source / 'clip.bin').unlink()
        run, result = self.cli()
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(result['checked_files'], 1)
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(before, {p.relative_to(self.bundle): p.read_bytes() for p in self.bundle.rglob('*') if p.is_file()})

    def test_same_size_tampering_is_detected(self):
        self.payload.write_bytes(b'\x00\xffjello')
        run, result = self.cli()
        self.assertEqual(run.returncode, 2)
        self.assertEqual(result['files'][0]['status'], 'mismatch')

    def test_wrong_recorded_size_is_detected(self):
        self.manifest['files'][0]['bytes'] += 1
        self.write_manifest(self.manifest)
        self.assertEqual(verifier.verify(self.bundle)['failed_files'], 1)

    def test_missing_file(self):
        self.payload.unlink()
        self.assertEqual(verifier.verify(self.bundle)['files'][0]['status'], 'missing')

    def test_partial_collection_never_reports_success(self):
        self.manifest['errors'].append({'path': 'other', 'reason': 'unreadable'})
        self.write_manifest(self.manifest)
        run, result = self.cli()
        self.assertEqual(run.returncode, 2)
        self.assertEqual(result['collection_errors'], 1)
        self.assertEqual(result['failed_files'], 0)

    def test_invalid_paths_rejected_before_payload_reads(self):
        for path in ('../escape', '/absolute', 'C:/file', 'a\\b', './clip', 'a//b', 'a/../b', '', 'a\x00b'):
            with self.subTest(path=path):
                manifest = copy.deepcopy(self.manifest)
                manifest['files'][0].update(path=path, output='bundle-files/' + path)
                self.write_manifest(manifest)
                with patch.object(verifier.os, 'open', side_effect=AssertionError('payload opened')):
                    with self.assertRaises(ValueError):
                        verifier.verify(self.bundle)

    def test_output_cannot_redirect_to_other_file(self):
        self.manifest['files'][0]['output'] = 'bundle-manifest.json'
        self.write_manifest(self.manifest)
        with self.assertRaises(ValueError):
            verifier.verify(self.bundle)

    def test_bad_record_types_and_duplicate_outputs(self):
        for field, value in [('sha256', 'not-a-hash'), ('bytes', True), ('bytes', -1), ('bytes', '7'), ('path', None)]:
            with self.subTest(field=field, value=value):
                manifest = copy.deepcopy(self.manifest)
                manifest['files'][0][field] = value
                self.write_manifest(manifest)
                with self.assertRaises(ValueError):
                    verifier.verify(self.bundle)
        self.manifest['files'].append(self.manifest['files'][0])
        self.write_manifest(self.manifest)
        with self.assertRaises(ValueError):
            verifier.verify(self.bundle)

    def test_malformed_manifest_returns_json_error(self):
        for value in ('{', '[]', '{"files": []}', '\ud800'):
            (self.bundle / 'bundle-manifest.json').write_bytes(value.encode('utf-8', errors='surrogatepass'))
            run, result = self.cli()
            self.assertEqual(run.returncode, 1)
            self.assertEqual(result['status'], 'error')
            self.assertNotIn('Traceback', run.stderr)

    def test_manifest_size_limit(self):
        with patch.object(verifier, 'MAX_MANIFEST_BYTES', 4):
            with self.assertRaisesRegex(ValueError, 'limit'):
                verifier.verify(self.bundle)

    def symlink(self, link, target, directory=False):
        try:
            link.symlink_to(target, target_is_directory=directory)
        except OSError:
            self.skipTest('Symlinks unavailable on this host')

    def test_payload_symlink_not_read(self):
        self.payload.unlink()
        self.symlink(self.payload, self.source / 'clip.bin')
        with patch.object(verifier.os, 'open', side_effect=AssertionError('symlink opened')):
            self.assertEqual(verifier.verify(self.bundle)['files'][0]['status'], 'unreadable')

    def test_parent_symlink_not_read(self):
        self.payload.unlink()
        self.payload.parent.rmdir()
        self.symlink(self.payload.parent, self.source, True)
        self.assertEqual(verifier.verify(self.bundle)['files'][0]['status'], 'unreadable')

    def test_manifest_symlink_rejected(self):
        original = self.bundle / 'bundle-manifest.json'
        external = self.root / 'manifest.json'
        original.rename(external)
        self.symlink(original, external)
        with self.assertRaises(ValueError):
            verifier.verify(self.bundle)

    def test_special_file_rejected_without_blocking(self):
        if not hasattr(os, 'mkfifo'):
            self.skipTest('FIFO unavailable')
        self.payload.unlink()
        os.mkfifo(self.payload)
        self.assertEqual(verifier.verify(self.bundle)['files'][0]['status'], 'unreadable')

    def test_empty_collection_and_recorded_links_are_explicit(self):
        self.manifest['files'] = []
        self.manifest['symlinks'] = [{'path': 'link', 'target': '/not/read'}]
        self.write_manifest(self.manifest)
        result = verifier.verify(self.bundle)
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(result['checked_files'], 0)
        self.assertEqual(result['recorded_symlinks'], 1)


if __name__ == '__main__':
    unittest.main()
