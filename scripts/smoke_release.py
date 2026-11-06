#!/usr/bin/env python3
"""Build, unpack and exercise the skill distribution in an isolated temp directory."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

from build_release import build


def smoke():
    with tempfile.TemporaryDirectory(prefix="traceglass beta ") as directory:
        root = Path(directory)
        archive = build(root / "release.zip")
        with zipfile.ZipFile(archive) as bundle:
            # This archive was just produced by our builder from this checkout.
            bundle.extractall(root / "unpacked")
        package = next((root / "unpacked").iterdir())
        manifest = json.loads((package / "DIST-MANIFEST.json").read_text())
        for name, expected in manifest["sha256"].items():
            if hashlib.sha256((package / name).read_bytes()).hexdigest() != expected:
                raise AssertionError(f"Distribution checksum mismatch: {name}")
        project = root / "new developer project"
        project.mkdir()

        def run(script, *arguments, expected=0):
            result = subprocess.run(
                [sys.executable, "-I", str(script), *map(str, arguments)],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode != expected:
                raise AssertionError(
                    f"{script.name}: {result.returncode}\n{result.stdout}\n{result.stderr}"
                )
            return result.stdout

        installer = package / "scripts/install.py"
        for skill in ("traceglass", "source-recovery"):
            run(installer, "--client", "all", "--project", project, "--skill", skill)
        scripts = project / ".agents/skills/source-recovery/scripts"
        fixture = package / "examples/demo-app"
        recovered = root / "recovered"
        run(scripts / "recover.py", "--target", fixture, "--output", recovered)
        records = json.loads((recovered / "manifest.json").read_text())["records"]
        assert len(records) == 1
        assert (recovered / records[0]["output"]).read_bytes() == (
            fixture / "export.js"
        ).read_bytes()
        evidence = root / "saved evidence"
        run(scripts / "collect_bundle.py", "--target", fixture, "--output", evidence)
        good = json.loads(run(scripts / "verify_bundle.py", "--bundle", evidence))
        assert good["status"] == "ok" and good["checked_files"] == 1
        with (evidence / "bundle-files/export.js").open("ab") as stream:
            stream.write(b"\n// changed fixture copy\n")
        bad = json.loads(run(scripts / "verify_bundle.py", "--bundle", evidence, expected=2))
        assert bad["files"][0]["status"] == "mismatch"
        run(installer, "--client", "codex", "--project", project, expected=1)
        print(
            "PASS: archive hashes, both skill installations, recovery, collection, verification, tamper detection, overwrite refusal"
        )


if __name__ == "__main__":
    smoke()
