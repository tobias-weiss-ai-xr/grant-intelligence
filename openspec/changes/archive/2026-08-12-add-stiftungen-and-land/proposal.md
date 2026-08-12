## Why

Three major German funding organisations are missing from the catalog despite being verified live:

1. **Humboldt Forschungsstipendium** — Germany's flagship international research fellowship for inbound/outbound postdocs. We have `humboldt-prof` (professur) but not the core research fellowship. Confirmed live at `humboldt-foundation.de/bewerben/foerderprogramme/humboldt-forschungsstipendium`.

2. **Robert Bosch Stiftung** — one of Germany's largest private foundations, funding health, education, and global issues research. Confirmed live at `bosch-stiftung.de/foerderung`.

3. **NRW MWK Wissenschaft** — Nordrhein-Westfalen's Ministry for Culture and Science is Germany's most populous state's science ministry. We have Hessen (LOEWE) and Bayern (Max Weber) but not NRW. Confirmed live at `mkw.nrw/wissenschaft`.

Additionally, the **Hightech Agenda Bayern** (STMWK) is a €5.5B state-level research investment programme — significant enough for catalog inclusion. Confirmed live at `stmwk.bayern.de/wissenschaftler/hightech-agenda-bayern.html`.

**Skipped (not verifiable)**: Alfried Krupp (website down), VW Momentum (renamed/ended), BayINNO (not found).

## What Changes

- Add 4 programme entries to `catalog.json`: `humboldt-forschungsstipendium`, `robert-bosch-stiftung`, `nrw-mwk-wissenschaft`, `hightech-agenda-bayern`
- Add 4 source groups to `sources.yaml`
- Add tests for all 4 entries
- Update docs

## Capabilities

### New Capabilities
- `stiftungen-extra`: Humboldt Forschungsstipendium, Robert Bosch Stiftung
- `land-extra`: NRW MWK Wissenschaft, Hightech Agenda Bayern

### Modified Capabilities
_(none — all changes are additive)_

## Impact

- **catalog.json**: +4 programmes (66 → 70)
- **sources.yaml**: +4 source groups
- **Stiftung**: 20 → 22, **Land**: 3 → 5
- **Tests**: 112 green (additive)
- **Affected docs**: Datenquellen.md, README.md, CHANGELOG.md
