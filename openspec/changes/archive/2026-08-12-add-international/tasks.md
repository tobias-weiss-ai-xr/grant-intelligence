# Tasks: add-international

## 1. Sources

- [x] 1.1 Add source group `nsf` to `sources.yaml`.
- [x] 1.2 Add source group `nih` to `sources.yaml`.
- [x] 1.3 Add source group `ukri` to `sources.yaml`.
- [x] 1.4 Add source group `dach-snsf-fwf` to `sources.yaml`.
- [x] 1.5 Add source group `wellcome` to `sources.yaml`.

## 2. Catalog entries

- [x] 2.1 Add `nsf-international` to `catalog.json` (International, postdoc+junior+prof, frei, partner, 3yr).
- [x] 2.2 Add `nih-international` to `catalog.json` (International, postdoc+prof, Medizin, partner, 5yr).
- [x] 2.3 Add `ukri-international` to `catalog.json` (International, postdoc+junior+prof, frei, lead+partner, 3yr).
- [x] 2.4 Add `dach-snsf-fwf` to `catalog.json` (International, postdoc+junior+prof, frei, lead+partner, 3yr).
- [x] 2.5 Add `wellcome-international` to `catalog.json` (International, postdoc+junior+prof, Gesundheit, lead+partner, 5yr).

## 3. Tests

- [x] 3.1 Validate all 5 entries via `Programm.from_dict()` — no `ValueError`.
- [x] 3.2 `match_profile()` returns NSF for prof+frei (score ≥ 2).
- [x] 3.3 `match_profile()` returns NIH for postdoc+Medizin (score ≥ 2).
- [x] 3.4 `match_profile()` returns UKRI for junior+frei (score ≥ 2).
- [x] 3.5 `match_profile()` returns DACH for postdoc+frei (score ≥ 2).
- [x] 3.6 `match_profile()` returns Wellcome for prof+Gesundheit (score ≥ 2).
- [x] 3.7 Full test suite green (112 tests, mypy clean).

## 4. Documentation

- [x] 4.1 Update `docs/Datenquellen.md` — add International section with NSF, NIH, UKRI, DACH, Wellcome.
- [x] 4.2 Update `README.md` — programme count (70 → 75).
- [x] 4.3 Update `CHANGELOG.md` — entry under Unreleased.
