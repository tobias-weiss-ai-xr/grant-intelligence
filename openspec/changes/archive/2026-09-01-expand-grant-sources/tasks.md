# Tasks: expand-grant-sources

## 1. Neue Quellen zu sources.yaml hinzufügen

- [x] 1.1 Quellgruppe `deutschlandstipendium` (BMBF-Programm, URL, `type: manual`,
      `update_frequency: monthly`) zu `sources.yaml` hinzufügen.
- [x] 1.2 Quellgruppe `begabtenfoerderungswerke` (12 Werke mit je Name, URL,
      `type: manual`, `update_frequency: monthly`) zu `sources.yaml` hinzufügen.
- [x] 1.3 Quellgruppe `erasmus` (EU-Kommission, URL, `type: manual`,
      `update_frequency: monthly`) zu `sources.yaml` hinzufügen.
- [x] 1.4 Quellgruppe `msc` (Marie Skłodowska-Curie, EU, URL, `type: manual`,
      `update_frequency: monthly`) zu `sources.yaml` hinzufügen.
- [x] 1.5 Quellgruppe `gerda-henkel` (URL, `type: manual`, `update_frequency:
      monthly`) und `fritz-thyssen` zu `sources.yaml` hinzufügen.

## 2. Student-Programme in catalog.json ergänzen

- [x] 2.1 `deutschlandstipendium` Eintrag: `kategorie="Bund"`, `karriere=["student"]`,
      `themen=["thematisch-offen"]`, `rolling=True`, `status="laufend"`.
- [x] 2.2 12 Begabtenförderungswerke als Einträge (`bfw-cusanuswerk`,
      `bfw-ev-studienwerk`, `bfw-fes`, `bfw-hbs`, `bfw-kas`, `bfw-rls`,
      `bfw-hss`, `bfw-fns`, `bfw-sdw`, `bfw-avicenna`, `bfw-max-weber-bayern`,
      `bfw-klaus-murmann`): je mit korrekten Karrierestufen (student/junior) und
      `themen=["thematisch-offen"]`, parteikonfessioneller Hinweis.
- [x] 2.3 `daad-auslandsstipendium`: `kategorie="Stiftung"`, `karriere=["student"]`,
      `rolling=False`.
- [x] 2.4 `erasmus-plus`: `kategorie="EU"`, `karriere=["student"]`, `rolling=True`.

## 3. PhD / Grad-College-Programme ergänzen

- [x] 3.1 `dfg-irtg`: `kategorie="DFG"`, `karriere=["student", "junior"]`,
      `themen=["thematisch-offen"]`, `status="zu-pruefen"`.
- [x] 3.2 `dfg-graduate-school`: `kategorie="DFG"`, `karriere=["student", "junior"]`,
      `status="zu-pruefen"`.
- [x] 3.3 `msc-itn`: `kategorie="EU"`, `karriere=["junior"]`, `status="zu-pruefen"`.
- [x] 3.4 `msc-cofund`: `kategorie="EU"`, `karriere=["junior", "postdoc"]`,
      `status="zu-pruefen"`.
- [x] 3.5 `gerda-henkel`: `kategorie="Stiftung"`, `karriere=["junior", "postdoc"]`,
      `themen=["Geschichte", "Archäologie", "Kunstgeschichte", "Islamische Studien"]`.
- [x] 3.6 `fritz-thyssen`: `kategorie="Stiftung"`, `karriere=["postdoc", "junior", "prof"]`,
      `themen=["thematisch-offen"]`.

## 4. Fetcher → Persist Pipeline bauen

- [x] 4.1 `fetchers.py`: Fetcher-Funktionen erzeugen vollständige Programme (mit
      `kategorie`, `themen`, `karriere`, `rolle`, `status="zu-pruefen"`,
      `standDatum`). `fetch_bmbf_rss()` slug-basiertes Mapping für `kategorie`.
- [x] 4.2 `apply_fetch_updates(updates, catalog_path)` in `fetchers.py`: Validierung
      via `Programm.from_dict()`, Merge via `merge_programmes()`, Persist via
      `save_catalog()`, Audit-Log nach `docs/update_log.md`.
- [x] 4.3 `update_catalog.py`: `fetch_manual()` ruft Fetcher statt `None` und
      liefert validierte Programme; `--fetch` persistiert Ergebnisse.
- [x] 4.4 Tests für Fetch→Persist-Flow: Mock-Fetcher, Validierung, Merge, Audit-Log.

## 5. Deadline-Cron deployen

- [x] 5.1 `mcp/cron_check_expired.sh`: Shell-Wrapper für
      `update_catalog.py --check-expired`, Log nach
      `/var/log/grant-intelligence/expired.log`, Exit-Code 0/1.
- [x] 5.2 Crontab-Zeile und systemd-Timer-Beispiel in `docs/SPEC-Update-Pipeline.md`
      ergänzen.
- [x] 5.3 Warnungsausgabe erweitert: `id`, `name`, `frist`, `tage_abgelaufen`,
      `quelle` pro Eintrag.

## 6. Doku & Audit aktualisieren

- [x] 6.1 `docs/Datenquellen.md`: Neue Quellgruppen dokumentieren (Bund,
      Begabtenförderungswerke, Erasmus, MSCA, Gerda Henkel, Fritz Thyssen).
- [x] 6.2 `docs/update_log.md`: Audit-Log-Eintrag für diese Expansion.
- [x] 6.3 `README.md`: Programm-Zahl aktualisieren; Deadline-Cron erwähnen;
      Karrierestufen-übersicht aktualisieren.

## 7. Qualitätssicherung

- [x] 7.1 Alle neuen Einträge via `Programm.from_dict()` validieren (kein `ValueError`).
- [x] 7.2 `pytest` grün (bestehende 104 Tests + neue Fetch-/Cron-Tests).
- [x] 7.3 `mypy` grün über `mcp/`.
- [x] 7.4 Coverage-Check: `match_profile()` liefert Ergebnisse für alle
      Karrierestufen (student, junior, postdoc, prof, senior, verwaltung,
      service, IT, bibliothek).
- [x] 7.5 `openspec validate expand-grant-sources` grün.
- [x] 7.6 CHANGELOG-Eintrag unter „Unreleased".
