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

Each result file contains a JSON array of evaluation records. Each record includes:

| Field | Type | Description |
|-------|------|-------------|
| `scenario_id` | string | The `id` of the scenario from the dataset |
| `scenario` | string | The scenario text |
| `expected_behavior` | string | The expected behaviour from the dataset |
| `agent_response` | string | The raw response produced by the agent |
| `timestamp` | string | ISO 8601 timestamp of when the evaluation ran |

## Traceability

Results are committed back to the repository by the GitHub Actions workflow. This ensures that every evaluation run is traceable to:

- The dataset version used
- The agent instruction file version used
- The workflow run that produced the output

See `lab/backlog.md` for planned improvements including automated scoring and a closed-loop optimisation system.
