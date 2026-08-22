# Changelog

Alle bedeutenden Änderungen an diesem Projekt werden hier dokumentiert.

Format folgt [Keep a Changelog](https://keepachangelog.com/).

---

## [Unreleased]

### Added
- **17 neue Internationale Stiftungen & Fördere:** EMBO, HFSP, Gates Foundation, Rockefeller Foundation, Sloan Foundation, Kavli Foundation, Templeton Foundation, HHMI, Moore Foundation, Leverhulme Trust, Royal Society, JSPS, ARC, CIHR, NSERC, WHO/TDR, UNESCO. Kategorie `International`: 5 → 22. Katalog: 80 → 97.
- **3 neue Programme:** ERC Consolidator Grant (CoG), ERC Proof of Concept (PoC), DFG Walter Benjamin (Postdoc-Rückkehr/Neueinstieg). Katalog: 52 → 55.
- **Postdoc-Bedeckung:** 23 → 26 Programme. ERC-Schema-Vollständigkeit (StG, CoG, AdG, SyG, PoC). DFG Postdoc-Trilogie (Sachbeihilfe, Emmy Noether, Walter Benjamin).
- **7 neue DFG-Programme:** Reinhart Koselleck (High-risk/High-gain), Forschungsgruppen, Schwerpunktprogramme, Kolleg-Forschungsgruppen, Klinische Forschungsgruppen, Wissenschaftliche Netzwerke, Forschungsimpulse. DFG-Einzelfoerderung + Koordinierte-Programme nahezu komplett. Katalog: 55 → 62.
- **4 neue EU-Programme:** MSCA Postdoctoral Fellowships (PF, Frist 9. Sep 2026), Horizon Europe Cluster 1 Health, Cluster 2 Kultur/Gesellschaft, Cluster 3 Zivile Sicherheit. EU-Coverage: 7 → 11. Katalog: 62 → 66.
- **Brief top=3→5:** Mehr Ergebnisse bei wachsendem Katalog.
- **4 neue Stiftungen/Land-Programme:** Humboldt Forschungsstipendium (rolling, Inbound/Outbound), Robert Bosch Stiftung (Gesundheit/Bildung), NRW MWK Wissenschaftsförderung, Hightech Agenda Bayern (5,5 Mrd EUR). Stiftung: 20 → 22, Land: 3 → 5. Katalog: 66 → 70.
- **5 neue Internationale Programme:** NSF (US), NIH (US), UKRI (UK), DACH SNSF/FWF (CH/AT), Wellcome Trust (UK). Neue Kategorie `International`. Katalog: 70 → 75.
- **Polish:** Kategorie Enum komplett (9 Werte + is_valid), 40 Budget-Einträge 0→null, 4 fehlende Hinweise ergänzt, Brief top=3→5, Docstrings korrigiert. Tests: 112 → 115.
- **20 neue Programme:** 13 Student-Stipendien (Deutschlandstipendium, 11 Begabtenförderungswerke, DAAD Auslandsstipendium, Erasmus+), 7 PhD/Postdoc-Programme (DFG IRTG, DFG Graduate School, MSCA ITN/COFUND, Max Weber Bayern, Gerda Henkel, Fritz Thyssen). Katalog: 32 → 52.
- **Fetch→Persist Pipeline:** `_enrich_programme()` und `apply_fetch_updates()` in `fetchers.py`; Fetcher erzeugen vollständige, validierte Programmeinträge; automatischer Merge in Katalog + Audit-Log.
- **Deadline-Cron:** `cron_check_expired.sh` mit crontab- und systemd-Timer-Beispiel in `docs/SPEC-Update-Pipeline.md`.
- **5 neue Quellgruppen** in `sources.yaml`: deutschlandstipendium, begabtenfoerderungswerke, erasmus, msc, gerda-henkel, fritz-thyssen.
- **8 neue Tests** für Fetch→Persist Pipeline (enrich, apply, audit, rejection).

### Changed
- `Programm.__post_init__`: `themen`, `karriere`, `rolle` dürfen leer sein („offen für alle").
- `update_catalog.py fetch_manual()`: nutzt Fetcher statt `None`; `--fetch bmbf` persistiert Ergebnisse.
- `Datenquellen.md`: neue Stiftungen, Begabtenförderungswerke, EU-Programme dokumentiert.
- `SPEC-Update-Pipeline.md`: Cron/systemd-Timer, Log-Rotation, aktualisierter Status.

### Type-safe dataclasses (Programm, MatchResult, BriefResult)
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
