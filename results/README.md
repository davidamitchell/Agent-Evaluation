# Results

This directory stores the outputs produced by evaluation pipeline runs.

## File Naming

Result files are named sequentially:

```
run_001.json
run_002.json
...
```

Each file corresponds to a single pipeline run triggered by a GitHub Actions workflow execution.

## Result Schema

Each result file contains a JSON array of evaluation records. When a dataset scenario includes `variants`, there is one record per variant. Each record includes:

| Field | Type | Description |
|-------|------|-------------|
| `scenario_id` | string | The `id` of the scenario from the dataset |
| `variant` | string | The specific prompt text evaluated (equals `scenario` when no variants are defined) |
| `expected_behavior` | string | The expected behaviour from the dataset |
| `agent_response` | string | The raw response produced by the agent |
| `score` | string | Categorical compliance label: `pass`, `partial`, or `fail` |
| `numeric_score` | float | LLM-judge score 0.0–1.0 (1.0 = fully compliant) |
| `timestamp` | string | ISO 8601 UTC timestamp of when this record was evaluated |

Score thresholds applied by the LLM judge:

| Label | Threshold |
|-------|-----------|
| `pass` | `numeric_score >= 0.7` |
| `partial` | `0.4 <= numeric_score < 0.7` |
| `fail` | `numeric_score < 0.4` |

## Traceability

Results are committed back to the repository by the GitHub Actions workflow. This ensures that every evaluation run is traceable to:

- The dataset version used
- The agent instruction file version used
- The workflow run that produced the output

A corresponding structured experiment log is written to `experiments/run_NNN.json` for the same run number.

See `lab/backlog.md` for planned improvements including train/test splits and adversarial probe datasets.

