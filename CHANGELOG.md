# Changelog

All notable changes to this project will be documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
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
