# Evaluation Lab

This directory contains the infrastructure used to test, measure, and improve AI agents.

## Contents

| Path | Description |
|------|-------------|
| `backlog.md` | Planned future tasks and improvements |
| `adr/` | Architecture Decision Records |

## Architecture Decision Records

Major design decisions are documented as Architecture Decision Records (ADRs) in the `adr/` directory. Each ADR captures context, decision, and consequences to maintain a clear audit trail of how the system has evolved.

See [adr.github.io](https://adr.github.io/) for background on ADR practice.

## Evaluation Workflow

The evaluation pipeline runs via GitHub Actions (`.github/workflows/evaluate.yml`). Each run:

1. Loads an agent instruction file from `agents/`
2. Loads a dataset of evaluation scenarios from `datasets/`
3. Submits each scenario to the model with the agent instructions as system context
4. Records outputs in `results/`
