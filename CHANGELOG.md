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

### Changed
- Refactored match.py to return MatchResult dataclasses
- Updated README with qualitative descriptions (no specific numbers)
- Enhanced documentation with Google-style docstrings

### Fixed
- All 52 tests passing
- XSS protection in UI
- Career level whitelist validation
- Empty form field handling (no 422 errors)

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
