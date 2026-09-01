## Context

Der Katalog (`catalog.json`) enthält 32 Programme, hauptsächlich für
Postdocs/Profs. Student (BA/MA) sind mit 3 Einträgen vertreten, PhD-förderung
ist dünn (ein generischer DFG-Graduiertenkolleg, Studienstiftung Promotion,
DAAD). Die `sources.yaml` listet bereits 9 Quellgruppen, aber viele
Stiftungen und EU-Programme fehlen als Katalog-Einträge.

Parallel dazu ist die Fetch-Pipeline unvollständig: `fetchers.py` kann COST,
EU Horizon und BMBF-RSS abrufen, aber die Ergebnisse werden nicht persistiert
(`fetch_manual()` in `update_catalog.py` gibt `None` zurück; `fetch_bmbf_rss()`
erzeugt unvollständige Datensätze, die die `Programm`-Validierung nicht
bestehen). Der dokumentierte Cron ist nicht deployt.

Bestehende Bausteine: `fetchers.py` (HTTP-Clients), `update_catalog.py`
(Validierung, Merge, Expired-Check), `sources.yaml` (Single Source of Truth),
`server.py` `ingest` (validierendes Upsert), `grant_types.py`
(`Programm.from_dict`).

## Goals / Non-Goals

**Goals:**
- Katalog von 32 auf ~57 Programme erweitern, mit vollständiger Coverage über
  Karrierestufen (student, junior, postdoc, prof, senior).
- Begabtenförderungswerke (12 Stiftungen) und EU-Programme als neue
  Katalog-Kategorien.
- Fetch→Persist-Pipeline: Fetcher erzeugen validierte Programme, Merge in
  Katalog, Audit-Log.
- Deadline-Cron deployt und laufend.
- Alle neuen Einträge mit `status="zu-pruefen"` bis manuelle Verifikation.

**Non-Goals:**
- Keine Volltext-Scraping von Stiftungsportalen (zu fragil, zu viele
  unterschiedliche Formate).
- Kein automatisches Stichtags-Matching für partieinahe Stiftungen (12 separate
  Portale; manuelle Prüfung bleibt nötig).
- Keine DFG-Graduiertenkolleg-Datenbank (zu viele standortspezifische Einträge;
  Generischer Eintrag + Marburg-Pilot-Kollegs ausreichend).
- Kein Authentifizierungssystem für Profile (separater Change).

## Decisions

### 1. Begabtenförderungswerke als Kategorie „Stiftung", nicht eigene Kategorie
Alle 12 Begabtenförderungswerke werden unter `kategorie="Stiftung"` geführt, mit
einem konsistenten ID-Schema (`bfw-{name}`, z.B. `bfw-cusanuswerk`). Jeder Eintrag
hat die Karrierestufen, die das jeweilige Werk tatsächlich fördert.

**Warum:** Vereinfacht Filterung (ein Kategorie-Filter „Stiftung" erfasst alle);
keine neue Kategorie für einen Querschnitt der Förderlandschaft.

### 2. DFG Graduiertenkollegs: generisch + Pilot-spezifisch
Der bestehende generische Eintrag `dfg-graduiertenkolleg` bleibt. Zusätzlich
werden standortspezifische Kollegs der Pilot-Fakultät (Marburg) als eigene
Einträge hinzugefügt, wenn identifizierbar. DFG IRTG und Graduate School werden
als separate generische Einträge angelegt.

**Warum:** ~200 GKs aufzulisten ist nicht sinnvoll; Pilot-Relevanz geht vor
Vollständigkeit. Generische Einträge zeigen „es gibt GKs" für jede
Forschungsrichtung; spezifische Einträge zeigen echten Nutzen.

### 3. Fetch→Persist: Fetcher erzeugen vollständige Programme
Die Fetcher werden so erweitert, dass sie Programme mit allen Pflichtfeldern
erzeugen (`id`, `name`, `kategorie`, `themen`, `karriere`, `rolle`, `quelle`,
`standDatum`). Für Felder, die sich nicht automatisch extrahieren lassen:
- `themen`: aus dem Titel abgeleitet (keyword extraction), manuell übersteuerbar.
- `karriere`: konservative Annahme (leer = offen), oder aus Quelle abgeleitet.
- `rolle`: `["lead"]` als Default (einziger Antragsteller).
- `status`: `"zu-pruefen"` (immer, bis manuell verifiziert).

**Warum:** Ohne vollständige Datensätze scheitert die `Programm.from_dict`-
Validierung; Suggestions ohne Persist sind nutzlos.

### 4. Fetch→Persist über `apply_fetch_updates()`-Funktion
Neue Funktion in `fetchers.py`: nimmt `ProgrammeUpdate`-Ergebnisse, validiert
jeden Eintrag via `Programm.from_dict`, merged via `merge_programmes()` in den
Katalog, persistiert via `save_catalog()`, loggt ins Audit-Log.

**Warum:** Deutlichere Trennung Fetchen vs. Persistieren; testbar; wiederverwendbar
für CLI und Cron.

### 5. Deadline-Cron als Shell-Wrapper
Ein Shell-Skript `mcp/cron_check_expired.sh` ruft
`python3 update_catalog.py --check-expired` auf, leitet Output nach
`/var/log/grant-intelligence/expired.log`, sendet bei Abo optional per Mail.
Dokumentation mit crontab-Zeile und systemd-Timer-Beispiel.

**Warum:** Shell-Wrapper ist portabel; Python-Cron bricht bei Import-Fehlern
still; Logging geht an eine definierte Stelle.

## Risks / Trade-offs

- **[Fetch-Ergebnisse veraltet/unvollständig]** → Alle Fetch-Einträge erhalten
  `status="zu-pruefen"`. Der Audit-Log zeigt, wann ein Eintrag zuletzt
  aktualisiert wurde.
- **[12 Begabtenförderungswerke: Stichtage schwer automatisierbar]** → Manuelle
  Quellen in `sources.yaml`; Fetcher generiert Hinweise, keine Daten.
  Regelmäßige manuelle Prüfung dokumentiert in `sources.yaml` `last_check`.
- **[BMBF-RSS-Titel → ungenaue Themen]** → Keyword-Extraktion aus Titeln;
  Nutzer können Themen manuell korrigieren. `status="zu-pruefen"` dokumentiert.
- **[Cron auf lokalem System läuft nicht]** → Dokumentation enthält
  Check-Anleitung; Pilotphase kann manuell starten.
- **[~25 neue Einträge überlasten Validierung]** → Jeder Eintrag durchläuft
  `Programm.from_dict`; ungültige werden abgelehnt und geloggt, kein Abbruch.

## Open Questions

- Welche konkreten DFG-Graduiertenkollegs gibt es an der Pilot-Fakultät
  Marburg? (Ggf. DFG-Portal-Abfrage.)
- Sollen parteinahe Stiftungen (FES, HBS, KAS, RLS, HSS, FNS) mit expliziter
  parteipolitischer Markierung geführt werden? (Empfehlung: Nein, nur in
  `hinweis`-Feld.)
- Erasmus+ Deadlines sind institutionell (nicht individuell) — wie darstellen?
  (Empfehlung: `rolling=true`, Hinweis „Fristen über Hochschule".)
