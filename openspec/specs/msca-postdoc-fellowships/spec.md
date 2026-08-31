# Spec: msca-postdoc-fellowships

## Purpose

Requirements derived from grant catalog expansion changes.

---

# Spec: MSCA Postdoctoral Fellowships

## Requirements

### Requirement: R1 — MSCA Postdoctoral Fellowships entry
The catalog.json MUST include a `msca-pf` programme entry for the MSCA Postdoctoral Fellowships action (max 8 years post-PhD, European + Global, all disciplines).

#### Scenario: Postdoc searches for EU mobility funding
Given a researcher profile with `karriere="postdoc"` and `themen=["KI"]`
When `match_profile()` is called
Then `msca-pf` appears in results with score ≥ 2

### Requirement: R2 — MSCA PF sub-source in sources.yaml
The sources.yaml MUST include `msca-pf` as a sub-source under `msc` with URL pointing to the MSCA PF action page.

#### Scenario: Source lookup for MSCA PF
Given `sources.yaml` is loaded
When `sources["msc"]` is accessed
Then it contains a program entry for `msca-pf`
