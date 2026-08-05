# Changelog

Alle bedeutenden Änderungen an diesem Projekt werden hier dokumentiert.

Format folgt [Keep a Changelog](https://keepachangelog.com/).

---

## [Unreleased]

### Added
- Type-safe dataclasses (Programm, MatchResult, BriefResult)
- Full type hints across all modules
- Structured logging throughout
- Custom exceptions (CatalogError)
- Export functions (CSV, JSON, Markdown)
- Auto-fetching with deadline checking
- sources.yaml for source registry
- **6-Sigma-Qualitätspass**: gemeinsame Helfer `parse_frist`/`budget_beschreibung`
- Programm-Dataclass mit `from_dict`/`to_dict` (camelCase-Katalog-Konvertierung)
- `_serialize()` für einheitliche camelCase-MCP-API
- Deterministische RSS-Ids via `_slug_id` (upsert-sicher)
- `pyproject.toml` (ruff, mypy, pytest) und `requirements-dev.txt`
- Tests für fetchers, update_catalog, export, grant_types, demo (neu: 104)

### Changed
- Refactored match.py to return MatchResult dataclasses
- Updated README with qualitative descriptions (no specific numbers)
- Enhanced documentation with Google-style docstrings
- Quellen-Registrierung vereinheitlicht (sources.yaml als Single Source of Truth)
- Datums-Parsing zentralisiert (10 Stellen -> `parse_frist`)
- MCP-API-Serialisierung auf camelCase vereinheitlicht
- `server.ingest` validiert Programme vor dem Persistieren
- `is_urgent` von @property zu parametrierter Methode

### Fixed
- All 52 tests passing
- XSS protection in UI
- Career level whitelist validation
- Empty form field handling (no 422 errors)
- **demo.py-Crash** (dict-API auf MatchResult-Dataclass)
- **Vakuer Test** `test_notify_warnfenster` (testete inexistenten Key)
- **XSS-Lücke** in `_format_deadline` (unescaped frist)
- Unbenutzte Imports, fehlende Deps (httpx, pyyaml) in requirements.txt
- Fragmentierter `{`-Escape-Hack in UI-Templates
- Statische Typprüfung grün (mypy, 0 Fehler)

---

## [2026-08-03]

### Added
- 32 programmes across research and service institutions
- Service/admin career levels (verwaltung, service, IT, bibliothek)
- Weekly brief generation
- MCP server tools (ingest, search, match, notify, brief)
- Update pipeline with audit trail
- CI/CD workflow (GitHub Actions)

### Changed
- Expanded catalog from 6 to 32 programmes
- Added theme diversity (Medizin, Technik, Digital, KI, Energie, Umwelt)
- Updated matching logic for service institutions

### Fixed
- 7 bugs from bug hunt (XSS, 422, persistence, no-op ingest)
- All edge cases handled (empty fields, unicode, XSS attempts)

---

## [2026-08-03] (Initial)

### Added
- MVP with 6 verified programmes (ERC, DFG, LOEWE)
- MCP server with ingest/search/match tools
- Single-screen UI
- Weekly brief generator
- Test suite (52 tests)
- Hermetic test environment

### Principles
- Official sources only
- No dead deadlines
- Stand-date on every programme
- Human-in-the-loop scoring
- Small pilot first (one faculty, one persona)

---

## Legend

| Tag | Meaning |
|-----|---------|
| **Added** | New features |
| **Changed** | Changes to existing functionality |
| **Deprecated** | Soon-to-be removed features |
| **Removed** | Removed features |
| **Fixed** | Bug fixes |
| **Security** | Security improvements |
