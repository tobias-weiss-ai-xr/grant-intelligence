# Spec: International Funders

## ADDED Requirements

### Requirement: R1 — NSF entry
The catalog.json MUST include a `nsf-international` programme entry for US National Science Foundation international collaboration (postdoc+junior+prof, partner role).

#### Scenario: Professor searches for all funding (frei theme)
Given a researcher profile with `karriere="prof"` and `themen=["frei"]`
When `match_profile()` is called with sufficient `top`
Then `nsf-international` appears in results with score ≥ 2

### Requirement: R2 — NIH entry
The catalog.json MUST include a `nih-international` programme entry for US NIH biomedical collaboration (postdoc+prof, Medizin themes).

#### Scenario: Postdoc searches for medical research funding
Given a researcher profile with `karriere="postdoc"` and `themen=["Medizin"]`
When `match_profile()` is called with sufficient `top`
Then `nih-international` appears in results with score ≥ 2

### Requirement: R3 — UKRI entry
The catalog.json MUST include a `ukri-international` programme entry for UK-German bilateral research (postdoc+junior+prof, lead+partner).

#### Scenario: Junior researcher searches for international collaboration
Given a researcher profile with `karriere="junior"` and `themen=["frei"]`
When `match_profile()` is called with sufficient `top`
Then `ukri-international` appears in results with score ≥ 2

### Requirement: R4 — DACH SNSF/FWF entry
The catalog.json MUST include a `dach-snsf-fwf` programme entry for DACH bilateral cooperation (postdoc+junior+prof, lead+partner).

#### Scenario: Postdoc searches for DACH cooperation
Given a researcher profile with `karriere="postdoc"` and `themen=["frei"]`
When `match_profile()` is called with sufficient `top`
Then `dach-snsf-fwf` appears in results with score ≥ 2

### Requirement: R5 — Wellcome Trust entry
The catalog.json MUST include a `wellcome-international` programme entry for global health research (postdoc+junior+prof, Gesundheit themes).

#### Scenario: Professor searches for global health funding
Given a researcher profile with `karriere="prof"` and `themen=["Gesundheit"]`
When `match_profile()` is called with sufficient `top`
Then `wellcome-international` appears in results with score ≥ 2
