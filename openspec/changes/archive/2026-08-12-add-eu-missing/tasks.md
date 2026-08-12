# Tasks: add-eu-missing

## 1. Sources

- [x] 1.1 Add `msca-pf` sub-source under `msc` in `sources.yaml`.

## 2. Catalog entries

- [x] 2.1 Add `msca-pf` to `catalog.json` (EU, postdoc, frei, 2yr, frist 2026-09-09, zu-pruefen).
- [x] 2.2 Add `eu-horizon-health` to `catalog.json` (EU, postdoc+junior+prof, Medizin, 4yr, zu-pruefen).
- [x] 2.3 Add `eu-horizon-culture` to `catalog.json` (EU, postdoc+junior+prof, Kultur/Sozialwissenschaften, 4yr, zu-pruefen).
- [x] 2.4 Add `eu-horizon-security` to `catalog.json` (EU, postdoc+junior+prof, Cybersicherheit, 4yr, zu-pruefen).

## 3. Tests

- [x] 3.1 Validate all 4 entries via `Programm.from_dict()` — no `ValueError`.
- [x] 3.2 `match_profile()` returns MSCA PF for postdoc.
- [x] 3.3 `match_profile()` returns Horizon Health for postdoc+Medizin.
- [x] 3.4 `match_profile()` returns Horizon Culture for junior+Kultur.
- [x] 3.5 `match_profile()` returns Horizon Security for prof+Cybersicherheit.
- [x] 3.6 Full test suite green (112 tests, mypy clean).

## 4. Documentation

- [x] 4.1 Update `docs/Datenquellen.md` — add MSCA PF, Horizon Clusters 1-3.
- [x] 4.2 Update `README.md` — programme count (62 → 66).
- [x] 4.3 Update `CHANGELOG.md` — entry under Unreleased.
