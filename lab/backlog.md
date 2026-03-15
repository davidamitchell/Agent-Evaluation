# Evaluation Lab Backlog

This backlog is the task source for this repository.

Each task is designed to be independently executable by a Copilot coding agent. Tasks include an explicit goal, constraints, deliverables, and acceptance criteria so the agent can produce coherent, verifiable output without drifting.

Tasks are numbered sequentially. Task 000 defines the first runnable slice of the system. All subsequent tasks build on it.

## Benchmark overfitting risk

As this system evolves, the primary long-term risk is **benchmark policy collapse**: the instruction optimisation loop may learn dataset-specific heuristics rather than general policy behaviour. Mitigations already built in or planned include:

- **Paraphrase variants** (implemented in Task 000/001): dataset items carry multiple semantically equivalent phrasings; the evaluator tests all of them
- **Train/test separation** (Task 005): a held-out test set that is never used for instruction tuning
- **Adversarial probe scenarios** (Task 011): prompts designed to test robustness to adversarial or out-of-distribution input
- **Synthetic probe generation** (Task 012): an adversarial generator agent that continuously produces novel test scenarios outside the training distribution

Every task that adds evaluation scenarios should consider distribution diversity, not just coverage of known policy rules.

---

## Task 000 — First runnable slice (reference definition)

**Goal**  
Define and document the thinnest complete pipeline that proves the system works end-to-end.

**What the slice is**

```
dataset (3 scenarios)
  → agent instruction file
  → evaluation runner (scripts/run_evaluation.py)
  → agent responses recorded
  → results/run_001.json committed to repo
```

No scoring. No optimisation. Just evaluation output recorded.

**Status:** Complete. See `datasets/example.json`, `agents/default_agent.md`, `scripts/run_evaluation.py`, and `.github/workflows/evaluate.yml`.

---

## Task 001 — Evaluation scoring system

**Goal**  
Replace raw text recording with a structured compliance score for each evaluation record so that agent behaviour can be measured numerically over time.

**Constraints**
- Must not require a new external dependency; use only Python stdlib or the existing GitHub Models API call.
- Scoring must use an LLM-as-judge with `temperature=0` for deterministic, reproducible results.
- Score must be recorded in both categorical form (`pass`/`partial`/`fail`) and numeric form (0.0–1.0).

**Status:** Complete. The LLM-as-judge scorer (`judge_response` function) is implemented inside `scripts/run_evaluation.py`. Each result record contains both `score` (categorical) and `numeric_score` (float). Thresholds: `pass >= 0.7`, `partial >= 0.4`, `fail < 0.4`. See `results/README.md` for the updated schema.

---

## Task 002 — Experiment logger

**Goal**  
Write a structured experiment log entry for every evaluation run so that the history of agent behaviour is fully traceable.

**Constraints**
- Log entries must be written to `experiments/` (one file per run, named to match the corresponding `results/run_NNN.json`)
- Log format must be JSON
- Must capture: run timestamp, agent file path, dataset file path, model used, per-variant scores, aggregate pass rate, and mean numeric score

**Status:** Complete. `scripts/run_evaluation.py` writes `experiments/run_NNN.json` at the end of every run. The log includes `pass_rate` and `mean_score`. See `experiments/README.md` for the full schema.

---

## Task 003 — Dataset invariance validator

**Goal**  
Verify that the agent produces consistent expected behaviour across semantically equivalent restatements of the same scenario. This is the core property the system depends on: the agent must be robust to phrasing variation, not just the exact wording of original scenarios.

**Constraints**
- Invariance test scenarios must live in a dedicated dataset file, not mixed with primary evaluation scenarios
- The validator must report which scenario groups pass (all restatements produce equivalent behaviour) and which fail
- "Equivalent behaviour" is defined as: all restatements in a group receive the same `pass`/`fail` score

**Deliverables**
- `datasets/invariance_example.json` — example invariance dataset with at least 2 scenario groups, each containing 3 semantically equivalent restatements
- `scripts/check_invariance.py` — loads an invariance dataset, runs each scenario through the agent, scores responses, and reports pass/fail per group
- `datasets/README.md` updated to document the invariance dataset format

**Acceptance criteria**
- Running `python scripts/run_evaluation.py --dataset datasets/invariance_example.json --agent agents/default_agent.md` exits 0 and writes results to `results/run_NNN.json`
- Running `python scripts/check_invariance.py --results results/run_NNN.json` exits 0 and prints a per-group result summary
- The script exits non-zero if any invariance group has inconsistent scores, so it can be used as a CI gate
- Invariance dataset schema is documented in `datasets/README.md`

**Status:** Complete. `datasets/invariance_example.json` migrated to flat `id`/`scenario`/`variants` schema (was `group_id`/`scenarios`). `scripts/check_invariance.py` reads a `results/run_NNN.json` file produced by `run_evaluation.py`, groups by `scenario_id`, and reports consistent/inconsistent groups with an invariance rate. Includes `--strict` flag. Tests in `tests/test_check_invariance.py` (44 tests, all passing). `datasets/README.md` updated. `load_dataset` in `run_evaluation.py` now validates schema and raises `ValueError` on `group_id`/`scenarios`-shaped records.

---

## Task 004 — Instruction mutation

**Goal**  
Implement the core experiment: given a baseline agent instruction file and evaluation results showing failures, produce a candidate improved instruction file and re-evaluate it.

**Constraints**
- The mutation must be driven by evaluation output (i.e. read `results/` or `experiments/` to identify failing scenarios)
- The candidate instruction file must be written to `agents/` with a versioned name (e.g. `candidate_agent_v2.md`)
- Human review is required before a candidate replaces the baseline; the script must not overwrite `default_agent.md` automatically

**Deliverables**
- `scripts/mutate_instructions.py` — reads failing scenario results, calls the model to suggest instruction improvements, writes a candidate agent file
- `agents/` updated with the generated candidate file
- An experiment log entry (see Task 002) covering the before/after evaluation scores

**Acceptance criteria**
- Running `python scripts/mutate_instructions.py --results results/run_001.json --agent agents/default_agent.md` produces a file `agents/candidate_agent_v2.md`
- The candidate file is valid Markdown and non-empty
- A follow-up evaluation run using the candidate agent produces a result file that can be compared against the baseline run

**Status:** Complete. `scripts/mutate_instructions.py` implemented. Accepts `--agent`, `--results`, `--version`, `--output-dir`, `--experiments-dir` arguments. Extracts fail/partial records, builds a brevity-constrained mutation prompt, calls Copilot CLI, writes candidate file and mutation log. 14 unit tests in `tests/test_mutate_instructions.py`.

---

## Task 005 — Train/test dataset separation

**Goal**  
Prevent overfitting agent instructions to the evaluation scenarios used during development by introducing a held-out test split.

**Constraints**
- The split must be a dataset-level convention, not a runtime flag
- Train and test datasets must live under `datasets/train/` and `datasets/test/` respectively
- The evaluation workflow must support running against either split independently

**Deliverables**
- `datasets/train/` and `datasets/test/` directories, each with a README and an example dataset
- Updated `.github/workflows/evaluate.yml` to accept a `split` input (`train` or `test`)
- Updated `datasets/README.md` to document the split convention

**Acceptance criteria**
- Running the workflow with `split: test` evaluates only scenarios in `datasets/test/`
- Running the workflow with `split: train` evaluates only scenarios in `datasets/train/`
- Existing `datasets/example.json` continues to work as a standalone dataset

**Status:** Complete. `datasets/train/example_train.json` (5 scenarios) and `datasets/test/example_test.json` (5 held-out scenarios) created, each with a README. `evaluate.yml` now accepts a `split` input (`train`/`test`) resolved in a "Resolve dataset path" step before the evaluation run. `datasets/README.md` updated with the split convention.

---

## Task 006 — Paraphrase scenario generation

**Goal**  
Automatically generate paraphrased variants of existing evaluation scenarios to build up the invariance dataset and increase overall dataset diversity.

**Constraints**
- Must use the GitHub Models API (no new external services)
- Generated scenarios must be written to a new dataset file, not overwrite the source dataset
- Each generated scenario must be linked back to its source scenario via a `source_id` field

**Deliverables**
- `scripts/generate_paraphrases.py` — takes a dataset file, calls the model to produce N paraphrases per scenario, writes output to a new dataset file
- Example generated dataset committed to `datasets/`

**Acceptance criteria**
- Running `python scripts/generate_paraphrases.py --dataset datasets/example.json --count 3 --output datasets/example_paraphrased.json` produces a valid dataset file
- Each scenario in the output contains a `source_id` field matching the original scenario's `id`
- The generated dataset passes validation (valid JSON, correct schema)

---

## Task 007 — Metrics collection and reporting

**Goal**  
Aggregate evaluation scores across runs and produce a summary report showing trends over time.

**Constraints**
- Must read from `experiments/` log files (see Task 002), not raw `results/`
- Report must be committed to the repository alongside results
- Report format must be both human-readable (Markdown) and machine-readable (JSON)

**Deliverables**
- `scripts/report.py` — reads all experiment log files and produces `experiments/summary.md` and `experiments/summary.json`
- A GitHub Actions step added to `.github/workflows/evaluate.yml` that runs `report.py` after each evaluation run
- `experiments/README.md` updated to document the summary report format

**Acceptance criteria**
- Running `python scripts/report.py` produces `experiments/summary.md` with a table of run scores over time
- The summary JSON contains an array of `{ run, pass_rate, mean_score, timestamp }` records
- The workflow step commits the updated summary alongside new results

---

## Task 008 — Multi-agent comparison

**Goal**  
Run the same dataset against multiple agent instruction files in a single workflow execution and produce a side-by-side comparison.

**Constraints**
- Workflow must accept a comma-separated list of agent file paths as input
- Each agent must produce its own results file and experiment log entry
- The comparison output must be a single Markdown table committed to `experiments/`

**Deliverables**
- Updated `.github/workflows/evaluate.yml` to accept multiple agent paths
- `scripts/compare_agents.py` — reads experiment log entries for a given run and produces a comparison table
- Example comparison output committed to `experiments/`

**Acceptance criteria**
- Running the workflow with two agent files produces two result files and one comparison table
- The comparison table shows per-scenario and aggregate scores for each agent side by side

---

## Task 009 — Results archival strategy

**Goal**  
Define and implement a strategy for managing the growth of `results/` and `experiments/` as evaluation runs accumulate.

**Constraints**
- The chosen strategy must not break traceability (every run must remain recoverable)
- Must be documented as an ADR

**Deliverables**
- `lab/adr/ADR-0003-results-archival.md`
- Implementation of the chosen archival approach (e.g. archival branch, GitHub Releases attachment, or external store)
- Updated `results/README.md` and `experiments/README.md` to document the archival policy

**Acceptance criteria**
- ADR is complete with context, decision, and consequences sections
- Archival can be triggered manually via a GitHub Actions workflow
- Archived runs remain accessible and linked from the repository

---

## Task 010 — Human review workflow

**Goal**  
Require human review and approval before any change to an agent instruction file is merged, with evaluation results surfaced automatically in the pull request.

**Constraints**
- Must use native GitHub pull request review features (branch protection, required reviewers)
- Evaluation results for the candidate agent must be posted as a PR comment automatically

**Deliverables**
- `.github/workflows/evaluate_on_pr.yml` — runs evaluation on any PR that modifies `agents/**` and posts a results summary comment
- `CODEOWNERS` or branch protection configuration documented in a new ADR
- `lab/adr/ADR-0004-human-review-gate.md`

**Acceptance criteria**
- Opening a PR that modifies an agent file triggers the evaluation workflow automatically
- A comment is posted on the PR with the evaluation summary before merge is permitted
- The ADR documents the review gate rationale and configuration

---

## Task 011 — Adversarial probe dataset

**Goal**  
Build a probe dataset containing adversarial scenarios designed to test whether the agent's compliance holds under injection attempts, ambiguity, and out-of-distribution prompts. This directly addresses the benchmark policy collapse risk described above.

**Constraints**
- Probe dataset must never be used for instruction tuning; it is a held-out stress test only
- Must include three prompt categories: (1) adversarial intent ("ignore previous policy"), (2) ambiguous operational context, (3) compositional policy cases
- Dataset must live at `datasets/probe/` separate from train/test splits

**Deliverables**
- `datasets/probe/adversarial_probe.json` — at least 6 scenarios across the three categories
- `datasets/probe/README.md` — explains the probe dataset purpose and category definitions
- `datasets/README.md` updated to document the probe directory

**Acceptance criteria**
- Running the evaluation pipeline against the probe dataset produces meaningful scores
- At least one scenario in each category is present
- The probe dataset is NOT referenced by the main `evaluate.yml` training workflow (it runs separately or manually)

**Status:** Complete. `datasets/probe/adversarial_probe.json` created with 8 scenarios across three categories: adversarial intent (3 scenarios including direct injection and system impersonation), ambiguous operational context (3 scenarios including role claims and inline authorisation), and compositional policy cases (2 scenarios covering code review injection and article summarisation injection). `datasets/probe/README.md` added. `datasets/README.md` updated with probe directory documentation. `evaluate.yml` updated to include the probe dataset in the workflow dropdown.

---

## Task 012 — Synthetic adversarial scenario generation

**Goal**  
Use an adversarial generator agent to automatically produce novel evaluation scenarios outside the training distribution, preventing the evaluator from ossifying around known scenario patterns.

**Constraints**
- Generator must use the GitHub Models API (no external services)
- Generated scenarios must be reviewed before use in evaluation (output to a staging file, not directly to a live dataset)
- Must not overwrite existing datasets

**Deliverables**
- `scripts/generate_adversarial.py` — calls the model with an adversarial-generation prompt to produce novel compliance test scenarios
- Staging output file `datasets/probe/adversarial_staged.json` (for human review before promotion)
- `datasets/probe/README.md` updated to document the staging and review workflow

**Acceptance criteria**
- Running `python scripts/generate_adversarial.py --count 5 --output datasets/probe/adversarial_staged.json` produces 5 novel scenarios in valid JSON
- Each generated scenario contains `id`, `scenario`, and `expected_behavior` fields
- The script exits non-zero if the model returns invalid JSON

---

## Task 013 — Instruction drift detection

**Goal**  
Track the length and structural complexity of agent instruction files across candidate versions and flag when a candidate has grown beyond an acceptable threshold relative to the baseline. This prevents instruction drift: a known failure mode where iterative rule additions lengthen prompts, causing recall degradation through context rot.

**Background**  
Research on automated prompt optimization (DSPy MIPRO, APE, OPRO) identifies instruction length growth as a primary reliability risk in any self-improvement loop. The "lost in the middle" effect and context rot (Chroma Research, 2025) demonstrate that recall accuracy degrades non-uniformly as prompts grow longer. The mitigation is a length-aware check on every candidate before promotion.

**Constraints**
- Must use only Python stdlib; no new pip dependencies
- Measure length in lines and word count (not tokens — no tokenizer dependency)
- The growth threshold is 20% above the baseline by default, configurable via `--threshold`
- Must integrate as a step in the PR evaluation workflow (Task 010)

**Deliverables**
- `scripts/check_drift.py` — reads two agent files (baseline and candidate), reports line count, word count, and percentage change; exits non-zero if growth exceeds threshold
- A step added to `.github/workflows/evaluate_on_pr.yml` to run `check_drift.py` and include the result in the PR comment
- `lab/adr/ADR-0004-instruction-drift.md` documenting the drift policy, threshold rationale, and mitigation approach
- Unit tests in `tests/test_unit.py` covering: baseline equals candidate (no drift), candidate within threshold, candidate exceeds threshold

**Acceptance criteria**
- `python scripts/check_drift.py --baseline agents/default_agent.md --candidate agents/candidate_agent_v2.md` prints a structured drift report and exits non-zero if growth > 20%
- `python scripts/check_drift.py --help` prints usage
- PR comment (from Task 010) includes drift metrics (line delta, word delta, growth %) alongside evaluation scores
- All new unit tests pass

---

## Task 014 — Score regression gate

**Goal**  
In PR evaluation, explicitly detect and flag any scenario that previously scored `pass` in the baseline agent but scores `partial` or `fail` in the candidate. A net improvement in pass rate is not sufficient to approve a candidate if it regresses on previously passing cases.

**Background**  
The research on automated instruction optimization (APE, OPRO, DSPy) identifies Goodhart's Law as the central risk: optimising a metric causes the metric to cease being a good proxy. Specifically, a candidate that gains passes on new scenarios while losing passes on old ones may have overfit to the failing scenarios used to drive mutation. A per-scenario regression check is the direct mitigation.

**Constraints**
- Must compare against the most recent baseline experiment log in `experiments/`
- A regression is: a scenario that scored `pass` in the baseline now scores `partial` or `fail` in the candidate
- Must produce a per-scenario table (pass, regressed, improved, unchanged) — not just aggregate pass rate
- Script must exit non-zero when any regressions are detected, enabling use as a CI gate

**Deliverables**
- Updated `scripts/compare_agents.py` to detect per-scenario regressions and produce a regression table
- Regression summary added to the PR comment format from Task 010
- Unit tests in `tests/test_unit.py` covering: no regressions, regression detected, scenario in candidate but not baseline (new scenario), scenario in baseline but not candidate (removed scenario)

**Acceptance criteria**
- `python scripts/compare_agents.py --baseline experiments/run_001.json --candidate experiments/run_002.json` outputs a Markdown table with per-scenario status (pass/regressed/improved/unchanged) and exits non-zero if any regressions exist
- PR comment includes the regression table
- All new unit tests pass

---

## Task 015 — Dataset freshness detection

**Goal**  
Detect when an evaluation dataset has become "stale" — consistently achieving near-perfect pass rates across recent runs — and surface a freshness flag in the summary report so that human reviewers know when to trigger a dataset refresh cycle.

**Background**  
The research on self-improving evaluation loops identifies the unresolved architectural gap: the outer-loop variation set (datasets) can itself overfit to known agent behaviour over time. A dataset where the agent always achieves pass_rate >= 0.95 for N consecutive runs is no longer discovering failures; it has become a regression test rather than an exploration tool. Detecting and signalling this condition is the first step toward structured dataset rotation.

**Constraints**
- Staleness detection must use existing experiment log data only — no new external data sources
- Staleness criterion: `pass_rate >= 0.95` for 3 or more consecutive runs against the same dataset
- Must not auto-rotate or modify datasets — detection only; human review required for action
- The staleness flag must appear in `experiments/summary.json` and `experiments/summary.md`

**Deliverables**
- Updated `scripts/report.py` to compute a per-dataset staleness flag and include it in `experiments/summary.json` and `experiments/summary.md`
- `lab/adr/ADR-0005-dataset-freshness.md` documenting the staleness criteria, rationale, and the deliberate choice not to auto-rotate
- `datasets/README.md` updated to document the staleness concept and recommended refresh actions
- Unit tests in `tests/test_unit.py` covering: fewer than 3 runs (not stale), exactly 3 runs all passing (stale), 3 runs with one below threshold (not stale), mixed datasets (only stale ones flagged)

**Acceptance criteria**
- `experiments/summary.json` includes a `datasets` object with a `stale` boolean per dataset after this task is complete
- `experiments/summary.md` includes a staleness column in the runs table
- All new unit tests pass

---

## Task 016 — Automated self-improvement retrospective

**Goal**  
After each evaluation run, generate a structured retrospective memo that summarises what failed, what improved, drift status, and dataset freshness — creating a human-readable record of the self-improvement loop's state at each cycle. This closes the automated feedback loop described in the self-improving evaluation loop architecture.

**Background**  
The research framework (DSPy / Meta-Optimizer architecture) requires a feedback signal from each evaluation cycle to the next: classify failures, identify patterns, surface improvement candidates. This task implements the lightweight GitHub-native version of that signal: a committed Markdown memo that a human reviewer (or a future mutation agent) can consume to drive the next instruction improvement cycle.

**Constraints**
- The retro script must use the GitHub Copilot CLI for its LLM synthesis call (if any); no direct HTTP calls
- Each memo must be committed as `experiments/retros/retro_NNN.md` (matching run number); never overwrite an existing memo
- The retro must not consume excessive tokens: the LLM call (if used) must be a single focused prompt, not a full re-evaluation
- If no LLM call is needed (all content is derived from structured data), the script should work without credentials

**Deliverables**
- `scripts/generate_retro.py` — reads an experiment log (`experiments/run_NNN.json`) and optionally the drift report and freshness flag; writes a structured Markdown memo to `experiments/retros/retro_NNN.md`
- `experiments/retros/` directory with a `README.md` explaining the memo format
- A GitHub Actions step added to `evaluate.yml` to generate the retro after each run and commit it
- Unit tests in `tests/test_unit.py` covering: memo is created with correct filename, memo contains all required sections, existing memo is not overwritten

**Memo format** (`experiments/retros/retro_NNN.md`)

```markdown
# Retrospective — run_NNN — <timestamp>

## Run summary
- Agent: <agent file>
- Dataset: <dataset file>
- Pass rate: <pass_rate>
- Mean score: <mean_score>

## Failures
| Scenario | Score | Expected |
|----------|-------|----------|
| ...      | ...   | ...      |

## Drift status
- Baseline: <word count>
- Candidate: <word count>
- Growth: <pct>% — <within threshold / EXCEEDS THRESHOLD>

## Dataset freshness
- <dataset>: <stale / fresh> (<N consecutive high-pass-rate runs>)

## Recommended next actions
- [ ] (auto-generated or human-filled)
```

**Acceptance criteria**
- `python scripts/generate_retro.py --experiment experiments/run_001.json --output experiments/retros/retro_001.md` produces a well-formed Markdown file at the specified path
- The script exits non-zero if the output file already exists (immutability rule)
- The evaluate workflow commits `experiments/retros/retro_NNN.md` alongside `results/run_NNN.json` and `experiments/run_NNN.json`
- All new unit tests pass

---

## Task 017 — Prompt injection testing dataset

**Goal**
Build a dedicated dataset that simulates prompt injection attacks sourced from untrusted and trusted external content — reproducing the class of failure where an agent processes external data and that data contains embedded instructions designed to override agent policy.

**Background**
Agents increasingly consume content from external sources: web pages, documents, emails, issue trackers, database records. Any of these can carry adversarial instructions directed at the agent. An agent that cannot distinguish between legitimate instructions (from its configuration) and injected instructions (from processed content) is vulnerable to indirect prompt injection. This task extends the probe dataset to cover this specific class of attack with realistic scenarios drawn from plausible operational contexts.

**Constraints**
- The dataset must live at `datasets/probe/` and follow the standard flat `id`/`scenario`/`expected_behavior` schema
- Scenarios must simulate realistic injection vectors: pasted documents, web content, code, emails, API responses, database records
- The dataset must NOT be used for instruction tuning — it is a held-out stress test only
- At least two scenarios must simulate injection via a **trusted** source (the source is legitimate but the content has been compromised)
- At least two scenarios must simulate injection via an **untrusted** source (web content, user-supplied documents)
- Scenarios must cover both direct injection (instructions addressed to the AI) and indirect injection (instructions embedded in data the AI is asked to process)

**Deliverables**
- `datasets/probe/prompt_injection.json` — at least 8 scenarios across two vectors (trusted source, untrusted source) and two injection styles (direct, indirect)
- `datasets/probe/README.md` updated to document the new dataset, its vectors, and its relationship to `adversarial_probe.json`
- `datasets/README.md` updated to include the new file in the Files table

**Acceptance criteria**
- Running `python scripts/run_evaluation.py --dataset datasets/probe/prompt_injection.json --agent agents/default_agent.md --output-dir results --experiments-dir experiments` completes without error and produces a results file
- At least two scenarios test injection from a trusted source
- At least two scenarios test injection from an untrusted source
- At least two scenarios use indirect injection (instructions embedded in data being processed, not addressed directly to the agent)
- `datasets/probe/adversarial_probe.json` added as an option in `evaluate.yml` (if not already present)
- `datasets/probe/prompt_injection.json` added as an option in `evaluate.yml`
- `datasets/probe/README.md` documents both probe datasets and their relationship

