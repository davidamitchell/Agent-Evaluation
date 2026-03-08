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

## Research foundation

This repository was built on research conducted in [davidamitchell/Research](https://github.com/davidamitchell/Research). Two research items directly informed its design:

1. **[General Agent Optimization Framework](https://github.com/davidamitchell/Research/blob/main/Research/completed/2026-03-05-general-agent-optimization-framework.md)** (2026-03-05) — survey of automated prompt optimisation frameworks (APE, OPRO, TextGrad, DSPy) and the canonical architecture for a self-improving agent evaluation loop. This directly shaped the instruction-drift detection, score-regression gate, dataset-freshness detection, and retrospective-memo pipeline (see [`lab/adr/ADR-0003-self-improvement-loop.md`](lab/adr/ADR-0003-self-improvement-loop.md)).

2. **[Guiding Headless Agents via LSP-Like Mechanisms for Org Policy Conformance](https://github.com/davidamitchell/Research/blob/main/Research/completed/2026-03-01-agent-lsp-policy-enforcement.md)** (2026-03-01) — analysis of how headless autonomous agents can be guided in real time to conform to an organisation's security, architectural, and engineering policies. This framed the core problem this repository addresses: measuring and improving agent compliance with defined behavioural rules.

### Primary sources

The research above draws on the following peer-reviewed papers and technical references:

| Reference | Link |
|-----------|------|
| Khattab et al. (2023) — DSPy: Compiling Declarative Language Model Calls into Self-Improving Pipelines | [arXiv:2310.03714](https://arxiv.org/abs/2310.03714) |
| Yang et al. (2024) — OPRO: Large Language Models as Optimizers | [arXiv:2309.03409](https://arxiv.org/abs/2309.03409) |
| Zhou et al. (2023) — APE: Large Language Models Are Human-Level Prompt Engineers | [arXiv:2211.01910](https://arxiv.org/abs/2211.01910) |
| Yuksekgonul et al. (2024) — TextGrad: Automatic "Differentiation" via Text | [arXiv:2406.07496](https://arxiv.org/abs/2406.07496) |
| Chroma Research (2025) — Context rot and the lost-in-the-middle effect | [research.trychroma.com/context-rot](https://research.trychroma.com/context-rot) |
| DSPy documentation | [dspy.ai](https://dspy.ai/) |

---

> AI agents working in this repository: see [`.github/copilot-instructions.md`](.github/copilot-instructions.md).
