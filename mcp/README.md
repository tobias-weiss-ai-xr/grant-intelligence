# Grant-Agent – MCP-Prototyp

Minimaler MCP-Server auf Basis des **offiziellen MCP-SDK** (FastMCP). Lädt die
kuratierte `catalog.json` und stellt eine Agent-Schleife (ingest -> search ->
match -> fristen -> notify) als MCP-Tools bereit.

> Demo zu Entwicklungszwecken; die Katalog-Daten sind Beispielwerte, nicht verbindlich.

## Dateien
- `catalog.json`  – kuratierte Förderprogramme (DFG/ERC/BMBF/Land/Stiftung).
- `match.py`      – Matching-/Logik-Schicht (ohne MCP, frei testbar).
- `server.py`     – MCP-Server (stdio).
- `demo.py`       – ausführbare Demo der Agent-Schleife (für Vorstellung / Test).
- `requirements.txt` – `mcp` (SDK).

## Ausprobieren
```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt

# Logik-/Agent-Schleife-Demo (ohne MCP-Client):
python3 demo.py

# Logik-Test ohne MCP:
python3 match.py

# Als MCP-Server über stdio:
python3 server.py
```

Dann mit einem MCP-Client verbinden (z. B. `npx @modelcontextprotocol/inspector`
oder ein `mcp`-fähiger Klient) und Tool-Aufrufe testen:
```text
match_best(felder=["Biologie","Landnutzung"], karriere="postdoc")
nächste_fristen(felder=["Biologie"], karriere="postdoc")
programs(kategorie="DFG")
```

## Tools
| Tool | Antwort |
|---|---|
| `programs(kategorie?)` | gefilterte Liste aus `catalog.json` |
| `search(kategorie?, stichwort?)` | Stichwort-Suche (Name/Themen/Quelle) |
| `ingest(programme)` | Quellen/Programme per Upsert in den laufenden Katalog |
| `match_best(felder, karriere, top)` | beste Programme + Begründung |
| `nächste_fristen(felder, karriere, top)` | wie zuvor + Tage bis Frist |
| `notify(felder, karriere, tage)` | Fristwarnungen (<= `tage` Tage / Rolling) |
| `brief(felder, karriere, top, tage)` | Wochen-Brief: Top-Matches + Frist + Warnungen in einem Aufruf |

## Weiteres
- Produktionsdaten pflegen und aus den offiziellen Quellen aktualisieren
  (siehe `docs/Datenquellen.md`).
- Langfristige Vision (nur skizziert): zentraler Uni-MCP-Server – siehe
  [`docs/Roadmap.md`](../docs/Roadmap.md).
- `ingest` mutiert den laufenden Katalog nur im Speicher; für die Demo genügt das.
- Transport standardmäßig stdio; ein Streamable-HTTP-Transport ist später möglich.