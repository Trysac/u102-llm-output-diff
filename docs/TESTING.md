# Testing

Tests are located in the `tests/` directory and executed via `pytest`. The following coverage exists:

- `test_acceptance_1_diff_json_basic`: Validates structural JSON change detection.
- `test_acceptance_2_rfc6901_escaping_and_type_changed`: Verifies RFC 6901 path escaping and type mismatch handling.
- `test_acceptance_3_numeric_tolerance`: Tests `rel_tol` functionality.
- `test_acceptance_4_diff_text_numbers`: Tests numeric pairing in prose.
- `test_acceptance_5_diff_text_claims`: Tests sentence alignment and claim change logic.
- `test_acceptance_6_diff_outputs_fencing_and_fallback`: Verifies code fence stripping and format detection.
- `test_acceptance_7_limits_and_errors`: Tests input size limits, recursion limits, and error codes.
