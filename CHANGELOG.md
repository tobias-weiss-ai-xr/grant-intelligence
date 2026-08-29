# Changelog

Alle bedeutenden Änderungen an diesem Projekt werden hier dokumentiert.

Format folgt [Keep a Changelog](https://keepachangelog.com/).

---

## [Unreleased]

### Added
- **Frist-Benachrichtigungs-Pipeline (`deadline_digest.py`):** Strukturierter Digest (dringend ≤30d, anstehend ≤90d, abgelaufen, rolling) aus dem Katalog; persistiert als `deadline-digest.json`; Deduplizierung gegen den vorherigen Lauf (nur *neue* dringende Fristen werden gemeldet). CLI mit `--check` (nur ausgeben). 23 neue Tests.
- **GitHub Action `deadline-check.yml`:** Wöchentlich (So 06:00 UTC) + manuell; berechnet und committet den Digest; öffnet/aktualisiert bei neuen dringenden Fristen ein GitHub Issue (Label `deadline-warning`).
- **Dashboard-Panel „Frist-Radar“:** Tabelle der Fristen ≤90 Tage, farbcodiert (≤14d rot, ≤30d orange, >30d grün); neue Kennzahl-Karte „Dringend ≤ 30 Tage“ (rot bei >0).
- **`sync-data.sh`:** Kopiert optional `deadline-digest.json` in `dashboard/data/`.
- **`cron_check_expired.sh`:** Ruft zusätzlich `deadline_digest.py` auf (lokaler/systemd-Lauf erzeugt ebenfalls den Digest).
- **Statisches GitHub-Pages-Dashboard:** `dashboard/` mit Alpine.js (15KB CDN) + Chart.js (70KB CDN). Kein Build-Step, kein Server. Katalog-Explorer (97 Programme, filterbar/sortierbar), Quellen-Browser (26 Quellen), Kategorie/Status/Deadline-Charts, Profil-Matcher (client-seitig, DSGVO-gefiltert). GitHub Action deployt auf Push zu `main`.
- **`dashboard/sync-data.sh`:** Synchronisiert `mcp/*.json` → `dashboard/data/`; DSGVO-Filter (nur `einwilligung=true` + `status=aktiv`).
- **Forscherprofil-Modell (`mcp/profile.py`):** `Profile`-Dataclass mit `id`, `name`, `karriere`, `themen`, `orcid`, `publikationen`, `einwilligung`, `status`, `standDatum`, `hinweis`. `from_dict`/`to_dict` mit camelCase-Mapping. `load_profiles()`/`save_profiles()` für Persistenz in `profiles.json`.
- **ORCID-Public-API-Adapter:** `fetch_orcid()` ruft ORCID-Werke ab (httpx, 10s Timeout, fail-open). `derive_themen()` leitet Forschungsfelder aus Publikationstiteln ab (Wort-Grenzen-Matching, 16 Felder). Einwilligungs-Gate: ohne `einwilligung=True` keine ORCID-Abruf.
- **Profil-basiertes Matching:** `match_profile()` und `next_deadline()` akzeptieren optionales `profil: Profile`-Argument. Profil-Themen/Karriere als Default; explizite `felder`/`karriere` haben Vorrang. Einwilligungs-Gate: ohne Consent → leere Ergebnisse.
- **MCP-Tool `profile(id?)`:** Profil nach ID laden oder alle Profile auflisten. `match_best`, `naechste_fristen`, `notify`, `brief` um `profil_id`-Parameter erweitert.
- **Web-UI Profil-Dropdown:** `app.py` mit Dropdown zur Profilauswahl, automatischem Pre-Fill von Themen/Karriere, Consent-Hinweis bei fehlender Einwilligung.
- **Pilot-Setup (Fachbereich Mathematik):** `profiles.json` mit 3 Profilen (Tobias Weiss Postdoc KI, 2 Mathematik-Platzhalter). `pilot_demo.py` generiert `docs/pilot-ergebnisse.md`.
- **Brief-CLI `--profil-id`:** `brief.py` akzeptiert `--profil-id` für profil-basierten Wochen-Brief.
- **64 neue Tests** (Profile-Dataclass, Persistenz, ORCID-Mock, Profil-Matching, Server-Tools, UI-Dropdown, Pilot-Demo). 181 → 245 Tests. 100% Coverage auf allen Kernmodulen.
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
- **Verallgemeinerter Link-Verifier `verify_sources.py`:** repo-agnostisches, config-getriebenes CLI (2-Stufen: HTTP + optional Playwright) prüft beliebige "Liste von Einträgen mit URL-Feldern". Identisch in `mcp/` (Katalog `quelle` + `sources.json` `url`) und `skeleton-research/scripts/` (`papers.yaml` `url`/`code_url`/`project_url`). `.github/workflows/verify-sources.yml` in beiden Repos (wöchentlich + dispatch + Pfad-Trigger, Report-Artifact). 8 + 7 Offline-Tests.

### Fixed
- **5 tote `sources.json`-URLs repariert** (vom verallgemeinerten Verifier entdeckt, vom Katalog-Audit übersehen): BMBF→BMFTR-Domain-Migration, LOEWE-Hessen-Pfad, NRW-MWK-Pfad, MSCA-Hostname (fehlender Bindestrich), SNSF-Pfad. Deterministic Regression-Test `test_sources_verify_run_repariert`.
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
