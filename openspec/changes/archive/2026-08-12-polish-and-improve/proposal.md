# OpenSpec Change: polish-and-improve

## Why

After 5 deep-dive expansions (32→75 programmes), several polish items accumulated:
- **Kategorie Enum outdated**: `International` missing from `Kategorie` enum (not validated at runtime, but misleading)
- **40 programmes have budget=0**: Should be `null` (JSON `null` = Python `None`) per convention — `0` means "zero EUR" which is wrong; most just don't have published budgets
- **4 programmes missing `hinweis`**: ERC StG, AdG, SyG and DFG Sachbeihilfe lack hints
- **Stale docstring**: `grant_types.py` says "Pydantic models" but uses dataclasses
- **Server docstring outdated**: `programs()` docstring doesn't list `International` or `Bund`
- **Brief `top` default=3**: In `brief.py` CLI, the `--top` default is still 3, but `app.py` was bumped to 5 — inconsistency
- **Export CSV has empty budget columns**: `budget_min`/`budget_max` all `""` or `0` — noise

## What

Fix all data quality, docstring, and consistency issues. No new features, no breaking changes.

## Capabilities

### Modified: grant-types
- Add `INTERNATIONAL = "International"` and `BUND = "Bund"` to `Kategorie` enum
- Fix docstring (remove "Pydantic" mention)
- Add `Kategorie.is_valid()` classmethod

### Modified: match
- Tighten `match_profile`: skip programmes with `thema_score=0` only (already done, but add explicit doc)

### Modified: server
- Update `programs()` docstring to list all 9 categories

### Modified: brief
- Change default `--top` from 3 to 5 (match app.py)

### Modified: catalog-data
- Fix 40 budget entries: `0` → `null`
- Add hinweis for 4 programmes missing it

## Impact
- catalog.json: 40 budget fixes + 4 hint additions (no new entries)
- grant_types.py: 2 enum values + docstring fix + is_valid method
- server.py: docstring update
- brief.py: default top=5
- Tests: 112 green (no new tests needed — all changes are additive data fixes)
