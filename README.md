# Agent-Evaluation

An experimental system for evaluating and improving AI agent instruction sets.

Agents are defined as Markdown instruction files. The pipeline submits evaluation scenarios to an agent via the GitHub Copilot CLI, scores the responses with an LLM-as-judge, and records structured results for analysis. The long-term goal is an automated loop: **evaluate → identify failures → mutate instructions → re-evaluate**.

---

## How it works

```
dataset (scenarios + variants)
  → agent instruction file
  → GitHub Copilot CLI (response generation)
  → LLM-as-judge (compliance scoring)
  → results/run_NNN.json   (raw per-variant responses + scores)
  → experiments/run_NNN.json  (metadata + aggregates)
```

Each evaluation scenario includes an `expected_behavior` description. The judge scores each agent response on a 0.0–1.0 scale and assigns a categorical label:

| Label | Threshold |
|-------|-----------|
| `pass` | `numeric_score >= 0.7` |
| `partial` | `0.4 <= numeric_score < 0.7` |
| `fail` | `numeric_score < 0.4` |

---

## Prerequisites

- **Python 3.11+** (no extra packages needed — stdlib only)
- **GitHub Copilot CLI**: `npm install -g @github/copilot`
- **`COPILOT_GITHUB_TOKEN`** environment variable: a GitHub personal access token with Copilot access

---

## Quick start

```bash
# 1. Clone the repository
git clone https://github.com/davidamitchell/Agent-Evaluation.git
cd Agent-Evaluation

# 2. Set your Copilot token
export COPILOT_GITHUB_TOKEN=<your-github-token>

# 3. Run an evaluation
python scripts/run_evaluation.py \
  --dataset datasets/example.json \
  --agent agents/default_agent.md \
  --output-dir results \
  --experiments-dir experiments
```

Results are written to `results/run_NNN.json` and `experiments/run_NNN.json`.

---

## Running via GitHub Actions

The evaluation workflow is triggered **on demand** — it does not run automatically on push.

1. Go to the **Actions** tab → **Evaluate Agent** → **Run workflow**.
2. The workflow installs the Copilot CLI, runs the evaluation pipeline, and commits the result files back to the repository.

---

## Running tests

```bash
pip install pytest

# Unit tests (no credentials required)
pytest tests/ -m "not integration" -v

# Integration tests (requires COPILOT_GITHUB_TOKEN)
pytest tests/ -v
```

The CI pipeline (`.github/workflows/ci.yml`) runs unit tests on every push and pull request, followed by integration tests when the token secret is available.

---

## Project structure

```
agents/                         # Agent instruction files (Markdown)
  default_agent.md              # Baseline instruction set
  example_agent.md              # Minimal agent for pipeline validation

datasets/                       # Evaluation datasets (JSON)
  example.json                  # Three scenarios with paraphrase variants

scripts/
  run_evaluation.py             # Main evaluation pipeline

results/                        # Raw per-variant agent responses and scores
experiments/                    # Structured experiment logs (metadata + aggregates)
tests/                          # Unit and integration tests

lab/
  backlog.md                    # Task backlog (source of truth for planned work)
  adr/                          # Architecture Decision Records

docs/
  adr/                          # Architecture Decision Records (MADR format)

BACKLOG.md                      # Root backlog (backlog-manager skill format)
PROGRESS.md                     # Append-only session history
CHANGELOG.md                    # User-facing change log (Keep a Changelog)

.github/
  copilot-instructions.md       # Instructions for AI agents working in this repo
  skills/                       # Skills submodule (davidamitchell/Skills)
  workflows/
    evaluate.yml                # On-demand evaluation workflow
    ci.yml                      # CI pipeline
    sync-skills.yml             # Weekly skills submodule update
```

---

## Key concepts

**Agent** — a Markdown file that defines the system instructions given to the model. Each agent must include `## Role`, `## Behavioural Expectations`, and `## Evaluation Context` sections. See [`agents/README.md`](agents/README.md).

**Dataset** — a JSON array of evaluation scenarios. Each scenario has an `id`, a `scenario` prompt, an `expected_behavior` description, and optional `variants` (semantically equivalent restatements). See [`datasets/README.md`](datasets/README.md).

**Result file** — raw per-variant agent responses and scores written to `results/run_NNN.json`. See [`results/README.md`](results/README.md).

**Experiment log** — structured metadata, per-variant scores, and aggregate `pass_rate` and `mean_score` written to `experiments/run_NNN.json`. See [`experiments/README.md`](experiments/README.md).

---

## Architecture and decisions

- [`lab/adr/`](lab/adr/) — Architecture Decision Records explaining key design choices
- [`docs/adr/`](docs/adr/) — Additional ADRs in MADR format
- [`lab/backlog.md`](lab/backlog.md) — Planned improvements with goals, constraints, deliverables, and acceptance criteria

---

> AI agents working in this repository: see [`.github/copilot-instructions.md`](.github/copilot-instructions.md).
