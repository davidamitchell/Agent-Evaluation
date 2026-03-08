# Backlog

---

## W-0001

status: done
created: 2026-03-07
updated: 2026-03-07

### Outcome

A thin end-to-end pipeline runs: a 3-scenario dataset is evaluated by the agent runner and responses are recorded to `results/run_001.json`.

### Context

Task 000 from lab/backlog.md. Defines the thinnest complete pipeline that proves the system works end-to-end. Dataset → agent instruction file → evaluation runner → results committed.

### Notes

Complete. See `datasets/example.json`, `agents/default_agent.md`, `scripts/run_evaluation.py`, and `.github/workflows/evaluate.yml`.

---

## W-0002

status: done
created: 2026-03-07
updated: 2026-03-07

### Outcome

Each evaluation record contains a structured compliance score (`pass`/`partial`/`fail`) and a numeric score (0.0–1.0), enabling numerical tracking of agent behaviour over time.

### Context

Task 001 from lab/backlog.md. Replaces raw text recording with a structured LLM-as-judge scoring system using `temperature=0` for deterministic results. Thresholds: pass ≥ 0.7, partial ≥ 0.4, fail < 0.4.

### Notes

Complete. `judge_response` function implemented in `scripts/run_evaluation.py`. Result records contain `score` and `numeric_score`. See `results/README.md`.

---

## W-0003

status: done
created: 2026-03-07
updated: 2026-03-07

### Outcome

A structured JSON experiment log is written to `experiments/` for every evaluation run, making agent behaviour history fully traceable.

### Context

Task 002 from lab/backlog.md. Log captures: run timestamp, agent file path, dataset file path, model used, per-variant scores, aggregate pass rate, and mean numeric score.

### Notes

Complete. `scripts/run_evaluation.py` writes `experiments/run_NNN.json`. See `experiments/README.md`.

---

## W-0004

status: done
created: 2026-03-07
updated: 2026-03-08

### Outcome

A dataset invariance validator verifies the agent produces consistent behaviour across semantically equivalent restatements of the same scenario.

### Context

Task 003 from lab/backlog.md. Invariance test scenarios live in dedicated dataset files. The validator reports which scenario groups pass (all restatements produce equivalent behaviour) and which fail.

### Notes

Complete. `datasets/invariance_example.json` (4 scenario groups, 3–4 variants each), `scripts/check_invariance.py` (reads results file, groups by scenario_id, reports consistent/inconsistent, --strict flag, exit codes 0/1/2), `tests/test_check_invariance.py` (44 tests), `datasets/README.md` updated.

---

## W-0005

status: ready
created: 2026-03-07
updated: 2026-03-07

### Outcome

Given a baseline agent instruction file and evaluation results showing failures, a candidate improved instruction file is produced and re-evaluated.

### Context

Task 004 from lab/backlog.md. Mutation is driven by evaluation output. Candidate instruction files are versioned (e.g. `candidate_agent_v2.md`). Human review required before replacing baseline.

### Notes

Deliverables: `scripts/mutate_instructions.py`, updated `agents/` with candidate file, experiment log entry.

---

## W-0006

status: ready
created: 2026-03-07
updated: 2026-03-07

### Outcome

A held-out test split prevents overfitting agent instructions to evaluation scenarios used during development.

### Context

Task 005 from lab/backlog.md. Train and test datasets live under `datasets/train/` and `datasets/test/` respectively. Evaluation workflow supports running against either split independently.

### Notes

Deliverables: `datasets/train/`, `datasets/test/` with READMEs and example datasets, updated `evaluate.yml`, updated `datasets/README.md`.

---

## W-0007

status: ready
created: 2026-03-07
updated: 2026-03-07

### Outcome

Paraphrased variants of existing evaluation scenarios are automatically generated to build up the invariance dataset and increase dataset diversity.

### Context

Task 006 from lab/backlog.md. Uses GitHub Models API. Generated scenarios written to a new dataset file with `source_id` field linking back to the source scenario.

### Notes

Deliverables: `scripts/generate_paraphrases.py`, example generated dataset in `datasets/`.

---

## W-0008

status: ready
created: 2026-03-07
updated: 2026-03-07

### Outcome

Evaluation scores are aggregated across runs and a summary report shows trends over time, in both Markdown and JSON formats.

### Context

Task 007 from lab/backlog.md. Reads from `experiments/` log files. Report is committed alongside results. Summary JSON contains `{ run, pass_rate, mean_score, timestamp }` records.

### Notes

Deliverables: `scripts/report.py`, GitHub Actions step in `evaluate.yml`, updated `experiments/README.md`.

---

## W-0009

status: ready
created: 2026-03-07
updated: 2026-03-07

### Outcome

The same dataset is run against multiple agent instruction files in a single workflow execution, producing a side-by-side Markdown comparison.

### Context

Task 008 from lab/backlog.md. Workflow accepts a comma-separated list of agent file paths. Each agent produces its own results file and experiment log entry.

### Notes

Deliverables: updated `evaluate.yml`, `scripts/compare_agents.py`, example comparison output in `experiments/`.

---

## W-0010

status: ready
created: 2026-03-07
updated: 2026-03-07

### Outcome

A strategy for managing growth of `results/` and `experiments/` is defined and implemented, ensuring traceability without unbounded repo size growth.

### Context

Task 009 from lab/backlog.md. Chosen strategy must not break traceability. Must be documented as an ADR.

### Notes

Deliverables: `lab/adr/ADR-0003-results-archival.md`, implementation of archival approach, updated READMEs.

---

## W-0011

status: ready
created: 2026-03-07
updated: 2026-03-07

### Outcome

Human review and approval is required before any change to an agent instruction file is merged, with evaluation results surfaced automatically in the pull request.

### Context

Task 010 from lab/backlog.md. Uses native GitHub pull request review features. Evaluation results for candidate agents are posted as PR comments automatically.

### Notes

Deliverables: `.github/workflows/evaluate_on_pr.yml`, CODEOWNERS or branch protection config, `lab/adr/ADR-0004-human-review-gate.md`.

---

## W-0012

status: needing_refinement
created: 2026-03-07
updated: 2026-03-07

### Outcome

A probe dataset of adversarial scenarios tests whether agent compliance holds under injection attempts, ambiguity, and out-of-distribution prompts.

### Context

Task 011 from lab/backlog.md. Probe dataset never used for instruction tuning — held-out stress test only. Three categories: adversarial intent, ambiguous operational context, compositional policy cases.

### Notes

Deliverables: `datasets/probe/adversarial_probe.json`, `datasets/probe/README.md`, updated `datasets/README.md`.

---

## W-0013

status: needing_refinement
created: 2026-03-07
updated: 2026-03-07

### Outcome

An adversarial generator agent automatically produces novel evaluation scenarios outside the training distribution.

### Context

Task 012 from lab/backlog.md. Uses GitHub Models API. Generated scenarios go to a staging file for human review before promotion to live datasets.

### Notes

Deliverables: `scripts/generate_adversarial.py`, `datasets/probe/adversarial_staged.json`, updated `datasets/probe/README.md`.

---
