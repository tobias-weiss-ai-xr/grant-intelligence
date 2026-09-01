# Spec: Deadline Pipeline

Delta for `deadline-pipeline`.

## ADDED Requirements

### Requirement: D1 — Structured deadline digest

A new `mcp/deadline_digest.py` module MUST compute a structured deadline digest
from the catalog:

- `compute_digest(programme, today, urgent_days=30, upcoming_days=90)` returns
  a dict with `stand`, `urgent`, `upcoming`, `expired` and `counts`.
- `urgent` = deadlines within `0..urgent_days` days (inclusive), sorted
  ascending by days-to-deadline; `upcoming` = `0..upcoming_days`, sorted;
  `expired` = past deadlines (not rolling), longest-expired first.
- Every entry carries `{id, name, kategorie, frist, tage_bis_frist, rolling,
  status, quelle}`.
- Rolling programmes are counted (`counts.rolling`) but never listed as a
  deadline; programmes without a parseable/invalid `frist` are ignored without
  crashing.
- `save_digest(digest, path)` / `load_digest(path)` persist/load a JSON digest
  (UTF-8, indent 2); `load_digest` returns `None` for missing or unreadable
  files.

#### Scenario: Digest of a small catalog
- **GIVEN** a catalogue with one programme due in 10 days, one due in 60 days
  and one overdue by 5 days
- **WHEN** `compute_digest` runs with `urgent_days=30, upcoming_days=90`
- **THEN** `counts` equals `{urgent:1, upcoming:2, expired:1, rolling:0}` and
  upcoming is sorted by days-to-deadline ascending

#### Scenario: Rolling and invalid deadlines do not crash
- **GIVEN** a catalogue with one rolling programme and one with `frist="bald"`
- **WHEN** `compute_digest` runs
- **THEN** the rolling count is 1, urgent/upcoming remain 0, and no exception
  is raised

### Requirement: D2 — Deduplicated urgent deadlines

`diff_urgent(new_digest, old_digest)` MUST return only the urgent entries whose
`id` was not present in the previous digest's `urgent` list (deduplication).
With no previous digest (`None`), ALL current urgent entries count as new;
entries that left the urgent set (e.g. expired) MUST never count as new.
The CLI (`deadline_digest.py`) MUST load the previous digest from `--out`
before saving, store `neu_urgent` in the written digest, and support `--check`
to print only without writing.

#### Scenario: Second run reports nothing new
- **GIVEN** a digest already saved with urgent id `x`
- **WHEN** `deadline_digest.py --out <same path>` runs again with the same
  catalogue
- **THEN** the stored digest has `neu_urgent == 0` and stdout says no new
  urgent deadlines

#### Scenario: First run flags all current urgent deadlines
- **GIVEN** no previous digest file exists
- **WHEN** `deadline_digest.py` runs
- **THEN** every currently-urgent entry is reported as new (`neu_urgent` equals
  the urgent count)

### Requirement: D3 — Scheduled GitHub Action with issue reporting

A `.github/workflows/deadline-check.yml` MUST run weekly (Sunday 06:00 UTC)
and via `workflow_dispatch`. It MUST compute the digest, commit
`mcp/deadline-digest.json` only when it changed, and — when `neu_urgent > 0` —
open a GitHub Issue labelled `deadline-warning` listing the new urgent
deadlines, or append a comment to an existing open issue with that label.
Permissions: `contents: write`, `issues: write`.

#### Scenario: New urgent deadline shoots an issue
- **GIVEN** a run where `neu_urgent > 0` and no open `deadline-warning` issue
- **WHEN** the workflow's issue step executes
- **THEN** a new issue titled with the new-deadline count is created and
  labelled `deadline-warning`

#### Scenario: No new deadlines stays silent
- **GIVEN** a run where `neu_urgent == 0`
- **WHEN** the workflow's issue step executes
- **THEN** no issue is created and exit code is 0

### Requirement: D4 — Dashboard Frist-Radar panel

The static dashboard MUST show a "Frist-Radar" section: a table of upcoming
deadlines (next 90 days) sorted by date with columns Programm, Kategorie,
Frist, Tage, Status. Rows MUST be colour-coded by urgency: red ≤ 14 days,
orange ≤ 30 days, green > 30 days (CSS classes `dl-critical`/`dl-soon`/
`dl-normal`), with an "empty" hint when there are no deadlines. `sync-data.sh`
MUST copy `mcp/deadline-digest.json` into `dashboard/data/` when present,
without failing when absent.

#### Scenario: Deadlines render colour-coded
- **GIVEN** the dashboard page loaded with a catalogue containing urgent and
  non-urgent deadlines
- **WHEN** the Frist-Radar table renders
- **THEN** rows ≤ 14 days get `dl-critical`, rows ≤ 30 days `dl-soon`, and the
  table is sorted by Frist ascending
