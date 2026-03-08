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
