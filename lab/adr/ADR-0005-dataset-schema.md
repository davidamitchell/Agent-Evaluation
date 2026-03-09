# ADR-0005: Unified Flat Dataset Schema for All Evaluation Datasets

**Date:** 2026-03-08  
**Status:** Accepted

---

## Context

Task 003 (dataset invariance validator) introduced `datasets/invariance_example.json` using a `group_id`/`scenarios` schema, matching the original task specification.

The implementation pivoted: `check_invariance.py` reads a results file produced by `run_evaluation.py`, not the dataset directly. This made the invariance dataset schema irrelevant to the pipeline.

`run_evaluation.py` uses `id`/`scenario`/`variants` fields. `invariance_example.json` used `group_id`/`scenarios`. The mismatch caused `run_evaluation.py` to silently construct empty-string prompts, exhausting retries and producing garbage results. ([`scripts/run_evaluation.py` `load_dataset()`](../../scripts/run_evaluation.py))

All other dataset files (`datasets/example.json`, `datasets/train/example_train.json`, `datasets/test/example_test.json`) already use the flat schema. All downstream tasks (006 paraphrase generation, 011 adversarial probe, 012 synthetic generation) assume `id`/`variants`/`source_id` fields. ([`lab/backlog.md`](../backlog.md))

---

## Decision

All evaluation datasets use a single flat schema:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Unique scenario identifier |
| `scenario` | string | yes | Canonical prompt text |
| `expected_behavior` | string | yes | Correct agent behaviour description |
| `variants` | array of strings | no | Semantically equivalent restatements including the canonical `scenario` |

There is no separate invariance dataset schema. Invariance grouping is implicit: multiple variants under the same `id` form a group. `check_invariance.py` recovers the grouping from `scenario_id` in the results file, not from the dataset directly.

`invariance_example.json` was migrated from `group_id`/`scenarios` to `id`/`scenario`/`variants` to match this schema.

---

## Consequences

**Positive:**
- One schema for all datasets; no adapter code needed; all tooling works uniformly.
- `load_dataset()` can validate all datasets with one set of rules.
- Tasks 006, 011, and 012 proceed without schema branching.

**Negative:**
- The original Task 003 acceptance criteria (single `check_invariance.py --dataset ... --agent ...` call) is not met. The two-step flow (`run_evaluation.py` then `check_invariance.py`) is required.
- `invariance_example.json` required a one-time migration.

---

## References

- [`lab/backlog.md`](../backlog.md) — Task 003 (invariance validator)
- [`datasets/README.md`](../../datasets/README.md) — dataset schema documentation
- [`scripts/run_evaluation.py`](../../scripts/run_evaluation.py) — `load_dataset()` implementation
- [`scripts/check_invariance.py`](../../scripts/check_invariance.py) — invariance validator
