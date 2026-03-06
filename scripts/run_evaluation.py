#!/usr/bin/env python3
"""
run_evaluation.py

Minimal evaluation pipeline for the Agent-Evaluation system.

Responsibilities:
  - Load a dataset of evaluation scenarios from datasets/
  - Load agent instructions from agents/
  - Submit each scenario to the OpenAI-compatible API (GitHub Models endpoint)
  - Capture the agent response
  - Store results in results/run_NNN.json

Usage:
  python scripts/run_evaluation.py \
      --dataset datasets/example.json \
      --agent agents/default_agent.md \
      --output-dir results

Environment variables:
  GITHUB_TOKEN   A GitHub personal access token with models:read permission,
                 used to authenticate against the GitHub Models API endpoint.
"""

import argparse
import datetime
import json
import os
import sys
import urllib.request
import urllib.error


GITHUB_MODELS_ENDPOINT = "https://models.inference.ai.azure.com"
DEFAULT_MODEL = "gpt-4o-mini"


def load_dataset(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError(f"Dataset at {path!r} must be a JSON array.")
    return data


def load_agent_instructions(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def call_model(system_prompt: str, user_message: str, token: str, model: str) -> str:
    """Send a chat completion request to the GitHub Models API."""
    payload = json.dumps(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "max_tokens": 512,
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        f"{GITHUB_MODELS_ENDPOINT}/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.load(resp)
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"HTTP {exc.code} from model API: {error_body}"
        ) from exc

    return body["choices"][0]["message"]["content"]


def next_run_path(output_dir: str) -> str:
    os.makedirs(output_dir, exist_ok=True)
    existing = [
        f for f in os.listdir(output_dir) if f.startswith("run_") and f.endswith(".json")
    ]
    run_numbers = []
    for name in existing:
        try:
            run_numbers.append(int(name[4:-5]))
        except ValueError:
            pass
    next_num = max(run_numbers, default=0) + 1
    return os.path.join(output_dir, f"run_{next_num:03d}.json")


def evaluate(dataset_path: str, agent_path: str, output_dir: str, model: str) -> str:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("Error: GITHUB_TOKEN environment variable is not set.")

    scenarios = load_dataset(dataset_path)
    agent_instructions = load_agent_instructions(agent_path)

    print(f"Loaded {len(scenarios)} scenario(s) from {dataset_path!r}")
    print(f"Agent instructions loaded from {agent_path!r}")
    print(f"Model: {model}")

    results = []
    for scenario in scenarios:
        scenario_id = scenario.get("id", "unknown")
        scenario_text = scenario.get("scenario", "")
        expected = scenario.get("expected_behavior", "")

        print(f"  Evaluating scenario: {scenario_id} ...", end=" ", flush=True)
        response = call_model(agent_instructions, scenario_text, token, model)
        print("done")

        results.append(
            {
                "scenario_id": scenario_id,
                "scenario": scenario_text,
                "expected_behavior": expected,
                "agent_response": response,
                "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            }
        )

    output_path = next_run_path(output_dir)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nResults written to {output_path!r}")
    return output_path


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
        "--model",
        default=DEFAULT_MODEL,
        help="Model identifier to use for evaluation.",
    )
    args = parser.parse_args()
    evaluate(args.dataset, args.agent, args.output_dir, args.model)


if __name__ == "__main__":
    main()
