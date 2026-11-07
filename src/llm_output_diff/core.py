"""Core diff algorithms and data structures for LLM outputs."""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Literal

DEFAULT_MAX_INPUT_CHARS: int = 200_000
DEFAULT_MAX_DEPTH: int = 64
DEFAULT_MAX_CHANGES: int = 1000
DEFAULT_SIMILARITY: float = 0.5

Kind = Literal[
    "added",
    "removed",
    "changed",
    "type_changed",
    "number_changed",
    "claim_added",
    "claim_removed",
    "claim_changed",
]

Mode = Literal["json", "text"]
ReportFormat = Literal["text", "json"]
DiffErrorCode = Literal["input_too_large", "too_deep", "invalid_option"]


class DiffError(ValueError):
    """Base error class with typed machine-readable code."""

    def __init__(self, code: DiffErrorCode, message: str) -> None:
        super().__init__(message)
        self.code: DiffErrorCode = code


@dataclass(frozen=True)
class Change:
    """A single detected difference."""

    kind: Kind
    path: str
    before: Any
    after: Any


@dataclass(frozen=True)
class DiffReport:
    """Summary report of detected differences."""

    mode: Mode
    changes: tuple[Change, ...]
    truncated: bool


_RE_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
_RE_WHITESPACE = re.compile(r"\s+")
_RE_WORD_TOKEN = re.compile(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b")
_RE_NUMBER = re.compile(r"(?<![\w.])-?\d+(?:\.\d+)?(?![\w])")


def _escape_json_pointer_segment(segment: str) -> str:
    return segment.replace("~", "~0").replace("/", "~1")


def _pointer_sort_key(path: str) -> list[tuple[int, Any]]:
    """Sort paths so array indexes order numerically (e.g., /b/2 before /b/10)."""
    if not path:
        return []
    parts = path.lstrip("/").split("/")
    key: list[tuple[int, Any]] = []
    for part in parts:
        if part.isdigit():
            key.append((0, int(part)))
        else:
            key.append((1, part))
    return key


def _is_number(val: Any) -> bool:
    return isinstance(val, (int, float)) and not isinstance(val, bool)


def _numbers_equal(a: int | float, b: int | float, rel_tol: float) -> bool:
    if rel_tol > 0.0:
        return bool(math.isclose(float(a), float(b), rel_tol=rel_tol, abs_tol=0.0))
    return a == b


def diff_json(
    a: object,
    b: object,
    *,
    rel_tol: float = 0.0,
    max_changes: int = DEFAULT_MAX_CHANGES,
    max_depth: int = DEFAULT_MAX_DEPTH,
) -> DiffReport:
    """Compare two JSON-like structures iteratively."""
    if rel_tol < 0.0:
        raise DiffError("invalid_option", "rel_tol must be non-negative")
    if max_changes < 0:
        raise DiffError("invalid_option", "max_changes must be non-negative")
    if max_depth < 0:
        raise DiffError("invalid_option", "max_depth must be non-negative")

    # Iterative BFS / stack traversal to enforce max_depth and avoid deep recursion
    changes: list[Change] = []
    stack: list[tuple[object, object, str, int]] = [(a, b, "", 0)]

    while stack:
        curr_a, curr_b, path, depth = stack.pop()

        if depth > max_depth:
            raise DiffError("too_deep", f"JSON nested deeper than {max_depth} at path {path}")

        # Check depth on container before expanding children
        if (
            isinstance(curr_a, (dict, list)) or isinstance(curr_b, (dict, list))
        ) and depth >= max_depth:
            raise DiffError("too_deep", f"JSON nested deeper than {max_depth} at path {path}")

        # Case 1: identical references or equal values of same fundamental type
        if curr_a is curr_b:
            # If it's a container, verify inner depth does not exceed max_depth
            if isinstance(curr_a, (dict, list)):
                pass
            else:
                continue

        a_is_num = _is_number(curr_a)
        b_is_num = _is_number(curr_b)

        if a_is_num and b_is_num:
            if not isinstance(curr_a, (int, float)) or not isinstance(curr_b, (int, float)):
                continue
            if not _numbers_equal(curr_a, curr_b, rel_tol):
                changes.append(Change("changed", path, curr_a, curr_b))
            continue

        if a_is_num != b_is_num:
            changes.append(Change("type_changed", path, curr_a, curr_b))
            continue

        type_a = type(curr_a)
        type_b = type(curr_b)

        if type_a is not type_b:
            changes.append(Change("type_changed", path, curr_a, curr_b))
            continue

        # Same types and not numeric
        if isinstance(curr_a, dict):
            if isinstance(curr_b, dict):
                all_keys = sorted(set(curr_a.keys()) | set(curr_b.keys()))
                # We iterate in reverse so when popped they are evaluated in order
                for k in reversed(all_keys):
                    seg = _escape_json_pointer_segment(str(k))
                    child_path = f"{path}/{seg}"
                    if k not in curr_a:
                        changes.append(Change("added", child_path, None, curr_b[k]))
                    elif k not in curr_b:
                        changes.append(Change("removed", child_path, curr_a[k], None))
                    else:
                        stack.append((curr_a[k], curr_b[k], child_path, depth + 1))
        elif isinstance(curr_a, list):
            if isinstance(curr_b, list):
                len_a = len(curr_a)
                len_b = len(curr_b)
                min_len = min(len_a, len_b)

                # For extra items
                if len_b > min_len:
                    for i in range(min_len, len_b):
                        child_path = f"{path}/{i}"
                        changes.append(Change("added", child_path, None, curr_b[i]))
                elif len_a > min_len:
                    for i in range(min_len, len_a):
                        child_path = f"{path}/{i}"
                        changes.append(Change("removed", child_path, curr_a[i], None))

                # For common prefix, push in reverse
                for i in reversed(range(min_len)):
                    child_path = f"{path}/{i}"
                    stack.append((curr_a[i], curr_b[i], child_path, depth + 1))
        else:
            if curr_a != curr_b:
                changes.append(Change("changed", path, curr_a, curr_b))

    # Sort changes by path with array indexes ordered numerically
    changes.sort(key=lambda c: (_pointer_sort_key(c.path), c.kind))

    truncated = False
    if len(changes) > max_changes:
        changes = changes[:max_changes]
        truncated = True

    return DiffReport(mode="json", changes=tuple(changes), truncated=truncated)


def _split_sentences(text: str) -> list[str]:
    collapsed = _RE_WHITESPACE.sub(" ", text).strip()
    if not collapsed:
        return []
    parts = _RE_SENTENCE_SPLIT.split(collapsed)
    return [p.strip() for p in parts if p.strip()]


def _extract_alignment_tokens(sentence: str) -> set[str]:
    tokens = _RE_WORD_TOKEN.findall(sentence.lower())
    return {t for t in tokens if not t.isdigit()}


def _jaccard_similarity(s1: set[str], s2: set[str]) -> float:
    if not s1 and not s2:
        return 1.0
    union = s1 | s2
    if not union:
        return 0.0
    return len(s1 & s2) / len(union)


def _extract_numbers(sentence: str) -> list[str]:
    # Return matched numbers normalized via Decimal string if valid
    raw_matches = _RE_NUMBER.findall(sentence)
    results: list[str] = []
    for m in raw_matches:
        try:
            # Decimal retains scale or string format comparison
            # We compare Decimal values: if Decimal(a) == Decimal(b), they are equal
            results.append(m)
        except Exception:
            results.append(m)
    return results


def diff_text(
    a: str,
    b: str,
    *,
    similarity: float = DEFAULT_SIMILARITY,
    max_changes: int = DEFAULT_MAX_CHANGES,
) -> DiffReport:
    """Compare two text documents sentence-by-sentence."""
    if not (0.0 < similarity <= 1.0):
        raise DiffError("invalid_option", "similarity must be in the interval (0, 1]")
    if max_changes < 0:
        raise DiffError("invalid_option", "max_changes must be non-negative")
    if len(a) > DEFAULT_MAX_INPUT_CHARS or len(b) > DEFAULT_MAX_INPUT_CHARS:
        raise DiffError(
            "input_too_large", f"Input text exceeds {DEFAULT_MAX_INPUT_CHARS} characters"
        )

    a_sents = _split_sentences(a)
    b_sents = _split_sentences(b)

    a_tokens = [_extract_alignment_tokens(s) for s in a_sents]
    b_tokens = [_extract_alignment_tokens(s) for s in b_sents]

    matched_b: set[int] = set()
    # map a_index -> b_index
    alignment: dict[int, int] = {}

    for i, a_tok in enumerate(a_tokens):
        best_score = -1.0
        best_j = -1
        for j, b_tok in enumerate(b_tokens):
            if j in matched_b:
                continue
            score = _jaccard_similarity(a_tok, b_tok)
            if score >= similarity and score > best_score:
                best_score = score
                best_j = j
        if best_j != -1:
            alignment[i] = best_j
            matched_b.add(best_j)

    changes: list[Change] = []

    # Process a sentences in order: aligned or removed
    for i, a_sent in enumerate(a_sents):
        path = f"s{i + 1}"
        if i in alignment:
            j = alignment[i]
            b_sent = b_sents[j]
            if a_sent == b_sent:
                continue
            a_nums = _extract_numbers(a_sent)
            b_nums = _extract_numbers(b_sent)
            if len(a_nums) == len(b_nums) and len(a_nums) > 0:
                differing = False
                pair_changes: list[Change] = []
                for an, bn in zip(a_nums, b_nums, strict=False):
                    try:
                        eq = Decimal(an) == Decimal(bn)
                    except Exception:
                        eq = an == bn
                    if not eq:
                        differing = True
                        pair_changes.append(Change("number_changed", path, an, bn))
                if differing:
                    changes.extend(pair_changes)
                else:
                    changes.append(Change("claim_changed", path, a_sent, b_sent))
            else:
                changes.append(Change("claim_changed", path, a_sent, b_sent))
        else:
            changes.append(Change("claim_removed", path, a_sent, None))

    # Process unaligned b sentences: added in b index order
    for j, b_sent in enumerate(b_sents):
        if j not in matched_b:
            changes.append(Change("claim_added", f"t{j + 1}", None, b_sent))

    truncated = False
    if len(changes) > max_changes:
        changes = changes[:max_changes]
        truncated = True

    return DiffReport(mode="text", changes=tuple(changes), truncated=truncated)


def _strip_code_fence(s: str) -> str:
    stripped = s.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 2 and lines[-1].strip() == "```":
            return "\n".join(lines[1:-1]).strip()
    return stripped


def _strict_json_loads(s: str) -> object:
    # parse_constant rejects NaN, Infinity, -Infinity
    def _reject_constant(c: str) -> None:
        raise ValueError(f"Invalid JSON constant: {c}")

    return json.loads(s, parse_constant=_reject_constant)


def diff_outputs(a: str, b: str, **kw: Any) -> DiffReport:
    """Diff two outputs as JSON if both parse as JSON, otherwise as text."""
    if len(a) > DEFAULT_MAX_INPUT_CHARS or len(b) > DEFAULT_MAX_INPUT_CHARS:
        raise DiffError(
            "input_too_large", f"Input text exceeds {DEFAULT_MAX_INPUT_CHARS} characters"
        )

    clean_a = _strip_code_fence(a)
    clean_b = _strip_code_fence(b)

    is_json = False
    parsed_a: object = None
    parsed_b: object = None

    try:
        parsed_a = _strict_json_loads(clean_a)
        parsed_b = _strict_json_loads(clean_b)
        is_json = True
    except Exception:
        is_json = False

    if is_json:
        # Pass allowed keyword arguments to diff_json
        json_kw: dict[str, Any] = {}
        for k in ("rel_tol", "max_changes", "max_depth"):
            if k in kw:
                json_kw[k] = kw[k]
        return diff_json(parsed_a, parsed_b, **json_kw)

    # Pass allowed keyword arguments to diff_text
    text_kw: dict[str, Any] = {}
    for k in ("similarity", "max_changes"):
        if k in kw:
            text_kw[k] = kw[k]
    return diff_text(a, b, **text_kw)


def format_report(report: DiffReport, fmt: ReportFormat = "text") -> str:
    """Format a DiffReport into human-readable text or JSON string."""
    if fmt == "json":
        data = {
            "mode": report.mode,
            "truncated": report.truncated,
            "changes": [
                {
                    "kind": c.kind,
                    "path": c.path,
                    "before": c.before,
                    "after": c.after,
                }
                for c in report.changes
            ],
        }
        return json.dumps(data, indent=2, sort_keys=True) + "\n"

    if fmt == "text":
        lines: list[str] = []
        for c in report.changes:
            before_json = json.dumps(c.before, ensure_ascii=False)
            after_json = json.dumps(c.after, ensure_ascii=False)
            if c.kind in ("changed", "type_changed", "number_changed", "claim_changed"):
                lines.append(f"~ {c.path}: {before_json} -> {after_json}")
            elif c.kind in ("removed", "claim_removed"):
                lines.append(f"- {c.path}: {before_json}")
            elif c.kind in ("added", "claim_added"):
                lines.append(f"+ {c.path}: {after_json}")
        if report.truncated:
            lines.append("... truncated")
        return "\n".join(lines) + ("\n" if lines else "")

    raise DiffError("invalid_option", f"Unsupported format: {fmt}")
