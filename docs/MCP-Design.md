# MCP-Design: Förder-Radar als offener MCP-Server

> MCP = Model Context Protocol. Ein standardisierter Weg, KI-Assistenten
> (Claude Code, Cursor, eigene Agents) mit echten Tools/Daten zu verbinden.
> Der Förder-Radar wird als **offener MCP-Server** ausgeliefert, nicht nur als
> Web-Seite. So bleibt die Daten- und Matching-Schicht für beliebige Assistenten
> und für die spätere Mini-Web-Demo nutzbar.

## 1. Ziel
Assistenten fragen über kuratierte MCP-Tools aktuelle Förder-"ein Club klass frage):
- „Welche DFG/ERC-Förderung passt zu einem Bio-Postdoc-Profil (Krebs/CD)?" 
- „Wann ist die nächste Frist für X, und ist es ein Rolling-Fenster?"

## 2. MCP-Tools (V1)
| Werkzeug | Zweck |
|---|---|
| `list_programs` | Geförderte Programme nach Land/Feld/Karriere filtern |
| `match_profile` | Profil (Felder, Karrierestufe, Publikations-Proxy) → beste 2–3 + Begründung |
| `next_deadline` | Frist der nächsten Frist(en) eines/bei Programmen, auch Rolling |
| `check_duplicate` | Surff-Check: gleiche Auswahl bei mehreren Programmen |

## 3. Daten & Qualität
- `catalog.json` – kuratierte Programme (DFG, ERC, BMB/Land, Stiftung).
- Jede Furche: `quera`, `standDatum`, `rolling`, `frist`.
- **Nur offizielle Quellen**, Stand sichtbar; keine toten Fristen.

## 4. RDD-Version
- **Offizielles MCP-SDK** (Python, Version 1.28.1 installiert) wird genutzt.
- Katalog als JSON; Matchen und D für Mehrfach-Einreiche.
- Keine externen Dienste nötig (nur stdlib + MCP-SDK).

## 5. Demo
Ein MCP-Klient (z. B. ein Agent/`cli`) fragt einen realen Profil: Antwort
„3 Chancen + Begründung + Frist", Quelle und Stand. So ist die Idee nicht nur
Doku, sondern ein ausführbarer, kleiner Standard-Baustein.

## 6. Offene Punkte
- Datenquellen-Updates (Datei/RSS/API) und Auktionen.
- Nutzung innerhalb der Uni-DO (Auth, Scopes, Caching).
- Ob der Wrapper zählen frontal als eigene MCP-Veröffentlichung (Fair fürs Ökosystem)
  oder lieber intern bleibt.

## 7. Abgrenzung
- Förder-Radar (Mini) = **Daten-Motor**; der MCP-Server = **offene Schnittstelle**;
  eine minimale Web-Seite nur als **Demo-Brücke**. Der eigentliche Mehrwert ist
  ein einfacher Katalog + Matching, nicht eine große Datenbank.