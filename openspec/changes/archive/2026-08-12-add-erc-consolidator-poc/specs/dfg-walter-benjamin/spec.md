# Spec: DFG Walter Benjamin Programme

## ADDED Requirements

### Requirement: R1: DFG Walter Benjamin entry in catalog.json
The catalog.json MUST include a `dfg-walter-benjamin` programme entry.
- `id`: `dfg-walter-benjamin`
- `kategorie`: `DFG`
- `themen`: `["frei"]`
- `karriere`: `["postdoc"]`
- `rolle`: `["lead"]`
- `dauerJahre`: 3
- `frist`: `null`
- `rolling`: `true`
- `status`: `laufend`
- `quelle`: `https://www.dfg.de/foerderung/foerdermoeglichkeiten/programme/einzelfoerderung/walter-benjamin`
- `standDatum`: date of entry creation
- `hinweis`: `DFG-Forschungsstipendium fuer Postdocs, Rueckkehr/Neueinstieg. Rolling-Bewerbung via elan-Portal.`

#### Scenario: Postdoc searches for DFG funding
Given a researcher profile with `karriere="postdoc"` and `themen=["Medizin"]`
When `match_profile()` is called
Then `dfg-walter-benjamin` appears in results with score ≥ 2

### Requirement: R2: Sub-source in sources.yaml
The sources.yaml MUST include `walter-benjamin` as a sub-source under `dfg`.
- Add `walter-benjamin` under existing `dfg` source group with `url`, `type: manual`, `update_frequency: monthly`

#### Scenario: Source lookup for Walter Benjamin
Given `sources.yaml` is loaded
When `sources["dfg"]["quellen"]["walter-benjamin"]` is accessed
Then it contains the Walter Benjamin programme URL
