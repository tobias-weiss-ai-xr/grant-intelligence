## Design: verify-sources-workflow

### Kerngedanke

Ein einziges, repo-agnostisches Skript `verify_sources.py` (stdlib + `requests`,
optionales `playwright`) wird **identisch** in beiden Repos abgelegt
(`mcp/verify_sources.py` bzw. `scripts/verify_sources.py`). Die Repo-spezifika
stecken komplett in einer Config (`verify-sources.json` / `verify-sources.yaml`):

```yaml
inputs:
  - file: papers.yaml
    format: yaml
    list_key: papers
    id_field: title
    url_fields: [url, code_url, project_url]
settings:
  timeout: 20
  workers: 12
  browser: false
  fail_on_broken: true
  report: verify-sources-report.json
```

`file`-Pfade werden relativ zur Config-Datei aufgelöst → CI kann im
jeweiligen Working-Directory laufen.

### Klassifizierung (Stage 1, HTTP)

| Status / Fehler            | Verdict (Stage 1) |
|----------------------------|-------------------|
| 2xx / 3xx                  | `ok`              |
| 404 / 410 / 400 / 405 / 5xx| `broken`          |
| 401 / 403                  | `uncertain`       |
| Timeout / SSL-Error        | `uncertain`       |
| ConnectionError (DNS/refused) | `broken`      |

### Verdict-Auflösung (Stage 2, optional Browser)

- `http == ok`      → `ok`
- `http == broken`  → `broken`
- `http == uncertain` + Browser-Ergebnis (`ok`/`broken`/`botblock`) → übernehmen
- `http == uncertain` + kein/unsicherer Browser → `botblock` (Warnung)

Exit-Code 1 **nur** wenn nach Stage 2 noch `broken` übrig und
`fail_on_broken=true`.

### Parallelisierung

`concurrent.futures.ThreadPoolExecutor` (default 12 Worker) prüft alle URLs
gleichzeitig; deterministisch für Tests durch Mock von `requests.get` bzw.
`browser_check`.

### CI

- grant-intelligence: `--fail` (Katalog-Regression muss fehlschlagen).
- skeleton-research: `--no-fail` (Template hält Platzhalter-Papers mit
  nicht-auflösbaren URLs; echte Forks werfen `--no-fail` weg).
- Beide: `upload-artifact` des Reports (`if: always()`).

### Testbarkeit

Kein Netzwerk in Tests: `http_check` wird über `mock.patch("requests.get", …)`
gesteuert; `browser_check` ist in Stage-1-only-Läufen nie involviert.
`iter_entries` wird mit temporären JSON/YAML-Dateien geprüft.
