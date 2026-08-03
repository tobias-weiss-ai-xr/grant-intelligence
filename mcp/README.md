# Grant-Agent – MCP-Prototyp

Minimaler MCP-Server auf Basis des **offiziellen MCP-SDK** (FastMCP) plus
Ein-Bildschirm-UI und automatisierbarem Wochen-Brief. Lädt die kuratierte
`catalog.json` und stellt eine Agent-Schleife (ingest -> search -> match ->
fristen -> notify) als MCP-Tools bereit.

> **Ehrlichkeits-Regel:** `status` je Programm = `verifiziert` (live geprüft am
> `standDatum`) | `laufend` (rolling, keine Frist) | `zu-pruefen` (bekanntes
> Programm, Frist vor Nutzung gegen Portal prüfen). Scores sind Orientierung,
> keine Zusage.

## Dateien
- `catalog.json` – kuratierte Förderprogramme (ERC/DFG/Land; Stand 2026-08-03;
  ERC-Fristen live vom Portal verifiziert).
- `match.py`     – Daten-/Matching-/Begründungs-Schicht (ohne MCP, frei testbar).
- `server.py`    – MCP-Server (stdio); `ingest`/`loeschen` persistieren in `catalog.json`.
- `app.py`       – Ein-Bildschirm-UI (FastAPI, lokal).
- `brief.py`     – automatisierbarer Wochen-Brief (Cron-fähig, Markdown).
- `demo.py`      – ausführbare Demo der Agent-Schleife (für Vorstellung / Test).
- `requirements.txt` – `mcp`, `fastapi`, `uvicorn`.

## Ausprobieren
```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt

# Logik-/Agent-Schleife-Demo (ohne MCP-Client):
python3 demo.py

# Logik-Test ohne MCP:
python3 match.py

# Wochen-Brief erzeugen (stdout oder Datei):
python3 brief.py --felder Biologie Nachhaltigkeit --karriere postdoc
python3 brief.py --felder Medizin --karriere prof --out ../docs/brief.md

# Ein-Bildschirm-UI (http://127.0.0.1:8000):
uvicorn app:app --port 8000

# Als MCP-Server über stdio:
python3 server.py
```

Dann mit einem MCP-Client verbinden (z. B. `npx @modelcontextprotocol/inspector`
oder ein `mcp`-fähiger Klient) und Tool-Aufrufe testen:
```text
match_best(felder=["Biologie","Nachhaltigkeit"], karriere="postdoc")
nächste_fristen(felder=["Biologie"], karriere="postdoc")
programs(kategorie="ERC")
```

## Tools
| Tool | Antwort |
|---|---|
| `programs(kategorie?)` | gefilterte Liste aus `catalog.json` |
| `search(kategorie?, stichwort?)` | Stichwort-Suche (Name/Themen/Quelle) |
| `ingest(programme)` | Upsert in den Katalog + persistiert nach `catalog.json` |
| `loeschen(programm_id)` | Programm entfernen + persistiert |
| `match_best(felder, karriere, rolle?, top)` | beste Programme + deutsche Begründung |
| `nächste_fristen(felder, karriere, top)` | wie zuvor + Tage bis Frist |
| `notify(felder, karriere, rolle?, tage)` | Fristwarnungen (<= `tage` Tage / Rolling) |
| `brief(felder, karriere, rolle?, top, tage)` | Wochen-Brief: Top-Matches + Frist + Warnungen in einem Aufruf |

## Cron-Beispiel (nächtlicher Brief)
```cron
0 6 * * 1  cd /opt/git/grant-intelligence/mcp && .venv/bin/python brief.py --felder Biologie Nachhaltigkeit --karriere postdoc --out ../docs/brief.md
```

## Weiteres
- Produktionsdaten pflegen und aus den offiziellen Quellen aktualisieren
  (siehe `docs/Datenquellen.md`); neue Fristen immer mit `standDatum` belegen.
- Langfristige Vision (nur skizziert): zentraler Uni-MCP-Server – siehe
  [`docs/Roadmap.md`](../docs/Roadmap.md).
- Transport standardmäßig stdio; ein Streamable-HTTP-Transport ist später möglich.
