# Tasks: Add International Foundations

## 1. Catalog entries

- [x] Add 17 international foundation entries to `mcp/catalog.json`
  - [x] EMBO – Fellowships & Young Investigators
  - [x] HFSP – Human Frontier Science Program
  - [x] Bill & Melinda Gates Foundation
  - [x] Rockefeller Foundation
  - [x] Alfred P. Sloan Foundation
  - [x] Kavli Foundation
  - [x] John Templeton Foundation
  - [x] Howard Hughes Medical Institute (International)
  - [x] Gordon and Betty Moore Foundation
  - [x] Leverhulme Trust
  - [x] Royal Society
  - [x] JSPS – Japan Society for the Promotion of Science
  - [x] ARC – Australian Research Council
  - [x] CIHR – Canadian Institutes of Health Research
  - [x] NSERC – Natural Sciences & Engineering Research Council
  - [x] WHO/TDR – Tropical Disease Research
  - [x] UNESCO – Research & Heritage
- [x] Verify each entry: non-empty `hinweis`, valid `kategorie="International"`,
      valid `karriere`/`rolle` values, `quelle` is a real URL, `standDatum`
      is `"2026-08-20"`
- [x] Add source group `international-foundations` to `mcp/sources.json`

## 2. Tests

- [x] Add test cases in `mcp/test_mvp.py` for each new entry (id present,
      kategorie=International, match_profile score ≥ 2 for matching profile)
- [x] Run full test suite: `python3 -m pytest -q` — all tests must pass
- [x] Run mypy: `python3 -m mypy mcp/*.py` — must be clean
- [x] Run coverage: `python3 -m pytest --cov=mcp --cov-report=term-missing` —
      core modules at 100%

## 3. Documentation

- [x] Update `docs/Datenquellen.md` — add new international foundations to
      Section 6 (International)
- [x] Update `mcp/README.md` — update programme count (80 → 97)
- [x] Update `CHANGELOG.md` — add entry for international foundations expansion

## 4. Validation

- [x] Run `python3 -c "import json; ..."` to validate catalog.json integrity
- [x] Run `python3 -m pytest -q` — 181 tests, all green
- [x] Commit and push
