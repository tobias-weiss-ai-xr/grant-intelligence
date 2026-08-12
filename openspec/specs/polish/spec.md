# Spec: Polish

## Purpose

Data quality, consistency, and enum completeness for the grant catalog.

---

# Spec: Polish

## ADDED Requirements

### Requirement: R1 — Kategorie enum complete
The `Kategorie` enum in `grant_types.py` MUST include all 9 categories present in the catalog (DFG, ERC, BMBF, EU, Land, Stiftung, Industrie, Bund, International) and MUST provide an `is_valid()` classmethod.

#### Scenario: International is valid
Given the string `"International"`
When `Kategorie.is_valid("International")` is called
Then it returns `True`

#### Scenario: Unknown category is invalid
Given the string `"Foobar"`
When `Kategorie.is_valid("Foobar")` is called
Then it returns `False`

### Requirement: R2 — Budget zero is null
All catalog entries with `"budget_min": 0` or `"budget_max": 0` MUST use `null` (JSON) instead. Zero means "zero Euro" which is semantically incorrect for programmes with unknown budgets.

#### Scenario: No programme has budget=0
Given the loaded catalog
When iterating all programme entries
Then no entry has `"budget_min": 0` or `"budget_max": 0`

### Requirement: R3 — All programmes have hinweis
Every programme entry in the catalog MUST have a non-empty `hinweis` string.

#### Scenario: No programme lacks hinweis
Given the loaded catalog
When iterating all programme entries
Then every entry has a non-empty `hinweis` field

### Requirement: R4 — Brief default top matches app
The `brief.py` CLI `--top` default MUST be 5, matching `app.py`'s behavior.

#### Scenario: Brief default
Given `brief.generate()` is called without explicit `top`
Then it returns up to 5 top matches (not 3)
