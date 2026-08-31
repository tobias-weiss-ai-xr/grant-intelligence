# Spec: dfg-koordinierte-programme

## Purpose

Requirements derived from grant catalog expansion changes.

---

# Spec: DFG Koordinierte Programme

## Requirements

### Requirement: R1 — DFG Forschungsgruppen entry
The catalog.json MUST include a `dfg-forschungsgruppen` programme entry for 5-year collaborative research groups (postdoc+junior+prof).

#### Scenario: Junior researcher searches for collaborative funding
Given a researcher profile with `karriere="junior"` and `themen=["frei"]`
When `match_profile()` is called
Then `dfg-forschungsgruppen` appears in results with score ≥ 2

### Requirement: R2 — DFG Schwerpunktprogramme entry
The catalog.json MUST include a `dfg-schwerpunktprogramme` programme entry for 6-year thematic priority programmes (all career levels, lead+member).

#### Scenario: Student searches for DFG thematic programmes
Given a researcher profile with `karriere="student"` and `themen=["frei"]`
When `match_profile()` is called
Then `dfg-schwerpunktprogramme` appears in results with score ≥ 1

### Requirement: R3 — DFG Kolleg-Forschungsgruppen entry
The catalog.json MUST include a `dfg-kolleg-forschungsgruppen` programme entry for 4-year interdisciplinary groups (postdoc+junior+prof).

#### Scenario: Postdoc searches for interdisciplinary groups
Given a researcher profile with `karriere="postdoc"` and `themen=["frei"]`
When `match_profile()` is called
Then `dfg-kolleg-forschungsgruppen` appears in results with score ≥ 2

### Requirement: R4 — DFG Klinische Forschungsgruppen entry
The catalog.json MUST include a `dfg-klinische-forschungsgruppen` programme entry for 4-year clinical research groups (postdoc+prof, medical themes).

#### Scenario: Postdoc searches for clinical research
Given a researcher profile with `karriere="postdoc"` and `themen=["Medizin"]`
When `match_profile()` is called
Then `dfg-klinische-forschungsgruppen` appears in results with score ≥ 2

### Requirement: R5 — DFG Forschungsimpulse entry
The catalog.json MUST include a `dfg-forschungsimpulse` programme entry for 3-year rapid-response funding (postdoc+junior+prof).

#### Scenario: Professor searches for urgent/emerging research funding
Given a researcher profile with `karriere="prof"` and `themen=["frei"]`
When `match_profile()` is called
Then `dfg-forschungsimpulse` appears in results with score ≥ 2
