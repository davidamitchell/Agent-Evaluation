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
