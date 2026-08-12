## Context

Der Förder-Radar-MVP hat ein funktionierendes Matching (`match.py`), einen MCP-Server
(`server.py`) und eine Web-UI (`app.py`), aber **kein Profildatenmodell**. Profile
werden ad-hoc als Listen von Forschungsfeldern + Karrierestufe durchgereicht
(`match_profile(programme, fields, karriere, ...)`). Die Architektur-Skizze
(`docs/Architektur.md` §3) definiert eine `Profil`-Entität mit ORCID, Publikationen
und Einwilligung – diese ist nicht umgesetzt. Der Pilot (Konzept §9) benötigt 2–3
reale Profile, um Wirkung zu messen.

Stakeholder: Pilot-Fakultät (Philipps-Universität Marburg), Einzelperson als
erster Nutzer (Postdoc, KI-Forschung).

Bestehende Bausteine, auf die aufgesetzt wird:
- `grant_types.py`: `Programm`-Dataclass mit `from_dict`/`to_dict`, `Status`-Enum,
  `parse_frist`, `budget_beschreibung`.
- `match.py`: `match_profile()`, `next_deadline()` (reine Logik, kein I/O).
- `server.py`: MCP-Tools `match_best`, `naechste_fristen`, `brief`, `notify`.
- `app.py`: FastAPI-UI mit Formular (Felder + Karriere).
- `catalog.json`: 32 verifizierte Programme, camelCase-Format.

## Goals / Non-Goals

**Goals:**
- Persistente Forscherprofile (Typ `Profile`) mit DSGVO-Einwilligung als harte
  Voraussetzung für Matching.
- ORCID-Public-API-Adapter, um Themen/Publikationen anzureichern (optional, nur
  mit Einwilligung).
- Profil-basiertes Matching als additives Interface (kein Breaking Change).
- Konkreter Pilot: Marburg, 2–3 reale Seed-Profile, demonstrierte Match-Ergebnisse.
- Profildaten bleiben lokal (keine Cloud-Übertragung ohne Einwilligung).

**Non-Goals:**
- Kein Antrags-Schreib-Assistent (bleibt bewusst_out of scope_ per Konzept §4.2).
- Keine Verwaltung bewilligter Projekte.
- Keine Authentifizierung/Multi-Tenant-System (Pilot = einzelner Fachbereich,
  lokal).
- Keine ORCID-Sandbox/Member-API – nur die öffentliche Read-API.
- Keine automatische Themen-Extraktion aus Publikations-Volltexten (nur Titelmetadaten).

## Decisions

### 1. Profildatenmodell als Dataclass (analog `Programm`)
`Profile` als `@dataclass` in neuem `mcp/profile.py` mit `from_dict`/`to_dict`
(camelCase-Konvention wie Katalog). Felder: `id`, `name`, `karriere`, `themen[]`,
`orcid`, `publikationen[]`, `einwilligung: bool`, `status`, `standDatum`, `hinweis`.
Persistenz als `mcp/profiles.json` (gleiche Bauart wie `catalog.json`: `stand` +
`quelleHinweis` + Liste).

**Warum:** Konsistenz mit `Programm`-Pattern; type-safe; testbar; keine neue
Abhängigkeit. Alternative (SQLite) wäre für einen Pilot mit 3 Profilen übertrieben.

### 2. Einwilligung als harte Matching-Voraussetzung
`match_profile()` und abgeleitete Funktionen prüfen `einwilligung`. Ohne
Einwilligung: leere Ergebnisliste + klare Meldung „Einwilligung fehlt". Profile
werden gespeichert, aber nicht gematcht.

**Warum:** DSGVO-Konformität (Konzept §7); Profil nur mit Einwilligung. Die
Prüfung in der Logikschicht (nicht nur UI) verhindert Umgehung über MCP/CLI.

### 3. ORCID-Public-API-Adapter (optional, einwilligungsbasiert)
Neue Funktion `fetch_orcid(orcid_id)` nutzt `https://pub.orcid.org/v3.0/{orcid}/`
(Public API, keine Auth nötig, JSON). Liest `works` (Titel) und ableitbare
Schlagworte. Themen bleiben manuell übersteuerbar – ORCID ergänzt nur, ersetzt
nicht. Aufruf nur, wenn `einwilligung=True` und `orcid` gesetzt.

**Warum:** ORCID Public API ist frei, DSGVO-konform (öffentliche Forschungsdaten),
reduziert manuelle Eingabe. Alternative (OpenAlex) benötigt keine ORCID, aber
weniger präzise Personen-Zuordnung. ORCID first, OpenAlex später denkbar.

### 4. Additives Matching-Interface (kein Breaking Change)
`match_profile()` erhält optionale Parameter `profil: Profile | None = None`.
Wenn gesetzt, werden `themen`/`karriere` aus dem Profil gezogen (überschreiben
explizite Parameter nicht – explizite Parameter haben Vorrang, damit die UI
weiterhin funktioniert). `brief`, `match_best`, `naechste_fristen` im MCP-Server
erhalten optionalen `profil_id`-Parameter, der das Profil aus `profiles.json`
lädt.

**Warum:** Bestehende Tests (104) und UI bleiben grün. Neue Funktionalität ist
rein additiv. Alternative (neue Funktion `match_profil()`) würde Logik duplizieren.

### 5. Pilot-Fakultät: Philipps-Universität Marburg
Pilot-Fachbereich: Naturwissenschaften/Technik mit KI-Schwerpunkt (deckt Postdoc
+ KI-Themen ab). Seed-Profile in `profiles.json`: 1 reales Profil (Postdoc,
KI-Forschung), 2 Platzhalter (andere Fachrichtung/Karrierestufe für Diversität).

**Warum:** Marburg ist in der Einreichung (V2) genannt; KI-Forschung passt zum
ersten Nutzer. Platzhalter zeigen Coverage über Karrierestufen (postdoc/junior).

### 6. Profildaten lokal, keine Cloud
`profiles.json` liegt im `mcp/`-Verzeichnis (wie Katalog). ORCID-Abruf erfolgt
nur auf expliziten Aufruf, nicht automatisch beim Startup. Kein Upload, kein
Teilen.

**Warum:** DSGVO, lokale Souveränität (Konzept §7, Einreichung V2).

## Risks / Trade-offs

- **[ORCID Rate-Limit/Erreichbarkeit]** → Adapter fängt Fehler ab, loggt Warnung,
  Matching läuft mit manuellen Themen weiter. ORCID ist Ergänzung, nicht Pflicht.
- **[Themen aus Publikationstiteln ungenau]** → ORCID-Adapter extrahiert nur
  Stichworte aus Titeln; Nutzer kann Themen manuell korrigieren. Kein
  NLP-Topic-Modeling in diesem Change.
- **[Einwilligung fälschlich `false` → leere Ergebnisse verwirren Nutzer]** →
  Klare Fehlermeldung „Einwilligung fehlt – Profil kann nicht gematcht werden".
- **[Profile ohne ORCID]** → Funktioniert; Themen manuell gepflegt. ORCID optional.
- **[DSGVO: Publikationen sind öffentlich, Profil aber personenbeziehen]** →
  `profiles.json` enthält Namen + ORCID; liegt lokal; `hinweis` dokumentiert
  Zweck. Kein automatischer Export ohne Einwilligung.
- **[Pilot mit nur 1 echten Profil]** → 2 Platzhalter zeigen Multi-Profil-Fähigkeit;
  echte Profile werden nachfolgen. Demo bleibt ehrlich (Konzept §7
  „Erwartungsmanagement").

## Migration Plan

1. `mcp/profile.py` erstellen (Dataclass + Persistenz + ORCID-Adapter) + Tests.
2. `mcp/profiles.json` mit Seed-Profilen anlegen (bereits begonnen).
3. `match.py` `match_profile()`/`next_deadline()` um optionales `profil` erweitern.
4. `server.py` MCP-Tools um `profil_id` erweitern; neues Tool `profile` (Profil
   laden/anlegen).
5. `app.py` Formular um Profil-Auswahl/Anlegen erweitern.
6. Tests ergänzen (Profil-Matching, Einwilligung-Gating, ORCID-Mock).
7. `docs/` aktualisieren (Architektur, MVP-Demo: Profil-Flow).

**Rollback:** Da rein additiv, genügt das Entfernen der neuen Parameter. Die
bestehende Felder-basierte API bleibt unverändert funktionsfähig.

## Open Questions

- Echte ORCID des Pilot-Nutzers (wartet auf Bestätigung).
- Zweite/dritte reale Profile (Platzhalter bis Pilot-Kolleg:innen benannt).
- Soll die ORCID-Aktualisierung per Cron oder nur manuell (Button) erfolgen?
  Empfehlung: manuell im Pilot, Cron später.
