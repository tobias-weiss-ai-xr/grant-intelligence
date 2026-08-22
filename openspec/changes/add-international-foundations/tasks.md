# Tasks: Add International Foundations

## 1. Catalog entries

- [ ] Add 17 international foundation entries to `mcp/catalog.json`
  - [ ] EMBO – Fellowships & Young Investigators
  - [ ] HFSP – Human Frontier Science Program
  - [ ] Bill & Melinda Gates Foundation
  - [ ] Rockefeller Foundation
  - [ ] Alfred P. Sloan Foundation
  - [ ] Kavli Foundation
  - [ ] John Templeton Foundation
  - [ ] Howard Hughes Medical Institute (International)
  - [ ] Gordon and Betty Moore Foundation
  - [ ] Leverhulme Trust
  - [ ] Royal Society
  - [ ] JSPS – Japan Society for the Promotion of Science
  - [ ] ARC – Australian Research Council
  - [ ] CIHR – Canadian Institutes of Health Research
  - [ ] NSERC – Natural Sciences & Engineering Research Council
  - [ ] WHO/TDR – Tropical Disease Research
  - [ ] UNESCO – Research & Heritage
- [ ] Verify each entry: non-empty `hinweis`, valid `kategorie="International"`,
      valid `karriere`/`rolle` values, `quelle` is a real URL, `standDatum`
      is `"2026-08-20"`
- [ ] Add source group `international-foundations` to `mcp/sources.json`

## 2. Tests

- [ ] Add test cases in `mcp/test_cutting_edge.py` or `mcp/test_mvp.py` for
      each new entry (id present, kategorie=International, match_profile
      score ≥ 2 for matching profile)
- [ ] Run full test suite: `python3 -m pytest -q` — all tests must pass
- [ ] Run mypy: `python3 -m mypy mcp/*.py` — must be clean
- [ ] Run coverage: `python3 -m pytest --cov=mcp --cov-report=term-missing` —
      core modules at 100%

## 3. Documentation

- [ ] Update `docs/Datenquellen.md` — add new international foundations to
      Section 6 (International)
- [ ] Update `mcp/README.md` — update programme count (80 → 97)
- [ ] Update `CHANGELOG.md` — add entry for international foundations expansion

## 4. Validation

- [ ] Run `python3 -c "import json; ..."` to validate catalog.json integrity
- [ ] Run `python3 -m pytest -q` — 181+ tests, all green
- [ ] Commit and push
