# Spec: fetch-persist

## Purpose

Requirements derived from initial grant catalog expansion (expand-grant-sources change).

---

## ADDED Requirements

### Requirement: Fetchers produce valid Programme records
The fetchers (`fetch_cost`, `fetch_eu_horizon`, `fetch_bmbf_rss`) SHALL produce
complete programme dictionaries that pass `Programm.from_dict()` validation.
Each fetched programme SHALL include all required fields: `id` (slug-based),
`name`, `kategorie` (derived from source), `themen` (derived from title or
default `["thematisch-offen"]`), `karriere` (default `[]` = open to all),
`rolle` (default `["lead"]`), `quelle` (source URL), `standDatum`
(fetch date), `status` (always `"zu-pruefen"`), and `hinweis` (source + fetch
note).

#### Scenario: BMBF RSS fetch produces valid programmes
- **WHEN** `fetch_bmbf_rss()` returns programmes.
- **THEN** each programme in `result.programmes` SHALL pass
  `Programm.from_dict()` without raising `ValueError`.

#### Scenario: Fetched programme has zu-pruefen status
- **WHEN** any fetcher produces a programme.
- **THEN** the programme's `status` SHALL be `"zu-pruefen"`.

#### Scenario: Fetched programme has today's standDatum
- **WHEN** any fetcher produces a programme.
- **THEN** the programme's `standDatum` SHALL be today's date in ISO format.

### Requirement: apply_fetch_updates function
The system SHALL provide an `apply_fetch_updates(updates, catalog_path)` function
in `fetchers.py` that: (1) validates each fetched programme via
`Programm.from_dict()`, (2) rejects invalid programmes with a logged error,
(3) merges valid programmes into the existing catalog via `merge_programmes()`,
(4) persists the updated catalog, and (5) appends an entry to the audit log
(`docs/update_log.md`) with timestamp, source, count of added/updated/rejected
programmes.

#### Scenario: Valid fetch results are merged into catalog
- **WHEN** `apply_fetch_updates([update_with_3_valid_programmes], catalog_path)`
  is called.
- **THEN** the catalog SHALL contain the 3 new programmes (upsert by ID).

#### Scenario: Invalid fetch results are rejected
- **WHEN** `apply_fetch_updates([update_with_invalid_programme], catalog_path)`
  is called and the programme fails `Programm.from_dict()`.
- **THEN** the programme SHALL NOT be added to the catalog; an error SHALL be
  logged; the audit log SHALL note the rejection.

#### Scenario: Audit log entry is created
- **WHEN** `apply_fetch_updates()` completes successfully.
- **THEN** a new line SHALL be appended to `docs/update_log.md` containing the
  date, source, and counts (added, updated, rejected).

### Requirement: fetch_manual uses fetcher results
The `fetch_manual()` function in `update_catalog.py` SHALL invoke the
corresponding fetcher from `fetchers.py` (instead of returning `None`) and
return the validated programme list, enabling `--fetch dfg,erc,bmbf` to produce
actual catalog updates.

#### Scenario: update_catalog --fetch persists changes
- **WHEN** `python3 update_catalog.py --fetch bmbf` is run and the BMBF RSS
  returns items.
- **THEN** the catalog SHALL be updated with the fetched items.

### Requirement: Status lifecycle for fetched entries
Fetched programme entries SHALL always have `status="zu-pruefen"`. A separate
manual step (via `server.ingest` or `update_catalog.py --validate-status`) is
required to change status to `"verifiziert"`. The system SHALL NOT
automatically promote fetched entries to `"verifiziert"`.

#### Scenario: Fetched entry stays zu-pruefen until manual verification
- **WHEN** a programme is added via `apply_fetch_updates()`.
- **THEN** its `status` SHALL be `"zu-pruefen"` regardless of source.

#### Scenario: Manual verification promotes status
- **WHEN** an admin updates a programme's `status` to `"verifiziert"` via
  `server.ingest`.
- **THEN** the programme SHALL retain `"verifiziert"` status after next fetch
  cycle (idempotent; existing verified entries are not downgraded).
