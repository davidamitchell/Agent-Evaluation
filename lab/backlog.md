# Evaluation Lab Backlog

This document tracks planned future tasks and improvements for the Agent-Evaluation system. Items are ordered loosely by priority. Each item includes a description, goal, and expected outcome.

---

## Backlog Items

### 1. Instruction Optimisation Loop

**Description:** Build an automated loop that uses evaluation results to suggest improvements to agent instruction files.  
**Goal:** Reduce manual effort in identifying where agent instructions are failing and what changes would improve compliance scores.  
**Expected outcome:** A script or workflow that reads `results/` output, identifies low-scoring scenarios, and produces candidate instruction improvements for human review.

---

### 2. Train/Test Dataset Separation

**Description:** Split evaluation datasets into training and test subsets so that instruction tuning is validated on held-out scenarios.  
**Goal:** Prevent overfitting agent instructions to the evaluation scenarios used during development.  
**Expected outcome:** A dataset convention and tooling that supports `train/` and `test/` splits, with evaluation runs that report separate scores for each.

---

### 3. Paraphrase Scenario Generation

**Description:** Automatically generate paraphrased variants of existing evaluation scenarios to increase dataset diversity.  
**Goal:** Test whether agent compliance is robust to variation in phrasing, not just the specific wording of original scenarios.  
**Expected outcome:** A script that takes an input dataset and produces an augmented dataset with paraphrased scenario variants.

---

### 4. Evaluation Scoring System

**Description:** Replace raw text recording with a structured scoring system that rates each agent response against the expected behaviour.  
**Goal:** Produce quantitative metrics that can be tracked over time as agent instructions are refined.  
**Expected outcome:** A scorer (rule-based or model-assisted) that assigns a pass/fail or numeric score to each evaluation record and aggregates results per run.

---

### 5. Metrics Collection and Reporting

**Description:** Aggregate scores across runs and produce a summary report showing trends over time.  
**Goal:** Make it easy to see whether agent compliance is improving, degrading, or stable across instruction iterations.  
**Expected outcome:** A report (Markdown or JSON) committed alongside results, or a GitHub Actions step that posts a summary to the PR.

---

### 6. Multi-Agent Comparison

**Description:** Extend the pipeline to run the same dataset against multiple agent instruction files in a single workflow run.  
**Goal:** Enable side-by-side comparison of different agent instruction strategies on the same scenarios.  
**Expected outcome:** A workflow that accepts a list of agent files, runs each through the full evaluation pipeline, and produces a comparative results summary.

---

### 7. Results Archival Strategy

**Description:** Define a strategy for managing the growth of the `results/` directory as evaluation runs accumulate.  
**Goal:** Prevent repository bloat while maintaining full traceability of evaluation history.  
**Expected outcome:** An ADR and implementation — options include periodic archival to a separate branch, GitHub Releases artifacts, or an external store.

---

### 8. Human Review Workflow

**Description:** Add a pull request–based workflow for reviewing and approving changes to agent instruction files.  
**Goal:** Ensure that instruction changes are reviewed against evaluation results before being merged.  
**Expected outcome:** A GitHub Actions workflow or PR template that surfaces relevant evaluation results for reviewer consideration.
