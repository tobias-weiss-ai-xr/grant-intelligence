# Tasks: define-pilot-faculty

## 1. Profildatenmodell & Persistenz

- [x] 1.1 `mcp/profile.py` erstellen: `Profile`-Dataclass mit Feldern `id`,
      `name`, `karriere`, `themen`, `orcid`, `publikationen`, `einwilligung`,
      `status`, `standDatum`, `hinweis`; `from_dict`/`to_dict` (camelCase-Mapping
      wie `Programm`); `__post_init__`-Validierung (Pflichtfelder,
      `Karrierestufe.is_valid`, Status validiert gegen `{aktiv, inaktiv}`).
- [x] 1.2 `load_profiles()` und `save_profiles()` in `mcp/profile.py`: Lesen/
      Schreiben von `mcp/profiles.json` mit Envelope (`stand`, `quelleHinweis`,
      `profile`). `load_profiles()` liefert `[]` bei fehlender Datei.
- [x] 1.3 Tests für `Profile` (`test_profile.py`): Round-Trip JSON, fehlende
      Pflichtfelder, ungültige Karrierestufe, fehlende Datei → leere Liste.

## 2. ORCID-Public-API-Adapter

- [x] 2.1 `fetch_orcid(orcid_id, einwilligung, timeout)` in `mcp/profile.py`: GET
      `https://pub.orcid.org/v3.0/{orcid}/works` (JSON, `httpx`, Timeout 10s);
      Rückgabe der Werktitel. `derive_themen()` leitet Stichworte ab.
- [x] 2.2 Einwilligungs-Gate: `fetch_orcid` prüft `einwilligung`; ohne
      Einwilligung leere Liste + Warnung. Netzwerk-/Parse-Fehler werden
      abgefangen (leere Liste, Warnung, keine Exception).
- [x] 2.3 Tests für `fetch_orcid` mit `httpx`-Mock (Erfolg, 404, Timeout,
      fehlende Einwilligung, malformed JSON, empty works).

## 3. Profil-basiertes Matching (additiv)

- [x] 3.1 `match_profile()` und `next_deadline()` in `match.py` um optionales
      `profil: Profile | None = None` erweitern: Profil-Themen/Karriere als
      Default; explizite `felder`/`karriere` haben Vorrang.
- [x] 3.2 Einwilligungs-Gate in `match_profile`: `profil.einwilligung=False`
      → leere Liste.
- [x] 3.3 Tests: Profil als Default, explizite Felder überschreiben,
      Einwilligung-Gating, `next_deadline` mit Profil, Profil-Parameter in
      `server.py`-Tools.

## 4. MCP-Server-Erweiterung

- [x] 4.1 Neues Tool `profile(id?)`: Profil nach ID laden oder alle Profile
      auflisten (ohne Matching).
- [x] 4.2 `match_best`, `naechste_fristen`, `notify`, `brief` um optionalen
      `profil_id`-Parameter erweitern: lädt Profil via `get_profile_by_id()`,
      reicht es an `match_profile` weiter; unbekannte ID → leere Liste /
      `fehler`-Feld; fehlende Einwilligung → `fehler` „Einwilligung fehlt …".
- [x] 4.3 Tests für die neuen Server-Tool-Pfade (Mock-Katalog + Profile,
      Edge Cases: unbekannte ID, kein Consent, aktives Profil).

## 5. Web-UI-Erweiterung

- [x] 5.1 `app.py`: Dropdown zur Profilauswahl (alle Profile aus
      `profiles.json`); bei Auswahl Themen/Karriere vorbelegen.
- [x] 5.2 Hinweis anzeigen, wenn gewähltes Profil keine Einwilligung hat
      (keine Match-Karten); Profilname in der Ergebnis-Überschrift.
- [x] 5.3 Tests: Profilauswahl füllt Formular, Matching läuft, Consent-Hinweis
      erscheint, unbekannte Profil-ID fällt auf manuelle Felder zurück.

## 6. Pilot-Setup & Demonstration

- [x] 6.1 `mcp/profiles.json` mit echtem Pilot-Profil (Tobias Weiss, Postdoc,
      KI-Forschung, `einwilligung=True`) und 2 Platzhalter-Profilen
      (Mathematik Postdoc/Junior, `einwilligung=False`, `status=inaktiv`).
- [x] 6.2 Pilot-Demo-Skript `mcp/pilot_demo.py`: lädt Profile, führt
      `match_profile` aus, schreibt Top-5-Matches nach `docs/pilot-ergebnisse.md`.
- [x] 6.3 `docs/pilot-ergebnisse.md` generiert und geprüft (Profile + Stand
      dokumentiert, Consent-Status sichtbar).
- [x] 6.4 `docs/Architektur.md` und `docs/MVP-Demo.md` um Profil-Flow
      ergänzt; Profil-Dropdown, Consent-Hinweis, ORCID-Adapter dokumentiert.

## 7. Qualitätssicherung

- [x] 7.1 `mypy` über `mcp/` grün (20 Source-Dateien, inkl. `profile.py`).
- [x] 7.2 `pytest` grün: 245 Tests (181 bestehend + 64 neue Profil-/ORCID-/
      Server-/UI-/Pilot-Tests). 100% Coverage auf allen Kernmodulen.
- [x] 7.3 `openspec validate define-pilot-faculty` grün.
- [x] 7.4 CHANGELOG-Eintrag unter „Unreleased" (Added: Profildatenmodell,
      ORCID-Adapter, Profil-Matching, Pilot-Setup).
