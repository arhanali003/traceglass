# Contributing

The most useful contribution is a small, reproducible investigation that improves the workflow.

Include the question, a redistributable fixture or artifact identity, the client and available backend, observed results, and what remains unknown. Do not submit proprietary binaries, credentials, private captures, or invented benchmark scores.

For skill changes, explain the decision the new instruction improves. Keep format-specific details in references. For installer changes, run:

```bash
python3 -m unittest discover -s tests -v
```

Client compatibility reports should distinguish skill discovery, invocation, and actual tool execution. Label untested integrations as untested. Keep upstream attribution intact.
