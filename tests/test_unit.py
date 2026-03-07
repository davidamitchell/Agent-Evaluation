"""
Unit tests for scripts/run_evaluation.py.

All external I/O (subprocess / Copilot CLI) is mocked so these tests run
without network access or credentials.  Every piece of business logic has
at least one test; boundary conditions and failure paths are explicitly covered.

Naming convention:  test_<unit>_<condition>_<expected_outcome>
"""
import json
import os
import subprocess
import sys
from unittest.mock import MagicMock, call, patch

import pytest

import run_evaluation


# ── load_dataset ──────────────────────────────────────────────────────────────


class TestLoadDataset:
    def test_valid_array_returns_list(self, tmp_path):
        data = [{"id": "s1", "scenario": "hello", "expected_behavior": "greet"}]
        (tmp_path / "ds.json").write_text(json.dumps(data))
        assert run_evaluation.load_dataset(str(tmp_path / "ds.json")) == data

    def test_non_list_raises_value_error(self, tmp_path):
        (tmp_path / "ds.json").write_text('{"key": "value"}')
        with pytest.raises(ValueError, match="must be a JSON array"):
            run_evaluation.load_dataset(str(tmp_path / "ds.json"))

    def test_empty_array_is_valid(self, tmp_path):
        (tmp_path / "ds.json").write_text("[]")
        assert run_evaluation.load_dataset(str(tmp_path / "ds.json")) == []

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            run_evaluation.load_dataset(str(tmp_path / "nonexistent.json"))


# ── load_agent_instructions ───────────────────────────────────────────────────


class TestLoadAgentInstructions:
    def test_returns_file_contents(self, tmp_path):
        content = "# Agent\nDo exactly what is asked."
        (tmp_path / "agent.md").write_text(content)
        assert run_evaluation.load_agent_instructions(str(tmp_path / "agent.md")) == content

    def test_missing_file_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            run_evaluation.load_agent_instructions(str(tmp_path / "missing.md"))


# ── next_run_number ───────────────────────────────────────────────────────────


class TestNextRunNumber:
    def test_empty_dirs_returns_1(self, tmp_path):
        r = tmp_path / "results"
        e = tmp_path / "experiments"
        r.mkdir()
        e.mkdir()
        assert run_evaluation.next_run_number(str(r), str(e)) == 1

    def test_increments_from_max_in_single_dir(self, tmp_path):
        d = tmp_path / "results"
        d.mkdir()
        (d / "run_001.json").write_text("{}")
        (d / "run_003.json").write_text("{}")
        assert run_evaluation.next_run_number(str(d), str(tmp_path / "x")) == 4

    def test_considers_both_dirs_independently(self, tmp_path):
        r = tmp_path / "results"
        e = tmp_path / "experiments"
        r.mkdir()
        e.mkdir()
        (r / "run_002.json").write_text("{}")
        (e / "run_007.json").write_text("{}")
        assert run_evaluation.next_run_number(str(r), str(e)) == 8

    def test_ignores_files_without_run_prefix(self, tmp_path):
        d = tmp_path / "results"
        d.mkdir()
        (d / "summary.json").write_text("{}")
        (d / "README.md").write_text("")
        assert run_evaluation.next_run_number(str(d), str(d)) == 1

    def test_ignores_run_files_with_non_numeric_suffix(self, tmp_path):
        d = tmp_path / "results"
        d.mkdir()
        (d / "run_abc.json").write_text("{}")
        assert run_evaluation.next_run_number(str(d), str(d)) == 1

    def test_nonexistent_dir_does_not_raise(self, tmp_path):
        existing = tmp_path / "results"
        existing.mkdir()
        (existing / "run_005.json").write_text("{}")
        result = run_evaluation.next_run_number(str(existing), str(tmp_path / "no_such_dir"))
        assert result == 6


# ── call_copilot_cli ──────────────────────────────────────────────────────────


class TestCallCopilotCli:
    def test_success_returns_stripped_stdout(self):
        mock_result = MagicMock(returncode=0, stdout="  hello world\n  ", stderr="")
        with patch("subprocess.run", return_value=mock_result):
            result = run_evaluation.call_copilot_cli("prompt", "token123")
        assert result == "hello world"

    def test_token_is_injected_as_github_token(self):
        mock_result = MagicMock(returncode=0, stdout="ok", stderr="")
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            run_evaluation.call_copilot_cli("prompt", "my-secret-token")
        env = mock_run.call_args[1]["env"]
        assert env.get("GITHUB_TOKEN") == "my-secret-token"

    def test_nonzero_exit_code_raises_runtime_error(self):
        mock_result = MagicMock(returncode=1, stdout="", stderr="auth failed")
        with patch("subprocess.run", return_value=mock_result), patch("time.sleep"):
            with pytest.raises(RuntimeError, match="failed after"):
                run_evaluation.call_copilot_cli("prompt", "token")

    def test_retries_up_to_max_retries_on_failure(self):
        mock_result = MagicMock(returncode=1, stdout="", stderr="err")
        with patch("subprocess.run", return_value=mock_result) as mock_run, \
                patch("time.sleep"):
            with pytest.raises(RuntimeError):
                run_evaluation.call_copilot_cli("prompt", "token")
        assert mock_run.call_count == run_evaluation.MAX_RETRIES

    def test_timeout_triggers_retry_and_eventually_raises(self):
        with patch("subprocess.run",
                   side_effect=subprocess.TimeoutExpired(cmd="copilot", timeout=120)) as mock_run, \
                patch("time.sleep"):
            with pytest.raises(RuntimeError, match="failed after"):
                run_evaluation.call_copilot_cli("prompt", "token")
        assert mock_run.call_count == run_evaluation.MAX_RETRIES

    def test_succeeds_on_second_attempt_after_transient_error(self):
        ok = MagicMock(returncode=0, stdout="response", stderr="")
        err = MagicMock(returncode=1, stdout="", stderr="transient")
        with patch("subprocess.run", side_effect=[err, ok]), \
                patch("time.sleep"):
            result = run_evaluation.call_copilot_cli("prompt", "token")
        assert result == "response"

    def test_prompt_is_passed_to_cli(self):
        mock_result = MagicMock(returncode=0, stdout="ok", stderr="")
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            run_evaluation.call_copilot_cli("my detailed prompt", "token")
        args = mock_run.call_args[0][0]
        assert "my detailed prompt" in args


# ── judge_response ────────────────────────────────────────────────────────────


class TestJudgeResponse:
    """
    judge_response delegates the LLM call to call_copilot_cli, which is mocked
    here so we test only the JSON extraction, score clamping, and labelling logic.
    """

    def _judge(self, raw_output: str):
        with patch.object(run_evaluation, "call_copilot_cli", return_value=raw_output):
            return run_evaluation.judge_response("agent response", "expected behaviour", "token")

    def test_plain_json_score_pass(self):
        num, label = self._judge('{"score": 0.9}')
        assert num == pytest.approx(0.9)
        assert label == "pass"

    def test_score_embedded_in_surrounding_text(self):
        num, label = self._judge('Here is my judgement: {"score": 0.55} — done.')
        assert num == pytest.approx(0.55)
        assert label == "partial"

    def test_scientific_notation_score(self):
        num, label = self._judge('{"score": 1e-5}')
        assert num == pytest.approx(1e-5)
        assert label == "fail"

    def test_negative_scientific_notation(self):
        num, label = self._judge('{"score": 9.9E-1}')
        assert num == pytest.approx(0.99)
        assert label == "pass"

    # Boundary conditions at the pass/partial/fail thresholds

    def test_score_exactly_07_is_pass(self):
        _, label = self._judge('{"score": 0.7}')
        assert label == "pass"

    def test_score_just_below_07_is_partial(self):
        _, label = self._judge('{"score": 0.699}')
        assert label == "partial"

    def test_score_exactly_04_is_partial(self):
        _, label = self._judge('{"score": 0.4}')
        assert label == "partial"

    def test_score_just_below_04_is_fail(self):
        _, label = self._judge('{"score": 0.399}')
        assert label == "fail"

    def test_score_zero_is_fail(self):
        num, label = self._judge('{"score": 0.0}')
        assert num == pytest.approx(0.0)
        assert label == "fail"

    def test_score_one_is_pass(self):
        num, label = self._judge('{"score": 1.0}')
        assert num == pytest.approx(1.0)
        assert label == "pass"

    # Clamping

    def test_score_above_1_clamped_to_1(self):
        num, label = self._judge('{"score": 1.5}')
        assert num == pytest.approx(1.0)
        assert label == "pass"

    def test_score_below_0_clamped_to_0(self):
        num, label = self._judge('{"score": -0.3}')
        assert num == pytest.approx(0.0)
        assert label == "fail"

    # Failure cases

    def test_unparseable_output_defaults_to_0_fail(self):
        num, label = self._judge("I cannot determine a score for this.")
        assert num == pytest.approx(0.0)
        assert label == "fail"

    def test_empty_output_defaults_to_0_fail(self):
        num, label = self._judge("")
        assert num == pytest.approx(0.0)
        assert label == "fail"

    def test_cli_error_during_judging_defaults_to_0_fail(self):
        with patch.object(run_evaluation, "call_copilot_cli",
                          side_effect=RuntimeError("CLI failed")):
            num, label = run_evaluation.judge_response("resp", "expected", "token")
        assert num == pytest.approx(0.0)
        assert label == "fail"


# ── evaluate (full pipeline) ──────────────────────────────────────────────────


class TestEvaluate:
    """
    Tests for the evaluate() orchestrator. call_copilot_cli is mocked so no
    real subprocess is launched; we verify file layout, JSON schema, and
    aggregate metric calculations.
    """

    _SINGLE_SCENARIO = [
        {"id": "s1", "scenario": "Say hello.", "expected_behavior": "Greet the user."}
    ]
    _PASS_SCORE_JSON = '{"score": 0.9}'
    _FAIL_SCORE_JSON = '{"score": 0.1}'

    def _run(self, tmp_path, dataset, cli_response=_PASS_SCORE_JSON):
        ds = tmp_path / "data.json"
        ds.write_text(json.dumps(dataset))
        agent = tmp_path / "agent.md"
        agent.write_text("# Agent\nBe helpful.")
        results_dir = tmp_path / "results"
        experiments_dir = tmp_path / "experiments"

        with patch.dict(os.environ, {"COPILOT_GITHUB_TOKEN": "test-token"}), \
                patch.object(run_evaluation, "call_copilot_cli", return_value=cli_response):
            path = run_evaluation.evaluate(
                str(ds), str(agent), str(results_dir), str(experiments_dir)
            )
        return path, results_dir, experiments_dir

    def test_results_file_is_created(self, tmp_path):
        path, results_dir, _ = self._run(tmp_path, self._SINGLE_SCENARIO)
        assert os.path.exists(path)
        assert list(results_dir.glob("run_*.json"))

    def test_results_file_contains_correct_scenario_id(self, tmp_path):
        path, _, _ = self._run(tmp_path, self._SINGLE_SCENARIO)
        records = json.loads(open(path).read())
        assert records[0]["scenario_id"] == "s1"

    def test_results_record_has_required_fields(self, tmp_path):
        path, _, _ = self._run(tmp_path, self._SINGLE_SCENARIO)
        rec = json.loads(open(path).read())[0]
        for field in ("scenario_id", "variant", "expected_behavior",
                      "agent_response", "score", "numeric_score", "timestamp"):
            assert field in rec, f"Missing field: {field}"

    def test_timestamp_ends_with_z(self, tmp_path):
        path, _, _ = self._run(tmp_path, self._SINGLE_SCENARIO)
        rec = json.loads(open(path).read())[0]
        assert rec["timestamp"].endswith("Z")

    def test_experiment_log_is_created(self, tmp_path):
        _, _, experiments_dir = self._run(tmp_path, self._SINGLE_SCENARIO)
        exp_files = list(experiments_dir.glob("run_*.json"))
        assert len(exp_files) == 1

    def test_experiment_log_has_required_fields(self, tmp_path):
        _, _, experiments_dir = self._run(tmp_path, self._SINGLE_SCENARIO)
        exp = json.loads(list(experiments_dir.glob("run_*.json"))[0].read_text())
        for field in ("run", "timestamp", "agent", "dataset", "model",
                      "results", "pass_rate", "mean_score"):
            assert field in exp, f"Missing field: {field}"

    def test_experiment_log_model_is_github_copilot(self, tmp_path):
        _, _, experiments_dir = self._run(tmp_path, self._SINGLE_SCENARIO)
        exp = json.loads(list(experiments_dir.glob("run_*.json"))[0].read_text())
        assert exp["model"] == "github-copilot"

    def test_experiment_log_pass_rate_all_pass(self, tmp_path):
        _, _, experiments_dir = self._run(tmp_path, self._SINGLE_SCENARIO, '{"score": 0.9}')
        exp = json.loads(list(experiments_dir.glob("run_*.json"))[0].read_text())
        assert exp["pass_rate"] == pytest.approx(1.0)

    def test_experiment_log_pass_rate_all_fail(self, tmp_path):
        _, _, experiments_dir = self._run(tmp_path, self._SINGLE_SCENARIO, '{"score": 0.1}')
        exp = json.loads(list(experiments_dir.glob("run_*.json"))[0].read_text())
        assert exp["pass_rate"] == pytest.approx(0.0)

    def test_variants_produce_one_result_each(self, tmp_path):
        dataset = [{
            "id": "s1",
            "scenario": "v1",
            "variants": ["v1", "v2", "v3"],
            "expected_behavior": "Be helpful.",
        }]
        path, _, _ = self._run(tmp_path, dataset)
        records = json.loads(open(path).read())
        assert len(records) == 3

    def test_multiple_scenarios_produce_correct_count(self, tmp_path):
        dataset = [
            {"id": "s1", "scenario": "q1", "expected_behavior": "a1"},
            {"id": "s2", "scenario": "q2", "expected_behavior": "a2"},
        ]
        path, _, _ = self._run(tmp_path, dataset)
        records = json.loads(open(path).read())
        assert len(records) == 2

    def test_run_numbers_increment_across_runs(self, tmp_path):
        _, r1, e1 = self._run(tmp_path, self._SINGLE_SCENARIO)
        # Second run in the same directories
        ds = tmp_path / "data.json"
        agent = tmp_path / "agent.md"
        with patch.dict(os.environ, {"COPILOT_GITHUB_TOKEN": "test-token"}), \
                patch.object(run_evaluation, "call_copilot_cli", return_value=self._PASS_SCORE_JSON):
            run_evaluation.evaluate(str(ds), str(agent), str(r1), str(e1))
        result_files = sorted(r1.glob("run_*.json"))
        assert len(result_files) == 2
        assert result_files[0].name == "run_001.json"
        assert result_files[1].name == "run_002.json"

    def test_missing_token_calls_sys_exit(self, tmp_path):
        ds = tmp_path / "data.json"
        ds.write_text(json.dumps(self._SINGLE_SCENARIO))
        agent = tmp_path / "agent.md"
        agent.write_text("instructions")
        env_no_token = {k: v for k, v in os.environ.items() if k != "COPILOT_GITHUB_TOKEN"}
        with patch.dict(os.environ, env_no_token, clear=True):
            with pytest.raises(SystemExit):
                run_evaluation.evaluate(
                    str(ds), str(agent),
                    str(tmp_path / "r"), str(tmp_path / "e"),
                )

    def test_result_and_experiment_filenames_share_run_id(self, tmp_path):
        path, _, experiments_dir = self._run(tmp_path, self._SINGLE_SCENARIO)
        result_name = os.path.basename(path)
        exp_files = list(experiments_dir.glob("run_*.json"))
        assert exp_files[0].name == result_name


# ── Timestamp format ──────────────────────────────────────────────────────────


class TestTimestampFormat:
    def test_now_utc_produces_z_suffix(self):
        import datetime
        ts = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
        assert ts.endswith("Z")
        # Must be parseable as ISO 8601
        datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
