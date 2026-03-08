# Changelog

All notable changes to this project will be documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- `scripts/mutate_instructions.py`: instruction mutation pipeline (Task 004 / W-0005). Given a baseline agent instruction file and evaluation results with failures, produces a candidate improved instruction file (`agents/candidate_agent_vN.md`) and a mutation log (`experiments/mutation_vN.json`). Uses Copilot CLI with a brevity-constrained prompt (±10% of current instruction length). Baseline agent file is never overwritten automatically.
- `tests/test_mutate_instructions.py`: 14 unit tests for the mutation pipeline (all business logic mocked, no network calls).
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
