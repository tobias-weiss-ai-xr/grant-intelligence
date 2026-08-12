# Tasks: add-dfg-personenfoerderung

## 1. Sources

- [x] 1.1 Add 7 program sub-sources under `dfg` in `sources.yaml`: reinhart-koselleck, forschungsgruppen, schwerpunktprogramme, kolleg-forschungsgruppen, klinische-forschungsgruppen, wissenschaftliche-netzwerke, forschungsimpulse.

## 2. Catalog entries

- [x] 2.1 Add `dfg-reinhart-koselleck` to `catalog.json` (DFG, prof+senior, frei, up to €1.25M, 5yr, stichtage).
- [x] 2.2 Add `dfg-forschungsgruppen` to `catalog.json` (DFG, postdoc+junior+prof, frei, 5yr, stichtage).
- [x] 2.3 Add `dfg-schwerpunktprogramme` to `catalog.json` (DFG, all career, frei, 6yr, stichtage).
- [x] 2.4 Add `dfg-kolleg-forschungsgruppen` to `catalog.json` (DFG, postdoc+junior+prof, frei, 4yr, stichtage).
- [x] 2.5 Add `dfg-klinische-forschungsgruppen` to `catalog.json` (DFG, postdoc+prof, Medizin, 4yr, stichtage).
- [x] 2.6 Add `dfg-wissenschaftliche-netzwerke` to `catalog.json` (DFG, postdoc+junior+prof, frei, 3yr, stichtage).
- [x] 2.7 Add `dfg-forschungsimpulse` to `catalog.json` (DFG, postdoc+junior+prof, frei, 3yr, stichtage).

## 3. Tests

- [x] 3.1 Validate all 7 entries via `Programm.from_dict()` — no `ValueError`.
- [x] 3.2 `match_profile()` returns Reinhart Koselleck for prof+senior.
- [x] 3.3 `match_profile()` returns Forschungsgruppen for junior.
- [x] 3.4 `match_profile()` returns Schwerpunktprogramme for student (all levels).
- [x] 3.5 `match_profile()` returns Klinische Forschungsgruppen for postdoc+Medizin.
- [x] 3.6 `match_profile()` returns Wissenschaftliche Netzwerke and Forschungsimpulse for postdoc.
- [x] 3.7 Full test suite green (112 tests, mypy clean).

## 4. Documentation

- [x] 4.1 Update `docs/Datenquellen.md` — add all 7 DFG programmes.
- [x] 4.2 Update `README.md` — programme count (55 → 62).
- [x] 4.3 Update `CHANGELOG.md` — entry under Unreleased.
