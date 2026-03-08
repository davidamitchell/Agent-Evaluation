#!/usr/bin/env python3
"""
mutate_instructions.py

Given a baseline agent instruction file and evaluation results showing failures,
produce a candidate improved instruction file using an LLM to analyse the failures
and rewrite the instructions.

Usage:
  python scripts/mutate_instructions.py \
      --agent agents/default_agent.md \
      --results results/run_001.json \
      --version 2

Environment variables:
  COPILOT_GITHUB_TOKEN   A GitHub token with Copilot access.  Passed to the
                         GitHub Copilot CLI as GITHUB_TOKEN so the CLI can
                         authenticate without a prior login step.

Prerequisites:
  - GitHub Copilot CLI (@github/copilot) must be installed and on PATH:
      npm install -g @github/copilot
"""

import argparse
import datetime
import json
import os
import subprocess
import sys
import time


MAX_RETRIES = 3


# NOTE: call_copilot_cli is copied from scripts/run_evaluation.py to keep this
# script independently runnable without requiring run_evaluation on sys.path.
# If the function signature changes in run_evaluation.py, update this copy too.
def call_copilot_cli(prompt: str, token: str) -> str:
    """Invoke the GitHub Copilot CLI with a prompt and return its response.

    Passes the token as GITHUB_TOKEN in the subprocess environment so the CLI
    can authenticate without a prior login step.  Retries up to MAX_RETRIES
    times with exponential backoff on transient errors.
    """
    env = {**os.environ, "GITHUB_TOKEN": token}

    last_exc: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            result = subprocess.run(
                # --autopilot runs without interactive prompts.
                # --allow-all auto-approves any tool/action the CLI requests,
                # which is required for unattended CI execution.
                ["copilot", "-p", prompt, "--autopilot", "--allow-all"],
                capture_output=True,
                text=True,
                timeout=120,
                env=env,
            )
            if result.returncode != 0:
                raise RuntimeError(
                    f"copilot CLI exited {result.returncode}: {result.stderr.strip()}"
                )
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            last_exc = RuntimeError("copilot CLI timed out after 120 seconds")
        except RuntimeError as exc:
            last_exc = exc
        except Exception as exc:
            last_exc = exc
        if attempt < MAX_RETRIES - 1:
            time.sleep(2 ** attempt)

    raise RuntimeError(
        f"copilot CLI call failed after {MAX_RETRIES} attempts"
    ) from last_exc


def load_results(path: str) -> list[dict]:
    """Load a results JSON file and return its records."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Results file at {path!r} must be a JSON array.")
    return data


def extract_failures(results: list[dict]) -> list[dict]:
    """Return records where score is 'fail' or 'partial'."""
    return [r for r in results if r.get("score") in ("fail", "partial")]


def build_mutation_prompt(instructions: str, failures: list[dict]) -> str:
    """Build the meta-prompt for the mutation LLM call.

    The prompt includes the current instructions, the failing/partial records,
    and an explicit brevity constraint to keep output length within ±10% of the
    input instruction character count.
    """
    base_char_count = len(instructions)
    lower_bound = int(base_char_count * 0.9)
    upper_bound = int(base_char_count * 1.1)

    failure_lines = []
    for i, rec in enumerate(failures, start=1):
        failure_lines.append(
            f"--- Failure {i} ---\n"
            f"scenario_id: {rec.get('scenario_id', 'unknown')}\n"
            f"score: {rec.get('score', 'unknown')}\n"
            f"variant: {rec.get('variant', '')}\n"
            f"expected_behavior: {rec.get('expected_behavior', '')}\n"
            f"agent_response: {rec.get('agent_response', '')}"
        )
    failures_text = "\n\n".join(failure_lines)

    prompt = (
        "You are an expert instruction engineer improving an AI agent's behaviour.\n\n"
        "Below are the current agent instructions, followed by a set of evaluation "
        "records where the agent failed or partially failed to meet the expected "
        "behaviour.\n\n"
        "Your task:\n"
        "1. Identify the *class* (pattern) of failures — what general capability or "
        "rule is missing or under-specified in the current instructions?\n"
        "2. Add or revise a rule in the instructions to address this pattern. "
        "Do NOT patch individual failures; fix the underlying gap.\n"
        f"3. IMPORTANT — brevity constraint: the revised instructions MUST be between "
        f"{lower_bound} and {upper_bound} characters (±10% of the current "
        f"{base_char_count} characters, counting all characters including whitespace, "
        "newlines, and Markdown formatting). Remove redundant content if you add new "
        "content. Context rot degrades agent performance.\n"
        "4. Return ONLY the full revised instruction text — no preamble, no "
        "commentary, no explanation. The output will be saved directly as the new "
        "agent instruction file.\n\n"
        "=== CURRENT INSTRUCTIONS ===\n"
        f"{instructions}\n\n"
        "=== FAILING / PARTIAL RECORDS ===\n"
        f"{failures_text}"
    )
    return prompt


def write_mutation_log(
    log_path: str,
    base_agent: str,
    results_file: str,
    failure_count: int,
    candidate_file: str,
    base_char_count: int,
    candidate_char_count: int,
) -> None:
    """Write a JSON mutation log entry to log_path."""
    entry = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc)
        .isoformat()
        .replace("+00:00", "Z"),
        "base_agent": base_agent,
        "results_file": results_file,
        "failure_count": failure_count,
        "candidate_file": candidate_file,
        "base_char_count": base_char_count,
        "candidate_char_count": candidate_char_count,
    }
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(entry, f, indent=2, ensure_ascii=False)


def mutate(
    agent_path: str,
    results_path: str,
    version: int,
    output_dir: str,
    experiments_dir: str,
) -> None:
    """Run the mutation pipeline."""
    token = os.environ.get("COPILOT_GITHUB_TOKEN")
    if not token:
        sys.exit("Error: COPILOT_GITHUB_TOKEN environment variable is not set.")

    # Safety: never overwrite the baseline agent file.
    candidate_filename = f"candidate_agent_v{version}.md"
    candidate_path = os.path.join(output_dir, candidate_filename)
    if os.path.realpath(candidate_path) == os.path.realpath(agent_path):
        sys.exit(
            f"Error: candidate output path {candidate_path!r} resolves to the same "
            f"file as the baseline agent {agent_path!r}. Refusing to overwrite."
        )

    with open(agent_path, encoding="utf-8") as f:
        instructions = f.read()

    results = load_results(results_path)
    failures = extract_failures(results)

    if not failures:
        print(
            f"No failures found in {results_path!r}. Nothing to mutate. Exiting."
        )
        return

    print(
        f"Found {len(failures)} failure(s)/partial(s) in {results_path!r}. "
        "Building mutation prompt..."
    )

    prompt = build_mutation_prompt(instructions, failures)
    print("Calling Copilot CLI for instruction mutation...")
    candidate_instructions = call_copilot_cli(prompt, token)

    os.makedirs(output_dir, exist_ok=True)
    with open(candidate_path, "w", encoding="utf-8") as f:
        f.write(candidate_instructions)
    print(f"Candidate instructions written to {candidate_path!r}")

    base_char_count = len(instructions)
    candidate_char_count = len(candidate_instructions)
    delta = candidate_char_count - base_char_count

    os.makedirs(experiments_dir, exist_ok=True)
    log_path = os.path.join(experiments_dir, f"mutation_v{version}.json")
    write_mutation_log(
        log_path=log_path,
        base_agent=agent_path,
        results_file=results_path,
        failure_count=len(failures),
        candidate_file=candidate_path,
        base_char_count=base_char_count,
        candidate_char_count=candidate_char_count,
    )
    print(f"Mutation log written to {log_path!r}")

    sign = "+" if delta >= 0 else ""
    print(
        f"\nSummary: {len(failures)} failure(s) processed | "
        f"candidate → {candidate_path!r} | "
        f"char delta: {sign}{delta} "
        f"({base_char_count} → {candidate_char_count})"
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Mutate agent instructions based on evaluation failures."
    )
    parser.add_argument(
        "--agent",
        default="agents/default_agent.md",
        help="Path to the baseline agent instruction Markdown file.",
    )
    parser.add_argument(
        "--results",
        required=True,
        help="Path to a results JSON file (results/run_NNN.json).",
    )
    parser.add_argument(
        "--version",
        type=int,
        default=2,
        help="Version number for the candidate output file (produces candidate_agent_vN.md).",
    )
    parser.add_argument(
        "--output-dir",
        default="agents",
        help="Directory to write the candidate instruction file.",
    )
    parser.add_argument(
        "--experiments-dir",
        default="experiments",
        help="Directory to write the mutation log.",
    )
    args = parser.parse_args()
    mutate(args.agent, args.results, args.version, args.output_dir, args.experiments_dir)


if __name__ == "__main__":
    main()
