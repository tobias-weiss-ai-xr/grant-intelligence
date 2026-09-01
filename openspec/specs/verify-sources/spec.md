# verify-sources Specification

## Purpose
TBD - created by archiving change verify-sources-workflow. Update Purpose after archive.

## Requirements

### Requirement: R1 — Repo-agnostic link verifier exists

The repository MUST contain a config-driven `verify_sources.py` CLI that accepts
a config file declaring one or more `inputs` (each a file + `list_key`/`object_map`
+ `id_field` + `url_fields`) and verifies every URL field. The same script MUST
work unchanged across repos (e.g. `catalog.json` `quelle` and `papers.yaml`
`url`/`code_url`/`project_url`).

#### Scenario: Run verifier against a corpus config
- **WHEN** `verify_sources.py CONFIG.yaml` is executed
- **THEN** the tool extracts every `(id, url, field)` tuple from the configured
  inputs and reports per-URL status without modifying any source file

### Requirement: R2 — Two-stage check with bot-block tolerance

The verifier MUST classify each URL in two stages: (1) HTTP via `requests`
→ `OK` / `BROKEN` (404/410/4xx/5xx/connection errors) / `UNCERTAIN`
(401/403/timeout/SSL); (2) optional Playwright recheck of `UNCERTAIN` →
`OK` / `BROKEN` / `BOTBLOCK`. Without a browser, `UNCERTAIN` MUST resolve to
`BOTBLOCK` (warning, never a failure), so official portals that bot-block
scripts are not reported as broken.

#### Scenario: Official portal returns 403 to scripts
- **GIVEN** a URL that returns HTTP 403 to automated requests but is a valid page
- **WHEN** the verifier runs without `--browser`
- **THEN** the URL is reported as `BOTBLOCK` and does NOT cause a non-zero exit
  when `fail_on_broken=true`

### Requirement: R3 — Scheduled CI audit with report artifact

Both repos MUST include `.github/workflows/verify-sources.yml` that runs the
verifier on a weekly schedule, on `workflow_dispatch`, and on changes to the
corpus/config, uploading the JSON report as an artifact (`if: always()`).
The job MUST fail only on definitively-dead links (not on bot-blocks).

#### Scenario: Weekly scheduled run on a healthy catalog
- **WHEN** the workflow runs and all URLs are `OK` or `BOTBLOCK`
- **THEN** the job exits 0 and uploads `verify-sources-report.json`
