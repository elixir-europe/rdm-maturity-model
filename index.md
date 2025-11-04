---
# Feel free to add content and custom Front Matter to this file.
# To modify the layout, see https://jekyllrb.com/docs/themes/#overriding-theme-defaults

layout: home
---
The **Research Data Management (RDM) Maturity Model** is a framework designed to assess the capabilities of institutions in managing research data effectively.
It provides a structured approach to evaluate various aspects of RDM practices, helping organizations identify strengths and areas for improvement.

The model is organized into several domains, each representing a key area of research data management:
* Strategy and sustainability
* Legal aspects
* Support and training
* Data and metadata management

The RDM Maturity Model is a product of the [RDM Community](https://elixir-europe.org/communities/research-data-management) 
of the European life sciences infrastructure [ELIXIR](https://elixir-europe.org/).

## RDM Maturity Model
<div class="accordion accordion-flush" id="indicatorsAccordion">
 {% for domain in site.data.maturity_model.domains %}
  <div class="accordion-item">
    <h3 class="accordion-header">
      <button class="accordion-button {% unless forloop.first %}collapsed{% endunless %}" 
              type="button"
              data-bs-toggle="collapse" 
              data-bs-target="#collapse2{{forloop.index}}" 
              aria-expanded="{% if forloop.first %}true{% else %}false{% endif %}" 
              aria-controls="collapse2{{forloop.index}}">
          <div class="container-fluid">
            <div class="row pb-1">
              <div class="col">
                <strong>{{ domain.domainName }}</strong>
              </div>
            </div>
            <div class="row">
              <div class="col">
                {{ domain.domainDescription }}
              </div>
            </div>
          </div>
      </button>
    </h3>
    <div id="collapse2{{forloop.index}}" class="accordion-collapse collapse {% if forloop.first %}show{% endif %}" data-bs-parent="#indicatorsAccordion">
      <div class="accordion-body">
        {% assign domain_indicators = site.data.maturity_model.indicators | where:"domain", domain.domainName %}
        {% if domain_indicators != empty %}
        <table class="table table-bordered table-striped">
          <thead>
            <tr>
              <th>Subdomain</th>
              <th>Indicator</th>
              <th>Maturity Levels</th>
            </tr>
          </thead>
          <tbody>
            {% for indicator in domain_indicators %}
            <tr>
              <td>{{ indicator.subdomain }}</td>
              <td>[{{ indicator.indicatorLevel }}] {{ indicator.indicator }}</td>
              <td>
                <ol>
                  {% for level in indicator.maturityLevels %}
                  <li>{{ level }}</li>
                  {% endfor %}
                </ol>
              </td>
            </tr>
            {% endfor %}
          </tbody>
        </table>
        {% endif %}
      </div>
    </div>
  </div>
  {% endfor %}
</div>
<p></p>

## Guidance
For guidance on how to use the RDM Maturity Model and explanation of covered topics and indicators,
please refer to the 
[DS Handbook](https://elixir-europe.github.io/ds-handbook/maturity-model).

## Availability
The RDM Maturity Model is available under the [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/) license.

It can be downloaded as [JSON](https://github.com/elixir-europe/rdm-maturity-model/blob/main/_data/maturity_model.json) and 
[YAML](https://github.com/elixir-europe/rdm-maturity-model/blob/main/_data/maturity_model.yaml) formats from the 
[GitHub](https://github.com/elixir-europe/rdm-maturity-model) repository.

## Version information
Version: {{ site.data.maturity_model.version.versionNumber }} [{{ site.data.maturity_model.version.versionDescription }}]  
Release date: {{ site.data.maturity_model.version.timestamp | date: "%Y-%m-%d" }}