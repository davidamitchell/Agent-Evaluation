# Not Doing

This file records design suggestions that have been explicitly considered and deliberately set aside. For each item, the reason is documented so that future contributors understand the boundary and do not re-propose the same approach without new context.

This is a living document. Items may be promoted to the backlog if circumstances change.

---

## Environment-variable-only script configuration

**Suggested:** Configure evaluation scripts via environment variables (e.g. `DATASET`, `AGENT`, `OUTPUT_DIR`) instead of command-line arguments.

**Decision:** Not adopting. All scripts in this repository use `argparse` for their configuration interface. This makes scripts independently runnable (`python scripts/foo.py --help` works), testable without environment setup, and consistent with the reference implementation (`run_evaluation.py`). Environment variables are reserved for secrets (`COPILOT_GITHUB_TOKEN`) only.

---

## Direct HTTP API calls for model interactions

**Suggested:** Call the GitHub Models API or GitHub Copilot API directly via `urllib.request` (or any other HTTP client) to send evaluation prompts and receive model responses.

**Decision:** Not adopting. All model interactions use the GitHub Copilot CLI (`copilot -p "..." --autopilot --allow-all`) invoked via subprocess. This keeps the pipeline free of endpoint URLs, avoids managing HTTP authentication headers, and aligns with the CLI-based pattern used in this repository's sibling projects. Scripts read `COPILOT_GITHUB_TOKEN` from the environment and pass it as `GITHUB_TOKEN` to the CLI subprocess.

---

## Timestamp-based result file naming

**Suggested:** Name result files by ISO 8601 timestamp (e.g. `run_20260306T202000.json`) rather than sequential integers.

**Decision:** Not adopting. Sequential zero-padded naming (`run_001.json`, `run_002.json`) is the established convention in this repository. It produces predictable sort order, simple human readability, and matching between `results/run_NNN.json` and `experiments/run_NNN.json`. Switching to timestamps would break the pairing convention and make chronological ordering dependent on filename parsing.

---

## External experiment tracking (MLflow, Weights & Biases, etc.)

**Suggested:** Use an established ML experiment tracking tool to store results, metrics, and artefacts.

**Decision:** Out of scope. This system is intentionally GitHub-native. All artefacts (results, experiment logs, summaries) are stored as version-controlled JSON files committed back to the repository. This preserves full traceability without external service dependencies, matches the CI/CD workflow, and keeps the system reproducible from a fresh clone. An external tracker would require credentials, network access, and account setup that are not available in every GitHub Actions environment.

---

## Replacing `run_evaluation.py` with a new standalone script

**Suggested:** Replace the existing evaluator with a new script rather than enhancing the existing one.

**Decision:** Not adopting. The existing `run_evaluation.py` is the established entry point referenced by the workflow, documentation, and backlog. Enhancements (LLM-as-judge scoring, variant support, retry logic, experiment logging) are integrated into the existing script to avoid breaking downstream references and to preserve commit history continuity.

---

## Full adversarial synthetic dataset generation (immediate)

**Suggested:** Implement an adversarial generator agent immediately as part of the baseline pipeline.

**Decision:** Deferred to Task 012. Adversarial generation is architecturally sound but requires a stable evaluation pipeline and a reviewed probe dataset schema (Task 011) before synthetic scenarios can be meaningfully staged and validated. Implementing it before the baseline is stable risks generating scenarios that cannot be reliably scored.

---

## DSPy integration for inner-loop instruction optimization

**Suggested:** Integrate DSPy (Khattab et al., 2023) as the inner-loop optimizer, using MIPRO to automatically search instruction and demonstration combinations via Bayesian optimization.

**Decision:** Deferred. DSPy requires `pip install dspy` (an external dependency outside the stdlib-only constraint), approximately 370 LLM API calls per optimization run (cost-prohibitive for CI runs), and significant pipeline restructuring. The principles it implements — systematic instruction search, explicit inner/outer loop separation — are incorporated incrementally via Tasks 013–016 using only stdlib tooling. DSPy should be reconsidered if the repository's token budget and dependency constraints are relaxed in a future phase. See `lab/adr/ADR-0003-self-improvement-loop.md`.

---

## TextGrad for compound-pipeline optimization

**Suggested:** Use TextGrad (Yuksekgonul et al., 2024) to perform "automatic differentiation via text", backpropagating natural language feedback signals through agent pipeline components.

**Decision:** Out of scope. TextGrad is designed for compound AI systems with multiple independently optimizable components (retrieval, synthesis, citation). This repository evaluates single-instruction agents. TextGrad's per-component backpropagation overhead (multiple LLM calls per update step) is not justified for single-component agents and would exceed the token budget constraint. Revisit if the architecture evolves to multi-component pipelines.

---

## LLMLingua prompt compression

**Suggested:** Apply LLMLingua to compress instruction files before each optimization cycle, achieving up to 20× compression with negligible performance loss to counter instruction drift.

**Decision:** Not adopting. LLMLingua requires a pip installation (external dependency). The vendor-claimed 20× compression ratio is not independently validated in the academic literature reviewed. Instruction drift is mitigated instead by the explicit length-check gate in `scripts/check_drift.py` (Task 013) — a simpler, dependency-free approach appropriate to the current scale of this repository's instruction files. Revisit if instruction files grow to hundreds of lines and manual pruning becomes impractical.

---

## Dynamic population of `evaluate.yml` workflow_dispatch options

**Suggested:** Automatically populate the `agent` and `dataset` dropdown options in `.github/workflows/evaluate.yml` at workflow trigger time so that newly added files appear without a manual YAML edit.

**Decision:** Not feasible. GitHub Actions `workflow_dispatch` inputs of `type: choice` require a static `options` list in the YAML. Dynamic option generation (e.g., scanning the repository at trigger time) is not supported by the platform. The maintenance burden is mitigated by a note in `.github/copilot-instructions.md` instructing contributors to update the `options` lists when adding new agent or dataset files.

---



The following suggestions from the same review are **being implemented** (not in this file because they are in scope):

- LLM-as-judge scoring → implemented in `scripts/run_evaluation.py`
- Paraphrase variants per dataset item → `datasets/example.json` and `datasets/README.md`
- Retry-safe model calls with exponential backoff → `scripts/run_evaluation.py`
- Deterministic evaluation (`temperature=0`) → `scripts/run_evaluation.py`
- Experiment metadata logging → `scripts/run_evaluation.py` writes `experiments/run_NNN.json`
- Benchmark overfitting risk documentation → `lab/adr/ADR-0002-evaluation-scoring.md` and `lab/backlog.md`
- Adversarial probe dataset → `lab/backlog.md` Task 011
- Synthetic adversarial generation → `lab/backlog.md` Task 012
- Train/test/probe dataset separation → `lab/backlog.md` Tasks 005 and 011
