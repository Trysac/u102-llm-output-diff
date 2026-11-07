# Architecture

## Overview
`llm-output-diff` implements a layered diffing engine.

## Components
- **`diff_outputs`**: The entry point for unknown formats. Strips code fences, performs an iterative parse, and dispatches to either `diff_json` or `diff_text`.
- **`diff_json`**: Compares structures using an iterative depth-first stack approach. It computes RFC 6901 paths and applies numerical tolerance (`math.isclose`) to floats/ints.
- **`diff_text`**: Splits text into sentences. It aligns sentences using Jaccard similarity on non-numeric tokens. Once aligned, it parses extracted numbers (using `Decimal` for comparison) to generate semantic change reports.
