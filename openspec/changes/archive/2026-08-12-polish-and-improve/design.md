# Design: polish-and-improve

## 1. Kategorie Enum

Add missing values:
```python
class Kategorie(Enum):
    DFG = "DFG"
    ERC = "ERC"
    BMBF = "BMBF"
    EU = "EU"
    LAND = "Land"
    STIFTUNG = "Stiftung"
    INDUSTRIE = "Industrie"
    BUND = "Bund"
    INTERNATIONAL = "International"
```

Add `is_valid()` classmethod (like `Status` and `Karrierestufe` already have).

## 2. Catalog Data Fixes

### budget_min/budget_max: 0 → null
40 programmes have `"budget_min": 0, "budget_max": 0`. These should be `null` — `0` implies "zero EUR budget" which is semantically wrong. The `Programm` dataclass already accepts `int | None`, and `budget_beschreibung()` returns `""` for falsy values.

### Missing hinweis (4 entries)
| id | hinweis |
|---|---|
| erc-stg-2027 | ERC Starting Grant. Bottom-up, exzellente Forschung. Alle Disziplinen. Rolling. |
| erc-adg-2027 | ERC Advanced Grant. Etablierte Forscherpersönlichkeiten. Alle Disziplinen. Rolling. |
| erc-syg-2027 | ERC Synergy Grant. 2-4 PIs, transdisziplinäre Großprojekte. Rolling. |
| dfg-sachbeihilfe | DFG Einzelprojektförderung. Alle Disziplinen, Bottom-up. Rolling. |

## 3. Docstring Fixes

| File | Change |
|---|---|
| grant_types.py | "Pydantic models" → "dataclass models" |
| server.py programs() | Add Bund, International to docstring |

## 4. Brief Default Top

`brief.py`: `--top` default `3` → `5` (match app.py's behavior).

## Verification

All changes are additive/fixes. No new tests needed. Existing 112 tests must remain green.
