"""
Integration tests for the evaluation pipeline.

These tests make real network calls to the GitHub Copilot CLI.  They are
decorated with @pytest.mark.integration and skip automatically when
COPILOT_GITHUB_TOKEN is not set, so they never block a developer working
offline or a fork with no access to the secret.

In CI the secret is provided, making these tests mandatory gate-keepers:
a config change that wires up an external service is not done until the
corresponding integration test exists AND passes here.

Run manually (credentials required):
    COPILOT_GITHUB_TOKEN=<token> pytest tests/test_integration.py -m integration -v
"""
import json
import os
import subprocess

import pytest

import run_evaluation

COPILOT_TOKEN = os.getenv("COPILOT_GITHUB_TOKEN")

_SKIP_REASON = (
    "COPILOT_GITHUB_TOKEN is not set — integration tests require live credentials. "
    "This is a blocker in CI; see .github/copilot-instructions.md § Testing standards."
)


@pytest.mark.integration
@pytest.mark.skipif(not COPILOT_TOKEN, reason=_SKIP_REASON)
class TestCopilotCliConnectivity:
    """Prove the GitHub Copilot CLI is installed, reachable, and authenticated."""

    def test_copilot_cli_is_on_path(self):
        """The npm-installed @github/copilot binary must be discoverable."""
        result = subprocess.run(
            ["copilot", "--version"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        # Some CLI builds exit non-zero for --version; accept any output that
        # mentions the word "copilot" or returns 0.
        output = (result.stdout + result.stderr).lower()
        assert result.returncode == 0 or "copilot" in output

    def test_cli_returns_non_empty_response_for_simple_prompt(self):
        """A trivial prompt must produce a non-empty response — proves auth works."""
        response = run_evaluation.call_copilot_cli(
            "Reply with only the single word HELLO and nothing else.",
            COPILOT_TOKEN,
        )
        assert len(response.strip()) > 0

    def test_judge_response_scores_obvious_pass(self):
        """
        A response that perfectly matches the expected behaviour must score
        pass or partial — proves the judge prompt round-trip works end-to-end.
        """
        numeric, label = run_evaluation.judge_response(
            response="The sky is blue.",
            expected_behavior="State that the sky is blue.",
            token=COPILOT_TOKEN,
        )
        assert label in ("pass", "partial"), (
            f"Expected pass/partial for an obvious match, got {label!r} ({numeric:.3f})"
        )
        assert 0.0 <= numeric <= 1.0

    def test_judge_response_scores_obvious_fail(self):
        """
        A response that is completely off-topic must score fail or partial —
        proves the judge can distinguish a bad response from a good one.
        """
        numeric, label = run_evaluation.judge_response(
            response="The answer is 42.",
            expected_behavior="Apologise for not being able to help and suggest contacting support.",
            token=COPILOT_TOKEN,
        )
        assert label in ("fail", "partial"), (
            f"Expected fail/partial for an irrelevant response, got {label!r} ({numeric:.3f})"
        )


@pytest.mark.integration
@pytest.mark.skipif(not COPILOT_TOKEN, reason=_SKIP_REASON)
class TestEvaluatePipelineEndToEnd:
    """
    Lightweight full-pipeline E2E: one scenario, real CLI calls, real filesystem writes.
    Proves the evaluate() orchestrator works with live external services.
    """

    _MINIMAL_DATASET = [
        {
            "id": "integration_hello",
            "scenario": "Greet the user warmly.",
            "expected_behavior": "The agent greets the user in a friendly manner.",
        }
    ]

    _MINIMAL_AGENT = (
        "## Role\n"
        "You are a friendly assistant.\n\n"
        "## Behavioural Expectations\n"
        "1. Always greet the user warmly.\n\n"
        "## Evaluation Context\n"
        "Used in integration tests to verify the evaluation pipeline."
    )

    def test_evaluate_creates_results_file(self, tmp_path):
        ds = tmp_path / "data.json"
        ds.write_text(json.dumps(self._MINIMAL_DATASET))
        agent = tmp_path / "agent.md"
        agent.write_text(self._MINIMAL_AGENT)

        results_path = run_evaluation.evaluate(
            str(ds), str(agent),
            str(tmp_path / "results"),
            str(tmp_path / "experiments"),
        )

        assert os.path.exists(results_path)

    def test_results_file_schema_is_valid(self, tmp_path):
        ds = tmp_path / "data.json"
        ds.write_text(json.dumps(self._MINIMAL_DATASET))
        agent = tmp_path / "agent.md"
        agent.write_text(self._MINIMAL_AGENT)

        results_path = run_evaluation.evaluate(
            str(ds), str(agent),
            str(tmp_path / "results"),
            str(tmp_path / "experiments"),
        )

        records = json.loads(open(results_path).read())
        assert len(records) == 1
        rec = records[0]
        assert rec["scenario_id"] == "integration_hello"
        assert rec["score"] in ("pass", "partial", "fail")
        assert 0.0 <= rec["numeric_score"] <= 1.0
        assert rec["timestamp"].endswith("Z")

    def test_experiment_log_schema_is_valid(self, tmp_path):
        ds = tmp_path / "data.json"
        ds.write_text(json.dumps(self._MINIMAL_DATASET))
        agent = tmp_path / "agent.md"
        agent.write_text(self._MINIMAL_AGENT)
        experiments_dir = tmp_path / "experiments"

        run_evaluation.evaluate(
            str(ds), str(agent),
            str(tmp_path / "results"),
            str(experiments_dir),
        )

        exp_files = list(experiments_dir.glob("run_*.json"))
        assert len(exp_files) == 1
        exp = json.loads(exp_files[0].read_text())

        assert exp["model"] == "github-copilot"
        assert 0.0 <= exp["pass_rate"] <= 1.0
        assert 0.0 <= exp["mean_score"] <= 1.0
        assert exp["timestamp"].endswith("Z")
        assert len(exp["results"]) == 1
