"""Regressions found during the beta audit; all targets are synthetic."""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills/source-recovery/scripts"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


recovery = load("beta_recovery", SCRIPTS / "recover.py")
collector = load("beta_collector", SCRIPTS / "collect_bundle.py")
installer = load("beta_installer", ROOT / "scripts/install.py")
builder = load("beta_builder", ROOT / "scripts/build_release.py")


class BetaTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="traceglass tests ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.source = self.root / "input with spaces"
        self.source.mkdir()
        self.output = self.root / "output with spaces"

    def cli(self, script, *args):
        return subprocess.run(
            [sys.executable, str(script), *map(str, args)],
            capture_output=True,
            text=True,
            timeout=20,
        )

    def test_recovery_partial_cli_status(self):
        (self.source / "bad.map").write_text("{")
        run = self.cli(SCRIPTS / "recover.py", "--target", self.source, "--output", self.output)
        self.assertEqual(run.returncode, 2, run.stderr)
        result = json.loads((self.output / "manifest.json").read_text())
        self.assertEqual(len(result["skipped"]), 1)
        self.assertEqual(result["records"], [])

    def test_empty_recovery_is_explicit_success(self):
        result = self.cli(SCRIPTS / "recover.py", "--target", self.source, "--output", self.output)
        self.assertEqual(result.returncode, 0)
        self.assertIn("Recovered 0 records", result.stdout)

    def test_special_root_rejected_before_output(self):
        if not hasattr(os, "mkfifo"):
            self.skipTest("FIFO unavailable")
        fifo = self.root / "pipe.js"
        os.mkfifo(fifo)
        with self.assertRaises(ValueError):
            recovery.recover(fifo, self.output)
        self.assertFalse(self.output.exists())

    def test_directory_creation_failure_retains_manifest_and_other_files(self):
        (self.source / "denied").mkdir()
        (self.source / "ok.js").write_text("hello")
        original = Path.mkdir
        blocked = self.output / "bundle-files/denied"

        def mkdir(path, *args, **kwargs):
            if path == blocked:
                raise PermissionError("simulated write denial")
            return original(path, *args, **kwargs)

        with patch.object(Path, "mkdir", mkdir):
            result = collector.collect(self.source, self.output)
        self.assertEqual(result["summary"]["errors"], 1)
        self.assertEqual(result["summary"]["copied_files"], 1)
        self.assertTrue((self.output / "bundle-manifest.json").is_file())

    def test_recovery_permission_error_is_recorded(self):
        blocked = self.source / "denied.js"
        blocked.write_text("private")
        original = os.open

        def opened(path, *args, **kwargs):
            if Path(path) == blocked:
                raise PermissionError("simulated read denial")
            return original(path, *args, **kwargs)

        with patch.object(recovery.os, "open", opened):
            result = recovery.recover(self.source, self.output)
        self.assertEqual(result["records"], [])
        self.assertIn("denial", result["skipped"][0]["reason"])

    def test_reparse_directory_is_not_traversed(self):
        child = self.source / "junction"
        child.mkdir()
        (child / "secret.js").write_text("not to be read")
        original = Path.lstat

        def lstat(path, *args, **kwargs):
            info = original(path, *args, **kwargs)
            return (
                SimpleNamespace(st_mode=info.st_mode, st_file_attributes=0x400)
                if path == child
                else info
            )

        with patch.object(Path, "lstat", lstat):
            collected = collector.collect(self.source, self.output)
            recovered = recovery.recover(self.source, self.root / "recovered")
        self.assertEqual(collected["files"], [])
        self.assertEqual(len(collected["errors"]), 1)
        self.assertEqual(recovered["records"], [])
        self.assertEqual(len(recovered["skipped"]), 1)

    @unittest.skipUnless(os.name == "nt", "Windows junction integration")
    def test_real_windows_junction(self):
        outside = self.root / "outside"
        outside.mkdir()
        (outside / "private.js").write_text("private")
        junction = self.source / "junction"
        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(junction), str(outside)], capture_output=True
        )
        if result.returncode:
            self.skipTest("Junction creation unavailable")
        self.addCleanup(junction.rmdir)
        self.assertEqual(collector.collect(self.source, self.output)["files"], [])
        self.assertEqual(recovery.recover(self.source, self.root / "recovered")["records"], [])

    def test_unknown_installer_client(self):
        with self.assertRaisesRegex(ValueError, "Unknown client"):
            installer.install("unknown", self.source)
        self.assertEqual(list(self.source.iterdir()), [])

    def test_all_cli_versions_and_help(self):
        version = (ROOT / "VERSION").read_text().strip()
        for script in [ROOT / "scripts/install.py", *sorted(SCRIPTS.glob("*.py"))]:
            with self.subTest(script=script.name):
                run = self.cli(script, "--version")
                self.assertEqual(run.returncode, 0)
                self.assertEqual(run.stdout.strip(), "Traceglass " + version)
                self.assertEqual(self.cli(script, "--help").returncode, 0)

    def test_missing_input_cli_has_no_traceback(self):
        for name in ("recover.py", "collect_bundle.py", "native_report.py"):
            with self.subTest(script=name):
                run = self.cli(
                    SCRIPTS / name, "--target", self.root / "missing", "--output", self.output
                )
                self.assertEqual(run.returncode, 1)
                self.assertNotIn("Traceback", run.stderr)
                self.assertFalse(self.output.exists())

    def test_larger_collection_roundtrip(self):
        verifier = load("beta_verifier", SCRIPTS / "verify_bundle.py")
        for index in range(300):
            (self.source / f"{index:04}.js").write_bytes(b"// fixture\n" * 100)
        result = collector.collect(self.source, self.output)
        self.assertEqual(result["summary"]["copied_files"], 300)
        checked = verifier.verify(self.output)
        self.assertEqual((checked["status"], checked["checked_files"]), ("ok", 300))

    def test_distribution_reproducible_and_exclusive(self):
        first = builder.build(self.root / "a.zip")
        second = builder.build(self.root / "b.zip")
        self.assertEqual(first.read_bytes(), second.read_bytes())
        before = first.read_bytes()
        with self.assertRaises(FileExistsError):
            builder.build(first)
        self.assertEqual(first.read_bytes(), before)

    def test_windows_ambiguous_manifest_paths_rejected(self):
        verifier = load("beta_path_verifier", SCRIPTS / "verify_bundle.py")
        for name in (
            ".. /escape",
            "name.",
            "name /file",
            "CON",
            "nul.txt",
            "COM1.js",
            "LPT¹",
            "bad\nname",
        ):
            with self.subTest(name=name), self.assertRaises(ValueError):
                verifier.relative_path(name)

    def test_collector_cli_roundtrip_and_existing_output(self):
        (self.source / "one.js").write_text("one")
        run = self.cli(
            SCRIPTS / "collect_bundle.py", "--target", self.source, "--output", self.output
        )
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(json.loads(run.stdout)["copied_files"], 1)
        again = self.cli(
            SCRIPTS / "collect_bundle.py", "--target", self.source, "--output", self.output
        )
        self.assertEqual(again.returncode, 1)
        self.assertEqual((self.output / "bundle-files/one.js").read_text(), "one")

    def test_native_success_with_trusted_tool_stub(self):
        native = load("beta_native", SCRIPTS / "native_report.py")
        target = self.source / "native fixture"
        target.write_bytes(bytes.fromhex("cffaedfe") + b"fixture")

        def run(command, **kwargs):
            self.assertIsInstance(command, list)
            self.assertNotIn("shell", kwargs)
            kwargs["stdout"].write(b"static metadata")
            return SimpleNamespace(returncode=0)

        with (
            patch.object(native.shutil, "which", return_value=str(target)),
            patch.object(native.subprocess, "run", side_effect=run),
        ):
            result = native.export(target, self.output, assembly=True)
        self.assertTrue(result["input_unchanged"])
        self.assertEqual(len(result["jobs"]), 5)
        self.assertTrue(all(job["status"] == "completed" for job in result["jobs"]))

    def test_recovery_source_changes_are_not_saved(self):
        target = self.source / "changing.js"
        target.write_text("first")
        original = recovery.os.fstat
        calls = 0

        def changed(fd):
            nonlocal calls
            calls += 1
            if calls == 2:
                target.write_text("changed to a longer value")
            return original(fd)

        with patch.object(recovery.os, "fstat", changed):
            result = recovery.recover(self.source, self.output)
        self.assertEqual(result["records"], [])
        self.assertIn("changed", result["skipped"][0]["reason"])

    def test_recovery_records_links_even_without_source_extension(self):
        target = self.root / "outside.txt"
        target.write_text("private")
        try:
            (self.source / "link.txt").symlink_to(target)
        except OSError:
            self.skipTest("Symlinks unavailable")
        result = recovery.recover(self.source, self.output)
        self.assertEqual(result["records"], [])
        self.assertEqual(len(result["skipped"]), 1)

    def test_builder_rejects_link_without_creating_archive(self):
        for name in builder.FILES:
            (self.source / name).write_text("0.2.0b1" if name == "VERSION" else "fixture")
        for name in builder.DIRECTORIES:
            (self.source / name).mkdir()
        outside = self.root / "private.txt"
        outside.write_text("private")
        try:
            (self.source / "assets/link.txt").symlink_to(outside)
        except OSError:
            self.skipTest("Symlinks unavailable")
        with self.assertRaises(ValueError):
            builder.build(self.output, self.source)
        self.assertFalse(self.output.exists())
