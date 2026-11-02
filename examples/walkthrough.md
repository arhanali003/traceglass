# A small investigation you can check

This example uses a deliberately small readable fixture, not a real application or a benchmark. It demonstrates the reporting style without requiring a backend.

Install into this checkout, then prompt your agent:

> Use Traceglass to inspect examples/demo-app/export.js. Does CSV export include archived contacts or email addresses? Do not execute it; cite the static evidence.

Expected findings from reading the fixture:

| Claim | Evidence | Status |
| --- | --- | --- |
| Truthy `archived` values exclude a contact | `demo-app/export.js:9` | Observed in code |
| The email column is omitted by default | `demo-app/export.js:7-8` | Observed in code |
| `includeEmail: true` adds email | `demo-app/export.js:8` | Observed in code |
| Quotes, commas, CR and LF cause CSV quoting | `demo-app/export.js:2-4` | Observed in code |
| A production UI uses this function | No caller or UI supplied | Unknown |

Trace: `exportContacts` → choose columns → filter rows → escape cells → join CSV records with CRLF.

Scope: a static reading of one fixture. No runtime, caller, filesystem write, or network behavior was observed. This is a hand-authored worked example, not a transcript of a live client run.
