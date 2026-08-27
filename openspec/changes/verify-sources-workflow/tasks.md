## Tasks

- [x] Repo-agnostisches `verify_sources.py` implementieren (Stage 1 HTTP + Stage 2 Browser, config-getrieben, parallele Prüfung)
- [x] `grant-intelligence/mcp/verify-sources.json` anlegen (catalog.json `quelle` + sources.json `url`)
- [x] `skeleton-research/verify-sources.yaml` anlegen (papers.yaml `url`/`code_url`/`project_url`)
- [x] `.github/workflows/verify-sources.yml` in beiden Repos (wöchentlich + dispatch + Pfad-Trigger, Report-Artifact)
- [x] `requests`/`pyyaml` zu grant-intelligence Dev-Deps; `verify-sources-report.json` zu `.gitignore` (beide Repos)
- [x] `grant-intelligence/mcp/test_verify_sources.py` (offline, 8 Tests)
- [x] `skeleton-research/tests/test_verify_sources.py` (offline, 7 Tests)
- [x] Smoke-Test gegen echte Kataloge: grant-intelligence 0 broken (exit 0), skeleton-research 5 OK (exit 0 mit --no-fail)
- [x] Verifier fand 5 tote `sources.json`-URLs (Katalog-Audit uebersah sie) -> repariert + Regression-Test
- [x] CI auf GitHub verifiziert (erster Run beider Repos: grant-intelligence BROKEN:0, exit 0; skeleton-research success)
- [x] **Rollout auf alle 24 `*-research` Corpus-Repos:** identischer Kit (scripts/verify_sources.py + tests/test_verify_sources.py + verify-sources.yaml + .github/workflows/verify-sources.yml + .gitignore). Repos mit `repos.yaml` (devops-, software-development-research) bekommen 2. Input. Alle 7 Offline-Tests gruen, alle gepusht.
- [x] **Bugfix HTTP 429:** Bulk-CI-Scans pruegeln doi.org/github -> 429 (rate-limit) wurde fälschlich als BROKEN gewertet. Fix: 429 -> UNCERTAIN (+ Retry/Backoff), sonst false-positive BROKEN in allen Corpus-Repos (devops 33, neuromorphic 4). In Skeleton + allen Repos + grant-intelligence propagiert, 429-Tests ergaenzt.
