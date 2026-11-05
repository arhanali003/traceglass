# Verify an agent's saved evidence

From the repository root, choose a new output directory outside the fixture:

```bash
python3 skills/source-recovery/scripts/collect_bundle.py --target examples/demo-app --output /tmp/traceglass-example-bundle
python3 skills/source-recovery/scripts/verify_bundle.py --bundle /tmp/traceglass-example-bundle
```

On Windows replace `/tmp/traceglass-example-bundle` with an unused local path.
The collector refuses existing output directories. Choose another path on repeat
runs. A successful verification exits 0 and reports `status: "ok"`.

To demonstrate failure, modify only the disposable collected copy:

```bash
python3 -c "from pathlib import Path; p = Path('/tmp/traceglass-example-bundle/bundle-files/export.js'); p.write_bytes(p.read_bytes() + b'\n// changed\n')"
python3 skills/source-recovery/scripts/verify_bundle.py --bundle /tmp/traceglass-example-bundle
```

The second verification exits 2 and reports `mismatch` for `export.js`. The original
fixture remains unchanged. An AI agent should report this failure rather than use
the old report as if the bytes still matched. This is a synthetic example, not a
claim of a production investigation or user adoption.

See [the command contract and limits](../docs/bundle-verification.md).
