# Spec: Polish

Delta for `polish`.

## ADDED Requirements

### Requirement: R5 — Source URLs point to live pages
No programme entry's `quelle` MAY reference a known-broken or deprecated URL (HTTP 404 or superseded domain/path). The curated list of verified replacements in this change MUST be reflected in the catalog. This requirement is enforced via the curated link audit (deterministic URL list), not a live-HTTP test, to avoid flaky anti-bot failures.

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
