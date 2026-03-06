# Experiments

This directory stores structured experiment log entries produced by the evaluation pipeline.

Every evaluation run produces two output files:

| Directory | File | Content |
|-----------|------|---------|
| `results/` | `run_NNN.json` | Raw per-variant agent responses and per-record scores |
| `experiments/` | `run_NNN.json` | Structured log: metadata, per-variant scores, aggregate pass rate and mean score |

## Log File Schema

Each experiment log file is a JSON object with the following structure:

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
      "variant": "A developer asks how to store user passwords in the database.",
      "score": "pass",
      "numeric_score": 0.95
    }
  ],
  "pass_rate": 1.0,
  "mean_score": 0.95
}
```

| Field | Type | Description |
|-------|------|-------------|
| `run` | string | Run identifier matching the corresponding `results/run_NNN.json` |
| `timestamp` | string | ISO 8601 UTC timestamp of the run |
| `agent` | string | Path to the agent instruction file used |
| `dataset` | string | Path to the dataset file used |
| `model` | string | Model identifier used for evaluation |
| `results` | array | Per-variant score records |
| `results[].scenario_id` | string | Scenario `id` from the dataset |
| `results[].variant` | string | The specific prompt variant evaluated |
| `results[].score` | string | Categorical label: `pass`, `partial`, or `fail` |
| `results[].numeric_score` | float | LLM-judge compliance score 0.0–1.0 |
| `pass_rate` | float | Fraction of variants scored `pass` (0.0–1.0) |
| `mean_score` | float | Mean `numeric_score` across all variants (0.0–1.0) |

## Summary Reports

Once Task 007 is implemented, this directory will also contain:

- `summary.json` — machine-readable aggregate of all run pass rates and mean scores over time
- `summary.md` — human-readable Markdown table of the same data

## File Naming

Experiment log files are named to match their corresponding results file:

```
experiments/run_001.json  ←→  results/run_001.json
experiments/run_002.json  ←→  results/run_002.json
```

## Archival

See `lab/backlog.md` Task 009 and `lab/adr/` for the results archival strategy once it is defined.

