## Why

Das Ad-hoc-Verfahren „sind meine Quell-Links noch erreichbar?" (entwickelt beim
Katalog-Repair `67c1f7c`) hat 9 kaputte `quelle`-Links gefunden und repariert.
Diese Prüfung soll **wiederholbar und verallgemeinerbar** werden — nicht nur für
den Förder-Radar-Katalog, sondern als repo-agnostischer Workflow, der auch auf
`skeleton-research` (`papers.yaml` → `url`/`code_url`/`project_url`) passt. Ziel:
tote Links werden automatisch und regelmäßig erkannt, bevor sie in Publikationen
oder Demos auftauchen.

## What Changes

### Repo-agnostischer Link-Verifier (`verify_sources.py`)

Ein konfigurationsgetriebenes CLI, das „eine Liste von Einträgen, jeder mit
einer oder mehreren URL-Feldern" beliebiger Repos prüft:

- **Stage 1 (HTTP, `requests`):** jede URL → `OK` / `BROKEN` / `UNCERTAIN`.
- **Stage 2 (Browser, `playwright`, optional `--browser`):** nur `UNCERTAIN`
  (401/403/Timeout) erneut prüfen → `OK` / `BROKEN` / `BOTBLOCK`.
- Ohne Browser wird `UNCERTAIN` als `BOTBLOCK` (Warnung, nie Fail) gewertet —
  so bleibt CI stabil, während definitiv tote Links (404/410/5xx/ConnectionError)
  weiterhin fehlschlagen. 403/Cloudflare-Blocks auf offiziellen Portalen
  (ec.europa.eu, DAAD, NIH, HFSP …) sind **keine** kaputten Links.

### Pro-Repo Artefakte

- `mcp/verify-sources.json` (grant-intelligence): prüft `catalog.json`
  (`quelle`) + `sources.json` (`url`).
- `verify-sources.yaml` (skeleton-research): prüft `papers.yaml`
  (`url`/`code_url`/`project_url`).
- `.github/workflows/verify-sources.yml` in **beiden** Repos: wöchentlich
  (Montag) + `workflow_dispatch` + bei Katalog-/Paper-Änderungen; lädt einen
  JSON/Markdown-Report als Artifact hoch.

### Tests

- `mcp/test_verify_sources.py` + `skeleton-research/tests/test_verify_sources.py`:
  Offline (gemocktes `requests`), decken Extraktion, Klassifizierung, Verdict-
  Auflösung und `run()`/`main()` ab.

## Impact

- Neue, optionale Dev-Abhängigkeit `requests`/`pyyaml` (grant-intelligence) —
  keine Runtime-Änderung, keine Katalog-Änderung, keine bestehenden Tests betroffen.
- CI wird um einen nicht-blockierenden Audit-Job erweitert (nur echte 404/5xx
  lassen den Job fehlschlagen; 403-Bot-Blocks sind Warnungen).
