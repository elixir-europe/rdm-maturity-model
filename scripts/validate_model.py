#!/usr/bin/env python3
"""Structural checks for the maturity model that JSON Schema cannot express.

`_data/maturity_model.schema.json` covers the shape of the file: types, required
keys, id and level patterns, string hygiene. What it cannot express is any rule
that compares one field with another, so those live here:

  * weights and maturityLevels are the same length
  * weights increase and end at 1
  * indicatorId and indicatorLevel are unique
  * every indicator's domain exists in the domains list
  * indicatorLevel's prefix and domainLevel agree with that domain

Usage:
    python scripts/validate_model.py [path/to/maturity_model.json]

Exits 0 when the model is valid, 1 otherwise, printing one line per problem.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_JSON = REPO_ROOT / "_data" / "maturity_model.json"


# ---------------------------------------------------------------- checks

def check_weights(model: dict) -> list[str]:
    """Weights line up with the levels they score."""
    problems = []
    for ind in model.get("indicators", []):
        ref = ind.get("indicatorId", "?")
        weights = ind.get("weights") or []
        levels = ind.get("maturityLevels") or []

        if len(weights) != len(levels):
            problems.append(
                f"{ref}: {len(weights)} weights for {len(levels)} maturity levels "
                f"-- every level needs exactly one weight"
            )
            continue

        try:
            values = [float(w) for w in weights]
        except (TypeError, ValueError):
            # The schema reports the offending value; nothing more to add here.
            continue

        if any(b <= a for a, b in zip(values, values[1:])):
            problems.append(f"{ref}: weights do not increase: {weights}")
        if values and values[-1] != 1:
            problems.append(
                f"{ref}: highest level scores {weights[-1]}, expected \"1\" "
                f"-- a fully mature indicator should score 1"
            )
    return problems


def check_identifiers(model: dict) -> list[str]:
    """indicatorId and indicatorLevel identify an indicator, so both are unique."""
    problems = []
    for field in ("indicatorId", "indicatorLevel"):
        seen: dict[str, int] = {}
        for ind in model.get("indicators", []):
            value = ind.get(field)
            if value is None:
                continue
            seen[value] = seen.get(value, 0) + 1
        for value, count in seen.items():
            if count > 1:
                problems.append(f"{field} {value!r} is used by {count} indicators")
    return problems


def check_domain_references(model: dict) -> list[str]:
    """Each indicator points at a real domain, and agrees with it on the numbering."""
    problems = []
    domains = {d["domainName"]: d for d in model.get("domains", []) if "domainName" in d}

    for ind in model.get("indicators", []):
        ref = ind.get("indicatorId", "?")
        name = ind.get("domain")

        if name not in domains:
            problems.append(
                f"{ref}: domain {name!r} is not in the domains list "
                f"(known: {', '.join(sorted(domains)) or 'none'})"
            )
            continue

        expected = domains[name].get("domainLevel")
        if ind.get("domainLevel") != expected:
            problems.append(
                f"{ref}: domainLevel is {ind.get('domainLevel')!r} but domain "
                f"{name!r} is {expected!r}"
            )

        prefix = str(ind.get("indicatorLevel", "")).split(".")[0]
        if prefix and prefix != expected:
            problems.append(
                f"{ref}: indicatorLevel {ind.get('indicatorLevel')!r} starts with "
                f"{prefix!r} but domain {name!r} is {expected!r}"
            )
    return problems


CHECKS = (check_weights, check_identifiers, check_domain_references)


# ---------------------------------------------------------------- entry point

def main(argv: list[str]) -> int:
    args = argv[1:]
    json_path = Path(args[0]).resolve() if args else DEFAULT_JSON

    if not json_path.exists():
        print(f"error: {json_path} not found")
        return 1

    try:
        with json_path.open(encoding="utf-8") as handle:
            model = json.load(handle)
    except json.JSONDecodeError as exc:
        print(f"error: {json_path.name} is not valid JSON: {exc}")
        return 1

    problems: list[str] = []
    for check in CHECKS:
        problems.extend(check(model))

    indicators = len(model.get("indicators", []))
    domains = len(model.get("domains", []))

    if problems:
        print(f"{len(problems)} problem(s) in {json_path.name}:")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    print(f"{json_path.name} is consistent: {domains} domains, {indicators} indicators")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
