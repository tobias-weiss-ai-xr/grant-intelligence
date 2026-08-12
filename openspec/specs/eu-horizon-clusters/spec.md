# Spec: eu-horizon-clusters

## Purpose

Requirements derived from grant catalog expansion changes.

---

# Spec: EU Horizon Europe Clusters 1, 2, 3

## ADDED Requirements

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
