# Agents

This directory contains instruction sets that define the behaviour of specific AI agents.

## What is an Agent?

An agent in this repository is a set of written instructions that guides an AI model's behaviour during evaluation. Each agent file describes:

- The purpose and role of the agent
- Behavioural expectations and constraints
- Rules and policies the agent must follow
- Requirements for safe and compliant responses

## Agent Files

| File | Description |
|------|-------------|
| `default_agent.md` | The baseline instruction set used by the evaluation pipeline |
| `example_agent.md` | A simple example agent used for testing and demonstration |

## Creating a New Agent

1. Create a new Markdown file in this directory (e.g., `my_agent.md`).
2. Describe the agent's purpose, rules, and constraints clearly.
3. Reference the agent file when running `scripts/run_evaluation.py`.

## Versioning

Agents are version-controlled alongside datasets and results. Every change to an agent instruction set should be traceable to an evaluation outcome. See `lab/backlog.md` for planned improvements to the traceability system.
