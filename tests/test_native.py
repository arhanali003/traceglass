import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('native', Path(__file__).resolve().parents[1] / 'skills/source-recovery/scripts/native_report.py')
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)


class NativeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.target = self.root / 'binary'
        self.target.write_bytes(bytes.fromhex('cffaedfe') + b'fixture')
        self.out = self.root / 'output'

    def test_rejects_non_native_before_output(self):
        self.target.write_text('not native')
        with self.assertRaises(ValueError):
            native.export(self.target, self.out)
        self.assertFalse(self.out.exists())

    def test_missing_tools_before_output(self):
        with patch.object(native.shutil, 'which', return_value=None):
            with self.assertRaises(ValueError):
                native.export(self.target, self.out)
        self.assertFalse(self.out.exists())

    def test_partial_timeout_is_preserved(self):
        def timeout(command, **kwargs):
            kwargs['stdout'].write(b'partial result')
            raise subprocess.TimeoutExpired(command, 1)
        with patch.object(native.shutil, 'which', return_value=str(self.target)), patch.object(native.subprocess, 'run', side_effect=timeout):
            result = native.export(self.target, self.out, timeout=1)
        self.assertTrue(result['input_unchanged'])
        self.assertTrue(all(j['status'] == 'timeout' for j in result['jobs']))
        self.assertEqual((self.out / 'symbols.txt').read_bytes(), b'partial result')

    def test_existing_output_is_preserved(self):
        self.out.mkdir()
        (self.out / 'keep').write_text('keep')
        with patch.object(native.shutil, 'which', return_value=str(self.target)):
            with self.assertRaises(FileExistsError):
                native.export(self.target, self.out)
        self.assertEqual((self.out / 'keep').read_text(), 'keep')
