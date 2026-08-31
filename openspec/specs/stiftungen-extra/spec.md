# Spec: stiftungen-extra

## Purpose

Requirements derived from grant catalog expansion for foundation programme coverage.

---

## Requirements

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

### Requirement: R3 — Humboldt Feodor Lynen Fellowship entry
The catalog.json MUST include a `humboldt-feodor-lynen` programme entry for the Alexander von Humboldt Foundation Feodor Lynen Research Fellowship (`kategorie="Stiftung"`, `karriere=["postdoc"]`, rolling applications). Its `quelle` MUST point to `https://www.humboldt-foundation.de/bewerben/foerderprogramme/feodor-lynen-forschungsstipendium` (200-verified, page confirms "Postdoc oder erfahrene Forschende"). Non-empty `hinweis` required.

#### Scenario: Postdoc searches for German outgoing mobility funding
Given a researcher profile with `karriere="postdoc"` and `themen=["thematisch-offen"]`
When `match_profile()` is called with sufficient `top`
Then `humboldt-feodor-lynen` appears in results with score ≥ 2
