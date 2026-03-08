# Changelog

All notable changes to this project will be documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Fixed
- `datasets/invariance_example.json`: migrated from dead `group_id`/`scenarios` schema to the standard flat `id`/`scenario`/`variants`/`expected_behavior` schema used by all other datasets. The old schema caused silent empty-prompt failures when passed to `run_evaluation.py`.
- `scripts/run_evaluation.py` (`load_dataset`): added schema validation that raises `ValueError` with an actionable message when a record is missing `id`, `scenario`, has an empty `scenario` or `expected_behavior`, or contains empty strings in `variants`. Prevents empty prompts from reaching the Copilot CLI.
- `scripts/run_evaluation.py` (`load_agent_instructions`): added validation that raises `ValueError` when the agent instructions file is empty.

### Added
- `tests/test_unit.py`: new tests for schema validation in `load_dataset` and empty-file detection in `load_agent_instructions`.
- `datasets/train/example_train.json`: five training scenarios (password storage, web scraping, PII logging, insecure hashing, discriminatory content) with variants, for use during instruction development.
- `datasets/test/example_test.json`: five held-out test scenarios (hardcoded credentials, TLS bypass, phishing, health record logging, unsafe eval) with variants, reserved for final agent evaluation.
- `datasets/train/README.md` and `datasets/test/README.md`: split-level documentation with schema reference and usage examples.
- `evaluate.yml`: `split` workflow input (`train` or `test`) and a "Resolve dataset path" step that maps the split to the appropriate dataset file. `dataset` input takes precedence when set; no input defaults to `datasets/example.json`.
- `datasets/README.md`: Train / Test Split section documenting the directory convention and how to use the `split` workflow input.

### Added
- `scripts/mutate_instructions.py`: instruction mutation pipeline (Task 004 / W-0005). Given a baseline agent instruction file and evaluation results with failures, produces a candidate improved instruction file (`agents/candidate_agent_vN.md`) and a mutation log (`experiments/mutation_vN.json`). Uses Copilot CLI with a brevity-constrained prompt (±10% of current instruction length). Baseline agent file is never overwritten automatically.
- `tests/test_mutate_instructions.py`: 14 unit tests for the mutation pipeline (all business logic mocked, no network calls).
- `datasets/invariance_example.json`: four invariance scenario groups (3–4 variants each) covering password storage, ToS scraping, sensitive data logging, and SQL injection
- `scripts/check_invariance.py`: standalone invariance validator — reads a results file, groups by scenario_id, reports consistent/inconsistent groups, invariance rate, and supports `--strict` mode
- `tests/test_check_invariance.py`: 44 unit tests covering all-consistent groups, inconsistent groups, single-variant groups, empty results, and strict mode
- Updated `datasets/README.md` with full invariance dataset schema and `check_invariance.py` usage guide

### Added
- Research foundation section in `README.md`: links to `davidamitchell/Research` repo, two research items (General Agent Optimization Framework, Guiding Headless Agents via LSP-Like Mechanisms), and primary source references (DSPy, OPRO, APE, TextGrad, Chroma Research context rot)
- Research repo and research item links in `lab/adr/ADR-0001-repository-purpose.md` References section
- Hyperlinked references in `lab/adr/ADR-0003-self-improvement-loop.md`: research item URLs, arXiv paper links (DSPy, OPRO, APE, TextGrad), Chroma Research context rot URL

### Changed
- Rewrote root `README.md`: added purpose, pipeline diagram, prerequisites, quick start, GitHub Actions instructions, test runner instructions, key concepts, and architecture references

### Added
- .github/copilot-instructions.md with skills, backlog, ADR, PROGRESS and CHANGELOG mandates
- .github/skills submodule pointing to davidamitchell/Skills
- .github/workflows/sync-skills.yml
- BACKLOG.md in backlog-manager skill format (ported from lab/backlog.md)
- PROGRESS.md for append-only session history
- CHANGELOG.md (this file)
- docs/adr/ with ADR index and first decision record
- Unified `Continuous Improvement & Learning` framework in copilot-instructions.md
- `Chain-of-Thought Reasoning` section in copilot-instructions.md, tailored to agent evaluation work

### Changed
- Replaced repo-specific "Continuous self-improvement" section in copilot-instructions.md with the shared unified framework
