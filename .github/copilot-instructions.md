# Copilot Instructions

This file tells GitHub Copilot how to work in this repository. Read it fully before making any change.

---

## Repository purpose

This repository is an experimental system for evaluating and improving AI agent instruction sets. It has two domains that must remain cleanly separated:

| Domain | Paths | What it contains |
|--------|-------|-----------------|
| **Agents** | `agents/` | Markdown instruction files that define agent behaviour |
| **Evaluation Lab** | `datasets/`, `scripts/`, `results/`, `experiments/`, `lab/`, `.github/workflows/` | Everything used to test and improve agents |

The long-term goal is an automated loop: evaluate → identify failures → mutate instructions → re-evaluate. The system is designed to run entirely inside GitHub Actions with no local environment required, though all scripts can be run locally for testing (see [Pipeline execution](#pipeline-execution)).

See `lab/adr/ADR-0001-repository-purpose.md` for the full architectural rationale.

---

## How to pick up a task

All planned work is in `lab/backlog.md`. Each task is independently executable and includes:

- **Goal** — what to achieve
- **Constraints** — what must not change
- **Deliverables** — exact files to create or modify
- **Acceptance criteria** — the conditions that must be true when the task is done

Pick the lowest-numbered incomplete task, read it fully, then implement exactly what its Deliverables and Acceptance criteria specify. Do not implement more than one task per PR.

---

## Documentation alignment — mandatory on every PR

Every pull request **must** keep all documentation consistent with the code changes made. This is not optional. Before marking a PR ready:

1. **READMEs** — update every README whose described schema, behaviour, or file list changed. The affected READMEs are typically `datasets/README.md`, `results/README.md`, `experiments/README.md`, and any directory-level README for paths you modified.
2. **`lab/backlog.md`** — if a task was completed, mark it with `**Status:** Complete` and a brief description of what was done. If new work was identified, add a new task entry.
3. **`lab/adr/`** — if a non-trivial architectural or design decision was made (new scoring approach, new file format, new naming convention, new external dependency), create or update the relevant ADR. ADRs are the permanent record of *why* decisions were made.
4. **`.github/copilot-instructions.md`** (this file) — if a file format, naming convention, safety rule, or script convention changed, update the relevant section here so future agents receive accurate context.
5. **`not-doing.md`** — if a reasonable approach was considered and explicitly rejected, document it there with the reason.

Failing to update these files will cause future agents to work from incorrect context and produce inconsistent implementations.

---

## Repository layout

```
agents/
  default_agent.md          # Baseline instruction set — do not overwrite automatically
  example_agent.md          # Minimal agent used for pipeline validation
  candidate_agent_vN.md     # Generated candidates (created by mutation tasks)

datasets/
  example.json              # Primary evaluation dataset (3 scenarios)
  invariance_example.json   # Invariance dataset (grouped scenario restatements)
  train/                    # Training split (added in Task 005)
  test/                     # Test split (added in Task 005)

scripts/
  run_evaluation.py         # Main evaluation runner
  score.py                  # Scorer (added in Task 001)
  check_invariance.py       # Invariance validator (added in Task 003)
  mutate_instructions.py    # Instruction mutator (added in Task 004)
  generate_paraphrases.py   # Paraphrase generator (added in Task 006)
  report.py                 # Metrics reporter (added in Task 007)
  compare_agents.py         # Multi-agent comparison (added in Task 008)

results/
  run_001.json              # Raw agent responses per evaluation run

experiments/
  run_001.json              # Structured experiment logs (metadata + scores + pass rate)
  summary.json              # Aggregate pass rates over time (added in Task 007)
  summary.md                # Human-readable version of summary.json

lab/
  backlog.md                # Task list — the source of truth for planned work
  adr/                      # Architecture Decision Records

.github/
  workflows/
    evaluate.yml            # Main evaluation workflow (push + workflow_dispatch)
    evaluate_on_pr.yml      # PR evaluation gate (added in Task 010)
```

---

## File format specifications

### Agent instruction file (`agents/*.md`)

Plain Markdown. Must include:
- A `## Role` section describing the agent's persona
- A `## Behavioural Expectations` section listing numbered rules
- An `## Evaluation Context` section explaining how the file is used during evaluation

The baseline is `agents/default_agent.md`. Generated candidates must be named `agents/candidate_agent_v<N>.md` (e.g. `candidate_agent_v2.md`) and must **not** overwrite `default_agent.md` automatically.

### Evaluation dataset (`datasets/*.json`)

JSON array. Each element:

```json
{
  "id": "unique_string",
  "scenario": "Natural language description of the situation.",
  "variants": [
    "Restatement 1 of the scenario.",
    "Restatement 2 of the scenario."
  ],
  "expected_behavior": "Description of what the agent should do."
}
```

`id`, `scenario`, and `expected_behavior` are required. `variants` is optional; when present, every variant is evaluated independently against `expected_behavior`. When absent, only `scenario` is evaluated. The first element of `variants` should match `scenario` verbatim.

### Invariance dataset (`datasets/invariance_*.json`)

JSON array of scenario groups:

```json
[
  {
    "group_id": "unique_string",
    "expected_behavior": "Description of expected agent behaviour for all restatements.",
    "scenarios": [
      "Restatement 1",
      "Restatement 2",
      "Restatement 3"
    ]
  }
]
```

Each group must contain at least 3 semantically equivalent restatements of the same question.

### Result file (`results/run_NNN.json`)

JSON array. Each element records one variant evaluation:

```json
{
  "scenario_id": "example_1",
  "variant": "The exact prompt text sent to the agent.",
  "expected_behavior": "The expected behaviour text.",
  "agent_response": "The raw model response.",
  "score": "pass",
  "numeric_score": 0.95,
  "timestamp": "2026-03-06T20:00:00Z"
}
```

`score` is `pass` (numeric_score >= 0.7), `partial` (>= 0.4), or `fail` (< 0.4). `numeric_score` is the raw LLM-judge float 0.0–1.0.

### Experiment log (`experiments/run_NNN.json`)

JSON object:

```json
{
  "run": "run_001",
  "timestamp": "2026-03-06T20:00:00Z",
  "agent": "agents/default_agent.md",
  "dataset": "datasets/example.json",
  "model": "gpt-4o-mini",
  "results": [
    {
      "scenario_id": "example_1",
      "variant": "The exact prompt text.",
      "score": "pass",
      "numeric_score": 0.95
    }
  ],
  "pass_rate": 1.0,
  "mean_score": 0.95
}
```

`pass_rate` is the fraction of variants scored `pass`. `mean_score` is the mean `numeric_score` across all variants. Both are floats 0.0–1.0. The file is named to match its corresponding `results/run_NNN.json`.

---

## Naming conventions

| Thing | Convention |
|-------|-----------|
| Result files | `results/run_NNN.json` (zero-padded 3-digit run number, e.g. `run_001`) |
| Experiment logs | `experiments/run_NNN.json` (same number as the corresponding result file) |
| Candidate agent files | `agents/candidate_agent_v<N>.md` (e.g. `candidate_agent_v2.md`) |
| Invariance datasets | `datasets/invariance_<name>.json` |
| Paraphrase datasets | `datasets/<source_name>_paraphrased.json` |
| Probe datasets | `datasets/probe/<name>.json` |
| ADRs | `lab/adr/ADR-NNNN-<slug>.md` (zero-padded 4-digit number) |
| Workflow files | `.github/workflows/<verb>_<noun>.yml` (snake_case) |

---

## Script conventions

All scripts in `scripts/` must:

- Use only Python stdlib plus subprocess calls to the GitHub Copilot CLI (no new pip dependencies unless a task explicitly introduces one)
- Accept all configurable inputs as command-line arguments with `argparse`
- Read `COPILOT_GITHUB_TOKEN` from the environment (never accept it as a CLI argument)
- Exit non-zero with a clear message on any unrecoverable error
- Be independently runnable: `python scripts/<script>.py --help` must print usage
- Use the GitHub Copilot CLI (`copilot -p "..." --autopilot --allow-all`) for all model interactions — no direct HTTP API calls

The existing `scripts/run_evaluation.py` is the reference implementation. Match its structure and style when adding new scripts.

---

## Pipeline execution

The evaluation pipeline runs in GitHub Actions. The primary workflow is `.github/workflows/evaluate.yml`, triggered on:
- Push to `agents/**`, `datasets/**`, or `scripts/run_evaluation.py`
- Manual `workflow_dispatch` (with optional `dataset` and `agent` inputs)

The workflow installs the GitHub Copilot CLI (`npm install -g @github/copilot`), calls `scripts/run_evaluation.py`, then commits the result file back to the repository.

To run the pipeline locally for testing:

```bash
# Prerequisites: npm install -g @github/copilot
export COPILOT_GITHUB_TOKEN=<your-token>
python scripts/run_evaluation.py \
  --dataset datasets/example.json \
  --agent agents/default_agent.md \
  --output-dir results \
  --experiments-dir experiments
```

There is no other build system, test runner, or dependency installation step. The pipeline is pure Python stdlib.

---

## Safety rules

These rules apply to every PR in this repository regardless of which task is being implemented:

1. **Never overwrite `agents/default_agent.md` automatically.** All instruction mutations must produce a new versioned candidate file. Human review is required before any candidate replaces the baseline.
2. **Never commit secrets.** `COPILOT_GITHUB_TOKEN` is injected via Actions secrets; it must never appear in source files or result files.
3. **Never modify a result or experiment file after it has been committed.** These are immutable records. If a run must be re-run, produce a new numbered file.
4. **Do not mix agent definitions and evaluation infrastructure.** Changes to `agents/` should not require changes to `scripts/` and vice versa (except when a task explicitly bridges both).
5. **Every new script must be reachable from a workflow.** If a script is added as a Deliverable, the corresponding task's Acceptance criteria will include a workflow step or manual invocation path.

---

## How to validate your changes

There is no test suite to run locally. Validation is done by running the pipeline:

1. Push your branch — the `evaluate.yml` workflow will trigger automatically if you modified `agents/`, `datasets/`, or `scripts/run_evaluation.py`.
2. Check the Actions run output for errors.
3. Confirm that new `results/run_NNN.json` and `experiments/run_NNN.json` files were committed back to the branch.
4. Check that both files match the schemas for their version (see File format specifications above).

For tasks that add new scripts, verify each Acceptance criterion by running the script directly with the exact command given in the task.
