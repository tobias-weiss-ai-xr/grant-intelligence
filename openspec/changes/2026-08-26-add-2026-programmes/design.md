# Design: Add 2026 Programmes + Source-Link Repair

## Context

See proposal.md — Why. The catalog is fully data-driven (`catalog.json`); matching, export, ingest, and dashboard all read it. A one-time link audit (HEAD + GET with browser User-Agent, 10–12 parallel workers, 12–15s timeout) separated real breakage (404/deprecated domains) from anti-bot blocks (403 on ec.europa.eu, NIH, HHMI, HFSP, Leverhulme, DAAD — fine in browsers, not touched).

## Goals / Non-Goals

**Goals:**
- Add only *verified* programmes (URL returns 200 at change time; deadline/rolling facts confirmed from the live page where possible).
- Fix every confirmed-broken `quelle` URL to its current live page.
- Remove the stale `dfg-graduate-school` duplicate cleanly (spec delta + tests).
- Keep all 9 categories and the existing data model intact; no schema change.

**Non-Goals:**
- Do **not** chase anti-bot 403 URLs (browser-valid) or the remaining unverifiable 404s (SNSF, UNESCO, Rosa-Luxemburg/HSS/SDW, ARC, CIHR) — each needs per-site research; tracked as backlog.
- No new categories, no code refactor, no `frist` inventions: entries with call-driven dates stay `frist: null` + `rolling` semantics as documented.

## Decisions

- **DFG URL scheme migration** — old `dfg.de/foerderung/foerdermoeglichkeiten/{einzelfoerderung|verbundfoerderung|personenfoerderung}/…` (404) → new `/de/foerderung/foerdermoeglichkeiten/programme/{einzelfoerderung|koordinierte-programme|infrastruktur/…}/…` (all 200-verified). Programme-specific mapping table in tasks.md.
- **BMBF → bundesweite Bekanntmachungs-Portale** — BMBF is now BMFTR (`bmftr.bund.de`); the 5 entries that pointed at the old `bekanntmachungen` list now point to the cross-ministry `foerderinfo.bund.de` portal (200-verified), which stays stable independent of ministry renames. Rationale: portal URL outlives ministry-domain churn; alternative (hard-coding `bmftr.bund.de` Bekanntmachungssuche) is valid too but more volatile.
- **MSCA hostname fix** — `msc-itn`/`msc-cofund` pointed at `marie-sklodowska-curieactions.ec.europa.eu` (wrong host, URLError). Correct host `marie-sklodowska-curie-actions.ec.europa.eu` verified; `doctoral-networks` and `cofund` paths 200-verified.
- **`dfg-graduate-school` removal** — the "Graduate School" line ended with the Excellence Initiative; `dfg-graduiertenkolleg` covers structured doctoral programmes (student/junior). Removing keeps the catalog honest (no fictional lived link). Spec requirement deleted via delta; `phd-grad-colleges` otherwise unchanged.
- **New entries use `status` honestly** — settled/rolling lines (`humboldt-feodor-lynen`, `dfg-int-veranstaltungen`, `msca-staff-exchanges` calls) get `laufend`/`zu-pruefen` per existing convention; call-dependent budgets stay `null`; every entry gets a non-empty `hinweis` (existing `polish` R3).
- **Spec addition for URL hygiene** — new `polish` requirement: no `quelle` may reference a known-404/deprecated URL (checked by a curated list rather than a live-HTTP test, to avoid flaky anti-bot CI failures).

## Risks / Trade-offs

- **Funder sites keep moving** → The `polish` spec requirement + a reviewed `links` audit script make regressions visible; catalog curator re-runs the audit before each FLASH milestone. Mitigation: audit script is deterministic (URL list), not live-network dependent.
- **Adding DFG international lines whose content is JS-rendered** → Verified the URLs are live; stipend/deadline facts are conservative (`hinweis` says "Stichtage/Infos via Portal bestätigen"). Mitigation: `status="zu-pruefen"` where any doubt.
- **Count churn (100→103)** → e2e tests hardcode `== 100` twice and the consistency story compares four surfaces; all are updated together and the dashboard data is regenerated in the same commit.

## Migration Plan

1. Edit `catalog.json` (add 4, remove 1, repair ~23 URLs, LOEWE refresh).
2. Update spec deltas + tests (counts).
3. Re-run `python3 mcp/validate` path + full pytest + mypy; regen dashboard data via `dashboard/sync-data.sh`; regen `docs/pilot-ergebnisse.md`.
4. Commit + push; deploy dashboard (existing GitHub Action).

## Open Questions

- None blocking. (Remaining broken-link backlog — SNSF, UNESCO, political-foundation stipend pages, ARC, CIHR — is tracked in tasks as `out of scope` for later rounds.)
