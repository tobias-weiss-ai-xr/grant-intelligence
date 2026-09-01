# Spec: Stiftungen Extra

Delta for `stiftungen-extra`.

## ADDED Requirements

### Requirement: R3 — Humboldt Feodor Lynen Fellowship entry
The catalog.json MUST include a `humboldt-feodor-lynen` programme entry for the Alexander von Humboldt Foundation Feodor Lynen Research Fellowship (`kategorie="Stiftung"`, `karriere=["postdoc"]`, rolling applications). Its `quelle` MUST point to `https://www.humboldt-foundation.de/bewerben/foerderprogramme/feodor-lynen-forschungsstipendium` (200-verified, page confirms "Postdoc oder erfahrene Forschende"). Non-empty `hinweis` required.

#### Scenario: Postdoc searches for German outgoing mobility funding
Given a researcher profile with `karriere="postdoc"` and `themen=["thematisch-offen"]`
When `match_profile()` is called with sufficient `top`
Then `humboldt-feodor-lynen` appears in results with score ≥ 2
