#!/usr/bin/env python3
"""
Extract maturity_model.json from a DSW Knowledge Model (.km) file.

The .km file is treated as the source of truth. Run this script (or let the CI
pipeline run it) whenever the KM changes to regenerate the JSON consumed by
downstream tools.

Usage:
    python scripts/km_to_json.py [km_file] [output_json]
    python scripts/km_to_json.py _data/datarex_RDM-MM_0.1.2.km _data/maturity_model.json

KM authoring notes
------------------
Chapter order:
    DSW resets chapter order via EditKnowledgeModelEvent.chapterUuids when you
    drag-to-reorder chapters in the DSW UI. If that event is absent, chapters
    are ordered by creation time, which may not match the intended domain-level
    numbering. To override, add a "domainLevel" annotation (key=domainLevel,
    value="1") to each chapter in DSW.

Question order:
    Questions within a chapter are ordered by their AddQuestionEvent createdAt
    timestamp unless an EditChapterEvent with questionUuids has been recorded.

indicatorId:
    Not stored natively in the DSW KM. If you want stable IDs that survive
    title changes, add an annotation with key="indicatorId" to each question in
    DSW (e.g. value="mm-strategy-defined"). Without that annotation, this
    script derives the ID from the question title slug, which changes if the
    title changes.
"""

import json
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _apply_changed(current, delta):
    """Apply a DSW event delta ({changed, value?}) to a current value."""
    if isinstance(delta, dict) and delta.get("changed"):
        return delta.get("value")
    return current


def _parse_annotations(raw) -> dict:
    """Convert a DSW annotations list [{key, value}] to a plain dict."""
    if isinstance(raw, list):
        return {a["key"]: a["value"] for a in raw if isinstance(a, dict)}
    return {}


def _slugify(text: str) -> str:
    """Lowercase slug, preserving only word chars and hyphens."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")


def _strip_answer_prefix(label: str) -> str:
    """Remove leading numeric prefix such as '1. ', '2) ', '3: '."""
    return re.sub(r"^\d+[.):\s]\s*", "", label).strip()


def _format_measure(value) -> str:
    """Convert a float measure (0, 0.25, 0.5 …) to a clean string."""
    try:
        f = float(value)
        return f"{f:g}"
    except (TypeError, ValueError):
        return str(value)


# ---------------------------------------------------------------------------
# Event replay
# ---------------------------------------------------------------------------

def _reconstruct(km: dict) -> dict:
    """Replay all KM events and return the final state of every entity."""

    km_chapter_uuids: list = []
    chapters: dict = {}
    questions: dict = {}
    answers: dict = {}
    metrics: dict = {}
    deleted_questions: set = set()
    deleted_chapters: set = set()
    deleted_answers: set = set()

    for pkg in km["packages"]:
        for event in pkg["events"]:
            c = event["content"]
            etype = c["eventType"]
            euuid = event["entityUuid"]
            puuid = event.get("parentUuid", "")
            ts = event.get("createdAt", "")

            # ---- Knowledge model root ----
            if etype == "EditKnowledgeModelEvent":
                ch = c.get("chapterUuids")
                if isinstance(ch, dict) and ch.get("changed"):
                    km_chapter_uuids = ch["value"]

            # ---- Chapters ----
            elif etype == "AddChapterEvent":
                chapters[euuid] = {
                    "uuid": euuid,
                    "title": c.get("title", ""),
                    "text": c.get("text"),
                    "question_uuids": [],
                    "created_at": ts,
                    "annotations": _parse_annotations(c.get("annotations", [])),
                }
            elif etype == "EditChapterEvent":
                if euuid in chapters:
                    ch = chapters[euuid]
                    ch["title"] = _apply_changed(ch["title"], c.get("title"))
                    ch["text"] = _apply_changed(ch["text"], c.get("text"))
                    q = c.get("questionUuids")
                    if isinstance(q, dict) and q.get("changed"):
                        ch["question_uuids"] = q["value"]
                    ann = c.get("annotations")
                    if isinstance(ann, dict) and ann.get("changed"):
                        ch["annotations"] = _parse_annotations(ann.get("value", []))
            elif etype == "DeleteChapterEvent":
                deleted_chapters.add(euuid)

            # ---- Questions ----
            elif etype == "AddQuestionEvent":
                questions[euuid] = {
                    "uuid": euuid,
                    "parent_uuid": puuid,
                    "title": c.get("title", ""),
                    "text": c.get("text"),
                    "answer_uuids": [],
                    "created_at": ts,
                    "annotations": _parse_annotations(c.get("annotations", [])),
                }
            elif etype == "EditQuestionEvent":
                if euuid in questions:
                    q = questions[euuid]
                    # parentUuid on EditQuestionEvent records a chapter move
                    if puuid and puuid != "00000000-0000-0000-0000-000000000000":
                        q["parent_uuid"] = puuid
                    q["title"] = _apply_changed(q["title"], c.get("title"))
                    q["text"] = _apply_changed(q["text"], c.get("text"))
                    a = c.get("answerUuids")
                    if isinstance(a, dict) and a.get("changed"):
                        q["answer_uuids"] = a["value"]
                    ann = c.get("annotations")
                    if isinstance(ann, dict) and ann.get("changed"):
                        q["annotations"] = _parse_annotations(ann.get("value", []))
            elif etype == "DeleteQuestionEvent":
                deleted_questions.add(euuid)

            # ---- Answers ----
            elif etype == "AddAnswerEvent":
                answers[euuid] = {
                    "uuid": euuid,
                    "parent_uuid": puuid,
                    "label": c.get("label", ""),
                    "metric_measures": c.get("metricMeasures", []),
                    "created_at": ts,
                }
            elif etype == "EditAnswerEvent":
                if euuid in answers:
                    a = answers[euuid]
                    a["label"] = _apply_changed(a["label"], c.get("label"))
                    mm = c.get("metricMeasures")
                    if isinstance(mm, dict) and mm.get("changed"):
                        a["metric_measures"] = mm["value"]
            elif etype == "DeleteAnswerEvent":
                deleted_answers.add(euuid)

            # ---- Metrics (one per domain — used for scoring in DSW) ----
            elif etype == "AddMetricEvent":
                metrics[euuid] = {
                    "uuid": euuid,
                    "title": c.get("title", ""),
                    "abbreviation": c.get("abbreviation"),
                    "created_at": ts,
                }
            elif etype == "EditMetricEvent":
                if euuid in metrics:
                    m = metrics[euuid]
                    m["title"] = _apply_changed(m["title"], c.get("title"))
                    m["abbreviation"] = _apply_changed(m["abbreviation"], c.get("abbreviation"))

    return {
        "km_chapter_uuids": km_chapter_uuids,
        "chapters": chapters,
        "questions": questions,
        "answers": answers,
        "metrics": metrics,
        "deleted_questions": deleted_questions,
        "deleted_chapters": deleted_chapters,
        "deleted_answers": deleted_answers,
    }


# ---------------------------------------------------------------------------
# JSON builder
# ---------------------------------------------------------------------------

def build_maturity_model_json(km_path: str) -> dict:
    with open(km_path) as f:
        km = json.load(f)

    state = _reconstruct(km)
    chapters = state["chapters"]
    questions = state["questions"]
    answers = state["answers"]
    deleted = state["deleted_questions"]
    deleted_chapters = state["deleted_chapters"]
    deleted_answers = state["deleted_answers"]

    # --- Chapter ordering ---
    # Prefer explicit order from EditKnowledgeModelEvent; fall back to creation time.
    if state["km_chapter_uuids"]:
        ordered_chapter_uuids = state["km_chapter_uuids"]
    else:
        ordered_chapter_uuids = [
            c["uuid"]
            for c in sorted(chapters.values(), key=lambda c: c["created_at"])
        ]

    # Keep only chapters that are not deleted and have at least one active question.
    def has_active_questions(ch_uuid: str) -> bool:
        return any(
            q["parent_uuid"] == ch_uuid and q["uuid"] not in deleted
            for q in questions.values()
        )

    active_chapters = [
        chapters[u]
        for u in ordered_chapter_uuids
        if u in chapters
        and u not in deleted_chapters
        and has_active_questions(u)
    ]

    # Respect "domainLevel" annotation to override creation-time ordering.
    # If any chapter carries the annotation, re-sort by it.
    if any(ch["annotations"].get("domainLevel") for ch in active_chapters):
        active_chapters.sort(
            key=lambda ch: int(ch["annotations"].get("domainLevel", 99))
        )

    # --- Version ---
    last_pkg = km["packages"][-1]
    version = {
        "versionNumber": km.get("version", ""),
        "versionDescription": last_pkg.get("description", ""),
        "timestamp": last_pkg.get("createdAt", ""),
    }

    # --- Domains ---
    domains_out = []
    for idx, ch in enumerate(active_chapters, 1):
        domains_out.append({
            "uuid": ch["uuid"],
            "domainName": ch["title"],
            "domainLevel": str(idx),
            "domainDescription": ch.get("text") or "",
        })

    # --- Indicators ---
    indicators_out = []
    for domain_idx, ch in enumerate(active_chapters, 1):
        ch_uuid = ch["uuid"]

        # Question ordering: explicit list from DSW, else creation time.
        if ch["question_uuids"]:
            q_uuids_ordered = [
                u for u in ch["question_uuids"] if u not in deleted
            ]
        else:
            q_uuids_ordered = [
                q["uuid"]
                for q in sorted(
                    [
                        q for q in questions.values()
                        if q["parent_uuid"] == ch_uuid and q["uuid"] not in deleted
                    ],
                    key=lambda q: q["created_at"],
                )
            ]

        for q_num, q_uuid in enumerate(q_uuids_ordered, 1):
            q = questions.get(q_uuid)
            if q is None:
                continue

            indicator_level = f"{domain_idx}.{q_num}"

            # indicatorId: annotation wins; otherwise derive from title slug (first 6 words).
            indicator_id = q["annotations"].get("indicatorId")
            if not indicator_id:
                first_six = " ".join(q["title"].split()[:6])
                indicator_id = "mm-" + _slugify(first_six)

            # Answer ordering: explicit list from DSW, else creation time.
            if q["answer_uuids"]:
                a_uuids_ordered = q["answer_uuids"]
            else:
                a_uuids_ordered = [
                    a["uuid"]
                    for a in sorted(
                        [a for a in answers.values() if a["parent_uuid"] == q_uuid],
                        key=lambda a: a["created_at"],
                    )
                ]

            maturity_levels = []
            answer_uuids = []
            weights = []
            for a_uuid in a_uuids_ordered:
                if a_uuid in deleted_answers:
                    continue
                a = answers.get(a_uuid)
                if a is None:
                    continue
                maturity_levels.append(_strip_answer_prefix(a["label"]))
                answer_uuids.append(a_uuid)
                mm_list = a.get("metric_measures", [])
                measure = mm_list[0]["measure"] if mm_list else 0
                weights.append(_format_measure(measure))

            indicators_out.append({
                "uuid": q_uuid,
                "domain": ch["title"],
                "indicatorId": indicator_id,
                "indicatorLevel": indicator_level,
                "indicator": q["title"],
                "maturityLevels": maturity_levels,
                "answerUuids": answer_uuids,
                "weights": weights,
                "indicatorDescription": q.get("text") or "",
                "domainLevel": str(domain_idx),
            })

    return {
        "version": version,
        "domains": domains_out,
        "indicators": indicators_out,
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def _find_km_file(model_dir: Path) -> Path:
    candidates = sorted(model_dir.glob("*.km"))
    if not candidates:
        raise FileNotFoundError(f"No .km file found in {model_dir}")
    return candidates[-1]  # latest by name (assumes semver suffix)


if __name__ == "__main__":
    km_file = Path(sys.argv[1]) if len(sys.argv) > 1 else _find_km_file(Path("model"))
    output_file = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("_data") / "maturity_model.json"

    result = build_maturity_model_json(str(km_file))

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(result, f, indent=2)
        f.write("\n")

    print(f"Generated {output_file} from {km_file}")
