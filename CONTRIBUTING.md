# CONTRIBUTING

**Note!** *This information is under development. Be aware that some information might not up to date.*

## MM Workflow

`_data/maturity_model.json` is the source of truth for the Maturity Model. Edit it directly in this repository — there is no separate authoring surface to export from, and no generated copy of the model in another format.

> A [DSW Knowledge Model](https://registry.ds-wizard.org/knowledge-models/datarex:RDM-MM:0.1.2) of the model exists in the DSW Registry and may become the way the model is managed in future. Until that happens, `maturity_model.json` is the file to edit.

---

### Step-by-Step Instructions

#### 1. Edit the model

Change [`_data/maturity_model.json`](https://github.com/elixir-europe/rdm-maturity-model/blob/main/_data/maturity_model.json) by either:

- Cloning the repo locally, editing on a branch, and committing, **or**
- Editing the file directly on GitHub.

See the [Content Authoring Guidelines](#content-authoring-guidelines) below for what each field means and how to word it.

#### 2. Bump the version

Update `versionNumber`, `versionDescription` and `timestamp` in the `version` block at the top of the file. [Versioning](#versioning) explains how to choose between a patch, minor and major bump.

#### 3. Validate before opening the pull request

```bash
pip install check-jsonschema
check-jsonschema --schemafile _data/maturity_model.schema.json _data/maturity_model.json
python scripts/validate_model.py
```

Both run in CI as well, but catching a problem locally is faster than waiting for the action.

#### 4. Automated validation (no action needed)

On every pull request and every push to `main` that touches the model, the _Validate model_ GitHub Action checks `maturity_model.json` against [`maturity_model.schema.json`](https://github.com/elixir-europe/rdm-maturity-model/blob/main/_data/maturity_model.schema.json) and runs the cross-field checks in [`scripts/validate_model.py`](https://github.com/elixir-europe/rdm-maturity-model/blob/main/scripts/validate_model.py).

> ✅ The README badge should read **"Validate model"** with a green **passing** status. If not, there is an error in the `maturity_model.json` file — the action log names the offending indicator.

---

### ds-handbook Integration

The [ds-handbook](https://github.com/elixir-europe/ds-handbook) repository is configured to pull `maturity_model.json` from `rdm-maturity-model` automatically. This was accomplished by:

- **Submodule setup** — `rdm-maturity-model` is set as a submodule of `ds-handbook` (see [.gitmodules](https://github.com/elixir-europe/ds-handbook/blob/main/.gitmodules)).  
  > When cloning `ds-handbook`, use the `--recurse-submodules` flag to pull the submodule.
- **CI configuration** — The [Jekyll site CI](https://github.com/elixir-europe/ds-handbook/commit/ea4b714e0b161b896bd3204cfb043de86e506876) GitHub Action is set to pull changes from submodules before every build.
- **Direct model usage** — `ds-handbook/_data/shared` is a symlink to this repository's `_data/` directory, so Jekyll reads `maturity_model.json` as `site.data.shared.maturity_model` and the model is used directly in Liquid code (e.g. [maturity-model.md](https://github.com/elixir-europe/ds-handbook/blob/743f807efd747ccb35747854e57344562d3455bf/pages/maturity-model.md?plain=1#L9)).

Every new build of `ds-handbook` (via the _Jekyll site CI_ action) will include the latest changes committed to `rdm-maturity-model`.

---

### Verifying the Pipeline

To confirm the change reached the website, compare the version number and description in both locations — they should match:

| Source | Where to check |
|--------|---------------|
| `rdm-maturity-model` repository | `maturity_model.json` [version](https://github.com/elixir-europe/rdm-maturity-model/blob/main/_data/maturity_model.json#L2-L6) |
| `ds-handbook` website | [Version information](https://elixir-europe.github.io/ds-handbook/maturity-model#version-information) |

---

## Content Authoring Guidelines

This section describes the intended meaning and conventions for each structural element of the model, to help keep content consistent across domains and versions.

Most of what follows is editorial guidance. A smaller set of rules is actually enforced: [`_data/maturity_model.schema.json`](_data/maturity_model.schema.json) checks the shape of the file, and [`scripts/validate_model.py`](scripts/validate_model.py) checks the rules that compare one field with another. Both run in CI on any change under `_data/`. Rules marked **(enforced)** below will fail that build; the rest are conventions.

Run both locally before opening a PR:

```bash
pip install check-jsonschema
check-jsonschema --schemafile _data/maturity_model.schema.json _data/maturity_model.json
python scripts/validate_model.py
```

`_data/maturity_model.json` is the source of truth for the model — the file these guidelines describe, the file CI validates, and the file the DS Handbook renders. The handbook consumes it directly as `site.data.shared.maturity_model`, through a symlink to this repository as a submodule. There is no generated copy of the model in another format. A DSW knowledge model exists in the [DSW Registry](https://registry.ds-wizard.org/knowledge-models/datarex:RDM-MM:0.1.2), but it is not the source of truth and is not an authoring surface for this content.

---

### Domains

A **domain** is a thematic area grouping related indicators. The model currently has **4 domains**:

| # | Domain |
|---|---|
| 1 | Strategy and sustainability |
| 2 | Legal and governance |
| 3 | RDM support |
| 4 | Data and metadata management |

New domains should be introduced only when a coherent cluster of indicators does not fit any existing domain.

**`domainLevel`:** **(enforced)** The domain's number as a string — `"1"`, `"2"`, … — which controls display order. It is required on the domain entry *and* repeated on every indicator belonging to that domain; the two must agree.

**Domain description:** 1–2 sentences covering the thematic scope, written in the form *"This area covers …"*. Existing descriptions run 76–167 characters; aim for roughly 100–170.

---

### Indicators

An **indicator** is a single measurable aspect of RDM maturity within a domain. The model currently has **25 indicators** (7 / 4 / 6 / 8 per domain). Before adding a new indicator, check that it is not already captured by an existing one.

**Indicator title:** Short noun phrase, ideally 3–6 words, e.g. *"Strategy for RDM"*, *"IT security framework"*. Some existing titles are far longer because they enumerate their own scope — for new indicators, put that detail in the description rather than the title.

**Indicator description:** One sentence, starting with *"Indicates …"*, describing what the indicator measures and for whom. Aim for 80–170 characters. Avoid repeating the title verbatim.

**`indicatorId`:** **(enforced)** Required on every indicator, unique across the model, and matching `^mm-[a-z0-9]+(-[a-z0-9]+)*$` — a kebab-case slug prefixed with `mm-`, e.g. `mm-strategy-defined`. The DS Handbook uses it as the `page_id` of the corresponding indicator page, so renaming one breaks that link (see [Versioning](#versioning)).

**`indicatorLevel`:** **(enforced)** Position in the model as `domain.indicator`, e.g. `"3.2"`. Unique, and the part before the dot must equal the indicator's `domainLevel`. Do not restate the number inside titles or descriptions.

---

### Maturity Levels

Each indicator has **3–5 maturity levels** (answers), ordered from lowest to highest maturity. **(enforced)** Use **4 levels** as the default; add a 5th only when a meaningful intermediate step cannot be collapsed.

#### Progression pattern

| Position | Typical meaning |
|---|---|
| Level 1 (lowest) | Nothing in place — absent, ad hoc, or purely reactive |
| Level 2 | Initial / planned / informal — awareness exists but not formalised |
| Level 3 | Formalised / documented / approved — a defined process or policy exists |
| Level 4 | Actively used, communicated, or enforced across the organisation |
| Level 5 (optional) | Continuously reviewed, optimised, or institutionally embedded |

Each level should be a strict superset of the previous: reaching level *n* implies that levels 1 through *n−1* are also satisfied.

#### Wording

- Write each level as a **complete, self-contained statement** — a reader should understand it without reading the others.
- Use **present tense**, third person: *"RDM training is provided ad hoc…"*, not *"We provide…"* or *"Training will be…"*.
- Avoid vague qualifiers like *"some"*, *"a little"*, *"quite"*. Prefer observable criteria: *"approved by management"*, *"documented and publicly available"*.
- **Length:** There is no fixed range. The lowest level is often a bare phrase (*"None"*, *"Nothing offered"*); the levels above it typically run 60–200 characters. Keep the levels within one indicator roughly comparable in length, and split anything beyond about 250 characters — a level that long is usually two criteria that belong in separate levels.

#### Weights

**(enforced)** One weight per maturity level, written as a **string**, strictly increasing, with the highest level scoring `"1"`. Values must match `^(0|1|0\.[0-9]{1,2})$` — at most two decimal places, and the top weight is `"1"`, never `"1.0"`. Where a fraction does not divide evenly, the convention is to truncate rather than round: two thirds is `"0.66"`, not `"0.67"`.

Space the weights evenly. Where the lowest level means nothing is in place, start at `"0"`:

| Levels | Weights |
|---|---|
| 3 | `"0"`, `"0.5"`, `"1"` |
| 4 | `"0"`, `"0.33"`, `"0.66"`, `"1"` |
| 5 | `"0"`, `"0.25"`, `"0.5"`, `"0.75"`, `"1"` |

A non-zero lowest weight is fine where the lowest level still describes something the organisation has in place, rather than an absence. Keep the spacing even by stepping from `1/n`:

| Levels | Weights |
|---|---|
| 3 | `"0.33"`, `"0.66"`, `"1"` |
| 4 | `"0.25"`, `"0.5"`, `"0.75"`, `"1"` |
| 5 | `"0.2"`, `"0.4"`, `"0.6"`, `"0.8"`, `"1"` |

Both patterns are in use — seven indicators currently start at `"0.25"` or `"0.33"`, including all four in Legal and governance. Choose whichever matches the indicator: a zero floor when level 1 is an absence, a non-zero floor when it is a genuine starting position. Bear in mind that changing an existing indicator's weights shifts aggregated scores and is a major version bump (see [Versioning](#versioning)).

---

### General style notes

- Write for a **self-assessment audience**: the reader is an RDM professional evaluating their own institution, not an external auditor.
- Use **plain language**. Avoid jargon unless it is standard in the RDM field and would be familiar to the target audience.
- Be **institution-neutral**: prefer *"the organisation"* over *"the university"* or *"the institute"*.
- Keep tense and voice consistent within a domain.

---

### Versioning

The model follows [Semantic Versioning](https://semver.org/) (`MAJOR.MINOR.PATCH`) and is currently at **1.2.1**. The key question when choosing a version bump is: **would a previous self-assessment score still be comparable to a new one?**

#### Patch — `1.2.1` → `1.2.2`

Backwards-compatible fixes that do not change scoring or meaning:

- Typo, grammar, or punctuation corrections
- Clarifications that do not alter the intent of a level description
- Correcting a `domainLevel` or `indicatorLevel` that was inconsistent, without changing content
- Fixing a weight that was clearly incorrect (e.g. a level accidentally assigned the wrong value)
- Updating metadata fields (`timestamp`, `versionDescription`)

#### Minor — `1.2.x` → `1.3.0`

Backwards-compatible additions or improvements that extend the model:

- Adding a new indicator to an existing domain
- Adding a new domain
- Extending an indicator with an additional highest maturity level (raising the ceiling)
- Substantive rewording of level descriptions that sharpens precision without changing the scoring threshold
- Deprecating an indicator (marking it as deprecated while keeping it in place)
- Additive changes to the JSON schema (new optional fields, no removals)

#### Major — `1.x.y` → `2.0.0`

Breaking changes that make previous self-assessment scores incomparable or invalid:

- Removing or merging indicators
- Removing a domain
- Adding or removing a level from an existing indicator (changes the scoring distribution)
- Significant reordering of levels that changes what a given score means
- Changing weights in a way that materially affects aggregated scores
- Renaming an indicator's `indicatorId` (breaks the DS Handbook page link and any downstream reference)
- Breaking changes to the JSON schema (removing or renaming existing fields, tightening a pattern)

> When in doubt between minor and major, ask: *"If an organisation scored themselves last year using the previous version, would their score still be valid today?"* If yes, it is a minor or patch bump. If not, it is a major bump.
