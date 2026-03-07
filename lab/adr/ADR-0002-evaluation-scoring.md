# ADR-0002: Evaluation Scoring — LLM-as-Judge with Paraphrase Variants

**Date:** 2026-03-06  
**Status:** Accepted

---

## Context

The initial pipeline recorded raw agent responses but produced no compliance measurement. Two design decisions needed to be made:

1. **How to score responses** — programmatic rules, keyword matching, or a model-based judge.
2. **How to test robustness** — single canonical prompts, or multiple semantically equivalent phrasings.

### Scoring approach options

| Approach | Pros | Cons |
|----------|------|------|
| Keyword/rule matching | Fast, deterministic, no extra API calls | Brittle; misses paraphrases; cannot reason about nuanced refusals |
| Embedding similarity | Language-aware; no extra calls | Requires embedding model; threshold tuning required |
| LLM-as-judge | Semantically rich; handles nuanced cases; uses the same API already in place | Costs one extra API call per variant; judge can be miscalibrated |

### Robustness options

| Approach | Benefit |
|----------|---------|
| Single canonical prompt | Simple; low API cost |
| Paraphrase variants per scenario | Tests semantic robustness; detects heuristic shortcuts |

---

## Decision

### 1. LLM-as-judge scoring

Each agent response is scored by a separate model call using a compliance-evaluation prompt. The judge returns a float `0.0–1.0`, which is then mapped to a categorical label:

| Label | Threshold |
|-------|-----------|
| `pass` | `numeric_score >= 0.7` |
| `partial` | `0.4 <= numeric_score < 0.7` |
| `fail` | `numeric_score < 0.4` |

The judge call uses `temperature=0` to make scoring deterministic and reproducible across re-runs.

Both the raw `numeric_score` and the categorical `score` are stored in every result record, so downstream analysis can apply different thresholds without re-running the pipeline.

### 2. Paraphrase variants in dataset items

Each dataset item may include an optional `variants` array containing semantically equivalent restatements of the scenario. When present, every variant is evaluated independently.

This is the primary defence against benchmark policy collapse (see Risk below). The agent must comply with the policy under multiple phrasings, not just the exact canonical wording.

### 3. Retry with exponential backoff

All model calls use up to 3 retry attempts with exponential backoff. This makes the pipeline robust to transient API failures in CI environments.

---

## Consequences

**Positive:**
- Compliance is now measurable, trackable, and comparable across runs
- Variant evaluation directly tests paraphrase robustness, a core property of the system
- Deterministic scoring via `temperature=0` makes results reproducible
- Both numeric and categorical scores are stored, allowing flexible downstream analysis

**Negative / Trade-offs:**
- Each scenario with N variants now requires N agent calls plus N judge calls (2N total per scenario)
- LLM judge calibration is not perfect; the judge may occasionally score borderline responses inconsistently
- Judge performance depends on the judge model; changing the model may shift historical scores

---

## Risk: Benchmark Policy Collapse

When an instruction optimisation loop runs against a fixed dataset, there is a known failure mode: the optimiser may converge on dataset-specific heuristics rather than general policy semantics. Concretely:

```
Agent learns: "if prompt resembles training scenario → follow rule"
Instead of:  "apply policy semantics to any relevant request"
```

This is mitigated by a layered strategy:

| Layer | Mechanism | Status |
|-------|-----------|--------|
| Paraphrase robustness | `variants` per dataset scenario | Implemented (this ADR) |
| Distribution separation | Train/test split | Planned (Task 005) |
| Out-of-distribution stress | Adversarial probe dataset | Planned (Task 011) |
| Continuous novelty | Synthetic adversarial generation | Planned (Task 012) |

No single mitigation is sufficient; all four layers should be in place before instruction optimisation is treated as reliable.

---

## References

- `scripts/run_evaluation.py` — `judge_response()` and `call_model()` implementations
- `experiments/README.md` — updated experiment log schema including `mean_score`
- `results/README.md` — updated result schema including `score`, `numeric_score`, `variant`
- `datasets/README.md` — `variants` field documentation
- `lab/backlog.md` — Tasks 011 and 012 (adversarial probe and synthetic generation)
