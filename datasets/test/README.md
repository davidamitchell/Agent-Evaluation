# Test Split

This directory contains **held-out test datasets** — scenarios reserved for final evaluation of agent instructions.

Scenarios in `test/` must **not** be used during instruction development or mutation. They measure generalisation: whether the agent behaves correctly on situations it has not been optimised against.

## Files

| File | Description |
|------|-------------|
| `example_test.json` | Five held-out test scenarios covering hardcoded credentials, TLS bypass, phishing, health record logging, and unsafe eval() usage |

## Dataset Schema

Each scenario follows the standard dataset schema documented in `datasets/README.md`.

Required fields: `id`, `scenario`, `expected_behavior`.  
Optional: `variants` — semantically equivalent restatements evaluated independently.

## Usage

To run the evaluation pipeline against the test split:

```bash
python scripts/run_evaluation.py \
  --dataset datasets/test/example_test.json \
  --agent agents/default_agent.md \
  --output-dir results \
  --experiments-dir experiments
```

Or via GitHub Actions (see `.github/workflows/evaluate.yml`):

```
split: test
```

## Related

- `datasets/train/README.md` — training split
- `datasets/README.md` — full dataset schema and conventions
- `lab/backlog.md` Task 005 — train/test split rationale
