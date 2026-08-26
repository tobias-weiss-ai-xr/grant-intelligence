# Spec: PhD & Graduate Colleges

Delta for `phd-grad-colleges`.

## DELETED Requirements

### Requirement: DFG Graduate School programme entry
The `dfg-graduate-school` entry (kategorie="DFG", karriere=["student","junior"], themen=["thematisch-offen"], rolling=False, status="zu-pruefen") is REMOVED from the catalog. It duplicated `dfg-graduiertenkolleg` and referenced the defunct Excellence-Initiative "Graduate School" line. Structured doctoral programmes remain covered by `dfg-graduiertenkolleg` (see `dfg-koordinierte-programme`).

#### Scenario: (obsolete) DFG Graduate School visible for PhD students
- **WHEN** `match_profile()` is called with `karriere="junior"`.
- **THEN** (removed) — `dfg-graduate-school` no longer appears; `dfg-graduiertenkolleg` provides the coverage.

## ADDED Requirements

### Requirement: URL hygiene for phd-grad entries
The `msc-itn` and `msc-cofund` entries MUST use the correct MSCA hostname `https://marie-sklodowska-curie-actions.ec.europa.eu` (paths `/actions/doctoral-networks` resp. `/actions/cofund`, both 200-verified). The `max-weber-bayern` entry MUST point to `https://www.studienstiftung.de/max-weber-programm` (200-verified).

#### Scenario: Source links resolve
Given the catalog
When resolving `msc-itn.quelle`, `msc-cofund.quelle`, `max-weber-bayern.quelle`
Then all three resolve to live pages (HTTP 200)
