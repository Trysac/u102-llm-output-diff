"""CLI entry point for llm-output-diff."""

from __future__ import annotations

import argparse
import sys

from .core import DiffError, diff_outputs, format_report


def main(argv: list[str] | None = None) -> int:
    """Run CLI.

    Exit 0 on no diff, 1 on diff findings or domain failure, 2 on usage/IO/parse error.
    """
    parser = argparse.ArgumentParser(
        prog="llm-output-diff",
        description="Diff two LLM outputs by JSON field, number and claim.",
    )
    parser.add_argument("file_a", help="Path to first output file")
    parser.add_argument("file_b", help="Path to second output file")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output report format (default: text)",
    )
    parser.add_argument(
        "--rel-tol",
        type=float,
        default=0.0,
        help="Relative numeric tolerance for JSON numbers",
    )
    parser.add_argument(
        "--similarity",
        type=float,
        default=0.5,
        help="Sentence alignment similarity threshold for text mode (0.0 < s <= 1.0)",
    )
    parser.add_argument(
        "--max-changes",
        type=int,
        default=1000,
        help="Maximum number of changes before truncation",
    )

    try:
        args = parser.parse_args(argv)
    except SystemExit as e:
        return 2 if e.code != 0 else 0

    try:
        with open(args.file_a, encoding="utf-8") as f:
            content_a = f.read()
        with open(args.file_b, encoding="utf-8") as f:
            content_b = f.read()
    except OSError as err:
        sys.stderr.write(f"Error reading input files: {err}\n")
        return 2

    try:
        report = diff_outputs(
            content_a,
            content_b,
            rel_tol=args.rel_tol,
            similarity=args.similarity,
            max_changes=args.max_changes,
        )
    except DiffError as err:
        sys.stderr.write(f"Diff error [{err.code}]: {err}\n")
        return 1
    except Exception as err:
        sys.stderr.write(f"Unexpected error: {err}\n")
        return 2

    output_str = format_report(report, fmt=args.format)
    if output_str:
        sys.stdout.write(output_str)

    return 1 if report.changes else 0


if __name__ == "__main__":
    sys.exit(main())
