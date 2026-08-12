## Why

The Förder-Radar catalog has three critical gaps for postdoctoral researchers:

1. **ERC Consolidator Grant (CoG)** — the middle ERC scheme (7–12 years experience, up to €2M) is missing. We have StG, AdG, and SyG, but CoG is the primary grant for postdocs transitioning to independence. Confirmed live on `erc.europa.eu`.

2. **ERC Proof of Concept (PoC)** — bridges ERC frontier research to market/societal application. Confirmed live on `erc.europa.eu`. Essential for innovation transfer, only accessible to ERC grantees.

3. **DFG Walter Benjamin Programme** — the DFG's flagship postdoc return/re-entry fellowship (up to 3 years, rolling). Confirmed via DFG sitemap (`/programme/einzelfoerderung/walter-benjamin`). This is the single biggest gap for German postdocs — without it, the catalog misses the most important DFG postdoctoral programme.

## What Changes

- Add 3 programme entries to `catalog.json`: `erc-cog-2027`, `erc-poc`, `dfg-walter-benjamin`
- Add 2 source groups to `sources.yaml`: `erc-cog`, `erc-poc` (DFG Walter Benjamin already covered by existing `dfg` source)
- Add 1 source sub-entry under `dfg` for Walter Benjamin programme page
- Add tests for the 3 new entries (validation + matching)
- Update `docs/Datenquellen.md` with ERC CoG and PoC URLs
- Update `README.md` programme count

## Capabilities

### New Capabilities
- `erc-consolidator-poc`: ERC Consolidator Grant and Proof of Concept programme entries
- `dfg-walter-benjamin`: DFG Walter Benjamin Programme (postdoc re-entry fellowship)

### Modified Capabilities
_(none — all changes are additive)_

## Impact

- **catalog.json**: +3 programmes (52 → 55)
- **sources.yaml**: +2 source groups + 1 sub-source
- **Postdoc coverage**: 23 → 26 programmes (largest single jump)
- **Tests**: 112 → 115+ (additive, no breaking changes)
- **Affected docs**: Datenquellen.md, README.md, CHANGELOG.md
