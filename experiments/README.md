# Experiments

This directory stores structured experiment log entries produced by the evaluation pipeline.

Every evaluation run produces two output files:

| Directory | File | Content |
|-----------|------|---------|
| `results/` | `run_NNN.json` | Raw agent responses per scenario |
| `experiments/` | `run_NNN.json` | Structured log: metadata, scores, aggregate pass rate |

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
      "score": "pass"
    }
  ],
  "pass_rate": 1.0
}
```

| Field | Type | Description |
|-------|------|-------------|
| `run` | string | Run identifier matching the corresponding `results/run_NNN.json` |
| `timestamp` | string | ISO 8601 UTC timestamp of the run |
| `agent` | string | Path to the agent instruction file used |
| `dataset` | string | Path to the dataset file used |
| `model` | string | Model identifier used for evaluation |
| `results` | array | Per-scenario score records |
| `results[].scenario_id` | string | Scenario `id` from the dataset |
| `results[].score` | string | `pass`, `fail`, or `partial` |
| `pass_rate` | float | Fraction of scenarios scored `pass` (0.0–1.0) |

## Summary Reports

Once Task 007 is implemented, this directory will also contain:

- `summary.json` — machine-readable aggregate of all run pass rates over time
- `summary.md` — human-readable Markdown table of the same data

## File Naming

Experiment log files are named to match their corresponding results file:

```
experiments/run_001.json  ←→  results/run_001.json
experiments/run_002.json  ←→  results/run_002.json
```

## Archival

See `lab/backlog.md` Task 009 and `lab/adr/` for the results archival strategy once it is defined.
