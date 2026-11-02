# Release comparison

Bind both versions before comparing: path, build/version, digest or revision, and analysis method. Keep environment and feature inputs comparable. State any mismatch that prevents a fair comparison.

Start with the behavior the user names. Compare relevant entry points, configuration, data shape, and sinks. Distinguish packaging churn, renamed symbols, and generated assets from changes that affect behavior.

For each finding include old evidence, new evidence, the observed difference, and behavioral interpretation. If a feature was not found, state the search boundary rather than claiming removal. Runtime differences require comparable scenarios; static differences alone do not establish that a user encountered them.

End with changed / unchanged within inspected scope / unresolved. Preserve unknown coverage on both sides.
