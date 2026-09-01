# catalog-lint Specification

## Purpose
TBD - created by archiving change catalog-quality-gate. Update Purpose after archive.

## Requirements

### Requirement: C1 — Catalog data-integrity linter

A new `mcp/catalog_lint.py` MUST lint the catalog against the project's data
rules. `lint_catalog(programme, today)` returns a list of `Finding` objects
(`pid`, `rule`, `severity`, `message`) and MUST NOT mutate the input.

- FAIL severities: `id-fehlt`, `name-fehlt`, `kategorie-ungueltig`,
  `status-ungueltig`, `frist-ungueltig` (not ISO), `hinweis-fehlt` (empty),
  `budget-null-statt-0`, `rolling-mit-frist`, `quelle-fehlt`, `duplicate-ids`.
- WARN severities: `frist-abgelaufen` (deadline before `today`, not rolling),
  `stand-datum-alt` (standDatum older than 60 days when `status=verifiziert`).
- The CLI supports `--catalog`, `--report PATH` (JSON report) and `--fail`
  (exit code 1 if any FAIL finding exists, 0 otherwise).

#### Scenario: Clean catalog yields no findings
- **GIVEN** a catalogue where every programme has id, name, valid
  kategorie/status, non-empty hinweis, null budgets, no rolling+frist, a
  quelle, a valid frist in the future and a fresh standDatum
- **WHEN** `catalog_lint.py` runs
- **THEN** the report result is `clean`, counts are `{fail:0, warn:0}` and the
  exit code is 0 even with `--fail`

#### Scenario: Expired deadline is a warning, not a failure
- **GIVEN** a programme whose frist lies 3 days in the past
- **WHEN** the linter runs with `--fail`
- **THEN** a `frist-abgelaufen` warning is reported, the report result is
  `warn`, and the exit code stays 0

#### Scenario: Structural defect fails the gate
- **GIVEN** a programme with an empty hinweis
- **WHEN** the linter runs with `--fail`
- **THEN** a `hinweis-fehlt` finding of severity `fail` is reported, the
  result is `problems`, and the exit code is 1

### Requirement: C2 — Scheduled catalog-lint CI

`.github/workflows/catalog-lint.yml` MUST run on a weekly schedule (Sunday
08:00 UTC), on `workflow_dispatch`, and on pushes touching
`mcp/catalog.json`, `mcp/catalog_lint.py`, or the workflow itself. It MUST
execute `catalog_lint.py --catalog mcp/catalog.json --report
catalog-lint-report.json --fail` and always upload the report as a workflow
artifact. The job fails (red) only when the `--fail` gate exits 1 (structural
defects), not on warnings.

#### Scenario: Weekly run on healthy catalog
- **GIVEN** a structurally clean catalog
- **WHEN** the workflow runs
- **THEN** the job is green and `catalog-lint-report.json` is uploaded

### Requirement: C3 — Honest expiry handling

A programme with a passed one-shot deadline MUST NOT keep an invented future
date and MUST NOT claim `verifiziert`. `erc-adg-2027` (deadline 2026-08-27
expired) MUST be set to `frist=null`, `status=zu-pruefen`, a fresh
`standDatum`, and a hinweis stating the 2026 deadline passed and the next call
must be checked against the portal.

#### Scenario: Expired ERC Advanced Grant is corrected
- **GIVEN** the catalogue entry `erc-adg-2027`
- **WHEN** the linter validates the catalogue
- **THEN** no `frist-abgelaufen` warning is emitted, the entry has
  `frist=null`, `status=zu-pruefen` and a hinweis pointing to portal checks
