# Spec: dfg-einzelfoerderung-extra

## Purpose

Requirements derived from grant catalog expansion changes.

---

# Spec: DFG Einzelförderung Extra

## ADDED Requirements

### Requirement: R1 — DFG Reinhart Koselleck entry
The catalog.json MUST include a `dfg-reinhart-koselleck` programme entry for high-risk/high-gain professor funding (up to €1.25M, 5yr).

#### Scenario: Senior professor searches for high-risk funding
Given a researcher profile with `karriere="prof"` and `themen=["frei"]`
When `match_profile()` is called
Then `dfg-reinhart-koselleck` appears in results with score ≥ 2

### Requirement: R2 — DFG Wissenschaftliche Netzwerke entry
The catalog.json MUST include a `dfg-wissenschaftliche-netzwerke` programme entry for 3-year scientific networking (postdoc+junior+prof).

#### Scenario: Postdoc searches for networking programmes
Given a researcher profile with `karriere="postdoc"` and `themen=["frei"]`
When `match_profile()` is called
Then `dfg-wissenschaftliche-netzwerke` appears in results with score ≥ 2
