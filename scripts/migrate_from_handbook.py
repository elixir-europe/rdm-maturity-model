#!/usr/bin/env python3
"""One-shot migration of indicator content from the DS Handbook into the model.

The handbook carried, per indicator page, content that the model had no home for:
a verbose level title, an Impact statement per level, the bullet list describing
what each level looks like in practice, and a long indicator introduction. This
script lifts all of it into `_data/maturity_model.json` so the pages can be
generated from the model instead of being retyped by hand.

It is kept in the repo for provenance: re-running it against the pre-migration
handbook pages reproduces the migrated model exactly.

Decisions it implements (agreed 2026-09-15):

  * maturityLevels entries become objects; `weights` stays a parallel array
  * the SHORTER of the two titles becomes `title`; the longer one is stored as
    `briefDescription` with the repeated title stripped off its front, so the
    level does not say its own name twice
  * bullets are stored verbatim, markdown included, as `criteria`
  * the page's opening paragraph becomes `indicatorLongDescription`, and the
    existing short `indicatorDescription` is left alone
  * four level titles that differ only by a typo take the handbook's wording,
    except that "standardized" keeps its -ize spelling (TYPO_FIXES below)
  * the eight indicator names that differed were settled one by one, and where the
    long form said more it is kept as `indicatorBriefDescription` (INDICATOR_NAMES)

Usage:
    python scripts/migrate_from_handbook.py ../ds-handbook [-o _data/maturity_model.json]
    python scripts/migrate_from_handbook.py ../ds-handbook --dry-run
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_JSON = REPO_ROOT / "_data" / "maturity_model.json"

NEW_VERSION = {
    "versionNumber": "2.0.0",
    "versionDescription": (
        "Maturity levels become objects carrying briefDescription, impact and criteria; "
        "indicator content migrated from the DS Handbook"
    ),
}

# Indicator names that differed between the handbook page and the model, settled
# one by one on 2026-09-15. Each is (indicator, indicatorBriefDescription or None).
# Where the longer name only enumerated what the descriptions already say, it was
# dropped rather than kept; the three that differed from the page only by
# punctuation kept the model's form, which is sentence case throughout.
INDICATOR_NAMES = {
    "mm-legal-ethics": (
        "Ethics",
        "ELSI for research data (regarding animal / human subjects, Nagoya matters)",
    ),
    "mm-strategy-policy-adherence": (
        "Adherence to policies",
        "Adherence to relevant governing RDM policies on international, European, national, "
        "local, organisational level",
    ),
    "mm-strategy-goals-kpis": ("RDM goals and KPIs", None),
    "mm-strategy-funding": ("Funding for RDM", None),
    "mm-strategy-personnel": ("RDM personnel", None),
    # Names that had grown into descriptions -- 147, 134, 79 and 58 characters, which
    # made an unusable navigation label and a heavy page heading. Each is replaced by
    # the short name the handbook's sidebar already used; in every case the existing
    # indicatorDescription already says what the long name said, so nothing moves.
    # "Information security" also settles the wording item in ds-handbook#49.
    "mm-strategy-align-with-best-practices": ("Align with best practices", None),
    "mm-support-network": ("Networking engagement", None),
    "mm-support-services": ("RDM services", None),
    "mm-legal-security": ("Information security", None),
    # Punctuation and capitalisation only: the model's form stands, the page follows.
    "mm-strategy-policies-and-procedures": ("Research data governance: policies and procedures", None),
    "mm-legal-framework": ("Legal framework for research data", None),
    "mm-support-guidelines-researchers": ("RDM information / guidelines for researchers", None),
}

# Levels where page and model disagree on the substance rather than the length, so
# no automatic rule can settle them. Each is (title, briefDescription or None).
TITLE_DECISIONS = {
    # ds-handbook#113: the page called this level "Established", the model
    # "Minimal". Settled 2026-09-15 in favour of the handbook's wording, so the
    # rejected label drops out and only its explanatory clause is kept.
    ("mm-support-network", 3): (
        "Established network participation",
        "Formal interaction with external RDM expert network(s) with occasional "
        "collaboration with external partners",
    ),
}

# Level titles where page and model differ only by a typo or spelling, so there is
# no short/long pair to split. The value is the wording the model should carry.
TYPO_FIXES = {
    ("mm-strategy-personnel", 2): "There are staff that have DM duties",
    ("mm-legal-framework", 3): (
        "The legal framework is well-defined and standardized across the organization. "
        "A dedicated personnel is responsible for supporting the establishment of a legal "
        "framework covering RDM requirements. Comprehensive templates and standardized "
        "contractual clauses for RDM issues."
    ),
    ("mm-data-publication", 4): (
        "Research data publication follows a standardized, documented process and support "
        "is available"
    ),
    ("mm-data-accessibility", 2): (
        "Standard access channel is in place. The data access requests have to be submitted"
    ),
}

HEADING = re.compile(r"^##\s+(.*)$", re.M)
LEVEL_PREFIX = re.compile(r"^Level\s+(\d+)\s*(?:[:–—-])\s*", re.I)
BULLET = re.compile(r"^\s*[*-]\s+(.*)$")
# The pages mark the Impact statement three different ways -- "**Impact:**",
# "**Impact**:" and "**Impact***:*" -- so anything made of asterisks, colons and
# spaces between the word and the sentence is punctuation, not content.
IMPACT = re.compile(r"^\s*\*\*Impact[:*\s]*(.*)$")
FRONTMATTER = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.S)


class MigrationError(Exception):
    pass


def clean(text: str) -> str:
    """Collapse internal whitespace the way the schema's cleanString expects."""
    return re.sub(r"\s+", " ", text).strip()


def explanatory_clause(title: str, longer: str) -> str:
    """The part of `longer` that says more than `title`.

    Most long wordings are "Title - explanation", so the title is stripped off the
    front and only the explanation is stored; the full string is title + " - " +
    clause again whenever a consumer wants it. Where the two are alternative
    phrasings rather than one extending the other, `longer` is returned whole.
    """
    if not longer.startswith(title):
        return longer
    clause = longer[len(title):].lstrip(" –—-:;,./")
    return clause or longer


def parse_page(path: Path) -> dict:
    """Pull page_id, the opening paragraph and one entry per level out of a page."""
    match = FRONTMATTER.match(path.read_text(encoding="utf-8"))
    if not match:
        raise MigrationError(f"{path.name}: no frontmatter")
    frontmatter, body = match.groups()

    page_id = re.search(r"^page_id:\s*(\S+)\s*$", frontmatter, re.M)
    if not page_id:
        raise MigrationError(f"{path.name}: no page_id")

    title = re.search(r"^title:\s*(.+?)\s*$", frontmatter, re.M)
    if not title:
        raise MigrationError(f"{path.name}: no title")

    # Everything before the first level heading; the first paragraph of it is the
    # long introduction.
    head, *sections = HEADING.split(body)
    paragraphs = [p.strip() for p in head.strip().split("\n\n") if p.strip()]
    if not paragraphs:
        raise MigrationError(f"{path.name}: no introduction paragraph")
    if len(paragraphs) > 1:
        raise MigrationError(
            f"{path.name}: {len(paragraphs)} paragraphs before the first level, expected 1"
        )

    levels = []
    for heading, section in zip(sections[0::2], sections[1::2]):
        heading = heading.replace("\\-", "-").strip()
        numbered = LEVEL_PREFIX.match(heading)
        if not numbered:
            raise MigrationError(f"{path.name}: cannot read level heading {heading!r}")
        order = int(numbered.group(1))
        if order != len(levels) + 1:
            raise MigrationError(
                f"{path.name}: level numbered {order}, expected {len(levels) + 1}"
            )

        criteria, impact = [], None
        for line in section.split("\n"):
            if "{% include" in line:
                continue
            bullet = BULLET.match(line)
            if bullet:
                criteria.append(clean(bullet.group(1)))
                continue
            found = IMPACT.match(line)
            if found:
                if impact is not None:
                    raise MigrationError(f"{path.name}: two Impact statements in level {order}")
                impact = clean(found.group(1))
            elif line.strip() and not line.strip().startswith("####"):
                raise MigrationError(f"{path.name}: unexpected line in level {order}: {line!r}")

        levels.append(
            {
                "order": order,
                "title": clean(LEVEL_PREFIX.sub("", heading)),
                "impact": impact,
                "criteria": criteria,
            }
        )

    return {
        "page_id": page_id.group(1),
        "title": title.group(1),
        "introduction": clean(paragraphs[0]),
        "levels": levels,
    }


def merge(model: dict, pages: dict[str, dict]) -> tuple[dict, list[str]]:
    """Fold the parsed pages into the model, returning the new model and a log."""
    log: list[str] = []
    migrated = json.loads(json.dumps(model))  # deep copy
    migrated["version"] = {**NEW_VERSION, "timestamp": model["version"]["timestamp"]}

    for indicator in migrated["indicators"]:
        indicator_id = indicator["indicatorId"]
        page = pages.get(indicator_id)
        if page is None:
            raise MigrationError(f"{indicator_id}: no handbook page")

        old_levels = indicator["maturityLevels"]
        if len(old_levels) != len(page["levels"]):
            raise MigrationError(
                f"{indicator_id}: model has {len(old_levels)} levels, "
                f"page has {len(page['levels'])}"
            )

        indicator["indicatorLongDescription"] = page["introduction"]

        decided_name = INDICATOR_NAMES.get(indicator_id)
        if decided_name is not None:
            name, brief = decided_name
            was = indicator["indicator"]
            indicator["indicator"] = name
            if brief is not None:
                indicator["indicatorBriefDescription"] = explanatory_clause(name, brief)
                log.append(
                    f"{indicator_id}: name {was!r} -> {name!r}, rest kept as "
                    f"indicatorBriefDescription"
                )
            else:
                log.append(f"{indicator_id}: name {was!r} -> {name!r}")

        levels = []
        for model_title, parsed in zip(old_levels, page["levels"]):
            model_title = clean(model_title)
            page_title = parsed["title"]
            override = TYPO_FIXES.get((indicator_id, parsed["order"]))

            decided = TITLE_DECISIONS.get((indicator_id, parsed["order"]))

            if decided is not None:
                title, brief = decided
                log.append(f"{indicator_id} L{parsed['order']}: settled by hand, title {title!r}")
            elif override is not None:
                title, brief = override, None
                log.append(f"{indicator_id} L{parsed['order']}: typo fix, one title kept")
            elif page_title == model_title:
                title, brief = model_title, None
            elif page_title.rstrip(" .") == model_title.rstrip(" ."):
                # Same sentence, and the model just ends it with a full stop. Not a
                # short/long pair: keep one title, punctuated like the indicator
                # names and descriptions, which never end with one.
                title, brief = page_title.rstrip(" ."), None
                log.append(f"{indicator_id} L{parsed['order']}: trailing full stop dropped")
            else:
                # The shorter of the two is the title; the longer keeps its detail
                # as briefDescription so no wording is lost.
                title, longer = sorted((page_title, model_title), key=len)
                brief = explanatory_clause(title, longer)
                source = "page" if title == page_title else "model"
                shape = "clause" if brief != longer else "full wording, no shared opening"
                log.append(
                    f"{indicator_id} L{parsed['order']}: title from {source} "
                    f"({len(title)} ch), briefDescription {len(brief)} ch [{shape}]"
                )

            level = {
                "levelId": f"{indicator_id}-{parsed['order']}",
                "order": parsed["order"],
                "title": title,
            }
            if brief is not None:
                level["briefDescription"] = brief
            if parsed["impact"] is not None:
                level["impact"] = parsed["impact"]
            else:
                log.append(f"{indicator_id} L{parsed['order']}: no Impact statement on the page")
            if parsed["criteria"]:
                level["criteria"] = parsed["criteria"]
            else:
                log.append(f"{indicator_id} L{parsed['order']}: no criteria bullets on the page")
            levels.append(level)

        indicator["maturityLevels"] = levels

        # Keep a stable, readable key order.
        order = [
            "domain",
            "domainLevel",
            "indicatorId",
            "indicatorLevel",
            "indicator",
            "indicatorBriefDescription",
            "indicatorDescription",
            "indicatorLongDescription",
            "maturityLevels",
            "weights",
        ]
        reordered = {key: indicator[key] for key in order if key in indicator}
        reordered.update({k: v for k, v in indicator.items() if k not in reordered})
        indicator.clear()
        indicator.update(reordered)

    return migrated, log


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("handbook", type=Path, help="path to a ds-handbook checkout")
    parser.add_argument("-o", "--output", type=Path, default=DEFAULT_JSON)
    parser.add_argument("-m", "--model", type=Path, default=DEFAULT_JSON)
    parser.add_argument("--dry-run", action="store_true", help="report, write nothing")
    args = parser.parse_args(argv[1:])

    pages_dir = args.handbook / "pages" / "maturity-model"
    if not pages_dir.is_dir():
        print(f"error: {pages_dir} not found")
        return 1

    pages = {}
    for path in sorted(pages_dir.glob("*/*.md")):
        parsed = parse_page(path)
        pages[parsed["page_id"]] = parsed

    with args.model.open(encoding="utf-8") as handle:
        model = json.load(handle)

    migrated, log = merge(model, pages)

    levels = sum(len(i["maturityLevels"]) for i in migrated["indicators"])
    briefs = sum(
        1 for i in migrated["indicators"] for l in i["maturityLevels"] if "briefDescription" in l
    )
    impacts = sum(1 for i in migrated["indicators"] for l in i["maturityLevels"] if "impact" in l)
    criteria = sum(
        len(l.get("criteria", [])) for i in migrated["indicators"] for l in i["maturityLevels"]
    )

    for line in log:
        print(f"  {line}")
    print(
        f"\n{len(pages)} pages -> {len(migrated['indicators'])} indicators, {levels} levels: "
        f"{briefs} briefDescription, {impacts} impact, {criteria} criteria bullets, "
        f"{len(migrated['indicators'])} indicatorLongDescription"
    )

    if args.dry_run:
        print("dry run, nothing written")
        return 0

    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(migrated, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    print(f"written to {args.output}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except MigrationError as exc:
        print(f"error: {exc}")
        sys.exit(1)
