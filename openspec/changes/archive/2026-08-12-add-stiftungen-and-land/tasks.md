# Tasks: add-stiftungen-and-land

## 1. Sources

- [x] 1.1 Add source group `humboldt-forschungsstipendium` to `sources.yaml`.
- [x] 1.2 Add source group `robert-bosch-stiftung` to `sources.yaml`.
- [x] 1.3 Add source group `nrw-mwk` to `sources.yaml`.
- [x] 1.4 Add source group `hightech-agenda-bayern` to `sources.yaml`.

## 2. Catalog entries

- [x] 2.1 Add `humboldt-forschungsstipendium` to `catalog.json` (Stiftung, postdoc+junior+prof, frei, 2yr, rolling, laufend).
- [x] 2.2 Add `robert-bosch-stiftung` to `catalog.json` (Stiftung, postdoc+junior+prof, Gesundheit/Bildung, 3yr, laufend).
- [x] 2.3 Add `nrw-mwk-wissenschaft` to `catalog.json` (Land, postdoc+junior+prof, frei, 5yr, laufend).
- [x] 2.4 Add `hightech-agenda-bayern` to `catalog.json` (Land, postdoc+junior+prof, KI/Digital/Life Sciences, 5yr, laufend).

## 3. Tests

- [x] 3.1 Validate all 4 entries via `Programm.from_dict()` — no `ValueError`.
- [x] 3.2 `match_profile()` returns Humboldt for postdoc (score ≥ 2).
- [x] 3.3 `match_profile()` returns Bosch for postdoc+Gesundheit (score ≥ 2).
- [x] 3.4 `match_profile()` returns NRW MWK for prof (score ≥ 2).
- [x] 3.5 `match_profile()` returns Hightech Agenda Bayern for junior+KI (score ≥ 2).
- [x] 3.6 Full test suite green (112 tests, mypy clean).

## 4. Documentation

- [x] 4.1 Update `docs/Datenquellen.md` — add Humboldt, Bosch, NRW MWK, HTA Bayern.
- [x] 4.2 Update `README.md` — programme count (66 → 70).
- [x] 4.3 Update `CHANGELOG.md` — entry under Unreleased.
