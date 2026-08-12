# Tasks: polish-and-improve

## 1. Enum & Types

- [x] 1.1 Add `BUND` and `INTERNATIONAL` to `Kategorie` enum.
- [x] 1.2 Add `Kategorie.is_valid()` classmethod.
- [x] 1.3 Fix docstring: "Pydantic models" → "dataclass models".

## 2. Catalog Data

- [x] 2.1 Fix 40 budget entries: `0` → `null`.
- [x] 2.2 Add hinweis for 4 programmes (erc-stg, erc-adg, erc-syg, dfg-sachbeihilfe).

## 3. Defaults & Docstrings

- [x] 3.1 Update `server.py programs()` docstring — add Bund, International.
- [x] 3.2 Change `brief.py --top` default from 3 to 5.

## 4. Tests

- [x] 4.1 Add `test_kein_budget_null` — no budget=0 in catalog.
- [x] 4.2 Add `test_alle_haben_hinweis` — all programmes have hints.
- [x] 4.3 Add `test_kategorien_vollstaendig` — all categories in Kategorie enum.
- [x] 4.4 Full test suite green (115 tests, mypy clean).

## 5. Documentation

- [x] 5.1 Update CHANGELOG.md.
