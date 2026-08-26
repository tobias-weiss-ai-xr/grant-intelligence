# Add 2026 Programmes + Source-Link Repair

## Why

The catalogue should broaden its coverage for the Marburg Mathematics pilot (MSCA Staff Exchanges, DFG international measures, Humboldt Feodor Lynen) and its source links degraded as funders restructured their websites in 2025/26. A link audit of all `quelle` URLs found ~48 non-200 responses; after re-checking with browser User-Agents (anti-bot 403s are fine in real browsers), **23 links are genuinely broken** (404/deprecated):
- **DFG** restructured to `/de/.../programme/...` paths (10 entries broken).
- **BMBF** became **BMFTR** (`bmbf.de` → `bmftr.bund.de`); its `bekanntmachungen` path is dead (5 entries).
- **LOEWE/Hessen** moved to `/forschen/landesprogramm-loewe` (2 entries).
- **MSCA** entries `msc-itn`/`msc-cofund` point at a **wrong hostname** (`marie-sklodowska-curieactions` without the second hyphen group).
- **VW Stiftung, Studienstiftung (Max Weber), NRW MWK, Krebshilfe, ERC Plus** also moved.
- One stale duplicate (`dfg-graduate-school`) refers to the cancelled Excellence-Initiative Graduate Schools and duplicates `dfg-graduiertenkolleg`.

## What Changes

- **Add 4 verified programme entries** (all source URLs verified live):
  - `msc-staff-exchanges` (EU) — Horizon Europe MSCA Staff Exchanges
  - `humboldt-feodor-lynen` (Stiftung) — Feodor Lynen Research Fellowship
  - `dfg-int-kooperationen` (DFG) — Aufbau internationaler Kooperationen
  - `dfg-int-veranstaltungen` (DFG) — Internationale wissenschaftliche Veranstaltungen
- **Remove 1 stale duplicate**: `dfg-graduate-school` (defunct Excellence-Initiative line; Graduiertenkollegs already covered by `dfg-graduiertenkolleg`). **BREAKING for the `phd-grad-colleges` spec** (its requirement is deleted).
- **Repair 23 confirmed-broken `quelle` URLs** (each verified returning HTTP 200).
- **Refresh the LOEWE entry** to the current Förderrlinien structure (Zentren/Schwerpunkte/Professuren).
- **Codify a data-quality requirement** in the `polish` spec: no known-404/deprecated source URLs.
- Update e2e count assertions (100 → 103) and dashboard data/docs counts.

Net catalogue size: 100 → 103 programmes (9 categories unchanged).

## Capabilities

### New Capabilities
(none — all target existing capabilities)

### Modified Capabilities
- `eu-horizon-clusters`: ADD `msc-staff-exchanges` requirement.
- `stiftungen-extra`: ADD `humboldt-feodor-lynen` requirement.
- `dfg-einzelfoerderung-extra`: ADD `dfg-int-kooperationen` + `dfg-int-veranstaltungen` requirements.
- `phd-grad-colleges`: DELETE the `dfg-graduate-school` requirement (consolidated into `dfg-graduiertenkolleg`).
- `polish`: ADD requirement that no programme `quelle` references a known-404 or deprecated URL.

## Impact

- `mcp/catalog.json` — 4 new entries, 1 removed, ~23 URL repairs, LOEWE refresh.
- `mcp/test_e2e.py` — count assertions 100 → 103.
- `dashboard/` data + docs (README, Promo) — programme counts 100 → 103; `pilot-ergebnisse.md` regeneration.
- No code/API changes; matching, export, ingest are data-driven and unaffected functionally.
