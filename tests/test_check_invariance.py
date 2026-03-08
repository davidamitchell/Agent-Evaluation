"""
Unit tests for scripts/check_invariance.py.

All tests are table-driven and cover the following cases:
  - All variants within a group have the same score (consistent)
  - Variants within a group have differing scores (inconsistent)
  - A single-variant group (always consistent by definition)
  - Empty results list (no groups, exit 0)
  - --strict mode: pass/partial treated as distinct categories
  - load_results error paths (missing file, non-array JSON, invalid JSON)

Naming convention: test_<unit>_<condition>_<expected_outcome>
"""

import json
import os
import sys
from typing import Any
from unittest.mock import patch

import pytest

import check_invariance


# ── helpers ────────────────────────────────────────────────────────────────────

def _make_record(scenario_id: str, score: str) -> dict[str, Any]:
    return {
        "scenario_id": scenario_id,
        "variant": f"prompt for {scenario_id}",
        "expected_behavior": "expected",
        "agent_response": "response",
        "score": score,
        "numeric_score": 0.8 if score == "pass" else 0.5 if score == "partial" else 0.2,
        "timestamp": "2026-03-08T00:00:00Z",
    }


# ── load_results ───────────────────────────────────────────────────────────────


class TestLoadResults:
    def test_valid_array_returns_list(self, tmp_path):
        records = [_make_record("s1", "pass")]
        p = tmp_path / "run_001.json"
        p.write_text(json.dumps(records))
        result = check_invariance.load_results(str(p))
        assert result == records

    def test_missing_file_raises_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            check_invariance.load_results(str(tmp_path / "missing.json"))

    def test_non_array_raises_value_error(self, tmp_path):
        p = tmp_path / "run_001.json"
        p.write_text('{"key": "value"}')
        with pytest.raises(ValueError, match="must be a JSON array"):
            check_invariance.load_results(str(p))

    def test_invalid_json_raises_json_decode_error(self, tmp_path):
        p = tmp_path / "run_001.json"
        p.write_text("not-json")
        with pytest.raises(json.JSONDecodeError):
            check_invariance.load_results(str(p))

    def test_empty_array_is_valid(self, tmp_path):
        p = tmp_path / "run_001.json"
        p.write_text("[]")
        assert check_invariance.load_results(str(p)) == []


# ── group_by_scenario ──────────────────────────────────────────────────────────


class TestGroupByScenario:
    def test_groups_by_scenario_id(self):
        records = [
            _make_record("s1", "pass"),
            _make_record("s1", "pass"),
            _make_record("s2", "fail"),
        ]
        groups = check_invariance.group_by_scenario(records)
        assert groups == {"s1": ["pass", "pass"], "s2": ["fail"]}

    def test_empty_records_returns_empty_dict(self):
        assert check_invariance.group_by_scenario([]) == {}


# ── is_consistent ──────────────────────────────────────────────────────────────


class TestIsConsistent:
    # Normal mode
    @pytest.mark.parametrize("scores", [
        ["pass"],
        ["partial"],
        ["fail"],
        ["pass", "pass"],
        ["fail", "fail"],
        ["partial", "partial"],
        ["pass", "partial"],          # pass+partial is consistent in normal mode
        ["partial", "pass", "pass"],  # still no fail
    ])
    def test_normal_mode_consistent(self, scores):
        assert check_invariance.is_consistent(scores, strict=False) is True

    @pytest.mark.parametrize("scores", [
        ["pass", "fail"],
        ["partial", "fail"],
        ["pass", "partial", "fail"],
        ["fail", "pass"],
    ])
    def test_normal_mode_inconsistent(self, scores):
        assert check_invariance.is_consistent(scores, strict=False) is False

    # Strict mode
    @pytest.mark.parametrize("scores", [
        ["pass"],
        ["partial"],
        ["fail"],
        ["pass", "pass"],
        ["fail", "fail"],
        ["partial", "partial"],
    ])
    def test_strict_mode_consistent(self, scores):
        assert check_invariance.is_consistent(scores, strict=True) is True

    @pytest.mark.parametrize("scores", [
        ["pass", "partial"],          # strict: mixed pass/partial is inconsistent
        ["pass", "fail"],
        ["partial", "fail"],
        ["pass", "partial", "fail"],
    ])
    def test_strict_mode_inconsistent(self, scores):
        assert check_invariance.is_consistent(scores, strict=True) is False

    def test_single_score_always_consistent_regardless_of_label(self):
        for label in ("pass", "partial", "fail"):
            assert check_invariance.is_consistent([label], strict=True) is True
            assert check_invariance.is_consistent([label], strict=False) is True


# ── check_invariance ───────────────────────────────────────────────────────────


class TestCheckInvariance:
    def test_all_consistent_returns_empty_inconsistent(self):
        records = [
            _make_record("s1", "pass"),
            _make_record("s1", "pass"),
            _make_record("s2", "fail"),
            _make_record("s2", "fail"),
        ]
        consistent, inconsistent = check_invariance.check_invariance(records)
        assert sorted(consistent) == ["s1", "s2"]
        assert inconsistent == []

    def test_inconsistent_group_reported(self):
        records = [
            _make_record("s1", "pass"),
            _make_record("s1", "fail"),  # inconsistent
            _make_record("s2", "pass"),
            _make_record("s2", "pass"),
        ]
        consistent, inconsistent = check_invariance.check_invariance(records)
        assert inconsistent == ["s1"]
        assert consistent == ["s2"]

    def test_single_variant_group_always_consistent(self):
        records = [_make_record("s1", "partial")]
        consistent, inconsistent = check_invariance.check_invariance(records)
        assert consistent == ["s1"]
        assert inconsistent == []

    def test_empty_records_returns_empty_lists(self):
        consistent, inconsistent = check_invariance.check_invariance([])
        assert consistent == []
        assert inconsistent == []

    def test_strict_pass_partial_mix_is_inconsistent(self):
        records = [
            _make_record("s1", "pass"),
            _make_record("s1", "partial"),
        ]
        consistent, inconsistent = check_invariance.check_invariance(records, strict=True)
        assert inconsistent == ["s1"]
        assert consistent == []

    def test_strict_pass_partial_mix_is_consistent_in_normal_mode(self):
        records = [
            _make_record("s1", "pass"),
            _make_record("s1", "partial"),
        ]
        consistent, inconsistent = check_invariance.check_invariance(records, strict=False)
        assert consistent == ["s1"]
        assert inconsistent == []

    def test_multiple_inconsistent_groups_all_reported(self):
        records = [
            _make_record("s1", "pass"),
            _make_record("s1", "fail"),
            _make_record("s2", "pass"),
            _make_record("s2", "fail"),
            _make_record("s3", "pass"),
            _make_record("s3", "pass"),
        ]
        consistent, inconsistent = check_invariance.check_invariance(records)
        assert inconsistent == ["s1", "s2"]
        assert consistent == ["s3"]


# ── main (CLI) ─────────────────────────────────────────────────────────────────


class TestMain:
    def _write_records(self, path, records):
        path.write_text(json.dumps(records))

    def test_main_exits_0_when_all_consistent(self, tmp_path):
        records = [
            _make_record("s1", "pass"),
            _make_record("s1", "pass"),
        ]
        p = tmp_path / "run.json"
        self._write_records(p, records)

        with patch.object(sys, "argv", ["check_invariance.py", "--results", str(p)]):
            with pytest.raises(SystemExit) as exc_info:
                check_invariance.main()
        assert exc_info.value.code == 0

    def test_main_exits_1_when_inconsistent(self, tmp_path):
        records = [
            _make_record("s1", "pass"),
            _make_record("s1", "fail"),
        ]
        p = tmp_path / "run.json"
        self._write_records(p, records)

        with patch.object(sys, "argv", ["check_invariance.py", "--results", str(p)]):
            with pytest.raises(SystemExit) as exc_info:
                check_invariance.main()
        assert exc_info.value.code == 1

    def test_main_exits_2_on_missing_file(self, tmp_path):
        with patch.object(sys, "argv", ["check_invariance.py", "--results", str(tmp_path / "nope.json")]):
            with pytest.raises(SystemExit) as exc_info:
                check_invariance.main()
        assert exc_info.value.code == 2

    def test_main_exits_0_for_empty_results(self, tmp_path):
        p = tmp_path / "run.json"
        p.write_text("[]")

        with patch.object(sys, "argv", ["check_invariance.py", "--results", str(p)]):
            with pytest.raises(SystemExit) as exc_info:
                check_invariance.main()
        assert exc_info.value.code == 0

    def test_main_strict_flag_makes_pass_partial_inconsistent(self, tmp_path):
        records = [
            _make_record("s1", "pass"),
            _make_record("s1", "partial"),
        ]
        p = tmp_path / "run.json"
        self._write_records(p, records)

        with patch.object(sys, "argv", ["check_invariance.py", "--results", str(p), "--strict"]):
            with pytest.raises(SystemExit) as exc_info:
                check_invariance.main()
        assert exc_info.value.code == 1

    def test_main_strict_flag_pass_only_is_still_consistent(self, tmp_path):
        records = [
            _make_record("s1", "pass"),
            _make_record("s1", "pass"),
        ]
        p = tmp_path / "run.json"
        self._write_records(p, records)

        with patch.object(sys, "argv", ["check_invariance.py", "--results", str(p), "--strict"]):
            with pytest.raises(SystemExit) as exc_info:
                check_invariance.main()
        assert exc_info.value.code == 0

    def test_main_prints_summary(self, tmp_path, capsys):
        records = [
            _make_record("s1", "pass"),
            _make_record("s1", "pass"),
            _make_record("s2", "pass"),
            _make_record("s2", "fail"),
        ]
        p = tmp_path / "run.json"
        self._write_records(p, records)

        with patch.object(sys, "argv", ["check_invariance.py", "--results", str(p)]):
            with pytest.raises(SystemExit):
                check_invariance.main()

        out = capsys.readouterr().out
        assert "Summary:" in out
        assert "2 group(s)" in out
        assert "1 consistent" in out
        assert "1 inconsistent" in out
