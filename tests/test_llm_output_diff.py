"""Tests for llm_output_diff fulfilling all specification requirements and acceptance criteria."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from llm_output_diff import (
    Change,
    DiffError,
    DiffReport,
    diff_json,
    diff_outputs,
    diff_text,
    format_report,
)
from llm_output_diff.__main__ import main


def test_acceptance_1_diff_json_basic() -> None:
    report = diff_json({"a": 1, "b": [1, 2]}, {"a": 2, "b": [1], "c": "x"})
    assert report.changes == (
        Change("changed", "/a", 1, 2),
        Change("removed", "/b/1", 2, None),
        Change("added", "/c", None, "x"),
    )


def test_acceptance_2_rfc6901_escaping_and_type_changed() -> None:
    report1 = diff_json({"a/b": 10, "m~n": 20}, {"a/b": 11, "m~n": 21})
    assert report1.changes == (
        Change("changed", "/a~1b", 10, 11),
        Change("changed", "/m~0n", 20, 21),
    )

    report2 = diff_json({"a": 1}, {"a": "1"})
    assert report2.changes == (Change("type_changed", "/a", 1, "1"),)

    report3 = diff_json({"a": True}, {"a": 1})
    assert report3.changes == (Change("type_changed", "/a", True, 1),)


def test_acceptance_3_numeric_tolerance() -> None:
    assert diff_json({"a": 1}, {"a": 1.0}).changes == ()
    assert diff_json({"p": 100}, {"p": 101}, rel_tol=0.01).changes == ()
    assert diff_json({"p": 100}, {"p": 101}, rel_tol=0.001).changes == (
        Change("changed", "/p", 100, 101),
    )


def test_acceptance_4_diff_text_numbers() -> None:
    a = "Revenue was 120 USD in 2025. The team grew."
    b = "Revenue was 135 USD in 2025. The team grew."
    report = diff_text(a, b)
    assert report.changes == (Change("number_changed", "s1", "120", "135"),)


def test_acceptance_5_diff_text_claims() -> None:
    r1 = diff_text("A is red. B is blue.", "A is red. C is green.")
    assert r1.changes == (
        Change("claim_removed", "s2", "B is blue.", None),
        Change("claim_added", "t2", None, "C is green."),
    )

    r2 = diff_text("The API is stable.", "The API is very stable.")
    assert r2.changes == (
        Change("claim_changed", "s1", "The API is stable.", "The API is very stable."),
    )


def test_acceptance_6_diff_outputs_fencing_and_fallback() -> None:
    r1 = diff_outputs('```json\n{"a":1}\n```', '{"a":1}')
    assert r1.mode == "json"
    assert r1.changes == ()

    r2 = diff_outputs('{"a":1}', "not json")
    assert r2.mode == "text"


def test_acceptance_literals_verbatim() -> None:
    # Verbatim checks matching acceptance criteria literals
    assert diff_outputs('```json\n{"a":1}\n```', '{"a":1}').mode == "json"
    assert diff_outputs('{"a":1}', "not json").mode == "text"
    assert (
        format_report(diff_json({"a": 1, "b": [1, 2]}, {"a": 2, "b": [1], "c": "x"}))
        == '~ /a: 1 -> 2\n- /b/1: 2\n+ /c: "x"\n'
    )


def test_acceptance_7_limits_and_errors() -> None:
    huge_text = "x" * 200_001
    with pytest.raises(DiffError) as exc_large:
        diff_text(huge_text, "hello")
    assert exc_large.value.code == "input_too_large"

    with pytest.raises(DiffError) as exc_large_out:
        diff_outputs(huge_text, "hello")
    assert exc_large_out.value.code == "input_too_large"

    # Deep nesting > 64
    deep: dict[str, object] = {}
    curr = deep
    for _ in range(66):
        curr["child"] = {}
        curr = curr["child"]  # type: ignore[assignment]

    with pytest.raises(DiffError) as exc_deep:
        diff_json(deep, deep, max_depth=64)
    assert exc_deep.value.code == "too_deep"

    # Max changes truncation
    a_dict = {f"k{i}": i for i in range(1500)}
    b_dict = {f"k{i}": i + 1 for i in range(1500)}
    rep = diff_json(a_dict, b_dict, max_changes=1000)
    assert len(rep.changes) == 1000
    assert rep.truncated is True


def test_acceptance_8_format_report_and_cli(tmp_path: Path) -> None:
    rep = diff_json({"a": 1, "b": [1, 2]}, {"a": 2, "b": [1], "c": "x"})
    formatted = format_report(rep)
    assert formatted == '~ /a: 1 -> 2\n- /b/1: 2\n+ /c: "x"\n'

    dir_path = tmp_path / "cli_test"
    dir_path.mkdir()
    f_a = dir_path / "a.json"
    f_b = dir_path / "b.json"
    f_same = dir_path / "same.json"

    f_a.write_text('{"a": 1}', encoding="utf-8")
    f_b.write_text('{"a": 2}', encoding="utf-8")
    f_same.write_text('{"a": 1}', encoding="utf-8")

    # Diff exists -> 1
    assert main([str(f_a), str(f_b)]) == 1
    # No diff -> 0
    assert main([str(f_a), str(f_same)]) == 0
    # Missing file -> 2
    assert main([str(f_a), str(dir_path / "missing.json")]) == 2


def test_sorting_array_indices_numerically() -> None:
    a = {"b": [0] * 12}
    b = {"b": [0] * 12}
    a["b"][2] = 10
    b["b"][2] = 20
    a["b"][10] = 30
    b["b"][10] = 40

    rep = diff_json(a, b)
    assert [c.path for c in rep.changes] == ["/b/2", "/b/10"]


def test_invalid_options() -> None:
    with pytest.raises(DiffError) as exc_tol:
        diff_json({}, {}, rel_tol=-0.1)
    assert exc_tol.value.code == "invalid_option"

    with pytest.raises(DiffError) as exc_mc:
        diff_json({}, {}, max_changes=-1)
    assert exc_mc.value.code == "invalid_option"

    with pytest.raises(DiffError) as exc_md:
        diff_json({}, {}, max_depth=-1)
    assert exc_md.value.code == "invalid_option"

    with pytest.raises(DiffError) as exc_sim:
        diff_text("a", "b", similarity=0.0)
    assert exc_sim.value.code == "invalid_option"

    with pytest.raises(DiffError) as exc_sim2:
        diff_text("a", "b", similarity=1.1)
    assert exc_sim2.value.code == "invalid_option"

    with pytest.raises(DiffError) as exc_fmt:
        format_report(DiffReport("json", (), False), fmt="html")  # type: ignore[arg-type]
    assert exc_fmt.value.code == "invalid_option"


def test_json_nan_infinity_fallback() -> None:
    # NaN should be rejected by strict loads and fall back to text mode
    r = diff_outputs('{"val": NaN}', '{"val": 1}')
    assert r.mode == "text"


def test_format_json_and_truncated() -> None:
    rep = DiffReport(
        mode="text",
        changes=(
            Change("claim_changed", "s1", "Old text", "New text"),
            Change("claim_added", "t2", None, "Added"),
            Change("claim_removed", "s2", "Removed", None),
        ),
        truncated=True,
    )
    text_out = format_report(rep, fmt="text")
    assert '~ s1: "Old text" -> "New text"' in text_out
    assert '+ t2: "Added"' in text_out
    assert '- s2: "Removed"' in text_out
    assert "... truncated" in text_out

    json_out = format_report(rep, fmt="json")
    parsed = json.loads(json_out)
    assert parsed["mode"] == "text"
    assert parsed["truncated"] is True
    assert len(parsed["changes"]) == 3


def test_cli_options_and_json_format(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    dir_path = tmp_path / "cli_json_test"
    dir_path.mkdir()
    f_a = dir_path / "a.txt"
    f_b = dir_path / "b.txt"
    f_a.write_text("Price is 100.", encoding="utf-8")
    f_b.write_text("Price is 101.", encoding="utf-8")

    exit_code = main([str(f_a), str(f_b), "--format", "json", "--rel-tol", "0.01"])
    captured = capsys.readouterr()
    assert exit_code == 1
    parsed = json.loads(captured.out)
    assert parsed["mode"] == "text"
    assert parsed["changes"][0]["kind"] == "number_changed"


def test_cli_domain_diff_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    dir_path = tmp_path / "cli_err_test"
    dir_path.mkdir()
    f_a = dir_path / "a.txt"
    f_b = dir_path / "b.txt"
    f_a.write_text("Hello", encoding="utf-8")
    f_b.write_text("Hello", encoding="utf-8")

    # Invalid similarity causes domain failure (DiffError)
    exit_code = main([str(f_a), str(f_b), "--similarity", "0.0"])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Diff error [invalid_option]" in captured.err
