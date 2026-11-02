# Feature tracing

Choose an observable entry point: command, handler, exported function, or route. Search for that symbol and its direct callers. Follow only the dependencies needed to explain the requested behavior.

Record a short chain: trigger → inputs → validation → transformation → sink. Cite each important transition. Inspect defaults, error paths, serialization, and resource configuration when they affect the result.

For minified bundles, preserve original byte/line locations and label any pretty-printed copies. For extracted packages, keep the source archive identity and extraction path. Do not equate a filename with a module identity if the backend exposes multiple graph nodes for it.

A network address in a bundle establishes its presence. A reachable call can support a static inference. A captured request supports execution only under the recorded conditions. Keep those claims separate.

Stop when the question has a supported answer or an explicit evidence gap. Offer the smallest observation that would resolve the gap, rather than broad instrumentation by default.
