# Förder-Radar – Update-Pipeline & Quellen-Integration

> **Zweck:** Reproduzierbare, nachvollziehbare Aktualisierung des Förderkatalogs
> mit Governance, Validierung und Audit-Trail.

---

## 1. Datenmodell

### 1.1 Programm-Schema
Jedes Programm im `catalog.json` hat folgende Felder:

| Feld | Typ | Pflicht | Beschreibung |
|------|-----|---------|--------------|
| `id` | string | ✓ | Eindeutige ID (z.B. `erc-stg-2027`, `dfg-sachbeihilfe`) |
| `name` | string | ✓ | Vollständiger Programmname |
| `kategorie` | string | ✓ | DFG, ERC, BMBF, EU, Land, Stiftung, Industrie, Bund, International |
| `themen` | string[] | ✓ | Themenliste oder `["frei"]` für themenoffen |
| `karriere` | string[] | ✓ | Zielkarrierestufen (postdoc, junior, prof, senior, student, verwaltung, service, IT, bibliothek) |
| `rolle` | string[] | ✓ | Mögliche Rollen (lead, partner) |
| `budget_min` | int | | Mindestbudget in Euro |
| `budget_max` | int | | Maximalbudget in Euro |
| `dauerJahre` | int | | Laufzeit in Jahren |
| `frist` | string | | ISO-8601-Datum (`YYYY-MM-DD`) oder `null` |
| `rolling` | bool | | `true` = keine feste Frist, jederzeit einreichbar |
| `status` | string | ✓ | `verifiziert` / `laufend` / `zu-pruefen` |
| `quelle` | string | ✓ | URL zur offiziellen Quelle |
| `standDatum` | string | ✓ | Datum der letzten Prüfung (ISO-8601) |
| `hinweis` | string | | Zusätzliche Hinweise (optional) |

### 1.2 Dokument-Struktur
```json
{
  "stand": "2026-08-03",
  "quelleHinweis": "...",
  "programme": [...]
}
```

---

## 2. Quellen-Integration

### 2.1 Quellen-Typen

| Typ | Beispiel | Update-Methode | Häufigkeit |
|-----|----------|----------------|------------|
| **RSS/API** | COST, EU Tenders Portal | Automatisches Fetching | wöchentlich |
| **RSS** | DFG, BMBF (wenn verfügbar) | Automatisches Fetching | wöchentlich |
| **Manuell** | ERC, DFG, Stiftungen | Portal-Check + manuelle Eintragung | monatlich |
| **E-Mail-Alerts** | BMBF-Bekanntmachungen | Manuelle Eintragung nach Alert | bei neuen Calls |

### 2.2 Quellen-Registrierung

Jede Quelle wird in `mcp/sources.json` registriert:

```yaml
erc:
  name: "ERC"
  url: "https://erc.europa.eu/funding"
  type: "manual"
  update_frequency: "monthly"
  last_check: "2026-08-03"
  hinweis: "ERC-Fristen per Portal-Check aktualisieren (StG, AdG, SyG)"
  calls:
    - id: "erc-stg-2027"
      name: "ERC Starting Grant 2027"
      deadline: "2026-10-14"
      status: "open"
    - id: "erc-adg-2027"
      name: "ERC Advanced Grant 2027"
      deadline: "2026-08-27"
      status: "open"

dfg:
  name: "DFG"
  url: "https://www.dfg.de/foerderung"
  type: "manual"
  update_frequency: "monthly"
  last_check: "2026-08-03"
  hinweis: "DFG-Stichtage (1.2./1.10.) strukturell bekannt"
  programs:
    - id: "dfg-sachbeihilfe"
      name: "DFG Sachbeihilfe"
      rolling: true
    - id: "dfg-emmy-noether"
      name: "DFG Emmy Noether"
      stichtage: ["02-01", "10-01"]

bmbf:
  name: "BMBF"
  url: "https://www.bmbf.de/bmbf/de/forschung/foerderung/bekanntmachungen"
  type: "manual"
  update_frequency: "weekly"
  last_check: "2026-08-03"
  hinweis: "BMBF-Bekanntmachungen per Portal-Check"
  rss: "https://www.bmbf.de/rss.xml"  # falls verfügbar
```

### 2.3 Automatisches Fetching (wenn verfügbar)

```python
# mcp/fetchers.py
import httpx
from bs4 import BeautifulSoup
from datetime import datetime

def fetch_erc_calls():
    """ERC Calls per HTTP-Request abrufen (falls API verfügbar)."""
    url = "https://erc.europa.eu/api/calls"  # Beispiel
    resp = httpx.get(url, timeout=10)
    resp.raise_for_status()
    # Parse JSON/XML → Liste von Programmen
    return []

def fetch_rss(url: str) -> list[dict]:
    """RSS-Feed parsen (wenn verfügbar)."""
    resp = httpx.get(url, timeout=10)
    resp.raise_for_status()
    # Parse RSS → Liste von Programmen
    return []
```

---

## 3. Reproduzierbare Ingestion

### 3.1 Update-Workflow

```
1. fetch_sources()       # Quellen abziehen (RSS/API/manual)
2. validate_programmes() # Schema-Validierung
3. merge_catalog()       # Upsert in bestehenden Katalog
4. check_expired()       # Tote Fristen melden
5. save_catalog()        # Mit standDatum speichern
6. audit_log()           # Änderungen protokollieren
```

### 3.2 Skript: `update_catalog.py`

```bash
# Manuell
python mcp/update_catalog.py --fetch erc,dfg,bmbf --out mcp/catalog.json --validate

# Per Cron (wöchentlich)
0 6 * * 0  cd /opt/git/grant-intelligence/mcp && \
           python update_catalog.py --fetch erc,dfg,bmbf --validate --check-expired

# Nur Prüfung (ohne Änderungen)
python mcp/update_catalog.py --check-expired --validate
```

### 3.3 Audit-Log

Jede Änderung wird in `docs/update_log.md` protokolliert:

```markdown
## Update 2026-08-03

**Operator:** Tobias Weiss
**Quellen:** erc, dfg, bmbf
**Änderungen:**
- Neu: erc-stg-2027, erc-adg-2027, bmbf-digital-ai
- Update: dfg-emmy-noether (Frist aktualisiert)
- Gelöscht: (keine)

**Validierung:** OK (24 Programme, 0 Fehler)
**Abgelaufene Fristen:** 0
```

### 3.4 Git-Workflow

```bash
# Vor Update
git checkout main
git pull

# Update durchführen
python mcp/update_catalog.py --fetch erc,dfg --out mcp/catalog.json --validate

# Prüfen
git diff mcp/catalog.json
git diff docs/update_log.md

# Commit
git add mcp/catalog.json docs/update_log.md
git commit -m "Update: ERC StG 2027 Frist aktualisiert, BMBF Digital/KI neu"
git push
```

---

## 4. Validierung

### 4.1 Pflichtfelder

Alle Felder laut Schema (s.o.) müssen vorhanden sein.

### 4.2 Format-Prüfung

- `frist`: ISO-8601-Datum (`YYYY-MM-DD`) oder `null`
- `standDatum`: ISO-8601-Datum
- `budget_min/max`: Integer ≥ 0
- `status`: `verifiziert` | `laufend` | `zu-pruefen`

### 4.3 Logik-Prüfung

- `rolling=true` → `frist` muss `null` sein
- `frist < heute` → als "abgelaufen" melden
- Duplicate IDs → Fehler
- Unbekannte `kategorie` → Warnung

### 4.4 Test-Suite

```python
# mcp/test_catalog.py
def test_catalog_valid():
    doc = load_catalog()
    for p in doc["programme"]:
        assert "id" in p
        assert p["status"] in ("verifiziert", "laufend", "zu-pruefen")
        if p.get("frist"):
            datetime.strptime(p["frist"], "%Y-%m-%d")
```

---

## 5. Governance

### 5.1 Verantwortlichkeiten

| Rolle | Aufgabe |
|-------|---------|
| **Operator** | Updates durchführen, Validierung, Git-Workflow |
| **Reviewer** | Änderungen prüfen vor Merge (optional) |
| **Pilot-Nutzer** | Feedback zu Fehlern/Veralteten Daten |

### 5.2 Update-Häufigkeit

| Quelle | Häufigkeit | Methode |
|--------|------------|---------|
| ERC | monatlich | manuell |
| DFG | monatlich | manuell |
| BMBF | wöchentlich | manuell + RSS (falls verfügbar) |
| EU Horizon | wöchentlich | manuell + Portal-Check |
| COST | wöchentlich | RSS/API (falls verfügbar) |
| Stiftungen | monatlich | manuell |

### 5.3 Qualitätskriterien

- **Keine abgelaufenen Fristen** im Katalog (außer `rolling`)
- **Alle `verifiziert`-Einträge** haben `standDatum` ≤ 30 Tage alt
- **Alle `zu-pruefen`-Einträge** haben `hinweis` mit Prüfungshinweis
- **Validierung** läuft vor jedem Commit (CI/CD)

### 5.4 Fehlerbehandlung

| Fehler | Aktion |
|--------|--------|
| Abgelaufene Frist | `frist` auf `null` setzen + `rolling=false` + Status "zu-pruefen" |
| Ungültiges Datum | Fehler im Audit-Log + manuelle Korrektur |
| Duplicate ID | Merge oder ID-Änderung |
| Fehlende Quelle | `hinweis` ergänzen mit "Quelle prüfen" |

---

## 6. CI/CD (optional)

### 6.1 GitHub Actions

```yaml
# .github/workflows/catalog-validate.yml
name: Catalog Validation
on: [push]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Validate catalog
        run: |
          python mcp/update_catalog.py --validate
          python mcp/update_catalog.py --check-expired
```

### 6.2 Pre-commit Hook

```bash
# .git/hooks/pre-commit
python mcp/update_catalog.py --validate || exit 1
```

---

## 7. Beispiel-Update

### 7.1 Manuelles Update (ERC)

1. Portal besuchen: `https://erc.europa.eu/funding`
2. Neue Calls notieren (Name, Deadline, Budget)
3. `mcp/sources.json` aktualisieren
4. `mcp/catalog.json` aktualisieren:
   ```json
   {
     "id": "erc-stg-2027",
     "name": "ERC Starting Grant (StG) 2027",
     "kategorie": "ERC",
     "themen": ["frei"],
     "karriere": ["postdoc", "junior"],
     "rolle": ["lead"],
     "budget_min": 0,
     "budget_max": 1500000,
     "frist": "2026-10-14",
     "rolling": false,
     "status": "verifiziert",
     "quelle": "https://erc.europa.eu/apply-grant/starting-grants",
     "standDatum": "2026-08-03"
   }
   ```
5. Validieren: `python mcp/update_catalog.py --validate`
6. Commit: `git commit -m "Update: ERC StG 2027 Frist verifiziert"`

### 7.2 Automatisches Update (wenn RSS verfügbar)

```bash
python mcp/update_catalog.py --fetch bmbf --out mcp/catalog.json --validate
```

---

## 8. Migration & Versionierung

### 8.1 Catalog-Version

Jeder Katalog hat eine implizite Version durch `standDatum`.

### 8.2 Breaking Changes

- Schema-Änderungen → Migration-Skript schreiben
- ID-Änderungen → Mapping in `docs/id_mapping.md`

### 8.3 Backup

```bash
# Vor Update
cp mcp/catalog.json mcp/catalog.backup.$(date +%Y%m%d).json

# Git-Tag
git tag catalog-2026-08-03
```

---

## 9. Deployment: Deadline-Cron

### 9.1 Cron (Empfehlung)

```crontab
# Förder-Radar Deadline-Check – wöchentlich Sonntag 06:00
0 6 * * 0 /opt/git/grant-intelligence/mcp/cron_check_expired.sh >> /var/log/grant-intelligence/deadline.log 2>&1
```

### 9.2 systemd-Timer (Alternative)

```ini
# /etc/systemd/system/grant-intelligence-deadline.service
[Unit]
Description=Foerder-Radar Deadline-Check

[Service]
Type=oneshot
ExecStart=/opt/git/grant-intelligence/mcp/cron_check_expired.sh
WorkingDirectory=/opt/git/grant-intelligence/mcp

# /etc/systemd/system/grant-intelligence-deadline.timer
[Unit]
Description=Foerder-Radar wöchentlicher Deadline-Check

[Timer]
OnCalendar=Sun 06:00
Persistent=true

[Install]
WantedBy=timers.target
```

```bash
sudo systemctl enable --now grant-intelligence-deadline.timer
sudo journalctl -u grant-intelligence-deadline.service -f
```

### 9.3 Log-Rotation

```
# /etc/logrotate.d/grant-intelligence
/var/log/grant-intelligence/*.log {
    weekly
    rotate 12
    compress
    missingok
    notifempty
}
```

---

## 10. Ingestion Pipeline (`ingest.py`)

### 10.1 Architektur

`ingest.py` implementiert eine **Registry-basierte Ingestion-Pipeline** mit folgenden Prinzipien:

1. **Repeatable**: Deterministische IDs (slug-basiert), idempotentes Upsert (Re-Run erzeugt keine Duplikate)
2. **Extensible**: Neuer Fetcher = eine Funktion + `@register`-Decorator
3. **Safe**: `--dry-run` ist Standard (kein Schreiben ohne `--apply`)
4. **Token-efficient**: Wiederverwendung von `fetchers.py`-Helfern (`_slug_id`, `_enrich_programme`, `apply_fetch_updates`)

### 10.2 Registry-Muster

```python
from ingest import register, ProgrammeUpdate

@register("my-source", "My Source", "Description", "api")
def fetch_my_source() -> ProgrammeUpdate:
    # HTTP fetch + parse
    return ProgrammeUpdate(
        source="my-source",
        programmes=[...],  # list of programme dicts
        errors=[],
        fetched_at=datetime.now().isoformat(),
        suggestions=[],
    )
```

### 10.3 CLI-Nutzung

```bash
# Alle Fetcher auflisten
python mcp/ingest.py --list

# Einzelnen Fetcher ausführen (Dry-Run, kein Schreiben)
python mcp/ingest.py --source openaire

# Einzelnen Fetcher ausführen und in Katalog mergen
python mcp/ingest.py --source openaire --apply

# Alle Fetcher ausführen (Dry-Run)
python mcp/ingest.py --all

# Alle Fetcher ausführen und in Katalog mergen
python mcp/ingest.py --all --apply
```

### 10.4 Verfügbare Fetcher

| Key | Name | Kategorie | API |
-----|------|----------|------|-----|
| `openaire` | OpenAIRE | api | EU-Forschungsprojekte (3.9M) |
| `nih` | NIH RePORTER | api | US biomedizinische Grants (76K) |
| `nsf` | NSF Awards | api | US Wissenschafts-Grants |
| `crossref` | Crossref Funder Registry | registry | 45K Funder mit DOIs |
| `bmbf` | BMBF | rss | BMBF Bekanntmachungen (RSS) |
| `cost` | COST | portal | COST European Cooperation |
| `eu` | EU Horizon | portal | Horizon Europe Portal |

### 10.5 Upsert-Mechanismus

- Jedes gefetchte Programm wird über `Programm.from_dict()` validiert
- Ungültige Programme werden verworfen und im Audit-Log protokolliert
- Bestehende Programme (gleiche ID) werden aktualisiert (Update)
- Neue Programme werden hinzugefügt (Insert)
- Deterministische IDs via `_slug_id(source, title)` verhindern Duplikate bei Re-Runs
- Audit-Log wird in `docs/update_log.md` appendiert

### 10.6 Erweiterung um neue Quellen

1. Fetcher-Funktion in `ingest.py` schreiben (HTTP + Parse)
2. Mit `@register("key", "Name", "Desc", "api")` registrieren
3. Test in `test_ingest.py` hinzufügen (HTTP gemockt)
4. `python mcp/ingest.py --source key` zum Testen (Dry-Run)
5. `python mcp/ingest.py --source key --apply` zum Importieren

---

## 11. Status

| Item | Status |
|------|--------|
| Datenmodell | ✓ definiert |
| Quellen-Registrierung | ✓ (`sources.json`, 26 Quellgruppen) |
| Update-Skript | ✓ (`update_catalog.py`) |
| Fetch→Persist Pipeline | ✓ (`fetchers.py` `apply_fetch_updates`) |
| **Ingestion Pipeline** | ✓ (`ingest.py` — Registry-basiert, 7 Fetcher, Dry-Run/Apply) |
| Validierung | ✓ (`Programm.from_dict`) |
| Audit-Log | ✓ (`docs/update_log.md`) |
| Deadline-Cron | ✓ (`cron_check_expired.sh` + systemd-Timer) |
| Katalog | ✓ 97 Programme (9 Kategorien: DFG, ERC, BMBF, EU, Land, Stiftung, Industrie, Bund, International) |
| CI/CD | optional |

---

**Letzte Aktualisierung:** 2026-08-22  
**Operator:** Tobias Weiss
