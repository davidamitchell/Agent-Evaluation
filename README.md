# Agent-Evaluation

An experimental system for evaluating and improving AI agent instruction sets.

AI agents: see `.github/copilot-instructions.md`.

## Repository layout

```
agents/                         # Agent instruction files
datasets/                       # Evaluation datasets
scripts/                        # Evaluation pipeline scripts
results/                        # Raw agent responses per run
experiments/                    # Structured experiment logs
tests/                          # Unit and integration tests
lab/                            # Legacy backlog and ADRs (evaluation lab)
docs/
  adr/                          # Architecture Decision Records (MADR format)

BACKLOG.md                      # Root backlog (backlog-manager skill format)
PROGRESS.md                     # Append-only session history
CHANGELOG.md                    # User-facing change log (Keep a Changelog)
.github/
  copilot-instructions.md       # Instructions for AI agents working in this repo
  skills/                       # Skills submodule (davidamitchell/Skills)
  workflows/
    evaluate.yml                # On-demand evaluation workflow
    ci.yml                      # CI pipeline
    sync-skills.yml             # Weekly skills submodule update
```
