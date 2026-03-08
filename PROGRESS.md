# Progress

---

## 2026-03-07

Standardisation pass: added .github/copilot-instructions.md with skills and backlog mandates. Added .github/skills submodule and sync-skills.yml. Created BACKLOG.md (porting items from lab/backlog.md). Created PROGRESS.md, CHANGELOG.md, docs/adr/. Updated README.md.

## 2026-03-07 — Remove contradictions in copilot-instructions.md

Updated `.github/copilot-instructions.md` to align with owner's personal Copilot instructions. Six targeted changes to cross-repo standard sections: added "Missing skill" row to signal table; added `CHANGELOG.md` and `remove-ai-slop` items to "Done" checklist; added action mandate after mini-retro questions; replaced hollow opener in Continuous Improvement section with direct guidance; added skills fallback note; added clarifying note to Backlog mandate to surface this repo's actual backlog path (`lab/backlog.md`). Evaluation pipeline, agent instruction format, dataset schemas, and all other repo-specific sections were not touched.

**Mini-Retro**
1. Did the process work? Yes — all six changes were surgical and straightforward.
2. What slowed down or went wrong? Nothing significant; section boundaries were well-defined.
3. What single change would prevent friction next time? Nothing — the file structure made targeted edits easy.
4. Is this a pattern? Standardisation PRs updating shared framework sections are expected; the approach (edit, don't delete) works well.


Replaced the repo-specific "Continuous self-improvement" instruction section with the shared Continuous Improvement & Learning framework. Added Chain-of-Thought Reasoning section tailored to agent evaluation work. The code-level retro feature (Task 016, generate_retro.py) is unchanged — only the instruction-level text was replaced.

**Mini-Retro**
1. Did the process work? Yes — the change was surgical: one section replaced, two new sections inserted, docs updated.
2. What slowed down or went wrong? Nothing significant; the existing section boundaries were clear.
3. What single change would prevent friction next time? Nothing to add — the pattern of "supersede, don't delete" worked well here.
4. Is this a pattern? Standardisation PRs like this are expected to recur as the shared framework evolves. The approach (replace instruction text, preserve code features) is the right class of fix.

## 2026-03-08 — Improve README

Rewrote the root `README.md` from a 30-line stub into a full project readme. Added: one-paragraph purpose summary, pipeline diagram, scoring threshold table, prerequisites, quick start commands, GitHub Actions trigger instructions, test runner instructions, annotated project structure, key concepts glossary, and architecture/decisions references. The note for AI agents is preserved at the bottom. CHANGELOG.md updated under `[Unreleased]`.

**Mini-Retro**
1. Did the process work? Yes — the existing docs (experiments/README.md, datasets/README.md, scripts/run_evaluation.py) provided accurate source material for all new sections.
2. What slowed down or went wrong? Nothing significant.
3. What single change would prevent friction next time? Nothing — the sub-directory READMEs gave sufficient detail to write accurate top-level documentation.
4. Is this a pattern? The root README being a thin stub is a common starting-point issue. Now that it is substantive, future changes to the pipeline should update it alongside the sub-directory READMEs.

## 2026-03-08 — Add research reference links

Added reference links to the davidamitchell/Research repository and the two research items that directly informed this project, plus hyperlinks to primary sources throughout the documentation.

Changes:
- `README.md`: new "Research foundation" section with links to the Research repo, both research items (General Agent Optimization Framework and Guiding Headless Agents via LSP-Like Mechanisms for Org Policy Conformance), and a primary-sources table (DSPy, OPRO, APE, TextGrad, Chroma Research context rot)
- `lab/adr/ADR-0001-repository-purpose.md`: added Research repo and research item links to References section
- `lab/adr/ADR-0003-self-improvement-loop.md`: upgraded plain-text references to hyperlinks (research item URL, arXiv papers for DSPy/OPRO/APE/TextGrad, Chroma Research context-rot URL)

**Mini-Retro**
1. Did the process work? Yes — the two research items were identified from ADR-0003 (explicit reference to General Agent Optimization Framework) and the thematic connection to policy compliance enforcement (Guiding Headless Agents). Primary source URLs were confirmed from the research item's Sources section and a web search for the Chroma context-rot paper.
2. What slowed down or went wrong? Identifying the second research item required reading multiple completed items and cross-referencing with the repo's stated purpose. The explicit reference in ADR-0003 made the first item clear; the second required judgment.
3. What single change would prevent friction next time? ADR-0001 should have included the research items in its initial References section — would have made the lineage unambiguous.
4. Is this a pattern? Missing provenance links are a recurring gap; this session closes it for the two founding research items.

## 2026-03-08 — Implement Task 004: instruction mutation (W-0005)

Implemented `scripts/mutate_instructions.py` — the instruction mutation pipeline for Task 004. Given a baseline agent instruction file and evaluation results showing failures, the script produces a candidate improved instruction file using the Copilot CLI as an LLM.

Changes:
- `scripts/mutate_instructions.py`: new script with `extract_failures`, `build_mutation_prompt`, `write_mutation_log`, `mutate`, and `main`. Accepts `--agent`, `--results`, `--version`, `--output-dir`, `--experiments-dir` CLI arguments. Includes brevity constraint (±10% character count) in mutation prompt. Never overwrites the baseline agent file. Writes candidate to `agents/candidate_agent_vN.md` and mutation log to `experiments/mutation_vN.json`.
- `tests/test_mutate_instructions.py`: 14 unit tests covering all business logic — `extract_failures` (all-pass, mixed, all-fail, empty, missing field), `build_mutation_prompt` (instruction text included, failure records included, brevity constraint present, bounds computed correctly, no-preamble instruction present), `write_mutation_log` (required fields, overwrite behaviour), and the no-failures early-exit path (LLM not called, no files written).
- `BACKLOG.md`: updated W-0005 status to `done`.
- `lab/backlog.md`: updated Task 004 status to `Complete`.
- `CHANGELOG.md`: added entry under `[Unreleased]`.

**Mini-Retro**
1. Did the process work? Yes — the existing `call_copilot_cli` pattern in `run_evaluation.py` provided a clean template. Tests passed on first run.
2. What slowed down or went wrong? Nothing significant. The constraint "copy, don't import" for `call_copilot_cli` required a brief decision on how to document the copy (added a comment in the script).
3. What single change would prevent friction next time? The backlog task spec was detailed enough that no ambiguity arose. The pattern (copy with comment) is now documented in the script.
4. Is this a pattern? Reusing `call_copilot_cli` across scripts will recur. If a third script needs it, extracting it to a shared `scripts/cli.py` module would be worth doing.
## 2026-03-08 — Task 003: Invariance validator

Implemented dataset invariance checking (Task 003 / W-0004).

Changes:
- `datasets/invariance_example.json`: four scenario groups covering password storage, ToS scraping, sensitive-data logging, and SQL injection. Three or four semantically equivalent restatements per group.
- `scripts/check_invariance.py`: standalone script that reads a `results/run_NNN.json` file, groups records by `scenario_id`, checks categorical score consistency, prints per-group pass/fail and an invariance rate summary. Supports `--strict` mode (pass ≠ partial). Exit codes: 0 (all consistent), 1 (any inconsistent), 2 (file error).
- `tests/test_check_invariance.py`: 44 unit tests covering all cases — consistent groups, inconsistent groups, single-variant groups, empty results, strict mode, CLI exit codes.
- `datasets/README.md`: added full invariance schema documentation and check_invariance.py usage guide.
- `BACKLOG.md` W-0004 status updated to `done`.
- `lab/backlog.md` Task 003 status updated to `Complete`.

**Mini-Retro**
1. Did the process work? Yes — the approach (results-file input rather than live agent runner) produced a simpler, more testable design than the original backlog deliverable spec implied.
2. What slowed down or went wrong? Nothing significant. The problem spec was clear and the existing code patterns (conftest.py sys.path injection, class-based test organisation) made test structure straightforward.
3. What single change would prevent friction next time? Nothing to add — the script conventions and test patterns in copilot-instructions.md matched actual practice.
4. Is this a pattern? No new pattern identified.

## 2026-03-08

### Task 005 — Train/test dataset separation

**What changed and why:**

Introduced a train/test split for evaluation datasets to prevent instruction overfitting.

- `datasets/train/example_train.json`: 5 training scenarios (password storage, web scraping, PII logging, insecure hashing, discriminatory content), each with 3 variants.
- `datasets/test/example_test.json`: 5 held-out test scenarios (hardcoded credentials, TLS bypass, phishing, health record logging, unsafe eval), each with 3 variants. These scenarios were not used during instruction development.
- `datasets/train/README.md` and `datasets/test/README.md`: split-level documentation with usage examples.
- `datasets/README.md`: updated Files table and added Train / Test Split section replacing the forward-reference placeholder.
- `.github/workflows/evaluate.yml`: added `split` input (`train` or `test`) and a "Resolve dataset path" step. When `dataset` is set directly it takes precedence; when `split` is set, the step maps it to the appropriate file; otherwise falls back to `datasets/example.json`.
- `lab/backlog.md`: Task 005 marked Complete.

All 107 unit tests pass.

**Mini-Retro**
1. Did the process work? Yes — the deliverables were concrete and unambiguous. Split is dataset-level (files in directories) rather than a runtime flag, which keeps the evaluation script unchanged and the convention easy to extend.
2. What slowed down or went wrong? Nothing significant. The workflow step pattern (`id: resolve_dataset` + `${{ steps.resolve_dataset.outputs.dataset }}`) required a two-step approach since GitHub Actions does not support conditional default values natively.
3. What single change would prevent friction next time? Documenting the GitHub Actions output variable pattern in copilot-instructions.md would remove ambiguity for future workflow tasks.
4. Is this a pattern? The two-step resolve-then-use pattern will likely recur in future workflow tasks that involve conditional dataset or agent selection.

## 2026-03-08 — ADR-0005: Unified flat dataset schema

Added `lab/adr/ADR-0005-dataset-schema.md` documenting the decision to use a single `id`/`scenario`/`expected_behavior`/`variants` schema for all evaluation datasets. The ADR records the context (invariance schema mismatch between `invariance_example.json` and `run_evaluation.py`), the decision, and the two-step pipeline consequence (`run_evaluation.py` → `check_invariance.py`).

Updated `.github/copilot-instructions.md`:
- Fixed ADR mandate path from `docs/adr/` to `lab/adr/` (the actual path used in this repo).
- Added explicit "ADRs are mandatory" rule listing the three triggers: schema change, CLI interface change, costly-to-reverse decision.
- Added "ADR written if any schema, interface, or architectural decision was made" to the "What Done Means" checklist.
- Updated repo layout to include `ADR-0005-dataset-schema.md` and renumbered the planned dataset-freshness ADR from 0005 to 0006.

**Mini-Retro**
1. Did the process work? Yes — the deliverable was precisely specified in the problem statement. The main work was writing the ADR in the correct format and updating the instructions file.
2. What slowed down or went wrong? The copilot-instructions.md had a stale path (`docs/adr/` instead of `lab/adr/`). This was caught while making the targeted update.
3. What single change would prevent friction next time? The fix is already in this PR: the ADR mandate now points to the correct directory.
4. Is this a pattern? Yes — copy-paste from a shared framework template left a wrong path in the instructions. The pattern of checking instructions for stale paths on every ADR-related PR would catch this early.
