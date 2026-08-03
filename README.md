# Förder-Radar – Grant Intelligence

> Status: **Arbeitsfähiger MVP (lokal).** FLASH-Einreichung abgegeben (2026-08).
> Kein fertiges Produkt, keine Versprechen – aber ein laufender Prototyp mit
> echten, verifizierten Quellen.

**Kern-These:** Es fehlt nicht an Förderangeboten (DFG, ERC, …), sondern an der
Übertragung auf *dein* Profil – und an der einzigen Zahl, die zählt: **deine Fristen**.

Förder-Radar ist ein **fristgesteuerter, profilbasierter Fördermittel-Monitor** –
für die eigene Fakultät/Pilot gedacht, auf offiziellen Quellen, mit transparenter
Begründung („Warum passt das?") und einer Deadline-Pipeline statt Meisterflut aus
Abo-Datenbanken.

---

## Inhalt

| Datei | Zweck |
|---|---|
| `docs/Konzept.md` | Vertieftes Konzept (Problem, These, Scope, Nutzen) |
| `docs/Architektur.md` | Bausteine, Datenquellen, Datenmodell-Skizze |
| `docs/MVP-Demo.md` | 1-Seiten-Demo-Skizze (was der Prototyp zeigt) |
| `docs/Wettbewerb.md` | Kompetitive Landschaft (Open Source & kommerziell) |
| `docs/Datenquellen.md` | Primär-Quellen (verifiziert) + Verarbeitung/Aktualisierung |
| `docs/Einreichung.md` | FLASH-Einreichungstext (≤300 Wörter) |
| `docs/brief.md` | Beispiel-Wochen-Brief (automatisch erzeugt) |
| `mcp/` | Prototyp: MCP-Server, Matching, UI, Wochen-Brief (Details: `mcp/README.md`) |

## Stand (2026-08-03)
- **Katalog:** 6 Programme aus ERC/DFG/Land; ERC-Fristen (StG 14.10.2026,
  AdG 27.08.2026, SyG 11.05.2027) live vom Portal verifiziert; je Programm
  `status` (verifiziert/laufend/zu-pruefen) + `standDatum`.
- **Läuft:** Agent-Schleife als MCP-Server (`mcp/server.py`), Ein-Bildschirm-UI
  (`mcp/app.py`), Wochen-Brief per Cron (`mcp/brief.py`), Persistenz über
  `ingest`/`loeschen`.

```bash
cd mcp && pip install -r requirements.txt
python3 demo.py                      # Agent-Schleife
uvicorn app:app --port 8000          # UI: http://127.0.0.1:8000
python3 brief.py --felder Biologie Nachhaltigkeit --karriere postdoc
```

## Grundsätze
- **Offizielle Quellen**, keine toten Fristen; jedes Datum mit Stand.
- **Einwilligung** für Profildaten (ORCID, Publikationen), DSGVO-fähig.
- **Kleiner Einstieg zuerst:** eine Fakultät, eine Persona, 2–3 Programmfamilien.
- **Human-in-the-loop:** Scoring orientiert, die Person entscheidet.

## Verwandt
Konzept-Ursprung im Repo [mafex-flash](https://github.com/tobias-weiss-ai-xr/mafex-flash)
(eine unter mehreren Kandidaten-Ideen).