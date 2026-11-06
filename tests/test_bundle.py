import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location(
    "collector",
    Path(__file__).resolve().parents[1] / "skills/source-recovery/scripts/collect_bundle.py",
)
collector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(collector)


class BundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.app = self.root / "App"
        self.app.mkdir()
        self.output = self.root / "out"

    def test_binary_resource_and_directory_preserved(self):
        (self.app / "empty").mkdir()
        (self.app / "binary").write_bytes(b"\x00\xff\x01")
        r = collector.collect(self.app, self.output)
        self.assertEqual(r["summary"]["copied_files"], 1)
        self.assertEqual(r["summary"]["errors"], 0)
        self.assertEqual((self.output / "bundle-files/binary").read_bytes(), b"\x00\xff\x01")
        self.assertTrue((self.output / "bundle-files/empty").is_dir())
        self.assertTrue(r["files"][0]["verified"])

    def test_symlinks_recorded_without_following(self):
        outside = self.root / "external"
        outside.mkdir()
        (outside / "private").write_text("private")
        try:
            (self.app / "link").symlink_to(outside, target_is_directory=True)
            (self.app / "broken").symlink_to(self.root / "missing")
        except OSError:
            self.skipTest("Symlinks unavailable")
        r = collector.collect(self.app, self.output)
        self.assertEqual(len(r["symlinks"]), 2)
        self.assertEqual(len(r["files"]), 0)
        self.assertFalse((self.output / "bundle-files/link").exists())

    def test_refuse_existing_and_nested_output(self):
        self.output.mkdir()
        with self.assertRaises(FileExistsError):
            collector.collect(self.app, self.output)
        with self.assertRaises(ValueError):
            collector.collect(self.app, self.app / "out")

    def test_missing_target_does_not_create_output(self):
        with self.assertRaises(ValueError):
            collector.collect(self.root / "missing", self.output)
        self.assertFalse(self.output.exists())
