# Architektur-Skizze

## 1. Prinzip
Kleine, offene Bausteine statt Monolith. Ein Beispiel-Profil erzeugt eine
Bewertungsansicht „nächste Chance + Begründung + Frist".

## 2. Bausteine
1. **Datenquellen / Förderkatalog**
   - DFG, ERC, BMBF, EU, Bund, Land, Stiftungen, Industrie, International.
   - Format je Abbildung: Ausschreibungstext, Themen-Keywords, Karrierestufe,
   Rolle, Budget, Frist, Rolling-Struktur, Quelle, Stand-Datum.
2. **Profile**
   - Eingabe ORCID / Publikationen / Stichworte (mit Einwilligung).
   - Öffentlich per Merge Request (`profiles.json`) oder privat lokal
   (`profiles.local`).
   - Themen-Vektor + Karrierestufe („Postdoc", „Junior-Prof").
   - **Implementiert:** `mcp/profile.py` (Dataclass, Persistenz, ORCID-Adapter),
     `mcp/profiles.json` (3 Pilot-Profile, Fachbereich Mathematik).
   - **DSGVO:** `einwilligung=True` erforderlich für Matching. Ohne Einwilligung:
     leere Ergebnisse, klare Meldung.
3. **Matching-Engine**
   - Gewichtete Punkte (Thema, Karriere, Rolle, Geo), Ausgabe Score +
   kurze Begründung je Treffer.
4. **Frist-Pipeline / Benachrichtigung**
   - Nächste Frist je Programm, Rolling-Fenster, Alarm (E-Mail/Kalender).
5. **Oberfläche**
   - Eine Seite: „Meine 5 Chancen + Begründung + Frist-Zähler".
   - Zusätzlich MCP-Server für Agent-Integration.

## 3. Datenmodell (Kernentitäten)
```
Programm {
  id, name, themen[],
  kategorie: DFG | ERC | BMBF | EU | Land | Stiftung | Industrie | Bund | International,
  frist: Date, rolling: boolean,
  budgetMin, budgetMax, rolle[lead|partner],
  karriere[postdoc|junior|prof|senior|student|verwaltung|service|IT|bibliothek],
  quelle, standDatum, status, hinweis
}
Profil {
  id, name, themen[], karriere, orcid, publikationen, einwilligung, status,
  standDatum, hinweis
}

**Implementiert in `mcp/profile.py`:**
- `Profile`-Dataclass mit `from_dict`/`to_dict` (camelCase-Mapping)
- `load_profiles()`/`save_profiles()` (Persistenz in `profiles.json`)
- `fetch_orcid()` (ORCID Public API, einwilligungsbasiert)
- `derive_themen()` (Schlagwort-Extraktion aus Publikationstiteln)
- Consent-Gate: `match_profile(profil=...)` verweigert Matching ohne Einwilligung
- MCP-Tool `profile(id?)` zum Laden/Auflisten von Profilen
- Web-UI: Profil-Dropdown mit Pre-Fill und Consent-Hinweis
Match { profilId, programmId, score, begruendung }
FristAlert { profilId, programmId, frist, alarm }
```

## 4. Technologie
- Backend: Python (FastAPI + FastMCP); Frontend: einfache HTML/JS.
- Katalog + Profile als kuratierte JSON, gepflegt über Update-Skript.
- Keine teuren Dienste; KI optional nur für die Begründung (SAIA-KI-API).

## 5. Offene Fragen
- ~~Zugriff auf ORCID/Uni-Daten~~ → ORCID Public API implementiert (`fetch_orcid`).
- Aktualisierungswege je Quelle (Datei / RSS / API).
- Sprach- und Datumsnormalisierung.
- Echte Pilot-Kollegen für Mathematik-Fachbereich (Platzhalter aktiv).
