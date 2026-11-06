# Traceglass early beta

Audience: 5–10 external developers trying a skill package and local evidence tools.
This is a feedback plan, not a claim that testers have participated. All commands
below run from the extracted distribution or repository root. Replace `python3`
with `python` on Windows if that is how Python is installed.

## Install and first success

Use Python 3.9+; CI targets 3.9 and 3.13. No API key, remote model or Python package
installation is needed for the helper workflow. Native reporting is macOS-only.
An AI coding client is needed only for the optional agent-guided investigation.

```sh
python3 scripts/install.py --version
python3 -c "from pathlib import Path; Path('beta-project').mkdir()"
python3 scripts/install.py --client all --project beta-project --dry-run
python3 scripts/install.py --client all --project beta-project
python3 scripts/install.py --client all --project beta-project --skill source-recovery
```

Version: `Traceglass 0.2.0b1`. Two skill locations per skill are printed: `.agents`
and `.claude`. Dry-run creates no files. No initial configuration file is required.
Use a new directory on repeated runs; an existing installation is deliberately
rejected. The helpers can also be run directly from this distribution.

## Scenarios

### 1. Normal workflow: preserve an export component before changing it

```sh
python3 skills/source-recovery/scripts/recover.py --target examples/demo-app --output beta-recovery
python3 skills/source-recovery/scripts/collect_bundle.py --target examples/demo-app --output beta-bundle
python3 skills/source-recovery/scripts/verify_bundle.py --bundle beta-bundle
```

Expected: one recovered source record, one copied file, verifier exit 0 with
`status: "ok"`, `checked_files: 1`. The fixture contains an export function, not a
full application. Compare its original bytes with the path recorded in the recovery
manifest. The source is never executed by these commands.

### 2. Invalid input

```sh
python3 skills/source-recovery/scripts/recover.py --target does-not-exist --output beta-invalid
```

Expected: exit 1, a readable error, no output directory. Missing required CLI
arguments instead use argparse exit 2 and show usage.

### 3. Larger input without private code

```sh
python3 -c "from pathlib import Path; p=Path('beta-large'); p.mkdir(); [(p / ('part-%04d.js' % i)).write_text('// synthetic fixture\n' * 100, encoding='utf-8') for i in range(300)]"
python3 skills/source-recovery/scripts/collect_bundle.py --target beta-large --output beta-large-bundle
python3 skills/source-recovery/scripts/verify_bundle.py --bundle beta-large-bundle
```

Expected: 300 copied and checked files, no collection errors. This is a modest
synthetic scale check, not a performance benchmark or proof of arbitrary scale.
Record elapsed time only if you measured it and include hardware/input details.

### 4. Saved evidence after a change

After scenario 1, alter only the collected fixture:

```sh
python3 -c "from pathlib import Path; p=Path('beta-bundle/bundle-files/export.js'); p.write_bytes(p.read_bytes()+b'\n// changed\n')"
python3 skills/source-recovery/scripts/verify_bundle.py --bundle beta-bundle
```

Expected: exit 2, `status: "failed"`, `mismatch`. This tests integrity, not
truthfulness or authenticity. Do not modify the original fixture.

### 5. Failure handling and partial results

```sh
python3 -c "from pathlib import Path; p=Path('beta-malformed'); p.mkdir(); (p/'broken.map').write_text('{', encoding='utf-8')"
python3 skills/source-recovery/scripts/recover.py --target beta-malformed --output beta-partial
```

Expected: exit 2, zero recovered records; `manifest.json` records the invalid map
in `skipped`. Exit 2 does not mean no output was written. Also repeat installation
from the first section: it must refuse to overwrite the existing skills.

### 6. Optional agent-guided feature trace

Start a fresh session in `beta-project`, invoke Traceglass and give it the absolute
path to `examples/demo-app/export.js`. Ask whether archived contacts and email
addresses appear in CSV export. Compare its evidence against
[the walkthrough](examples/walkthrough.md). Record client/version, discovery,
invocation, tool execution and errors separately. Agent answers vary; the helper
tests do not certify model-generated conclusions. Do not execute unfamiliar code.

## Feedback template

Open a bug/compatibility issue with sanitized output, or send this to the maintainer:

1. Did installation succeed? Which command did you run?
2. OS, Python version, Traceglass version and (if used) client/version?
3. Which scenarios or real workflows did you test?
4. Errors, exact exit code and minimal reproduction?
5. Was the output useful and understandable?
6. What was confusing?
7. What single improvement would help most?
8. Would you use Traceglass again? Why or why not?

Do not send source bundles, credentials, private paths, customer data or proprietary
binaries. Replace them with synthetic reproductions. Ask permission before quoting
any tester publicly. There is no telemetry or automatic feedback collection.

Clean up only the `beta-*` directories you created after reviewing their contents.
The package has no uninstall daemon or system registration.
