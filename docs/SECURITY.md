# Security

## Threat Model

- **Unbounded Input Size**: Defended. Payloads exceeding 200,000 characters result in an `input_too_large` `DiffError`.
- **Denial of Service (Recursion)**: Defended. The JSON parser uses iterative stack-based traversal with a strict `max_depth` (default 64) to prevent stack overflow attacks.
- **Denial of Service (Output Size)**: Defended. The library truncates results to `max_changes` (default 1000) and marks the report as `truncated=True`.
- **Information Disclosure**: Defended. All logging uses `logging.NullHandler`; the library does not log input content.
