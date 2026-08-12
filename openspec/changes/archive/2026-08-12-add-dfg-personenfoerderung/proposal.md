## Why

The DFG is Germany's largest research funder, yet our catalog only covers 5 of 10 einzelfoerderung programmes and 1 of 7 koordinierte-programme. After adding Walter Benjamin (change `add-erc-consolidator-poc`), the biggest gaps are:

1. **Reinhart Koselleck Projects** — DFG's high-risk/high-gain programme for experienced professors (up to €1.25M, 5 years). Confirmed live at `dfg.de/.../reinhart-koselleck-projekte`.
2. **Koordinierte Programme** (6 missing): Forschungsgruppen, Schwerpunktprogramme, Kolleg-Forschungsgruppen, Klinische Forschungsgruppen — all confirmed live at `dfg.de/.../koordinierte-programme/`. Plus two einzelfoerderung bonuses discovered: Wissenschaftliche Netzwerke and Forschungsimpulse.

Dropping **1.000-Köpfe-Plus** — not found on live DFG site (likely ended pilot).

## What Changes

- Add 7 programme entries to `catalog.json`:
  - `dfg-reinhart-koselleck` (einzelfoerderung, prof, high-risk/high-gain)
  - `dfg-forschungsgruppen` (koordiniert, postdoc+prof, 5yr collaborative)
  - `dfg-schwerpunktprogramme` (koordiniert, all career levels, thematic priority)
  - `dfg-kolleg-forschungsgruppen` (koordiniert, postdoc+prof, interdisciplinary)
  - `dfg-klinische-forschungsgruppen` (koordiniert, postdoc+prof, clinical)
  - `dfg-wissenschaftliche-netzwerke` (einzelfoerderung, postdoc+junior, networking)
  - `dfg-forschungsimpulse` (koordiniert, postdoc+junior+prof, rapid-response)
- Add 7 sub-sources under `dfg` in `sources.yaml`
- Add tests for all 7 entries
- Update docs

## Capabilities

### New Capabilities
- `dfg-einzelfoerderung-extra`: Reinhart Koselleck, Wissenschaftliche Netzwerke (einzelfoerderung additions)
- `dfg-koordinierte-programme`: Forschungsgruppen, Schwerpunktprogramme, Kolleg-Forschungsgruppen, Klinische Forschungsgruppen, Forschungsimpulse (all koordinierte-programme)

### Modified Capabilities
_(none — all changes are additive)_

## Impact

- **catalog.json**: +7 programmes (55 → 62)
- **sources.yaml**: +7 sub-sources under `dfg`
- **DFG coverage**: 11 → 18 programmes (complete for listed DFG programmes)
- **Tests**: 112 → 115+ (additive)
- **Affected docs**: Datenquellen.md, README.md, CHANGELOG.md
