import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location(
    "installer", Path(__file__).resolve().parents[1] / "scripts/install.py"
)
installer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name).resolve()

    def test_dry_run_does_not_write(self):
        self.assertEqual(len(installer.install("all", self.project, True)), 2)
        self.assertEqual(list(self.project.iterdir()), [])

    def test_each_client_gets_complete_skill(self):
        for client, directory in installer.LOCATIONS.items():
            with self.subTest(client=client):
                project = self.project / client
                project.mkdir()
                destinations = installer.install(client, project)
                self.assertEqual(destinations, [project / directory / "skills/traceglass"])
                for source in installer.SOURCE.rglob("*"):
                    if source.is_file():
                        self.assertEqual(
                            source.read_bytes(),
                            (destinations[0] / source.relative_to(installer.SOURCE)).read_bytes(),
                        )

    def test_all_deduplicates_shared_location(self):
        self.assertEqual(len(installer.install("all", self.project)), 2)

    def test_conflict_preflight_preserves_existing_files(self):
        existing = self.project / ".claude/skills/traceglass"
        existing.mkdir(parents=True)
        (existing / "custom.md").write_text("keep me")
        with self.assertRaises(ValueError):
            installer.install("all", self.project)
        self.assertEqual((existing / "custom.md").read_text(), "keep me")
        self.assertFalse((self.project / ".agents").exists())

    def test_missing_project_is_not_created(self):
        with self.assertRaises(ValueError):
            installer.install("codex", self.project / "missing")
        self.assertFalse((self.project / "missing").exists())

    def test_copy_failure_rolls_back_skill(self):
        with patch.object(
            installer.shutil, "copytree", side_effect=OSError("simulated disk error")
        ):
            with self.assertRaises(OSError):
                installer.install("all", self.project)
        self.assertFalse((self.project / ".agents/skills/traceglass").exists())

    def test_external_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as outside:
            try:
                (self.project / ".agents").symlink_to(outside, target_is_directory=True)
            except OSError:
                self.skipTest("Symlinks unavailable on this host")
            with self.assertRaises(ValueError):
                installer.install("codex", self.project)
            self.assertEqual(list(Path(outside).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
