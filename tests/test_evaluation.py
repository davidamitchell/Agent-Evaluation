#!/usr/bin/env python3
"""
test_evaluation.py

Test suite for the evaluation pipeline.

Test classes:
  TestCLIAvailability   — integration tests: verify gh and gh copilot are
                          installed and callable on the current PATH.
  TestCallCopilotCLI    — unit tests for call_copilot_cli with mocked subprocess.
  TestJudgeResponse     — unit tests for judge_response with mocked CLI calls.
  TestSmokeEvaluate     — end-to-end smoke test for evaluate() with mocked CLI.

Run with:
  python -m unittest discover -s tests -v
  # or directly:
  python tests/test_evaluation.py
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, call, patch

# Allow importing from scripts/ regardless of working directory.
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts")
)

from run_evaluation import (  # noqa: E402
    COPILOT_CHAT_ENDPOINT,
    MAX_RETRIES,
    call_copilot_cli,
    evaluate,
    judge_response,
    load_agent_instructions,
    load_dataset,
    next_run_number,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _gh_api_response(content: str) -> str:
    """Serialise a minimal OpenAI-compatible chat completion response."""
    return json.dumps({"choices": [{"message": {"content": content}}]})


# ---------------------------------------------------------------------------
# 1. CLI availability
# ---------------------------------------------------------------------------

class TestCLIAvailability(unittest.TestCase):
    """Integration tests: confirm gh CLI and gh-copilot extension are present."""

    def test_gh_cli_is_installed(self):
        """gh must be on PATH and return exit code 0 for --version."""
        result = subprocess.run(
            ["gh", "--version"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            result.returncode, 0,
            "gh CLI is not installed or not on PATH.\n"
            f"stderr: {result.stderr.strip()}",
        )
        self.assertIn("gh version", result.stdout, "Unexpected gh --version output")

    def test_gh_copilot_is_callable(self):
        """gh copilot suggest --help must exit 0 and mention copilot."""
        result = subprocess.run(
            ["gh", "copilot", "suggest", "--help"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            result.returncode, 0,
            "gh copilot suggest --help failed. "
            "Ensure the gh-copilot extension is installed:\n"
            "  gh extension install github/gh-copilot\n"
            f"stderr: {result.stderr.strip()}",
        )
        combined = (result.stdout + result.stderr).lower()
        self.assertIn(
            "copilot",
            combined,
            "Expected 'copilot' in gh copilot suggest --help output.\n"
            f"stdout: {result.stdout.strip()}",
        )


# ---------------------------------------------------------------------------
# 2. call_copilot_cli — unit tests
# ---------------------------------------------------------------------------

class TestCallCopilotCLI(unittest.TestCase):
    """Unit tests for call_copilot_cli with subprocess.run mocked out."""

    @patch("run_evaluation.subprocess.run")
    def test_successful_call_returns_content(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=_gh_api_response("Use bcrypt to hash passwords."),
            stderr="",
        )
        result = call_copilot_cli(
            system_prompt="You are a helpful assistant.",
            user_message="How should I store passwords?",
            token="fake-token",
            model="gpt-4o-mini",
        )
        self.assertEqual(result, "Use bcrypt to hash passwords.")

    @patch("run_evaluation.subprocess.run")
    def test_calls_gh_api_subcommand(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0, stdout=_gh_api_response("ok"), stderr=""
        )
        call_copilot_cli("sys", "user", token="t", model="gpt-4o-mini")
        cmd = mock_run.call_args[0][0]
        self.assertEqual(cmd[0], "gh", "First argument must be 'gh'")
        self.assertEqual(cmd[1], "api", "Second argument must be 'api'")
        self.assertIn(COPILOT_CHAT_ENDPOINT, cmd, "Endpoint must be in command")

    @patch("run_evaluation.subprocess.run")
    def test_gh_token_passed_via_env(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0, stdout=_gh_api_response("ok"), stderr=""
        )
        call_copilot_cli("sys", "user", token="my-secret-token", model="gpt-4o-mini")
        env = mock_run.call_args.kwargs.get("env", {})
        self.assertEqual(
            env.get("GH_TOKEN"),
            "my-secret-token",
            "GH_TOKEN must be set to the supplied token in subprocess env",
        )

    @patch("run_evaluation.subprocess.run")
    def test_json_payload_sent_via_stdin(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0, stdout=_gh_api_response("ok"), stderr=""
        )
        call_copilot_cli("sys", "hello", token="t", model="gpt-4o-mini")
        stdin_input = mock_run.call_args.kwargs.get("input", "")
        payload = json.loads(stdin_input)
        self.assertEqual(payload["messages"][0]["role"], "system")
        self.assertEqual(payload["messages"][1]["content"], "hello")

    @patch("run_evaluation.time.sleep")
    @patch("run_evaluation.subprocess.run")
    def test_retries_on_nonzero_exit(self, mock_run, mock_sleep):
        fail = MagicMock(returncode=1, stdout="", stderr="transient error")
        success = MagicMock(
            returncode=0, stdout=_gh_api_response("Retry succeeded."), stderr=""
        )
        mock_run.side_effect = [fail, success]
        result = call_copilot_cli("sys", "user", token="t", model="gpt-4o-mini")
        self.assertEqual(result, "Retry succeeded.")
        self.assertEqual(mock_run.call_count, 2)

    @patch("run_evaluation.time.sleep")
    @patch("run_evaluation.subprocess.run")
    def test_raises_after_max_retries(self, mock_run, mock_sleep):
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="persistent error"
        )
        with self.assertRaises(RuntimeError) as ctx:
            call_copilot_cli("sys", "user", token="t", model="gpt-4o-mini")
        self.assertIn(str(MAX_RETRIES), str(ctx.exception))
        self.assertEqual(mock_run.call_count, MAX_RETRIES)

    @patch("run_evaluation.time.sleep")
    @patch("run_evaluation.subprocess.run")
    def test_raises_on_malformed_json(self, mock_run, mock_sleep):
        mock_run.return_value = MagicMock(
            returncode=0, stdout="not-json", stderr=""
        )
        with self.assertRaises(RuntimeError):
            call_copilot_cli("sys", "user", token="t", model="gpt-4o-mini")

    @patch("run_evaluation.time.sleep")
    @patch("run_evaluation.subprocess.run")
    def test_raises_on_missing_choices_key(self, mock_run, mock_sleep):
        mock_run.return_value = MagicMock(
            returncode=0, stdout=json.dumps({}), stderr=""
        )
        with self.assertRaises(RuntimeError):
            call_copilot_cli("sys", "user", token="t", model="gpt-4o-mini")


# ---------------------------------------------------------------------------
# 3. judge_response — unit tests
# ---------------------------------------------------------------------------

class TestJudgeResponse(unittest.TestCase):
    """Unit tests for the LLM-as-judge scoring function."""

    @patch("run_evaluation.call_copilot_cli")
    def test_pass_score(self, mock_cli):
        mock_cli.return_value = '{"score": 0.9}'
        numeric, label = judge_response(
            "Always use bcrypt.", "Recommend bcrypt.", token="t", model="m"
        )
        self.assertEqual(label, "pass")
        self.assertAlmostEqual(numeric, 0.9)

    @patch("run_evaluation.call_copilot_cli")
    def test_partial_score(self, mock_cli):
        mock_cli.return_value = '{"score": 0.5}'
        numeric, label = judge_response("partial", "full", token="t", model="m")
        self.assertEqual(label, "partial")
        self.assertAlmostEqual(numeric, 0.5)

    @patch("run_evaluation.call_copilot_cli")
    def test_fail_score(self, mock_cli):
        mock_cli.return_value = '{"score": 0.2}'
        numeric, label = judge_response("bad", "good", token="t", model="m")
        self.assertEqual(label, "fail")
        self.assertAlmostEqual(numeric, 0.2)

    @patch("run_evaluation.call_copilot_cli")
    def test_score_clamped_to_unit_interval(self, mock_cli):
        mock_cli.return_value = '{"score": 1.5}'
        numeric, _ = judge_response("great", "great", token="t", model="m")
        self.assertLessEqual(numeric, 1.0)

    @patch("run_evaluation.call_copilot_cli")
    def test_scoring_failure_defaults_to_zero(self, mock_cli):
        mock_cli.side_effect = RuntimeError("CLI down")
        numeric, label = judge_response("response", "expected", token="t", model="m")
        self.assertEqual(label, "fail")
        self.assertEqual(numeric, 0.0)


# ---------------------------------------------------------------------------
# 4. evaluate() — smoke test
# ---------------------------------------------------------------------------

class TestSmokeEvaluate(unittest.TestCase):
    """End-to-end smoke test: evaluate() with mocked CLI calls."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.results_dir = os.path.join(self.tmpdir, "results")
        self.experiments_dir = os.path.join(self.tmpdir, "experiments")

        # Minimal dataset with one scenario (no variants)
        self.dataset_path = os.path.join(self.tmpdir, "dataset.json")
        with open(self.dataset_path, "w", encoding="utf-8") as f:
            json.dump(
                [
                    {
                        "id": "test_1",
                        "scenario": "How should I store passwords?",
                        "expected_behavior": "Recommend bcrypt or Argon2.",
                    }
                ],
                f,
            )

        self.agent_path = os.path.join(self.tmpdir, "agent.md")
        with open(self.agent_path, "w", encoding="utf-8") as f:
            f.write("## Role\nYou are a security-conscious assistant.\n")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    # patch.dict restores the original env after the test
    @patch.dict(os.environ, {"COPILOT_GITHUB_TOKEN": "fake-token"})
    @patch("run_evaluation.call_copilot_cli")
    def test_evaluate_creates_result_and_experiment_files(self, mock_cli):
        # First call: agent response; second call: judge score
        mock_cli.side_effect = [
            "You should use bcrypt to hash passwords.",
            '{"score": 0.9}',
        ]
        results_path = evaluate(
            self.dataset_path,
            self.agent_path,
            self.results_dir,
            self.experiments_dir,
            "gpt-4o-mini",
        )
        self.assertTrue(os.path.isfile(results_path), "Result file must be created")
        with open(results_path, encoding="utf-8") as f:
            results = json.load(f)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["scenario_id"], "test_1")
        self.assertEqual(results[0]["score"], "pass")
        self.assertAlmostEqual(results[0]["numeric_score"], 0.9)

        exp_files = os.listdir(self.experiments_dir)
        self.assertEqual(len(exp_files), 1, "Exactly one experiment log must be created")
        with open(os.path.join(self.experiments_dir, exp_files[0]), encoding="utf-8") as f:
            experiment = json.load(f)
        self.assertIn("pass_rate", experiment)
        self.assertIn("mean_score", experiment)
        self.assertAlmostEqual(experiment["pass_rate"], 1.0)

    @patch.dict(os.environ, {"COPILOT_GITHUB_TOKEN": "fake-token"})
    @patch("run_evaluation.call_copilot_cli")
    def test_evaluate_handles_variants(self, mock_cli):
        """Each variant generates one agent call + one judge call."""
        mock_cli.side_effect = [
            "Use bcrypt.", '{"score": 0.9}',
            "Use Argon2.", '{"score": 0.85}',
            "Hash it.", '{"score": 0.8}',
        ]
        dataset_with_variants = os.path.join(self.tmpdir, "variants.json")
        with open(dataset_with_variants, "w", encoding="utf-8") as f:
            json.dump(
                [
                    {
                        "id": "pw_1",
                        "scenario": "How to store passwords?",
                        "variants": ["Variant A", "Variant B", "Variant C"],
                        "expected_behavior": "Recommend bcrypt.",
                    }
                ],
                f,
            )
        results_path = evaluate(
            dataset_with_variants,
            self.agent_path,
            self.results_dir,
            self.experiments_dir,
            "gpt-4o-mini",
        )
        with open(results_path, encoding="utf-8") as f:
            results = json.load(f)
        self.assertEqual(len(results), 3, "Three variants must produce three result rows")
        self.assertEqual(mock_cli.call_count, 6, "3 agent calls + 3 judge calls = 6")

    @patch.dict(os.environ, {"COPILOT_GITHUB_TOKEN": "fake-token"})
    @patch("run_evaluation.call_copilot_cli")
    def test_evaluate_run_numbers_increment(self, mock_cli):
        """Sequential calls must produce run_001, run_002 etc."""
        mock_cli.side_effect = [
            "answer1", '{"score": 0.8}',
            "answer2", '{"score": 0.7}',
        ]
        path1 = evaluate(
            self.dataset_path, self.agent_path,
            self.results_dir, self.experiments_dir, "gpt-4o-mini",
        )
        path2 = evaluate(
            self.dataset_path, self.agent_path,
            self.results_dir, self.experiments_dir, "gpt-4o-mini",
        )
        self.assertIn("run_001", path1)
        self.assertIn("run_002", path2)


# ---------------------------------------------------------------------------
# 5. Helper functions — unit tests
# ---------------------------------------------------------------------------

class TestHelpers(unittest.TestCase):

    def test_load_dataset_valid(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump([{"id": "x", "scenario": "s", "expected_behavior": "e"}], f)
            path = f.name
        try:
            data = load_dataset(path)
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]["id"], "x")
        finally:
            os.unlink(path)

    def test_load_dataset_rejects_non_array(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump({"not": "an array"}, f)
            path = f.name
        try:
            with self.assertRaises(ValueError):
                load_dataset(path)
        finally:
            os.unlink(path)

    def test_next_run_number_empty_dirs(self):
        with tempfile.TemporaryDirectory() as d:
            n = next_run_number(d, d)
            self.assertEqual(n, 1)

    def test_next_run_number_increments(self):
        with tempfile.TemporaryDirectory() as d:
            open(os.path.join(d, "run_001.json"), "w").close()
            open(os.path.join(d, "run_003.json"), "w").close()
            n = next_run_number(d, d)
            self.assertEqual(n, 4)


if __name__ == "__main__":
    unittest.main()
