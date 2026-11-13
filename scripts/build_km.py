#!/usr/bin/env python3
"""Build the DSW knowledge model of the maturity model.

The model is published in the DSW Registry as the knowledge model datarex:RDM-MM.
A DSW knowledge model is a chain of packages, each holding the events (add, edit,
move, delete) that turn the previous version into the next one. This script reads
the bundle of the previous version, works out the events that turn it into the
model in _data/maturity_model.json, and writes a bundle with one new package on
top. Projects in DSW can then be migrated from the previous version to the new one.

How the model maps to the knowledge model (elixir-europe/rdm-maturity-model#26):

  domain     chapter, and a metric with the same title
  indicator  options question in its domain's chapter. Its text is the indicator's
             description and a table of its levels, with their criteria and
             impact, so that they can be compared before one is chosen. It links
             to the indicator's page in the DS Handbook.
  level      answer, labelled "title – briefDescription", with no advice. It
             scores the domain's metric with the level's weight.

Each entity carries an annotation with the id it was built from: domainLevel on
chapters and metrics, indicatorId on questions, levelId on answers. The next
version finds it again by that annotation. Version 0.1.2 was made by hand and has
no annotations, so km/0.1.2-uuids.json maps its UUIDs to the model's ids.

Fields the model has nothing for, such as metric abbreviations, are kept as they
are in the previous version.

Before writing, the script replays the whole chain and checks that the result is
the model. It exits 1 if it is not.

Usage:
    python scripts/build_km.py PREVIOUS.km OUTPUT.km
"""

from __future__ import annotations

import copy
import json
import string
import sys
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MODEL_JSON = REPO_ROOT / "_data" / "maturity_model.json"
SEED_JSON = REPO_ROOT / "km" / "0.1.2-uuids.json"

ORGANIZATION_ID = "datarex"
KM_ID = "RDM-MM"
METAMODEL_VERSION = 20
NAME = "RDM Maturity Model"
REPO_URL = "https://github.com/elixir-europe/rdm-maturity-model"
HANDBOOK_URL = "https://elixir-europe.github.io/ds-handbook/"
NIL_UUID = "00000000-0000-0000-0000-000000000000"

# New entities and events get UUIDs derived from this namespace, so the same
# input always gives the same bundle.
NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, REPO_URL)

# Fields of each entity type in metamodel 20, as its edit event lists them.
EDIT_FIELDS = {
    "KnowledgeModel": ["annotations", "chapterUuids", "tagUuids", "integrationUuids",
                       "metricUuids", "phaseUuids", "resourceCollectionUuids"],
    "Chapter": ["annotations", "questionUuids", "text", "title"],
    "Question": ["annotations", "answerUuids", "expertUuids", "referenceUuids",
                 "requiredPhaseUuid", "tagUuids", "text", "title"],
    "Answer": ["advice", "annotations", "followUpUuids", "label", "metricMeasures"],
    "Metric": ["abbreviation", "annotations", "description", "title"],
    "Reference": ["annotations", "label", "url"],
}

# Fields an add event carries. Child lists are filled by the children's own add events.
ADD_FIELDS = {
    "Chapter": ["annotations", "text", "title"],
    "Question": ["annotations", "questionType", "requiredPhaseUuid", "tagUuids", "text", "title"],
    "Answer": ["advice", "annotations", "label", "metricMeasures"],
    "Metric": ["abbreviation", "annotations", "description", "title"],
    "Reference": ["annotations", "label", "referenceType", "url"],
}

# Fields this script sets. The others keep their value from the previous version.
MANAGED_FIELDS = {
    "KnowledgeModel": ["chapterUuids", "metricUuids"],
    "Chapter": ["annotations", "questionUuids", "text", "title"],
    "Question": ["annotations", "answerUuids", "referenceUuids", "text", "title"],
    "Answer": ["advice", "annotations", "label", "metricMeasures"],
    "Metric": ["annotations", "description", "title"],
    "Reference": ["annotations", "label", "url"],
}

# Entities of these types that the model does not have are deleted.
MANAGED_TYPES = {"Chapter", "Question", "Answer", "Metric", "Reference"}

# The list on its parent that holds an entity of each type.
PARENT_LIST = {
    "Chapter": "chapterUuids", "Metric": "metricUuids", "Tag": "tagUuids",
    "Integration": "integrationUuids", "Phase": "phaseUuids",
    "ResourceCollection": "resourceCollectionUuids", "Answer": "answerUuids",
    "Reference": "referenceUuids", "Expert": "expertUuids", "Choice": "choiceUuids",
}
QUESTION_LIST = {"Chapter": "questionUuids", "Answer": "followUpUuids",
                 "Question": "itemTemplateQuestionUuids"}

ACTIONS = ("Add", "Edit", "Delete", "Move")


# ---------------------------------------------------------------- replay

def split_event_type(event_type: str) -> tuple[str, str]:
    """'AddChapterEvent' -> ('Add', 'Chapter')."""
    for action in ACTIONS:
        if event_type.startswith(action) and event_type.endswith("Event"):
            return action, event_type[len(action):-len("Event")]
    raise ValueError(f"unknown event type {event_type}")


def km_uuid(state: dict) -> str:
    return next(u for u, e in state.items() if e["type"] == "KnowledgeModel")


def list_on_parent(state: dict, parent: str, kind: str) -> list:
    field = QUESTION_LIST[state[parent]["type"]] if kind == "Question" else PARENT_LIST[kind]
    return state[parent].setdefault(field, [])


def new_entity(kind: str, parent: str | None) -> dict:
    entity = {"type": kind, "parent": parent}
    for field in EDIT_FIELDS.get(kind, []):
        entity[field] = [] if field.endswith("Uuids") or field in ("annotations", "metricMeasures") else None
    if kind == "Question":
        entity["questionType"] = "OptionsQuestion"
    if kind == "Reference":
        entity["referenceType"] = "URLReference"
    return entity


def remove(state: dict, uid: str) -> None:
    for child in [u for u, e in state.items() if e["parent"] == uid]:
        remove(state, child)
    del state[uid]


def apply(state: dict, event: dict) -> None:
    """Apply one event to the state, the way DSW does."""
    content = event["content"]
    action, kind = split_event_type(content["eventType"])
    uid = event["entityUuid"]
    if action == "Add":
        if kind == "KnowledgeModel":
            parent = None
        else:
            parent = event["parentUuid"]
            # The first 0.0.0 events give the nil UUID as the parent of chapters and metrics.
            if parent not in state and PARENT_LIST.get(kind) in EDIT_FIELDS["KnowledgeModel"]:
                parent = km_uuid(state)
        entity = new_entity(kind, parent)
        entity.update({k: copy.deepcopy(v) for k, v in content.items() if k != "eventType"})
        state[uid] = entity
        if parent is not None:
            list_on_parent(state, parent, kind).append(uid)
    elif action == "Edit":
        entity = state[uid]
        for field, value in content.items():
            if isinstance(value, dict) and "changed" in value:
                if value["changed"]:
                    entity[field] = copy.deepcopy(value["value"])
            elif field != "eventType":
                entity[field] = value
    elif action == "Delete":
        parent = state[uid]["parent"]
        list_on_parent(state, parent, kind).remove(uid)
        remove(state, uid)
    else:  # Move
        old_parent, new_parent = state[uid]["parent"], content["targetUuid"]
        list_on_parent(state, old_parent, kind).remove(uid)
        list_on_parent(state, new_parent, kind).append(uid)
        state[uid]["parent"] = new_parent


def replay(packages: list[dict], extra_events: list[dict] = ()) -> dict:
    """State after all events: {uuid: entity}, each with its fields, type and parent."""
    state: dict = {}
    for package in packages:
        for event in package["events"]:
            apply(state, event)
    for event in extra_events:
        apply(state, event)
    return state


# ---------------------------------------------------------------- target

def annotation(key: str, value: str) -> dict:
    return {"key": key, "value": value}


def annotated(entity: dict, key: str) -> str | None:
    return next((a["value"] for a in entity.get("annotations") or [] if a["key"] == key), None)


def number(weight: str) -> int | float:
    value = float(weight)
    return int(value) if value.is_integer() else value


def cell(text: str) -> str:
    """Text for a Markdown table cell: one line, with | escaped."""
    return " ".join(text.split()).replace("|", "\\|")


def levels_table(indicator: dict) -> str:
    """The indicator's levels as a table, lettered as DSW letters the answers.

    A table cell can't hold a list, and DSW's Markdown doesn't allow HTML such as
    <br>, so the criteria of a level are separated by bullets on one line.
    """
    rows = ["| Level | Criteria | Impact |", "|---|---|---|"]
    levels = sorted(indicator["maturityLevels"], key=lambda l: l["order"])
    for letter, level in zip(string.ascii_lowercase, levels):
        criteria = " • ".join(cell(c) for c in level.get("criteria") or [])
        rows.append(f"| **{letter}. {cell(level['title'])}** | {criteria} "
                    f"| {cell(level.get('impact') or '')} |")
    return "\n".join(rows)


def question_text(indicator: dict) -> str:
    text = indicator["indicatorLongDescription"]
    if indicator.get("indicatorBriefDescription"):
        text = f"*{indicator['indicatorBriefDescription']}*\n\n{text}"
    return f"{text}\n\n{levels_table(indicator)}"


def answer_label(level: dict) -> str:
    if level.get("briefDescription"):
        return f"{level['title']} – {level['briefDescription']}"
    return level["title"]


def build_target(model: dict, previous: dict, seed: dict | None) -> dict:
    """The knowledge model the events have to produce: {uuid: entity}."""
    km = km_uuid(previous)
    target = {km: copy.deepcopy(previous[km])}
    used = set()

    def match(kind: str, key: str, value: str) -> str:
        """UUID of the entity built from this id: from its annotation in the
        previous version, else from the 0.1.2 seed, else derived from the id."""
        uid = next((u for u, e in previous.items()
                    if e["type"] == kind and annotated(e, key) == value), None)
        if uid is None and seed is not None:
            candidate = seed.get(kind, {}).get(value)
            if candidate in previous and previous[candidate]["type"] == kind:
                uid = candidate
        if uid is None:
            uid = str(uuid.uuid5(NAMESPACE, f"{kind}:{value}"))
        if uid in used:
            raise ValueError(f"{kind} {value}: UUID {uid} is already used")
        used.add(uid)
        return uid

    def put(uid: str, kind: str, parent: str, **fields) -> None:
        entity = copy.deepcopy(previous[uid]) if uid in previous else new_entity(kind, parent)
        entity.update(parent=parent, **fields)
        target[uid] = entity

    def level_key(indicator: dict) -> tuple:
        return tuple(int(p) for p in indicator["indicatorLevel"].split("."))

    domains = sorted(model["domains"], key=lambda d: int(d["domainLevel"]))
    chapters, metrics = [], []
    for domain in domains:
        level = domain["domainLevel"]
        chapter = match("Chapter", "domainLevel", level)
        metric = match("Metric", "domainLevel", level)
        chapters.append(chapter)
        metrics.append(metric)
        put(metric, "Metric", km,
            title=domain["domainName"],
            description=domain["domainDescription"],
            annotations=[annotation("domainLevel", level)])

        questions = []
        indicators = sorted((i for i in model["indicators"] if i["domainLevel"] == level), key=level_key)
        for indicator in indicators:
            iid = indicator["indicatorId"]
            question = match("Question", "indicatorId", iid)
            questions.append(question)

            answers = []
            for lvl, weight in zip(sorted(indicator["maturityLevels"], key=lambda l: l["order"]),
                                   indicator["weights"]):
                answer = match("Answer", "levelId", lvl["levelId"])
                answers.append(answer)
                put(answer, "Answer", question,
                    label=answer_label(lvl),
                    advice=None,
                    annotations=[annotation("levelId", lvl["levelId"])],
                    metricMeasures=[{"measure": number(weight), "metricUuid": metric, "weight": 1}])

            reference = match("Reference", "indicatorId", iid)
            put(reference, "Reference", question,
                url=HANDBOOK_URL + iid,
                label="All levels of this indicator in the DS Handbook",
                annotations=[])

            put(question, "Question", chapter,
                title=indicator["indicator"],
                text=question_text(indicator),
                annotations=[annotation("indicatorId", iid),
                             annotation("indicatorDescription", indicator["indicatorDescription"])],
                answerUuids=answers,
                referenceUuids=[reference])

        put(chapter, "Chapter", km,
            title=domain["domainName"],
            text=domain["domainDescription"],
            annotations=[annotation("domainLevel", level)],
            questionUuids=questions)

    target[km].update(chapterUuids=chapters, metricUuids=metrics)
    return target


# ---------------------------------------------------------------- events

def walk(state: dict, uid: str):
    """Entities parent first, children in their list order."""
    yield uid
    entity = state[uid]
    for field in EDIT_FIELDS.get(entity["type"], []):
        if field.endswith("Uuids") and field != "tagUuids":
            for child in entity.get(field) or []:
                if child in state and state[child]["parent"] == uid:
                    yield from walk(state, child)


def diff(previous: dict, target: dict, package_id: str, created_at: str) -> list[dict]:
    """Events that turn the previous knowledge model into the target."""
    events: list[dict] = []
    km = km_uuid(target)

    def emit(event_type: str, uid: str, parent: str | None, content: dict) -> None:
        events.append({
            "content": {"eventType": event_type, **content},
            "createdAt": created_at,
            "entityUuid": uid,
            "parentUuid": parent or NIL_UUID,
            "uuid": str(uuid.uuid5(NAMESPACE, f"{package_id}/{len(events)}")),
        })

    order = list(walk(target, km))

    for uid in order:
        if uid not in previous:
            entity = target[uid]
            kind = entity["type"]
            emit(f"Add{kind}Event", uid, entity["parent"],
                 {f: copy.deepcopy(entity[f]) for f in ADD_FIELDS[kind]})

    for uid in order:
        if uid in previous and previous[uid]["parent"] != target[uid]["parent"]:
            kind = target[uid]["type"]
            emit(f"Move{kind}Event", uid, previous[uid]["parent"], {"targetUuid": target[uid]["parent"]})

    gone = {u for u, e in previous.items() if e["type"] in MANAGED_TYPES and u not in target}
    for uid in walk(previous, km_uuid(previous)):
        if uid in gone and previous[uid]["parent"] not in gone:
            emit(f"Delete{previous[uid]['type']}Event", uid, previous[uid]["parent"], {})

    state = copy.deepcopy(previous)
    for event in events:
        apply(state, event)
    for uid in order:
        entity, current = target[uid], state[uid]
        kind = entity["type"]
        changed = {f for f in MANAGED_FIELDS[kind] if current.get(f) != entity[f]}
        if not changed:
            continue
        content = {f: ({"changed": True, "value": copy.deepcopy(entity[f])} if f in changed
                       else {"changed": False})
                   for f in EDIT_FIELDS[kind]}
        if kind == "Question":
            content["questionType"] = current["questionType"]
        if kind == "Reference":
            content["referenceType"] = current["referenceType"]
        emit(f"Edit{kind}Event", uid, entity["parent"], content)

    return events


def check(previous_packages: list[dict], events: list[dict], target: dict) -> list[str]:
    """Replay the chain with the new events and compare the result with the target."""
    final = replay(previous_packages, events)
    problems = []
    for uid, entity in target.items():
        if uid not in final:
            problems.append(f"{entity['type']} {uid} is missing")
            continue
        for field in MANAGED_FIELDS[entity["type"]]:
            if final[uid].get(field) != entity[field]:
                problems.append(f"{entity['type']} {uid}: {field} differs")
    extra = {u for u, e in final.items() if e["type"] in MANAGED_TYPES} - set(target)
    problems += [f"{final[u]['type']} {u} should have been deleted" for u in sorted(extra)]
    return problems


# ---------------------------------------------------------------- package

def readme(model: dict) -> str:
    version = model["version"]["versionNumber"]
    return f"""# {NAME}

The Research Data Management (RDM) Maturity Model helps an organisation assess how \
well it supports research data management, and plan what to improve. It has \
{len(model["indicators"])} indicators in {len(model["domains"])} domains.

Each chapter is a domain and each question an indicator. The table in a question \
gives the criteria and the impact of each maturity level: choose the level your \
organisation has reached. The link under each question opens the indicator in the \
[DS Handbook]({HANDBOOK_URL}maturity-model). Each domain has a metric, scored with \
the weights of the chosen levels.

## Version {version}

{model["version"]["versionDescription"]}

## Source

This knowledge model is built from version {version} of the model in \
[rdm-maturity-model]({REPO_URL}), where its \
[contributors]({REPO_URL}/blob/v{version}/_data/contributors.yaml) are listed. \
To suggest a change, open an issue there.
"""


def version_tuple(version: str) -> tuple[int, ...]:
    return tuple(int(p) for p in version.split("."))


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__)
        return 2
    previous_bundle = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    model = json.loads(MODEL_JSON.read_text(encoding="utf-8"))

    version = model["version"]["versionNumber"]
    package_id = f"{ORGANIZATION_ID}:{KM_ID}:{version}"
    previous_id = previous_bundle["id"]
    if (previous_bundle["organizationId"], previous_bundle["kmId"]) != (ORGANIZATION_ID, KM_ID):
        print(f"{argv[1]} is {previous_id}, not a version of {ORGANIZATION_ID}:{KM_ID}")
        return 1
    if previous_bundle["metamodelVersion"] != METAMODEL_VERSION:
        print(f"{previous_id} has metamodel {previous_bundle['metamodelVersion']}; "
              f"this script writes metamodel {METAMODEL_VERSION}")
        return 1
    if version_tuple(version) <= version_tuple(previous_bundle["version"]):
        print(f"model version {version} is not newer than {previous_id}")
        return 1

    seed = json.loads(SEED_JSON.read_text(encoding="utf-8"))
    seed = seed if seed["knowledgeModel"] == previous_id else None

    previous = replay(previous_bundle["packages"])
    target = build_target(model, previous, seed)
    created_at = model["version"]["timestamp"]
    events = diff(previous, target, package_id, created_at)

    problems = check(previous_bundle["packages"], events, target)
    if problems:
        print(f"The events do not produce the model ({len(problems)} problems):")
        for problem in problems:
            print(f"  {problem}")
        return 1

    package = {
        "createdAt": created_at,
        "description": "Self-assessment of an organisation's research data management "
                       "services, in four domains",
        "events": events,
        "forkOfPackageId": previous_id,
        "id": package_id,
        "kmId": KM_ID,
        "license": "CC-BY-4.0",
        "mergeCheckpointPackageId": previous_id,
        "metamodelVersion": METAMODEL_VERSION,
        "name": NAME,
        "nonEditable": False,
        "organizationId": ORGANIZATION_ID,
        "phase": "ReleasedKnowledgeModelPackagePhase",
        "previousPackageId": previous_id,
        "readme": readme(model),
        "version": version,
    }
    bundle = {
        "id": package_id,
        "kmId": KM_ID,
        "metamodelVersion": METAMODEL_VERSION,
        "name": NAME,
        "organizationId": ORGANIZATION_ID,
        "packages": previous_bundle["packages"] + [package],
        "version": version,
    }
    Path(argv[2]).write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    counts: dict[str, int] = {}
    for event in events:
        action, _ = split_event_type(event["content"]["eventType"])
        counts[action] = counts.get(action, 0) + 1
    summary = ", ".join(f"{n} {a.lower()}" for a, n in counts.items()) or "no changes"
    print(f"{package_id} on top of {previous_id}: {summary} events")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
