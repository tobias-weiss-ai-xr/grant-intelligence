# Spec: EU Horizon Clusters

Delta for `eu-horizon-clusters`.

## ADDED Requirements

### Requirement: R4 — MSCA Staff Exchanges (SE) entry
The catalog.json MUST include an `msc-staff-exchanges` programme entry for the Horizon Europe Marie Skłodowska-Curie Actions Staff Exchanges scheme (`kategorie="EU"`, `karriere` covering postdoc/junior/prof, `themen=["thematisch-offen"]`). Its `quelle` MUST point to `https://marie-sklodowska-curie-actions.ec.europa.eu/actions/staff-exchanges` (200-verified). Non-empty `hinweis` required.

#### Scenario: Postdoc searches for EU mobility/exchange funding
Given a researcher profile with `karriere="postdoc"` and `themen=["thematisch-offen"]`
When `match_profile()` is called with sufficient `top`
Then `msc-staff-exchanges` appears in results with score ≥ 2
