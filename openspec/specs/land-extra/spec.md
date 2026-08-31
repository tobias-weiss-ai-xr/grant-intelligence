# Spec: land-extra

## Purpose

Requirements derived from grant catalog expansion changes.

---

# Spec: Land Extra

## Requirements

### Requirement: R1 — NRW MWK Wissenschaft entry
The catalog.json MUST include a `nrw-mwk-wissenschaft` programme entry for NRW state research funding (postdoc+junior+prof, all disciplines).

#### Scenario: Professor searches for NRW research funding
Given a researcher profile with `karriere="prof"` and `themen=["KI"]`
When `match_profile()` is called
Then `nrw-mwk-wissenschaft` appears in results with score ≥ 2

### Requirement: R2 — Hightech Agenda Bayern entry
The catalog.json MUST include a `hightech-agenda-bayern` programme entry for Bayern's €5.5B tech investment programme (postdoc+junior+prof, KI/Digital/Life Sciences).

#### Scenario: Junior researcher searches for AI funding in Bayern
Given a researcher profile with `karriere="junior"` and `themen=["KI"]`
When `match_profile()` is called
Then `hightech-agenda-bayern` appears in results with score ≥ 2
