"""
Unit tests for scripts/mutate_instructions.py.

All external I/O (subprocess / Copilot CLI) is mocked so these tests run
without network access or credentials.  Every piece of business logic has
at least one test; boundary conditions and failure paths are explicitly covered.

Naming convention:  test_<unit>_<condition>_<expected_outcome>
"""
import json
import os
from unittest.mock import MagicMock, patch

import pytest

import mutate_instructions


# ── extract_failures ──────────────────────────────────────────────────────────


class TestExtractFailures:
    def test_extract_failures_all_pass_returns_empty(self):
        results = [
            {"scenario_id": "s1", "score": "pass", "numeric_score": 0.9},
            {"scenario_id": "s2", "score": "pass", "numeric_score": 0.8},
        ]
        assert mutate_instructions.extract_failures(results) == []

    def test_extract_failures_mixed_returns_only_fail_and_partial(self):
        results = [
            {"scenario_id": "s1", "score": "pass", "numeric_score": 0.9},
            {"scenario_id": "s2", "score": "fail", "numeric_score": 0.1},
            {"scenario_id": "s3", "score": "partial", "numeric_score": 0.5},
        ]
        failures = mutate_instructions.extract_failures(results)
        assert len(failures) == 2
        assert all(r["score"] in ("fail", "partial") for r in failures)
        ids = [r["scenario_id"] for r in failures]
        assert "s2" in ids
        assert "s3" in ids
        assert "s1" not in ids

    def test_extract_failures_all_fail_returns_all(self):
        results = [
            {"scenario_id": "s1", "score": "fail", "numeric_score": 0.0},
            {"scenario_id": "s2", "score": "fail", "numeric_score": 0.2},
        ]
        assert len(mutate_instructions.extract_failures(results)) == 2

    def test_extract_failures_empty_list_returns_empty(self):
        assert mutate_instructions.extract_failures([]) == []

    def test_extract_failures_missing_score_field_excluded(self):
        results = [{"scenario_id": "s1"}]
        assert mutate_instructions.extract_failures(results) == []


# ── build_mutation_prompt ─────────────────────────────────────────────────────


class TestBuildMutationPrompt:
    def _make_failure(self, scenario_id: str = "s1") -> dict:
        return {
            "scenario_id": scenario_id,
            "score": "fail",
            "variant": "How do I do X?",
            "expected_behavior": "Decline and explain.",
            "agent_response": "Sure, here is how to do X.",
        }

    def test_build_mutation_prompt_includes_instruction_text(self):
        instructions = "## Role\nYou are a helpful agent."
        failures = [self._make_failure()]
        prompt = mutate_instructions.build_mutation_prompt(instructions, failures)
        assert instructions in prompt

    def test_build_mutation_prompt_includes_failure_records(self):
        instructions = "## Role\nYou are a helpful agent."
        failure = self._make_failure("my_scenario")
        prompt = mutate_instructions.build_mutation_prompt(instructions, [failure])
        assert "my_scenario" in prompt
        assert failure["variant"] in prompt
        assert failure["expected_behavior"] in prompt
        assert failure["agent_response"] in prompt

    def test_build_mutation_prompt_includes_brevity_constraint(self):
        instructions = "A" * 1000
        failures = [self._make_failure()]
        prompt = mutate_instructions.build_mutation_prompt(instructions, failures)
        # Brevity constraint: ±10% of 1000 chars = 900–1100
        assert "900" in prompt
        assert "1100" in prompt

    def test_build_mutation_prompt_brevity_bounds_computed_correctly(self):
        instructions = "B" * 500
        failures = [self._make_failure()]
        prompt = mutate_instructions.build_mutation_prompt(instructions, failures)
        assert "450" in prompt   # 500 * 0.9
        assert "550" in prompt   # 500 * 1.1

    def test_build_mutation_prompt_no_preamble_instruction_present(self):
        instructions = "## Role\nDo X."
        failures = [self._make_failure()]
        prompt = mutate_instructions.build_mutation_prompt(instructions, failures)
        assert "no preamble" in prompt.lower() or "no commentary" in prompt.lower()


# ── write_mutation_log ────────────────────────────────────────────────────────


class TestWriteMutationLog:
    def test_write_mutation_log_creates_valid_json_with_required_fields(
        self, tmp_path
    ):
        log_path = str(tmp_path / "mutation_v2.json")
        mutate_instructions.write_mutation_log(
            log_path=log_path,
            base_agent="agents/default_agent.md",
            results_file="results/run_001.json",
            failure_count=3,
            candidate_file="agents/candidate_agent_v2.md",
            base_char_count=1000,
            candidate_char_count=1050,
        )
        assert os.path.exists(log_path)
        with open(log_path, encoding="utf-8") as f:
            entry = json.load(f)

        assert entry["base_agent"] == "agents/default_agent.md"
        assert entry["results_file"] == "results/run_001.json"
        assert entry["failure_count"] == 3
        assert entry["candidate_file"] == "agents/candidate_agent_v2.md"
        assert entry["base_char_count"] == 1000
        assert entry["candidate_char_count"] == 1050
        assert "timestamp" in entry
        # Timestamp should be an ISO 8601 string ending in Z
        assert entry["timestamp"].endswith("Z")

    def test_write_mutation_log_overwrites_existing_file(self, tmp_path):
        log_path = str(tmp_path / "mutation_v2.json")
        # Write once with failure_count=1
        mutate_instructions.write_mutation_log(
            log_path=log_path,
            base_agent="a",
            results_file="r",
            failure_count=1,
            candidate_file="c",
            base_char_count=100,
            candidate_char_count=105,
        )
        # Write again with failure_count=5
        mutate_instructions.write_mutation_log(
            log_path=log_path,
            base_agent="a",
            results_file="r",
            failure_count=5,
            candidate_file="c",
            base_char_count=100,
            candidate_char_count=105,
        )
        with open(log_path, encoding="utf-8") as f:
            entry = json.load(f)
        assert entry["failure_count"] == 5


# ── no-failures early-exit path ───────────────────────────────────────────────


class TestNoFailuresEarlyExit:
    def test_mutate_no_failures_exits_without_calling_llm(self, tmp_path):
        """When results contain no fail/partial records, mutate() returns without
        calling call_copilot_cli or writing any output files."""
        results = [
            {
                "scenario_id": "s1",
                "score": "pass",
                "numeric_score": 1.0,
                "variant": "How to X?",
                "expected_behavior": "Explain X.",
                "agent_response": "Here is how to X.",
                "timestamp": "2026-01-01T00:00:00Z",
            }
        ]
        results_file = tmp_path / "run_001.json"
        results_file.write_text(json.dumps(results))

        agent_file = tmp_path / "default_agent.md"
        agent_file.write_text("## Role\nDo the right thing.")

        output_dir = str(tmp_path / "agents_out")
        experiments_dir = str(tmp_path / "experiments_out")

        with patch.dict(os.environ, {"COPILOT_GITHUB_TOKEN": "fake-token"}):
            with patch(
                "mutate_instructions.call_copilot_cli"
            ) as mock_llm:
                mutate_instructions.mutate(
                    agent_path=str(agent_file),
                    results_path=str(results_file),
                    version=2,
                    output_dir=output_dir,
                    experiments_dir=experiments_dir,
                )

        mock_llm.assert_not_called()
        # Candidate file must NOT have been created
        assert not os.path.exists(os.path.join(output_dir, "candidate_agent_v2.md"))

    def test_mutate_with_failures_calls_llm_and_writes_files(self, tmp_path):
        """When failures exist, mutate() calls the LLM and writes candidate + log."""
        results = [
            {
                "scenario_id": "s1",
                "score": "fail",
                "numeric_score": 0.1,
                "variant": "How to do bad thing?",
                "expected_behavior": "Refuse.",
                "agent_response": "Sure!",
                "timestamp": "2026-01-01T00:00:00Z",
            }
        ]
        results_file = tmp_path / "run_001.json"
        results_file.write_text(json.dumps(results))

        agent_file = tmp_path / "default_agent.md"
        agent_file.write_text("## Role\nDo the right thing.")

        output_dir = str(tmp_path / "agents_out")
        experiments_dir = str(tmp_path / "experiments_out")

        with patch.dict(os.environ, {"COPILOT_GITHUB_TOKEN": "fake-token"}):
            with patch(
                "mutate_instructions.call_copilot_cli",
                return_value="## Role\nImproved instructions.",
            ):
                mutate_instructions.mutate(
                    agent_path=str(agent_file),
                    results_path=str(results_file),
                    version=2,
                    output_dir=output_dir,
                    experiments_dir=experiments_dir,
                )

        candidate_path = os.path.join(output_dir, "candidate_agent_v2.md")
        assert os.path.exists(candidate_path)
        with open(candidate_path, encoding="utf-8") as f:
            content = f.read()
        assert content == "## Role\nImproved instructions."

        log_path = os.path.join(experiments_dir, "mutation_v2.json")
        assert os.path.exists(log_path)
        with open(log_path, encoding="utf-8") as f:
            log = json.load(f)
        assert log["failure_count"] == 1
