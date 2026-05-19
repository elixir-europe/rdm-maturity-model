[![Generate JSON and YAML from KM file](https://github.com/elixir-europe/rdm-maturity-model/actions/workflows/km-to-json.yml/badge.svg)](https://github.com/elixir-europe/rdm-maturity-model/actions/workflows/km-to-json.yml)

# RDM Maturity Model

The **Research Data Management (RDM) Maturity Model** is a framework designed to assess the capabilities of institutions in managing research data effectively.
It provides a structured approach to evaluate various aspects of RDM practices, helping organizations identify strengths and areas for improvement.

The model is organized into several domains, each representing a key area of research data management:

- Strategy and sustainability
- Legal and governance
- RDM support
- Data and metadata management

The RDM Maturity Model is a product of the [RDM Community](https://elixir-europe.org/communities/research-data-management)
of the European life sciences infrastructure [ELIXIR](https://elixir-europe.org/).

## Guidance

For guidance on how to use the RDM Maturity Model and an explanation of the covered topics and indicators,
please refer to the [DS Handbook](https://elixir-europe.github.io/ds-handbook/maturity-model).

## Repository structure

| Path | Contents |
|---|---|
| `model/` | DSW Knowledge Model (`.km`) — source of truth |
| `_data/` | Generated `maturity_model.json` and `maturity_model.yaml` |
| `scripts/` | `km_to_json.py` — extraction script used by CI |

## Availability

The RDM Maturity Model is available under the [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/) license.

The generated outputs can be downloaded directly from this repository:

- [maturity_model.json](_data/maturity_model.json)
- [maturity_model.yaml](_data/maturity_model.yaml)

The model is also available as a knowledge model in the [DSW Registry](https://registry.ds-wizard.org/knowledge-models/),
enabling direct use within [Data Stewardship Wizard](https://ds-wizard.org/) instances.

## Version information

Version: 0.1.3  
Release date: 2026-05-19
