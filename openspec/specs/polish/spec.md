# Spec: Polish

## Purpose

Data quality, consistency, and enum completeness for the grant catalog.

---

## Requirements

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

### Requirement: R5 — Source URLs point to live pages
No programme entry's `quelle` MAY reference a known-broken or deprecated URL (HTTP 404 or superseded domain/path). The curated list of verified replacements in the `2026-08-26-add-2026-programmes` change MUST be reflected in the catalog. This requirement is enforced via the curated link audit (deterministic URL list), not a live-HTTP test, to avoid flaky anti-bot failures.

#### Scenario: No known-404 quelle remains
Given the loaded catalog and the curated list of verified-broken URLs from the `2026-08-26-add-2026-programmes` change
When checking each programme `quelle` against that list
Then no `quelle` matches a deprecated domain/path (DFG pre-`/de/` paths, BMBF `bmbf.de` bekanntmachungen, LOEWE `/forschung/loewe`, wrong MSCA hostname, ERC `plus-grants`, etc.)

### Requirement: R6 — thematisch-offen ist ein Wildcard
Programme with `themen` containing `"thematisch-offen"` MUST be matchable for any non-empty search field, identical to `"frei"`/`"alle"`. (`_fits` treats all three as wildcards; without this, open-ended entries like `deutschlandstipendium`, `msc-itn`, `fritz-thyssen` are invisible in normal searches.)

#### Scenario: Open-ended programme is found
Given a researcher searching field `"Astroteilchenphysik"` as postdoc
When `match_profile()` is called with sufficient `top`
Then at least one `themen==["thematisch-offen"]` programme appears in results
