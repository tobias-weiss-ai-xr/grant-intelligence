# Spec: Stiftungen Extra

## ADDED Requirements

### Requirement: R1 — Humboldt Forschungsstipendium entry
The catalog.json MUST include a `humboldt-forschungsstipendium` programme entry for international research fellowships (postdoc+junior+prof, all disciplines, rolling).

#### Scenario: Postdoc searches for international fellowship
Given a researcher profile with `karriere="postdoc"` and `themen=["KI"]`
When `match_profile()` is called
Then `humboldt-forschungsstipendium` appears in results with score ≥ 2

### Requirement: R2 — Robert Bosch Stiftung entry
The catalog.json MUST include a `robert-bosch-stiftung` programme entry for health/education/global issues funding (postdoc+junior+prof).

#### Scenario: Postdoc searches for health funding
Given a researcher profile with `karriere="postdoc"` and `themen=["Gesundheit"]`
When `match_profile()` is called
Then `robert-bosch-stiftung` appears in results with score ≥ 2
