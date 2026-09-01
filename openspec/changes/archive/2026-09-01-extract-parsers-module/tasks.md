# Tasks: extract-parsers-module

## 1. Neue Modulstruktur

- [x] 1.1 `mcp/parsers.py` erstellen: `slug_id()`, `parse_bmbf_rss()`
      (pur, offline, kein Zeitbezug).
- [x] 1.2 `mcp/fetchers.py`: XML-Parsing entfernt, nutzt `parsers`;
      `_slug_id`-Alias für Rückwärtskompatibilität.
- [x] 1.3 `mcp/ingest.py`: `slug_id` direkt aus `parsers` importieren.

## 2. Tests

- [x] 2.1 `mcp/test_parsers.py`: slug_id (deterministisch, Sonderzeichen,
      Kürzung, leer) + parse_bmbf_rss (Items, Bytes, Fallback, ohne Titel,
      leer, kaputtes XML).
- [x] 2.2 Bestehende fetchers-/ingest-/update_catalog-Tests grün
      (Verhalten unverändert).
- [x] 2.3 `pytest` gesamt grün, `mypy` grün.

## 3. Qualitätssicherung

- [x] 3.1 `openspec validate extract-parsers-module` grün.
- [x] 3.2 commit + push, CI nicht rot.
