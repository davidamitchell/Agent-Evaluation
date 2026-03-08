# Train Split

This directory contains **training datasets** — scenarios used during agent development and instruction tuning.

Scenarios in `train/` are used when iterating on agent instructions. Because these scenarios are seen during development, agents may indirectly be optimised against them. They must **not** be used as the final measure of agent quality.

## Files

| File | Description |
|------|-------------|
| `example_train.json` | Five training scenarios covering password storage, web scraping, PII logging, insecure hashing, and discriminatory content |

## Dataset Schema

Each scenario follows the standard dataset schema documented in `datasets/README.md`.

Required fields: `id`, `scenario`, `expected_behavior`.  
Optional: `variants` — semantically equivalent restatements evaluated independently.

## Usage

To run the evaluation pipeline against the training split:

```bash
python scripts/run_evaluation.py \
  --dataset datasets/train/example_train.json \
  --agent agents/default_agent.md \
  --output-dir results \
  --experiments-dir experiments
```

Or via GitHub Actions (see `.github/workflows/evaluate.yml`):

```
split: train
```

## Related

- `datasets/test/README.md` — held-out test split
- `datasets/README.md` — full dataset schema and conventions
- `lab/backlog.md` Task 005 — train/test split rationale
