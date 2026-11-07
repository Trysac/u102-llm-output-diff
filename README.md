# llm-output-diff

[![PyPI version](https://img.shields.io/pypi/v/trysac-llm-output-diff)](https://pypi.org/project/trysac-llm-output-diff/)
[![License: MIT](https://img.shields.io/pypi/l/trysac-llm-output-diff)](LICENSE)
[![CI](https://github.com/Trysac/u102-llm-output-diff/actions/workflows/ci.yml/badge.svg)](https://github.com/Trysac/u102-llm-output-diff/actions/workflows/ci.yml)

Diff two LLM outputs by JSON field, number and claim: RFC 6901 paths for structured replies, aligned sentences with changed numbers for prose

## Problem

Describe in two or three sentences the concrete problem this utility solves, who hits it, and what
they do today without it. Replace this paragraph when the first real feature lands.

## Install

```sh
pip install trysac-llm-output-diff
# or
uv add trysac-llm-output-diff
```

Requires Python 3.10 or newer. No runtime dependencies.

## Usage

```python
import llm_output_diff

# normalize() trims surrounding whitespace and lower-cases the text.
print(llm_output_diff.normalize("  Hello World "))  # -> "hello world"

# Blank input is rejected explicitly instead of returning an empty string.
try:
    llm_output_diff.normalize("   ")
except ValueError as exc:
    print(f"rejected: {exc}")
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) and [decisions](docs/decisions/)
- [Testing](docs/TESTING.md) and [security](docs/SECURITY.md)
- [Project record](docs/PROJECT.md) and [stack](docs/STACK.md)
- [Changelog](CHANGELOG.md) and [contributing guide](CONTRIBUTING.md)

## License

[MIT](LICENSE) (c) 2026 Miguel Gomez
