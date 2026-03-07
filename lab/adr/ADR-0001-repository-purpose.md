# ADR-0001: Repository Purpose and Two-Domain Architecture

**Date:** 2026-03-06  
**Status:** Accepted

---

## Context

This repository was created to build a controlled experimentation environment for evaluating and improving AI agent instruction sets. The system needs to:

- Define agents through instruction files
- Test those agents against scenario datasets
- Measure behaviour and compliance
- Iteratively refine the instructions based on evaluation results

The long-term objective is to develop agents that consistently follow defined organisational rules, policies, and constraints. The system functions as both an agent evaluation laboratory and a compliance testing framework for AI agents operating inside an organisation.

A structural decision was needed about how to organise the repository so that the two primary concerns — defining agents and evaluating them — are cleanly separated and independently evolvable.

---

## Decision

The repository is structured around two primary domains:

### 1. Agents (`agents/`)

This domain contains instruction sets that define the behaviour of specific AI agents. Each agent is a Markdown file that describes the agent's purpose, role, rules, and constraints. Agents are treated as versioned artifacts that can be tested and improved over time.

### 2. Evaluation Lab (`lab/`, `datasets/`, `scripts/`, `results/`, `.github/workflows/`)

This domain contains the infrastructure used to test, measure, and improve agents. It includes:

- **`datasets/`** — Scenario datasets representing organisational expectations and compliance requirements
- **`scripts/`** — The evaluation runner that loads agent instructions and datasets, submits scenarios to the model, and records outputs
- **`results/`** — Outputs produced by evaluation pipeline runs, committed back to the repository for traceability
- **`.github/workflows/`** — GitHub Actions workflows that execute the pipeline in a reproducible, GitHub-native way
- **`lab/`** — Meta-infrastructure: the backlog of planned work and ADRs documenting design decisions

This two-domain separation ensures that agent definitions and evaluation infrastructure can evolve independently while remaining version-controlled together.

---

## Consequences

**Positive:**

- Clear separation of concerns between what is being tested (agents) and how it is tested (evaluation lab)
- Both domains are version-controlled together, enabling full traceability from evaluation results back to the exact agent and dataset versions that produced them
- New agents can be added without modifying evaluation infrastructure
- New evaluation scenarios can be added without modifying agent definitions
- The structure is legible and navigable to new contributors

**Negative / Trade-offs:**

- The `lab/` directory groups meta-infrastructure (ADRs, backlog) alongside evaluation-support files; this grouping may need revisiting as the system grows
- Results are committed back to the repository, which will grow the repository size over time; a future ADR should address archival or external storage strategy

---

## References

- [adr.github.io](https://adr.github.io/) — ADR practice reference
- `lab/backlog.md` — Planned future work including scoring, optimisation loops, and metrics
