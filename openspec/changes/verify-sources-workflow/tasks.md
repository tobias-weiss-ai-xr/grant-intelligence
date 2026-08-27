## Tasks

- [x] Repo-agnostisches `verify_sources.py` implementieren (Stage 1 HTTP + Stage 2 Browser, config-getrieben, parallele Prüfung)
- [x] `grant-intelligence/mcp/verify-sources.json` anlegen (catalog.json `quelle` + sources.json `url`)
- [x] `skeleton-research/verify-sources.yaml` anlegen (papers.yaml `url`/`code_url`/`project_url`)
- [x] `.github/workflows/verify-sources.yml` in beiden Repos (wöchentlich + dispatch + Pfad-Trigger, Report-Artifact)
- [x] `requests`/`pyyaml` zu grant-intelligence Dev-Deps; `verify-sources-report.json` zu `.gitignore` (beide Repos)
- [x] `grant-intelligence/mcp/test_verify_sources.py` (offline, 8 Tests)
- [x] `skeleton-research/tests/test_verify_sources.py` (offline, 7 Tests)
- [x] Smoke-Test gegen echte Kataloge: grant-intelligence 0 broken (exit 0), skeleton-research 5 OK (exit 0 mit --no-fail)
- [ ] CI auf GitHub verifizieren (erster scheduled/dispatch Run in beiden Repos)
