# llm-output-diff

![Build](https://github.com/u102-llm-output-diff/actions/workflows/ci.yml/badge.svg)

Diff two LLM outputs by JSON field, number and claim: RFC 6901 paths for structured replies, aligned sentences with changed numbers for prose.

## Installation

```bash
pip install llm-output-diff
```

## Usage

```python
from llm_output_diff import diff_outputs, format_report

a = '{"metric": "revenue", "total": 100}'
b = '{"metric": "revenue", "total": 105}'
report = diff_outputs(a, b, rel_tol=0.01)
print(format_report(report))
```

## Public API

- `diff_json(a: object, b: object, *, rel_tol: float = 0.0, max_changes: int = 1000, max_depth: int = 64) -> DiffReport`
- `diff_text(a: str, b: str, *, similarity: float = 0.5, max_changes: int = 1000) -> DiffReport`
- `diff_outputs(a: str, b: str, **kw: Any) -> DiffReport`: Automatically detects format, striping code fences.
- `format_report(report: DiffReport, fmt: Literal['text', 'json'] = 'text') -> str`

### Limits and Options
- **Input Limit**: 200,000 characters maximum.
- **Depth Limit**: 64 nested levels for JSON.
- **Truncation**: Returns max 1000 changes.
- **Numeric Tolerance**: `rel_tol` parameter controls `math.isclose` behavior.

## Why not <best-known alternative>?

Existing tools like `difflib` are line-based and cannot detect semantic changes across reworded prose. `deepdiff` supports JSON diffs but provides no specialized mode for prose, sentence alignment, or numeric pairing, which are critical for evaluating LLM outputs.

## Security
See [docs/SECURITY.md](docs/SECURITY.md).
