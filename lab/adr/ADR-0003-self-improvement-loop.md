# ADR-0003: Self-Improving Evaluation Loop Architecture

**Date:** 2026-03-07  
**Status:** Accepted

---

## Context

The repository's long-term goal is an automated loop: evaluate → identify failures → mutate instructions → re-evaluate. The first generation of this loop (Tasks 000–012) built the foundational plumbing: an evaluation runner, a scorer, an experiment logger, dataset splits, paraphrase generation, adversarial probes, and an instruction mutation script.

Concurrent research (2026-03-05: *General Agent Optimization Framework*) established the canonical architecture for self-improving agent evaluation loops and surfaced two critical failure modes not yet addressed in this repository:

1. **Instruction drift** — iterative mutation accumulates rules without removing redundant ones; prompt length grows; recall accuracy degrades through the "lost in the middle" effect and context rot (Chroma Research, 2025).
2. **Dataset ossification** — when the outer-loop variation set (evaluation datasets) consistently produces near-perfect pass rates, it stops discovering agent failures and functions as a pure regression suite rather than an exploration tool.

Both failure modes are slow-acting: they degrade quality over multiple optimization cycles rather than causing an immediate, visible failure. Without explicit detection mechanisms, they will only be discovered after significant degradation has accumulated.

The research surveyed four automated prompt optimization frameworks (APE, OPRO, TextGrad, DSPy) and concluded that DSPy is the most principled foundation for a self-improving loop because it is the only framework providing native support for both inner-loop instruction search and outer-loop metric-based evaluation. However, DSPy requires a `pip install dspy` dependency, typically ~370 LLM API calls per optimization run, and significant pipeline restructuring — all of which exceed this repository's current constraints (GitHub-native, Python stdlib only, no permanent filesystem, limited token budget).

A decision was needed about how to extend the self-improvement loop within the existing constraints rather than adopting DSPy wholesale.

---

## Decision

The self-improvement loop is extended in four targeted steps that add the missing detection and feedback mechanisms without introducing new external dependencies or restructuring the pipeline:

### 1. Instruction drift detection (Task 013)

A new script (`scripts/check_drift.py`) measures the line and word count of a candidate agent file relative to the baseline. A candidate that exceeds 20% growth triggers a non-zero exit code, surfaced in the PR evaluation workflow as a gating check. This is the lightweight analogue of DSPy's Brevity Penalty objective term.

**Rationale:** Context rot is an empirically grounded risk. The 20% threshold is conservative — any larger growth should trigger a mandatory structural review, not an automatic block.

### 2. Score regression gate (Task 014)

The existing multi-agent comparison script (`scripts/compare_agents.py`) is extended to detect per-scenario regressions: any scenario that scored `pass` in the baseline that now scores `partial` or `fail`. The comparison exits non-zero on any regression, preventing a candidate that improves headline pass rate while regressing on previously passing cases from being silently merged.

**Rationale:** Net pass rate improvement is a Goodhart's Law trap. The specific regressions matter more than the aggregate.

### 3. Dataset freshness detection (Task 015)

The metrics reporter (`scripts/report.py`) is extended to compute a staleness flag per dataset: `pass_rate >= 0.95` for 3 or more consecutive runs against the same dataset. The flag appears in `experiments/summary.json` and `experiments/summary.md` as a signal that a dataset refresh cycle is warranted.

**Rationale:** This is the detection half of the outer-loop refresh problem identified in the research as "the primary open architectural question" — no surveyed framework addresses when to rotate the outer-loop test set. Detection without automatic rotation is the correct first step: human review is required before a dataset is retired.

### 4. Automated retrospective memo (Task 016)

After each evaluation run, a script (`scripts/generate_retro.py`) produces a structured Markdown memo committed to `experiments/retros/retro_NNN.md`. The memo consolidates: pass rate summary, failing scenarios, drift status, and dataset freshness — providing the feedback signal for the next mutation cycle. Memos are immutable once committed.

**Rationale:** The feedback loop is only closed if the failure signal from each run is durable and human-readable. A committed memo serves both as an audit trail and as input for a human (or future mutation agent) initiating the next instruction improvement cycle.

---

## Consequences

**Positive:**

- Instruction drift is now detectable and surfaced in PR review before it causes silent performance degradation
- Score regressions are caught at the per-scenario level rather than hidden by aggregate pass rate improvement
- Dataset ossification is detectable via the staleness flag before it renders evaluations meaningless
- The feedback loop is closed with a lightweight, GitHub-native mechanism (committed Markdown memos) that requires no new external services
- All four extensions are independently implementable and do not break existing pipeline components

**Negative / Trade-offs:**

- The 20% drift threshold is heuristic, not empirically calibrated for this codebase. It will need revision as the instruction files evolve.
- Dataset freshness detection is detection only; it does not automatically refresh or rotate datasets. Human action is required after a staleness flag, which may be delayed.
- The retro memo synthesis does not include a full LLM-driven analysis of failure patterns (that would require too many API calls for CI). The memo is structured data, not a semantic failure analysis.
- DSPy's inner-loop instruction search (MIPRO) remains out of scope. The mutation step (Task 004) continues to be a single LLM call rather than a Bayesian optimization sweep. This is intentional for the current token budget but represents a ceiling on optimization quality.

---

## What Is Explicitly Not Done

See `not-doing.md` for documented deferrals including:

- **DSPy integration** — too many API calls per run (~370), external pip dependency, GitHub Actions cost constraints
- **TextGrad** — compound-pipeline optimization not needed for single-component agents
- **LLMLingua prompt compression** — external pip dependency; vendor compression claims not independently validated

---

## References

- [General Agent Optimization Framework](https://github.com/davidamitchell/Research/blob/main/Research/completed/2026-03-05-general-agent-optimization-framework.md) (davidamitchell/Research, 2026-03-05) — survey of APE, OPRO, TextGrad, DSPy and the canonical self-improving evaluation loop architecture
- `lab/backlog.md` — Tasks 013–016 implementing this ADR
- `lab/adr/ADR-0004-instruction-drift.md` — detailed drift threshold rationale (created in Task 013)
- `lab/adr/ADR-0005-dataset-freshness.md` — detailed staleness criteria and rotation policy (created in Task 015)
- ADR-0002 — Benchmark policy collapse risk mitigation layers
- [Chroma Research (2025) — Context rot and the lost-in-the-middle effect](https://research.trychroma.com/context-rot)
- [Khattab et al. (2023) — DSPy: Compiling Declarative Language Model Calls into Self-Improving Pipelines (arXiv:2310.03714)](https://arxiv.org/abs/2310.03714)
- [Yang et al. (2024) — OPRO: Large Language Models as Optimizers (arXiv:2309.03409)](https://arxiv.org/abs/2309.03409)
- [Zhou et al. (2023) — APE: Large Language Models Are Human-Level Prompt Engineers (arXiv:2211.01910)](https://arxiv.org/abs/2211.01910)
- [Yuksekgonul et al. (2024) — TextGrad: Automatic "Differentiation" via Text (arXiv:2406.07496)](https://arxiv.org/abs/2406.07496)
