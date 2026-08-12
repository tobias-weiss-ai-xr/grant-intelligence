## Why

The EU Horizon Europe framework has 6 clusters (1–6) plus MSCA individual actions. Our catalog currently covers Cluster 4 (Digital), Cluster 5 (Climate), MSCA ITN, and MSCA COFUND — but misses:

1. **MSCA Postdoctoral Fellowships (PF)** — the flagship individual postdoc mobility scheme. Confirmed live with **deadline 9 September 2026** (€399M call). Up to 8 years post-PhD. European + Global types. This is the single biggest missing EU programme for postdocs.

2. **Horizon Europe Cluster 1 (Health)** — €8.5B health research programme. We have clusters 4 and 5 but not 1, 2, or 3.

3. **Horizon Europe Cluster 2 (Culture, Creativity, Inclusive Society)** — covers culture, media, social sciences, democracy research.

4. **Horizon Europe Cluster 3 (Civil Security for Society)** — covers security, disaster resilience, cybersecurity.

## What Changes

- Add 4 programme entries to `catalog.json`: `msca-pf`, `eu-horizon-health`, `eu-horizon-culture`, `eu-horizon-security`
- Add MSCA PF as sub-source under existing `msc` source group in `sources.yaml`
- Add tests for all 4 entries
- Update docs

## Capabilities

### New Capabilities
- `msca-postdoc-fellowships`: MSCA Postdoctoral Fellowships (European + Global)
- `eu-horizon-clusters`: Horizon Europe Clusters 1, 2, 3 (Health, Culture, Security)

### Modified Capabilities
_(none — all changes are additive)_

## Impact

- **catalog.json**: +4 programmes (62 → 66)
- **sources.yaml**: +1 sub-source under `msc`
- **EU coverage**: 7 → 11 programmes (MSCA: 2→3, Horizon clusters: 2→5)
- **Postdoc coverage**: significant — MSCA PF is a primary postdoc mobility grant
- **Tests**: 112 green (additive)
- **Affected docs**: Datenquellen.md, README.md, CHANGELOG.md
