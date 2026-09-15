#!/usr/bin/env python3
"""Check that the migrated model still holds every word the handbook pages held.

The migration is only acceptable if the content did not change. This compares the
pre-migration handbook pages against the migrated model, text by text:

  * the opening paragraph == indicatorLongDescription
  * every bullet == the matching entry of criteria, character for character
  * every Impact statement == impact
  * every level heading is still somewhere on the level: as the title, or as the
    title recombined with briefDescription, which holds only the part that says
    more than the title
  * every pre-migration model title is likewise still present, except where a
    wording was deliberately rejected (migrate_from_handbook.TITLE_DECISIONS)
  * the page's own title is still the indicator's name, unless that name was
    settled by hand (migrate_from_handbook.INDICATOR_NAMES)

Run it against a handbook checkout that still has the hand-written pages:

    python scripts/verify_migration.py ../ds-handbook [--model _data/maturity_model.json]

Exits 0 when nothing was lost, 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from migrate_from_handbook import (
    INDICATOR_NAMES,
    TITLE_DECISIONS,
    TYPO_FIXES,
    clean,
    parse_page,
)


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_JSON = REPO_ROOT / "_data" / "maturity_model.json"


def normalise(text: str) -> str:
    return text.replace("–", "-").rstrip(" .").lower()


def covers(level: dict, wording: str) -> bool:
    """Can the level still produce this wording?

    briefDescription stores only the part that says more than the title, so a long
    wording survives as title + separator + briefDescription. The separator differs
    from level to level -- a dash, a colon, a full stop, a bare space -- so rather
    than enumerate them, this checks that the wording opens with the title, closes
    with the clause, and holds nothing but punctuation in between.
    """
    text = normalise(wording)
    title = normalise(level["title"])
    if text == title:
        return True

    brief = level.get("briefDescription")
    if not brief:
        return False
    clause = normalise(brief)
    if text == clause:
        return True
    if text.startswith(title) and text.endswith(clause):
        joint = text[len(title):len(text) - len(clause)]
        return not any(char.isalnum() for char in joint)
    return False



def pre_migration(model: dict | None) -> dict | None:
    """A model is only a useful baseline while its levels are still plain strings."""
    if model is None:
        return None
    levels = model.get("indicators", [{}])[0].get("maturityLevels", [])
    return model if levels and isinstance(levels[0], str) else None


def original_model(handbook: Path) -> dict | None:
    """The model as it was before the migration.

    `main` is the branch this migration is cut from, so it holds the authoritative
    pre-migration model. The handbook's pinned submodule is the fallback, for
    running this from a checkout with no git history -- but only while it, too, is
    still pre-migration: once the submodule is bumped it is no longer a baseline.
    """
    try:
        blob = subprocess.run(
            ["git", "show", "main:_data/maturity_model.json"],
            cwd=REPO_ROOT, capture_output=True, text=True, check=True,
        ).stdout
        from_git = pre_migration(json.loads(blob))
        if from_git is not None:
            return from_git
    except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError):
        pass

    pinned = handbook / "_external" / "rdm-maturity-model" / "_data" / "maturity_model.json"
    if pinned.exists():
        with pinned.open(encoding="utf-8") as handle:
            return pre_migration(json.load(handle))
    return None


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("handbook", type=Path)
    parser.add_argument("-m", "--model", type=Path, default=DEFAULT_JSON)
    args = parser.parse_args(argv[1:])

    with args.model.open(encoding="utf-8") as handle:
        model = json.load(handle)
    indicators = {i["indicatorId"]: i for i in model["indicators"]}

    before = original_model(args.handbook)
    old_titles = (
        {i["indicatorId"]: [clean(t) for t in i["maturityLevels"]] for i in before["indicators"]}
        if before
        else {}
    )

    problems: list[str] = []
    checked = {"intro": 0, "criteria": 0, "impact": 0, "title": 0}

    for path in sorted((args.handbook / "pages" / "maturity-model").glob("*/*.md")):
        page = parse_page(path)
        indicator = indicators.get(page["page_id"])
        if indicator is None:
            problems.append(f"{page['page_id']}: no indicator in the model")
            continue

        if page["title"] != indicator["indicator"] and page["page_id"] not in INDICATOR_NAMES:
            problems.append(
                f"{page['page_id']}: page title {page['title']!r} is not the indicator name "
                f"{indicator['indicator']!r}, and no decision was recorded for it"
            )

        if indicator.get("indicatorLongDescription") != page["introduction"]:
            problems.append(f"{page['page_id']}: introduction paragraph differs")
        checked["intro"] += 1

        for parsed, level in zip(page["levels"], indicator["maturityLevels"]):
            key = (page["page_id"], parsed["order"])
            where = f"{page['page_id']} L{parsed['order']}"
            # A typo fix or a settled conflict rewrites the level on purpose, so
            # the wording it replaced is not expected to survive.
            rewritten = key in TYPO_FIXES or key in TITLE_DECISIONS

            if not rewritten and not covers(level, parsed["title"]):
                problems.append(f"{where}: page heading {parsed['title']!r} is gone")
            checked["title"] += 1

            was = old_titles.get(page["page_id"], [])
            if was and parsed["order"] <= len(was) and not rewritten:
                old = was[parsed["order"] - 1]
                if not covers(level, old):
                    problems.append(f"{where}: pre-migration model title {old!r} is gone")

            if parsed["impact"] != level.get("impact"):
                problems.append(f"{where}: Impact statement differs")
            elif parsed["impact"] is not None:
                checked["impact"] += 1

            if parsed["criteria"] != level.get("criteria", []):
                problems.append(f"{where}: criteria bullets differ")
            checked["criteria"] += len(parsed["criteria"])

    # Once the handbook generates its indicator pages there is nothing left to
    # compare against, and an empty run must not read as a pass.
    if checked["intro"] == 0:
        print(
            f"error: no indicator pages found under {args.handbook}/pages/maturity-model/. "
            f"This checks the migration against the hand-written pages, so it needs a "
            f"handbook checkout from before they were replaced."
        )
        return 1

    if problems:
        print(f"{len(problems)} problem(s):")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    note = "" if before else " (pre-migration model not found, titles checked against pages only)"
    print(
        f"nothing lost: {checked['intro']} introductions, {checked['title']} level titles, "
        f"{checked['impact']} Impact statements and {checked['criteria']} criteria bullets "
        f"match the handbook exactly{note}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
