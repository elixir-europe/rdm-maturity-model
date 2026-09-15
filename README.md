[![MM format conversion](https://github.com/elixir-europe/rdm-maturity-model/actions/workflows/convert-json-to-yaml.yml/badge.svg?branch=main)](https://github.com/elixir-europe/rdm-maturity-model/actions/workflows/convert-json-to-yaml.yml)
[![Model version](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Felixir-europe%2Frdm-maturity-model%2Fmain%2F_data%2Fmaturity_model.json&query=%24.version.versionNumber&label=model%20version&color=blue)](_data/maturity_model.json)

# RDM Maturity Model

The **Research Data Management (RDM) Maturity Model** is a framework designed to assess the capabilities of institutions in managing research data effectively.
It provides a structured approach to evaluate various aspects of RDM practices, helping organizations identify strengths and areas for improvement.

The model is organized into four domains, each representing a key area of research data management:
* Strategy and sustainability
* Legal and governance
* RDM support
* Data and metadata management

Across these domains the model defines **25 indicators**. Each indicator has three to five maturity levels,
ranging from no provision to fully implemented, and each level carries a weight between 0 and 1 that is used to score an assessment.

The RDM Maturity Model is a product of the [RDM Community](https://elixir-europe.org/communities/research-data-management)
of the European life sciences infrastructure [ELIXIR](https://elixir-europe.org/).

## Guidance
For guidance on how to use the RDM Maturity Model and explanation of covered topics and indicators,
please refer to the
[DS Handbook](https://elixir-europe.github.io/ds-handbook/maturity-model).

## Availability
The RDM Maturity Model is available under the [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/) license.

It can be downloaded as [JSON](_data/maturity_model.json) and
[YAML](_data/maturity_model.yaml) formats from the
[rdm-maturity-model](https://github.com/elixir-europe/rdm-maturity-model) repository.

The model is also published as a knowledge model in the
[DSW Registry](https://registry.ds-wizard.org/knowledge-models/datarex:RDM-MM:0.1.2),
so it can be imported into any [Data Stewardship Wizard](https://ds-wizard.org/) instance.
Knowledge model `datarex:RDM-MM:0.1.2` carries its own version numbering and corresponds to
model version 1.2.1.

## Version information
[![Model version](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Felixir-europe%2Frdm-maturity-model%2Fmain%2F_data%2Fmaturity_model.json&query=%24.version.versionNumber&label=model%20version&color=blue)](_data/maturity_model.json)
[![Version description](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Felixir-europe%2Frdm-maturity-model%2Fmain%2F_data%2Fmaturity_model.json&query=%24.version.versionDescription&label=description&color=lightgrey)](_data/maturity_model.json)
[![Released](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Felixir-europe%2Frdm-maturity-model%2Fmain%2F_data%2Fmaturity_model.json&query=%24.version.timestamp&label=released&color=blue)](_data/maturity_model.json)

The badges above are read directly from the `version` block of
[`_data/maturity_model.json`](_data/maturity_model.json) on `main`, so they follow the model without manual updates.
The same version is shown on the
[DS Handbook maturity model page](https://elixir-europe.github.io/ds-handbook/maturity-model#version-information).

## Contributors

The model is the work of contributors from across the RDM Community, listed with
their affiliations and ORCIDs in [`_data/contributors.yaml`](_data/contributors.yaml).

The DS Handbook renders that list on its
[maturity model page](https://elixir-europe.github.io/ds-handbook/maturity-model#contributors).
