# Project Record

## Objective
When a prompt or model changes, teams compare outputs with a plain text diff that flags every reworded sentence and hides the specific figures that changed. This library compares two outputs structurally: JSON replies field-by-field, and prose sentence-by-sentence with numbers paired explicitly.

## Scope
- Structural diffing for valid JSON using RFC 6901 paths.
- Prose diffing via sentence splitting and Jaccard similarity alignment.
- Numeric comparison for textual data.
- CLI interface for quick batch comparison.

## Out-of-Scope
- Semantic similarity comparisons via embedding models.
- LCS (Longest Common Subsequence) diff algorithms for arrays.
- HTML-based reports.

## Factory run u102 (measured from API usage)

| Phase | Model | Batch | Input | Output | Cache write | Cache read | Cost (USD) |
|---|---|---|---|---|---|---|---|
| generation | gemini-3.8-flash | yes | 4510 | 9923 | 0 | 0 | 0.0203 |
| fix-1 | gemini-3.8-flash | no | 51154 | 2005 | 0 | 74765 | 0.0515 |
| fix-2 | gemini-3.8-flash | no | 80682 | 1257 | 0 | 347897 | 0.0913 |
| fix-3 | gemini-3.8-flash | no | 69865 | 561 | 0 | 169041 | 0.0672 |
| fix-4 | gemini-3.8-flash | no | 88393 | 2532 | 0 | 698193 | 0.1282 |
| fix-1 | gemini-3.8-flash | no | 12628 | 225 | 0 | 8304 | 0.0109 |
| fix-2 | gemini-3.8-flash | no | 54913 | 1968 | 0 | 187797 | 0.0626 |
| audit | gemini-3.1-flash-lite | no | 71578 | 405 | 0 | 243840 | 0.0246 |
| fix-3 | gemini-3.8-flash | no | 58909 | 8074 | 0 | 316198 | 0.0982 |
| fix-4 | gemini-3.8-flash | no | 19667 | 405 | 0 | 1182 | 0.0164 |
| docs | gemini-3.1-flash-lite | no | 173652 | 1608 | 0 | 0 | 0.0458 |

Total: $0.6170. Prices: Anthropic list prices.
