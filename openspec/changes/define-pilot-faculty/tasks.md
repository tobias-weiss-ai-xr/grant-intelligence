# Tasks: define-pilot-faculty

## 1. Profildatenmodell & Persistenz

- [ ] 1.1 `mcp/profile.py` erstellen: `Profile`-Dataclass mit Feldern `id`,
      `name`, `karriere`, `themen`, `orcid`, `publikationen`, `einwilligung`,
      `status`, `standDatum`, `hinweis`; `from_dict`/`to_dict` (camelCase-Mapping
      wie `Programm`); `__post_init__`-Validierung (Pflichtfelder,
      `Karrierestufe.is_valid`, `Status.is_valid`).
- [ ] 1.2 `load_profiles()` und `save_profiles()` in `mcp/profile.py`: Lesen/
      Schreiben von `mcp/profiles.json` mit Envelope (`stand`, `quelleHinweis`,
      `profile`). `load_profiles()` liefert `[]` bei fehlender Datei.
- [ ] 1.3 Tests für `Profile` (`test_profile.py`): Round-Trip JSON, fehlende
      Pflichtfelder, ungültige Karrierestufe, fehlende Datei → leere Liste.

## 2. ORCID-Public-API-Adapter

- [ ] 2.1 `fetch_orcid(orcid_id)` in `mcp/profile.py`: GET
      `https://pub.orcid.org/v3.0/{orcid}/works` (JSON, `httpx`, Timeout 10s);
      Rückgabe der Werktitel und abgeleiteter Stichworte.
- [ ] 2.2 Einwilligungs-Gate: `fetch_orcid` prüft `einwilligung` des Profils;
      ohne Einwilligung leere Liste + Warnung. Netzwerk-/Parse-Fehler werden
      abgefangen (leere Liste, Warnung, keine Exception).
- [ ] 2.3 Tests für `fetch_orcid` mit `httpx`-Mock (Erfolg, 404, Timeout,
      fehlende Einwilligung).

## 3. Profil-basiertes Matching (additiv)

- [ ] 3.1 `match_profile()` und `next_deadline()` in `match.py` um optionales
      `profil: Profile | None = None` erweitern: Profil-Themen/Karriere als
      Default; explizite `felder`/`karriere` haben Vorrang.
- [ ] 3.2 Einwilligungs-Gate in `match_profile`: `profil.einwilligung=False`
      → leere Liste.
- [ ] 3.3 Tests: Profil als Default, explizite Felder überschreiben,
      Einwilligung-Gating, unbekanntes Profil.

## 4. MCP-Server-Erweiterung

- [ ] 4.1 Neues Tool `profile(id?)`: Profil nach ID laden oder alle Profile
      auflisten (ohne Matching).
- [ ] 4.2 `match_best`, `naechste_fristen`, `notify`, `brief` um optionalen
      `profil_id`-Parameter erweitern: lädt Profil via `load_profiles()`,
      reicht es an `match_profile` weiter; unbekannte ID → `fehler`-Feld;
      fehlende Einwilligung → `fehler` „Einwilligung fehlt …".
- [ ] 4.3 Tests für die neuen Server-Tool-Pfade (Mock-Katalog + Profile).

## 5. Web-UI-Erweiterung

- [ ] 5.1 `app.py`: Dropdown zur Profilauswahl (alle Profile aus
      `profiles.json`); bei Auswahl Themes/Karriere vorbelegen.
- [ ] 5.2 Hinweis anzeigen, wenn gewähltes Profil keine Einwilligung hat
      (keine Match-Karten); Profilname in der Ergebnis-Überschrift.
- [ ] 5.3 Tests/ manueller Check: Profilauswahl füllt Formular, Matching
      läuft, Consent-Hinweis erscheint.

## 6. Pilot-Setup & Demonstration

- [ ] 6.1 `mcp/profiles.json` mit echtem Pilot-Profil (Postdoc, KI-Forschung,
      `einwilligung=True` nach Bestätigung) und 2 Platzhalter-Profilen
      (andere Karrierestufe) finalisieren.
- [ ] 6.2 Pilot-Demo-Skript (`mcp/pilot_demo.py` oder Erweiterung `demo.py`):
      lädt reales Profil, führt `brief` aus, schreibt Top-3-Matches nach
      `docs/pilot-ergebnisse.md` (Name, Score, Begründung, Frist, Katalog-Stand).
- [ ] 6.3 `docs/pilot-ergebnisse.md` generieren und prüfen (Profile + Stand
      dokumentiert, Consent-Status sichtbar).
- [ ] 6.4 `docs/Architektur.md` und `docs/MVP-Demo.md` um Profil-Flow
      ergänzen; README „Status" aktualisieren (Profile-Fähigkeit).

## 7. Qualitätssicherung

- [ ] 7.1 `mypy` über `mcp/` grün (inkl. `profile.py`).
- [ ] 7.2 `pytest` grün (bestehende 104 + neue Profil-/ORCID-/Server-Tests).
- [ ] 7.3 `openspec validate define-pilot-faculty` grün.
- [ ] 7.4 CHANGELOG-Eintrag unter „Unreleased" (Added: Profildatenmodell,
      ORCID-Adapter, Profil-Matching, Pilot-Setup).
