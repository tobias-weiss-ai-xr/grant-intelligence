# Tasks: add-erc-consolidator-poc

## 1. Sources

- [x] 1.1 Add source group `erc-cog` to `sources.yaml` (URL: `erc.europa.eu/apply-grant/consolidator-grant`, `type: manual`, `update_frequency: quarterly`).
- [x] 1.2 Add source group `erc-poc` to `sources.yaml` (URL: `erc.europa.eu/apply-grant/proof-concept`, `type: manual`, `update_frequency: quarterly`).
- [x] 1.3 Add sub-source `walter-benjamin` under `dfg` in `sources.yaml`.

## 2. Catalog entries

- [x] 2.1 Add `erc-cog-2027` to `catalog.json` (ERC, postdoc+junior, frei, up to €2M, 5yr, zu-pruefen).
- [x] 2.2 Add `erc-poc` to `catalog.json` (ERC, postdoc+junior+prof, Innovation+Transfer, up to €150K, 1yr, rolling, zu-pruefen).
- [x] 2.3 Add `dfg-walter-benjamin` to `catalog.json` (DFG, postdoc, frei, 3yr, rolling, laufend).

## 3. Tests

- [x] 3.1 Validate all 3 entries via `Programm.from_dict()` — no `ValueError`.
- [x] 3.2 `match_profile()` returns CoG for postdoc+junior.
- [x] 3.3 `match_profile()` returns PoC for Innovation/Transfer theme.
- [x] 3.4 `match_profile()` returns Walter Benjamin for postdoc.
- [x] 3.5 Full test suite green (112+ tests, mypy clean).

## 4. Documentation

- [x] 4.1 Update `docs/Datenquellen.md` — add ERC CoG, ERC PoC, Walter Benjamin.
- [x] 4.2 Update `README.md` — programme count (52 → 55).
- [x] 4.3 Update `CHANGELOG.md` — entry under Unreleased.
