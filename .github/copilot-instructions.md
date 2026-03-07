# Copilot Instructions

This file tells GitHub Copilot how to work in this repository. Read it fully before making any change.

---

## Skills

Skills are available at `.github/skills/`. Key skills: `backlog-manager`, `research`, `technical-writer`, `code-review`, `strategy-author`, `decisions`.

---

## Backlog mandate

The backlog is `BACKLOG.md` at the repo root. Use the `backlog-manager` skill from `.github/skills/backlog-manager/SKILL.md`. Read it at the start of every session.

---

## ADR mandate

Every non-trivial architectural or design decision must be recorded as an ADR in `docs/adr/`. Use the `decisions` skill from `.github/skills/decisions/SKILL.md`. Format is MADR. Files named `docs/adr/NNNN-short-title.md`.

---

## PROGRESS.md mandate

Append a dated entry to `PROGRESS.md` after every meaningful session or PR. Never edit old entries — append only. Format: `## YYYY-MM-DD` then what changed and why. Append-only prevents merge conflicts.

---

## CHANGELOG.md mandate

Record every user-facing change in `CHANGELOG.md`. Follow Keep-a-Changelog 1.0.0. New entries go under `## [Unreleased]` at the top.

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

tests/
  __init__.py               # Package marker
  conftest.py               # Path setup and shared fixtures
  test_unit.py              # Unit tests — all business logic, mocked network
  test_integration.py       # Integration tests — live CLI, real filesystem

pytest.ini                  # pytest marker definitions

lab/
  backlog.md                # Task list — the source of truth for planned work
  adr/                      # Architecture Decision Records

.github/
  workflows/
    evaluate.yml            # On-demand evaluation workflow (workflow_dispatch only)
    ci.yml                  # CI pipeline: unit + integration tests on every push/PR
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

## Testing standards — mandatory on every PR

This project ships to `main` on merge. That confidence comes entirely from the
test suite. Every change must leave the suite green.

### Test runner and setup

- **Framework**: `pytest`. Run locally with `pytest tests/ -m "not integration" -v`.
- **Setup lives in the CI workflow** (`.github/workflows/ci.yml`), not in test
  files. `pip install pytest` is a workflow step, not a `requirements.txt` entry.
- Unit tests: `tests/test_unit.py`. Integration tests: `tests/test_integration.py`.

### Testing pyramid

Apply three layers — unit → integration → (manual / watch-only on real evaluation runs).

| Layer | What to test | Credentials needed |
|-------|-------------|-------------------|
| **Unit** | All business logic; every branch, boundary, and failure path | None — mock every network call |
| **Integration** | Live external services: real Copilot CLI call, real filesystem write, full pipeline round-trip | `COPILOT_GITHUB_TOKEN` required |

Do not skip layers. A bug found at unit level is 100× cheaper to fix than one
found in production.

### Unit tests

- **Mock every network call.** The only real I/O allowed is `tmp_path` (pytest
  built-in). Use `unittest.mock.patch` — no extra test libraries needed.
- **Test behaviour, not implementation.** Assert on return values and
  observable side-effects; do not assert on internal call order.
- **Cover every public function.** Every function in `scripts/` must have at
  least one happy-path test, one sad-path test, and explicit boundary tests
  wherever thresholds appear.
- **Naming convention**: `test_<unit>_<condition>_<expected_outcome>`
  (e.g. `test_judge_response_score_above_1_clamped_to_1`).
- **Test isolation**: tests must be independent and idempotent regardless of
  run order. Use `patch.dict(os.environ, ...)` to manipulate env vars without
  leaking state across tests.

### Integration tests

- Mark every integration test with `@pytest.mark.integration`.
- Skip automatically when credentials are absent:
  ```python
  @pytest.mark.skipif(not os.getenv("COPILOT_GITHUB_TOKEN"), reason="COPILOT_GITHUB_TOKEN not set")
  ```
- Must prove **connectivity** (CLI installed, token authenticates) and at least
  one **simple pathway** (minimal end-to-end scenario produces valid output files).
- **The absence of `COPILOT_GITHUB_TOKEN` in CI is a blocker on shipping, not
  a reason to fall back to unit tests alone.** Expose the secret in `ci.yml`
  so the integration job actually runs.

### External service configuration — testing pyramid

Any code that wires up an external service (Copilot CLI, API client, MCP server)
is production code and must be proven correct at every layer:

| Layer | What to prove | How |
|-------|--------------|-----|
| **Unit** | Config is well-formed: JSON valid, required fields present, env var names correct | Mock the service; assert the config object |
| **Integration** | The configuration actually connects — real credential, real service | `@pytest.mark.integration` + `skipif` |

A config change that adds or modifies an external service entry is **not done**
until the integration test exists and passes in CI.

### TDD workflow — mandatory for bug fixes

1. **Write a failing test** that reproduces the bug exactly. Run it; confirm red.
2. **Fix the code.** Run the test; confirm green.
3. **Run the full unit suite.** Confirm no regressions.

This red-green cycle is permanent proof that the bug cannot silently return.

### CI gate

`.github/workflows/ci.yml` enforces:

1. **`unit`** — runs on every push/PR; no credentials needed; must pass first.
2. **`integration`** — runs after `unit` succeeds; requires `COPILOT_GITHUB_TOKEN`.

`main` is only safe to merge when both jobs are green (or `integration` is
skipped because the credential is absent in a fork — forks are expected; missing
credentials in the main repo is a blocker).

---

## Pipeline execution

The **CI pipeline** runs in `.github/workflows/ci.yml`, triggered on every push
and pull request. It runs unit tests first (no credentials required), then
integration tests (requires `COPILOT_GITHUB_TOKEN` secret).

The **evaluation pipeline** runs in `.github/workflows/evaluate.yml`, triggered
**on demand only** via `workflow_dispatch`. It is not triggered automatically on
push. Trigger it manually from the Actions tab to score an agent against a dataset.

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

Run the unit test suite locally before pushing:

```bash
pip install pytest
pytest tests/ -m "not integration" -v
```

All 49+ unit tests must pass. No credentials required.

For evaluation pipeline changes, trigger the on-demand workflow manually:

1. Go to the **Actions** tab → **Evaluate Agent** → **Run workflow**.
2. Check the run output for errors.
3. Confirm that new `results/run_NNN.json` and `experiments/run_NNN.json` files
   were committed back to the branch.
4. Check that both files match the schemas in [File format specifications](#file-format-specifications).
