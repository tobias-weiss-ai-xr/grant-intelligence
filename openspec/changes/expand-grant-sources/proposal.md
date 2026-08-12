## Why

Der Katalog hat 32 Programme, aber **Student (BA/MA) sind mit nur 3 Einträgen
vertreten** (DFG Graduiertenkolleg, DAAD, Studienstiftung Promotion). Es fehlen
das Deutschlandstipendium, 11 der 12 Begabtenförderungswerke (Cusanuswerk,
Evangelisches Studienwerk, parteinahe Stiftungen, SDW), Erasmus+, DAAD
Auslandsstipendien und Marie Skłodowska-Curie Actions (EU). DFG Graduiertenkollegs
sind nur als ein generischer Eintrag vorhanden, nicht als Kategorie mit ~200
standortspezifischen Kollegs. Gleichzeitig ist die Update-Pipeline nicht
angeschlossen: `fetchers.py` generiert nur Suggestions, `update_catalog.py`'s
`fetch_manual()` gibt `None` zurück, der dokumentierte Cron ist nicht deployt.
Neue Quellen ohne automatische Pipeline veralten sofort.

## What Changes

### Neue Quellen (~25 Programme)

**Student (BA/MA) — 8 neue:**
- Deutschlandstipendium (Bundesprogramm, über Hochschulen)
- Cusanuswerk (katholisch, BA+MA+PhD)
- Evangelisches Studienwerk Villigst (evangelisch, BA+MA+PhD)
- Friedrich-Ebert-Stiftung (SPD-nah, BA+MA+PhD)
- Heinrich-Böll-Stiftung (Grüne, BA+MA+PhD)
- Konrad-Adenauer-Stiftung (CDU, BA+MA+PhD)
- Rosa-Luxemburg-Stiftung (Die Linke, BA+MA+PhD)
- Hanns-Seidel-Stiftung (CSU, BA+MA+PhD)
- Friedrich-Naumann-Stiftung (FDP, BA+MA+PhD)
- Stiftung der Deutschen Wirtschaft (SDW, BA+MA+PhD)
- Avicenna-Stiftung (muslimisch, BA+MA+PhD)
- DAAD Auslandsstipendium (BA/MA outgoing)
- Erasmus+ (EU Mobilität, BA/MA)

**PhD / Graduiertenkollegs — 5 neue:**
- DFG International Research Training Group (IRTG) — generisch
- DFG Graduate School (Clausthal-Modell) — generisch
- DFG Graduiertenkolleg Marburg (pilot-relevant: GRK 2501 Transcend, falls zutreffend)
- Marie Skłodowska-Curie ITN (EU doctoral networks)
- Marie Skłodowska-Curie COFUND (EU doctoral/postdoc programmes)

**Promotion/Stiftungen — 3 neue:**
- Begabtenförderungswerke: Promotionsförderung (konsolidierter Eintrag für alle 12 Werke)
- Max Weber Programm Bayern (Hochbegabtenförderung)
- Gerda Henkel Stiftung (Geisteswissenschaften)

**Postdoc+ — 2 neue:**
- Fritz Thyssen Stiftung (interdisziplinär)
- Avicenna-Stiftung Promotions-/Postdoc-Förderung

### Automatische Ingestion-Pipeline

- Fetcher erzeugen vollständige, validierte Programmeinträge (nur Suggestions).
- `apply_fetch_updates()` verbindet Fetcher-Ergebnisse mit `merge_programmes()`.
- Deadline-Cron deployt (systemd timer oder crontab).
- Status-Lebenszyklus: Fetch-Einträge → `status="zu-pruefen"` → manuell → `verifiziert`.

## Capabilities

### New Capabilities
- `student-grants`: Katalog-Erweiterung um Bachelor/Master-Stipendien
  (Deutschlandstipendium, Begabtenförderungswerke, DAAD, Erasmus+) mit passenden
  Karrierestufen, Themen und Deadlines.
- `phd-grad-colleges`: Katalog-Erweiterung um Promotionsförderung und
  Graduiertenkollegs (DFG IRTG/Graduate School, MSCA ITN/COFUND, Max Weber) mit
  standortspezifischen Einträgen.
- `fetch-persist`: Automatisches Fetchen offizieller Quellen, Validierung,
  Upsert in den Katalog und Audit-Logging.
- `deadline-cron`: Deployter, wiederkehrender Frist-Check mit Warnung bei
  abgelaufenen/dringenden Fristen.

### Modified Capabilities
<!-- Keine bestehenden Specs. -->

## Impact

- **Katalog:** ~25 neue Programmeinträge in `catalog.json` (32 → ~57).
- **Quellen:** `sources.yaml` um 5 neue Quellgruppen erweitert (deutschlandstipendium,
  begabtenfoerderungswerke, erasmus, msc, gerda-henkel).
- **Geändert:** `mcp/fetchers.py` (Fetch→Persist-Brücke, `apply_fetch_updates()`),
  `mcp/update_catalog.py` (`fetch_manual` nutzt Fetcher statt `None`).
- **Neu:** `mcp/cron_check_expired.sh` (Cron-Wrapper).
- **Docs:** `docs/update_log.md` (Audit), `docs/Datenquellen.md` (neue Quellen).
- **Tests:** Neue Test-Cases für Fetch→Persist-Flow.
- **Kein Breaking Change:** Alles additiv; bestehende 104 Tests bleiben grün.
