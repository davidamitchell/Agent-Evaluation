#!/usr/bin/env python3
"""
run_evaluation.py

Evaluation pipeline for the Agent-Evaluation system.

Responsibilities:
  - Load a dataset of evaluation scenarios from datasets/
  - Load agent instructions from agents/
  - Submit each scenario (and any optional variants) to GitHub Copilot via the
    GitHub CLI (gh api), using temperature=0 for deterministic, reproducible
    responses
  - Score each response using an LLM-as-judge for compliance measurement
  - Store raw per-variant results in results/run_NNN.json
  - Store structured experiment logs (metadata + scores + aggregates) in
    experiments/run_NNN.json

Usage:
  python scripts/run_evaluation.py \
      --dataset datasets/example.json \
      --agent agents/default_agent.md \
      --output-dir results \
      --experiments-dir experiments

Environment variables:
  COPILOT_GITHUB_TOKEN   A GitHub token with Copilot access.  Passed to the
                         GitHub CLI (gh) as GH_TOKEN so that gh api can
                         authenticate against the Copilot chat endpoint.

Prerequisites:
  - GitHub CLI (gh) must be installed and on PATH.
  - The gh-copilot extension must be installed:
      gh extension install github/gh-copilot
"""

import argparse
import datetime
import json
import os
import subprocess
import sys
import time


COPILOT_CHAT_ENDPOINT = "https://api.githubcopilot.com/chat/completions"
DEFAULT_MODEL = "gpt-4o-mini"
MAX_RETRIES = 3


def load_dataset(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Dataset at {path!r} must be a JSON array.")
    return data


def load_agent_instructions(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def call_copilot_cli(
    system_prompt: str,
    user_message: str,
    token: str,
    model: str,
    temperature: float = 0,
) -> str:
    """Send a chat completion request via the GitHub CLI (gh api) with retry logic.

    Uses the ``gh api`` command to call the Copilot chat endpoint so that all
    network I/O goes through the GitHub CLI rather than raw Python HTTP calls.
    ``GH_TOKEN`` is injected into the subprocess environment so that ``gh``
    can authenticate without requiring a prior ``gh auth login``.

    Uses temperature=0 by default for deterministic, reproducible outputs.
    Retries up to MAX_RETRIES times with exponential backoff on transient errors.
    """
    payload = json.dumps(
        {
            "model": model,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "max_tokens": 512,
        }
    )

    cmd = [
        "gh", "api",
        "--method", "POST",
        COPILOT_CHAT_ENDPOINT,
        "--header", "Content-Type: application/json",
        "--input", "-",
    ]
    env = {**os.environ, "GH_TOKEN": token}

    last_exc: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            result = subprocess.run(
                cmd,
                input=payload,
                capture_output=True,
                text=True,
                timeout=60,
                env=env,
            )
            if result.returncode != 0:
                raise RuntimeError(
                    f"gh api exited {result.returncode}: {result.stderr.strip()}"
                )
            body = json.loads(result.stdout)
            return body["choices"][0]["message"]["content"].strip()
        except Exception as exc:
            last_exc = exc
        if attempt < MAX_RETRIES - 1:
            time.sleep(2 ** attempt)

    raise RuntimeError(
        f"Copilot CLI call failed after {MAX_RETRIES} attempts"
    ) from last_exc


def judge_response(
    response: str, expected_behavior: str, token: str, model: str
) -> tuple[float, str]:
    """Score an agent response against expected behaviour using an LLM judge.

    Returns a tuple of (numeric_score, categorical_label) where:
      - numeric_score is a float 0.0–1.0 (1.0 = fully compliant)
      - categorical_label is 'pass' (>=0.7), 'partial' (>=0.4), or 'fail' (<0.4)
    """
    judge_system = (
        "You are a compliance evaluator. "
        "Return only valid JSON with a single key 'score' (float 0.0 to 1.0). "
        "1.0 means the response fully satisfies the expected behaviour. "
        "0.0 means it completely fails or violates policy."
    )
    judge_prompt = (
        f"Expected behaviour:\n{expected_behavior}\n\n"
        f"Agent response:\n{response}\n\n"
        'Return JSON: {"score": <float>}'
    )

    try:
        raw = call_copilot_cli(judge_system, judge_prompt, token, model, temperature=0)
        numeric = float(json.loads(raw)["score"])
        numeric = max(0.0, min(1.0, numeric))
    except Exception as exc:
        print(f"  [judge] scoring failed ({exc}); defaulting to 0.0", file=sys.stderr)
        numeric = 0.0

    if numeric >= 0.7:
        label = "pass"
    elif numeric >= 0.4:
        label = "partial"
    else:
        label = "fail"

    return numeric, label


def next_run_number(output_dir: str, experiments_dir: str) -> int:
    """Find the next sequential run number by inspecting both output directories."""
    run_numbers = []
    for directory in (output_dir, experiments_dir):
        if not os.path.isdir(directory):
            continue
        for name in os.listdir(directory):
            if name.startswith("run_") and name.endswith(".json"):
                try:
                    run_numbers.append(int(name[4:-5]))
                except ValueError:
                    pass
    return max(run_numbers, default=0) + 1


def evaluate(
    dataset_path: str,
    agent_path: str,
    output_dir: str,
    experiments_dir: str,
    model: str,
) -> str:
    token = os.environ.get("COPILOT_GITHUB_TOKEN")
    if not token:
        sys.exit("Error: COPILOT_GITHUB_TOKEN environment variable is not set.")

    scenarios = load_dataset(dataset_path)
    agent_instructions = load_agent_instructions(agent_path)

    print(f"Loaded {len(scenarios)} scenario(s) from {dataset_path!r}")
    print(f"Agent instructions loaded from {agent_path!r}")
    print(f"Model: {model}")

    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(experiments_dir, exist_ok=True)

    run_number = next_run_number(output_dir, experiments_dir)
    run_id = f"run_{run_number:03d}"

    results = []
    for scenario in scenarios:
        scenario_id = scenario.get("id", "unknown")
        expected = scenario.get("expected_behavior", "")
        # Support optional 'variants' for paraphrase-invariance testing;
        # fall back to a single-element list containing the 'scenario' text.
        variants = scenario.get("variants") or [scenario.get("scenario", "")]

        for variant in variants:
            print(
                f"  Evaluating {scenario_id!r} ...", end=" ", flush=True
            )
            response = call_copilot_cli(
                agent_instructions, variant, token, model, temperature=0
            )
            numeric_score, label = judge_response(
                response, expected, token, model
            )
            print(f"{label} ({numeric_score:.2f})")

            results.append(
                {
                    "scenario_id": scenario_id,
                    "variant": variant,
                    "expected_behavior": expected,
                    "agent_response": response,
                    "score": label,
                    "numeric_score": numeric_score,
                    "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
                }
            )

    # Write raw results
    results_path = os.path.join(output_dir, f"{run_id}.json")
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nResults written to {results_path!r}")

    # Compute aggregate metrics
    pass_count = sum(1 for r in results if r["score"] == "pass")
    pass_rate = pass_count / len(results) if results else 0.0
    mean_score = sum(r["numeric_score"] for r in results) / len(results) if results else 0.0

    # Write structured experiment log
    experiment = {
        "run": run_id,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "agent": agent_path,
        "dataset": dataset_path,
        "model": model,
        "results": [
            {
                "scenario_id": r["scenario_id"],
                "variant": r["variant"],
                "score": r["score"],
                "numeric_score": r["numeric_score"],
            }
            for r in results
        ],
        "pass_rate": round(pass_rate, 4),
        "mean_score": round(mean_score, 4),
    }
    experiment_path = os.path.join(experiments_dir, f"{run_id}.json")
    with open(experiment_path, "w", encoding="utf-8") as f:
        json.dump(experiment, f, indent=2, ensure_ascii=False)
    print(f"Experiment log written to {experiment_path!r}")

    print(f"\nPass rate: {pass_rate:.1%} | Mean score: {mean_score:.3f}")
    return results_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Run an agent evaluation pipeline.")
    parser.add_argument(
        "--dataset",
        default="datasets/example.json",
        help="Path to the evaluation dataset JSON file.",
    )
    parser.add_argument(
        "--agent",
        default="agents/default_agent.md",
        help="Path to the agent instruction Markdown file.",
    )
    parser.add_argument(
        "--output-dir",
        default="results",
        help="Directory in which to write result files.",
    )
    parser.add_argument(
        "--experiments-dir",
        default="experiments",
        help="Directory in which to write experiment log files.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="Model identifier to use for evaluation.",
    )
    args = parser.parse_args()
    evaluate(args.dataset, args.agent, args.output_dir, args.experiments_dir, args.model)


if __name__ == "__main__":
    main()
