#!/usr/bin/env python3
"""
check_invariance.py

Validates that semantically equivalent scenario variants in a results file
produce consistent categorical scores.

Given a results/run_NNN.json file, groups records by scenario_id and checks
that every variant within a group received the same categorical score label
(pass / partial / fail).  In strict mode, partial and pass are treated as
distinct — any mix of pass and partial within a group also counts as
inconsistent.

Usage:
  python scripts/check_invariance.py --results results/run_001.json
  python scripts/check_invariance.py --results results/run_001.json --strict

Exit codes:
  0  All scenario groups have consistent variant scores.
  1  One or more scenario groups have inconsistent variant scores.
  2  Input file error (missing, unreadable, or invalid JSON).
"""

import argparse
import json
import sys
from typing import Any


def load_results(path: str) -> list[dict[str, Any]]:
    """Load a results JSON array from *path*.

    Raises:
        FileNotFoundError: if the file does not exist.
        ValueError: if the file is not a JSON array.
        json.JSONDecodeError: if the file contains invalid JSON.
    """
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise ValueError(f"Results file at {path!r} must be a JSON array.")
    return data


def group_by_scenario(records: list[dict[str, Any]]) -> dict[str, list[str]]:
    """Return a mapping of scenario_id → list of categorical score labels."""
    groups: dict[str, list[str]] = {}
    for record in records:
        sid = record["scenario_id"]
        score = record["score"]
        groups.setdefault(sid, []).append(score)
    return groups


def is_consistent(scores: list[str], strict: bool) -> bool:
    """Return True if all *scores* are considered equivalent.

    In normal mode, pass/partial are in the same "acceptable" bucket, so a
    group is inconsistent only when pass or partial is mixed with fail, or when
    the set contains both pass and fail.

    In strict mode every distinct label counts as its own category — any group
    containing more than one distinct label is inconsistent.
    """
    if len(scores) <= 1:
        return True
    if strict:
        return len(set(scores)) == 1
    # Normal mode: inconsistent only if fail is mixed with pass or partial.
    unique = set(scores)
    if "fail" in unique and len(unique) > 1:
        return False
    return True


def check_invariance(
    records: list[dict[str, Any]], strict: bool = False
) -> tuple[list[str], list[str]]:
    """Check invariance across scenario groups.

    Args:
        records: Flat list of result records (each with scenario_id and score).
        strict:  When True, any mix of distinct labels is inconsistent.

    Returns:
        A tuple (consistent_ids, inconsistent_ids) where each element is a
        sorted list of scenario_id strings.
    """
    groups = group_by_scenario(records)
    consistent: list[str] = []
    inconsistent: list[str] = []
    for scenario_id, scores in sorted(groups.items()):
        if is_consistent(scores, strict=strict):
            consistent.append(scenario_id)
        else:
            inconsistent.append(scenario_id)
    return consistent, inconsistent


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check that variant scores are consistent within each scenario group.",
    )
    parser.add_argument(
        "--results",
        required=True,
        help="Path to a results/run_NNN.json file.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help=(
            "Strict mode: treat pass and partial as distinct categories. "
            "Any group with mixed pass/partial scores is inconsistent."
        ),
    )
    args = parser.parse_args()

    try:
        records = load_results(args.results)
    except FileNotFoundError:
        print(f"Error: file not found: {args.results!r}", file=sys.stderr)
        sys.exit(2)
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(2)

    if not records:
        print("No records found — nothing to check.")
        print("\nSummary: 0 groups, 0 consistent, 0 inconsistent, invariance rate: N/A")
        sys.exit(0)

    consistent, inconsistent = check_invariance(records, strict=args.strict)
    total = len(consistent) + len(inconsistent)
    rate = len(consistent) / total if total else 0.0

    mode_label = " [strict]" if args.strict else ""
    print(f"Invariance check{mode_label}: {args.results}")
    print()

    if consistent:
        print("Consistent groups (all variants scored the same):")
        for sid in consistent:
            print(f"  ✓  {sid}")
    if inconsistent:
        print("Inconsistent groups (variants scored differently):")
        for sid in inconsistent:
            print(f"  ✗  {sid}")

    print()
    print(
        f"Summary: {total} group(s), "
        f"{len(consistent)} consistent, "
        f"{len(inconsistent)} inconsistent, "
        f"invariance rate: {rate:.1%}"
    )

    sys.exit(0 if not inconsistent else 1)


if __name__ == "__main__":
    main()
