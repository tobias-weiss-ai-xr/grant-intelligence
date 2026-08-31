# Spec: eu-horizon-clusters

## Purpose

Requirements derived from grant catalog expansion for Horizon Europe and MSCA programmes.

---

## Requirements

### Requirement: R1 — Horizon Europe Cluster 1 (Health) entry
The catalog.json MUST include a `eu-horizon-health` programme entry for health/medical research consortia (postdoc+junior+prof, Medizin/Gesundheit themes).

#### Scenario: Postdoc searches for health research funding
Given a researcher profile with `karriere="postdoc"` and `themen=["Medizin"]`
When `match_profile()` is called
Then `eu-horizon-health` appears in results with score ≥ 2

### Requirement: R2 — Horizon Europe Cluster 2 (Culture) entry
The catalog.json MUST include a `eu-horizon-culture` programme entry for culture/creativity/social sciences (postdoc+junior+prof, Kultur/Sozialwissenschaften themes).

#### Scenario: Junior researcher searches for culture funding
Given a researcher profile with `karriere="junior"` and `themen=["Kultur"]`
When `match_profile()` is called
Then `eu-horizon-culture` appears in results with score ≥ 2

### Requirement: R3 — Horizon Europe Cluster 3 (Security) entry
The catalog.json MUST include a `eu-horizon-security` programme entry for civil security/cybersecurity (postdoc+junior+prof, Cybersicherheit themes).

#### Scenario: Professor searches for cybersecurity funding
Given a researcher profile with `karriere="prof"` and `themen=["Cybersicherheit"]`
When `match_profile()` is called
Then `eu-horizon-security` appears in results with score ≥ 2

### Requirement: R4 — MSCA Staff Exchanges (SE) entry
The catalog.json MUST include an `msc-staff-exchanges` programme entry for the Horizon Europe Marie Skłodowska-Curie Actions Staff Exchanges scheme (`kategorie="EU"`, `karriere` covering postdoc/junior/prof, `themen=["thematisch-offen"]`). Its `quelle` MUST point to `https://marie-sklodowska-curie-actions.ec.europa.eu/actions/staff-exchanges` (200-verified). Non-empty `hinweis` required.

#### Scenario: Postdoc searches for EU mobility/exchange funding
Given a researcher profile with `karriere="postdoc"` and `themen=["thematisch-offen"]`
When `match_profile()` is called with sufficient `top`
Then `msc-staff-exchanges` appears in results with score ≥ 2
