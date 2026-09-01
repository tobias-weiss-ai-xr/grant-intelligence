## Why

Der MVP läuft mit Beispielfeldern statt realen Profilen. Die Konzept-Roadmap
(`docs/Konzept.md` §9) nennt als nächsten Schritt „eine Pilot-Fakultät und 2–3
reale Profile festlegen" – das ist der Engpass für jede messbare Wirkung
(früh erkannte Calls, weniger verpasste Fristen). Heute existiert kein
persistentes Profil: `match_profile()` erhält nur Listen von Forschungsfeldern
und eine Karrierestufe; ORCID, Publikationen und DSGVO-Einwilligung sind in
der Architektur skizziert (`docs/Architektur.md` §3), aber nicht umgesetzt.

## What Changes

- **Neues Profildatenmodell** `Profile` (type-safe dataclass, analog zu
  `Programm`): `id`, `name`, `themen[]`, `karriere`, `orcid`, `publikationen[]`,
  `einwilligung` (bool), `status`, `standDatum`. Persistenz als
  `mcp/profiles.json` (gleiche Bauart wie `catalog.json`).
- **DSGVO-Einwilligung als harte Voraussetzung**: Matching akzeptiert nur
  Profile mit `einwilligung=True`; sonst Rückgabe einer klaren Fehlermeldung.
  Profile ohne Einwilligung werden gespeichert, aber nicht gematcht.
- **ORCID-/Publikations-Adapter (Public API)**: ORCID Public API Abruf, um
  `themen` und `publikationen` aus dem Profil zu ergänzen (optional, nur mit
  Einwilligung). Themen bleiben manuell übersteuerbar.
- **Profil-basiertes Matching**: `match_profile()` und `brief` akzeptieren
  wahlweise eine `profil_id` statt loser Felder. Das bestehende Felder-Interface
  bleibt für die Demo/UI erhalten (kein Breaking Change für die Web-UI).
- **Pilot-Fakultät definieren**: Philipps-Universität Marburg, Fachbereich
  ausgewählt (siehe design.md). 2–3 reale Seed-Profile in `profiles.json`.
- **Profil-UI**: Formular zum Anlegen/Anzeigen eines Profils (ORCID-Feld,
  Einwilligungs-Checkbox, Themen). Das bestehende „Felder eingeben"-Formular
  wird um „Profil speichern" erweitert.

## Capabilities

### New Capabilities
- `researcher-profile`: Persistentes, einwilligungsbasiertes Forscherprofil
  (Datenmodell, Speicherung, ORCID-Adapter) als Grundlage für Matching und
  Frist-Warnungen.
- `pilot-setup`: Konkrete Pilot-Fakultät (Marburg) mit 2–3 realen Seed-Profilen
  und Match-Ergebnissen, die den Pilotbetrieb zeigen.

### Modified Capabilities
<!-- Keine bestehenden Specs – dieses Projekt hat noch keine OpenSpec-Specs. -->

## Impact

- **Neue Dateien:** `mcp/profiles.json` (Seed-Profile), `mcp/profile.py`
  (Datenmodell + Persistenz + ORCID-Adapter), Tests.
- **Geändert:** `mcp/match.py` (`match_profile`, `next_deadline` akzeptieren
  optional `profil_id`), `mcp/server.py` (`brief`, `match_best`,
  `naechste_fristen` mit Profil-Bezug), `mcp/app.py` (Profil-Formular).
- **Abhängigkeiten:** `httpx` (bereits vorhanden) für ORCID Public API.
- **DSGVO:** Profile speichern nur minimale Daten mit Einwilligung; keine
  Cloud-Übertragung ohne `einwilligung=True`.
- **Kein Breaking Change:** Das bestehende Felder-Interface der UI bleibt
  funktionsfähig; das Profil-Interface ist additiv.
