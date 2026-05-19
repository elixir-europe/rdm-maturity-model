# CONTRIBUTING

**Note!** *This information is under development. Be aware that some information might not up to date.*

## _TODO_
 - Get rid of the Google Sheet as the Main Source of Truth (MSOT)
   - Make sure all information in the Google Sheet is captured and kept in this repository
   - Decide on the format of the MSOT: json or YAML
   - Decide date from which the Google Sheet will be deprecated
     - Edit the Google Sheet to make it obvious that it is deprecated and which file is the MSOT
   - Update workflow description
 - Idea for the future: consider using a DSW Knowledge Model to be the MSOT

## MM Workflow

The Maturity Model workflow is straightforward. Maintain the Maturity Model in the **master Google Sheet** ([RDM Maturity Model](https://docs.google.com/spreadsheets/d/1Uw3BYs5B49jZXAqP7PTOF4jfvVGpO8JhQ74fd2mcKCU/edit?gid=1393024628#gid=1393024628)) and then add it to the [rdm-maturity-model](https://github.com/elixir-europe/rdm-maturity-model) repo. Follow the steps below.

---

### Step-by-Step Instructions

#### 1. Make changes to the [RDM Maturity Model](https://docs.google.com/spreadsheets/d/1Uw3BYs5B49jZXAqP7PTOF4jfvVGpO8JhQ74fd2mcKCU/edit?gid=1393024628#gid=1393024628) sheet

- Bump the **version** and **description** in columns `A`, `B` of the `data` sheet.
- Optionally, name the current version in sheet history: _File > Version history > Name current version_.

#### 2. Export to JSON

- From the top menu go to **Export** and click **"MM in JSON format"** _(approve the script on first run)_.
- Copy the JSON from the dialog and save it as `maturity_model.json`.

#### 3. Update the model in the GitHub repository

Update [rdm-maturity-model/_data/maturity_model.json](https://github.com/elixir-europe/rdm-maturity-model/blob/main/_data/maturity_model.json) by either:

- Cloning the repo locally, replacing the file, and committing, **or**
- Editing the file directly on GitHub and committing.

#### 4. Automated JSON → YAML conversion (no action needed)

On every push to `main` or update to `_data/maturity_model.json`, a GitHub Action will automatically convert `maturity_model.json` to [`maturity_model.yaml`](https://github.com/elixir-europe/rdm-maturity-model/blob/main/_data/maturity_model.yaml) and commit it.

> ✅ The README badge should read **"Convert JSON to YAML and commit"** with a green **passing** status. If not, there is an error with the GH Action or the `maturity_model.json` file.

---

### ds-handbook Integration

The [ds-handbook](https://github.com/elixir-europe/ds-handbook) repository is configured to pull `maturity_model.yaml` from `rdm-maturity-model` automatically. This was accomplished by:

- **Submodule setup** — `rdm-maturity-model` is set as a submodule of `ds-handbook` (see [.gitmodules](https://github.com/elixir-europe/ds-handbook/blob/main/.gitmodules)).  
  > When cloning `ds-handbook`, use the `--recurse-submodules` flag to pull the submodule.
- **CI configuration** — The [Jekyll site CI](https://github.com/elixir-europe/ds-handbook/commit/ea4b714e0b161b896bd3204cfb043de86e506876) GitHub Action is set to pull changes from submodules before every build.
- **Direct model usage** — The model is used directly in Jekyll/Liquid code (e.g. [maturity-model.md](https://github.com/elixir-europe/ds-handbook/blob/743f807efd747ccb35747854e57344562d3455bf/pages/maturity-model.md?plain=1#L9)).

Every new build of `ds-handbook` (via the _Jekyll site CI_ action) will include the latest changes committed to `rdm-maturity-model`.

---

### Verifying the Pipeline

To confirm the full pipeline worked, compare the version numbers and comments across all three locations — they should all match:

| Source | Where to check |
|--------|---------------|
| RDM Maturity Model Google Sheet | Last non-empty row in [data!A5:A](https://docs.google.com/spreadsheets/d/1Uw3BYs5B49jZXAqP7PTOF4jfvVGpO8JhQ74fd2mcKCU/edit?gid=1393024628#gid=1393024628&range=A4) |
| `rdm-maturity-model` repository | `maturity_model.json` [version](https://github.com/elixir-europe/rdm-maturity-model/blob/122e52ecca70929450bb00096936f8ef5f86a690/_data/maturity_model.json#L3) |
| `ds-handbook` website | [Version information](https://elixir-europe.github.io/ds-handbook/maturity-model#version-information) |

---

## Content Authoring Guidelines

This section describes the intended meaning and conventions for each structural element of the model, to help keep content consistent across domains and versions.

### Domains

A **domain** is a thematic area grouping related indicators. The model currently has **4 domains**:

| # | Domain |
|---|---|
| 1 | Strategy and sustainability |
| 2 | Legal and governance |
| 3 | RDM support |
| 4 | Data and metadata management |

New domains should be introduced only when a coherent cluster of indicators does not fit any existing domain. The `domainLevel` annotation (set in DSW or in the `.km` file) controls display order and must be set explicitly when adding a domain.

**Domain description:** 1–2 sentences covering the thematic scope. Aim for 80–170 characters. Write in the form *"This area covers …"*.

---

### Indicators

An **indicator** is a single measurable aspect of RDM maturity within a domain. The model currently has **25 indicators** (7 / 4 / 6 / 8 per domain). Before adding a new indicator, check that it is not already captured by an existing one.

**Indicator title:** Short noun phrase (3–6 words), e.g. *"Strategy for RDM"*, *"IT security framework"*.

**Indicator description:** One sentence, starting with *"Indicates …"*, describing what the indicator measures and for whom. Aim for 80–160 characters. Avoid repeating the title verbatim.

**`indicatorId` annotation:** A stable kebab-case slug prefixed with `mm-`, e.g. `mm-strategy-defined`. Set this explicitly so the ID survives future title edits. If omitted, the script auto-derives it from the first six words of the title.

**Numbering (`indicatorLevel`):** Assigned automatically based on domain and question order in DSW. Do not hard-code numbers in descriptions.

---

### Maturity Levels

Each indicator has **3–5 maturity levels** (answers), ordered from lowest to highest maturity. Use **4 levels** as the default; add a 5th only when a meaningful intermediate step cannot be collapsed. Fewer than 3 levels is not allowed.

#### Progression pattern

| Position | Typical meaning |
|---|---|
| Level 1 (lowest) | Nothing in place — absent, ad hoc, or purely reactive |
| Level 2 | Initial / planned / informal — awareness exists but not formalised |
| Level 3 | Formalised / documented / approved — a defined process or policy exists |
| Level 4 | Actively used, communicated, or enforced across the organisation |
| Level 5 (optional) | Continuously reviewed, optimised, or institutionally embedded |

Each level must be a strict superset of the previous: reaching level *n* implies that levels 1 through *n−1* are also satisfied.

#### Wording

- Write each level as a **complete, self-contained statement** — a reader should understand it without reading the others.
- Use **present tense**, third person: *"RDM training is provided ad hoc…"*, not *"We provide…"* or *"Training will be…"*.
- Avoid vague qualifiers like *"some"*, *"a little"*, *"quite"*. Prefer observable criteria: *"approved by management"*, *"documented and publicly available"*.
- **Length:** Concise indicators (binary or near-binary criteria) may use 20–60 characters per level. Indicators covering complex or multi-faceted practices may use 100–250 characters. Do not pad short levels for the sake of consistency.

#### Weights

Weights run from `0` (lowest level) to `1.0` (highest level), distributed evenly. For a 4-level indicator the default weights are `0`, `0.33`, `0.66`, `1.0`. Do not assign a non-zero weight to the lowest level.

---

### General style notes

- Write for a **self-assessment audience**: the reader is an RDM professional evaluating their own institution, not an external auditor.
- Use **plain language**. Avoid jargon unless it is standard in the RDM field and would be familiar to the target audience.
- Be **institution-neutral**: prefer *"the organisation"* over *"the university"* or *"the institute"*.
- Keep tense and voice consistent within a domain.
