# Dual-mode diffing with iterative traversal and sentence alignment

Status: accepted (generated, pending human review)

## Context

LLM outputs vary between structured JSON and free-form prose. Comparing them requires format-aware diffing with RFC 6901 pointers, numeric tolerance, and sentence-level number pairing without recursion vulnerabilities.

## Decision

Implement iterative BFS traversal with strict depth limits for JSON diffing and Jaccard-based sentence alignment for prose diffing, adhering to RFC 6901 pointer syntax and Decimal numeric comparison.

## Consequences

Provides structured, explainable diffs for both JSON and text responses while maintaining standard library purity, linear complexity bounds, and resilience against deep JSON nesting.
