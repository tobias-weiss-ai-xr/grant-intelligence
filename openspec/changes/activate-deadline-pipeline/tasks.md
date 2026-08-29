# Tasks: activate-deadline-pipeline

## 1. Frist-Digest-Modul

- [ ] 1.1 `mcp/deadline_digest.py` erstellen: `compute_digest()`,
      `diff_urgent()`, `save_digest()`, `load_digest()`, CLI `main()`.
- [ ] 1.2 Wiederverwendung von `grant_types.parse_frist` und
      `match.load_catalog` (keine Duplikation).

## 2. Tests

- [ ] 2.1 `mcp/test_deadline_digest.py`: compute_digest (urgent, upcoming,
      expired, rolling, keine-frist, kaputte-frist, sortierung, grenzen).
- [ ] 2.2 diff_urgent (erster lauf, keine-neuen, neu-dazu, abgelaufen).
- [ ] 2.3 save/load (roundtrip, fehlt, kaputt).
- [ ] 2.4 CLI main (schreibt digest, dedup zweiter lauf, --check schreibt
      nicht).
- [ ] 2.5 `pytest` grün (bestehend + neu), `mypy` grün.

## 3. GitHub Action

- [ ] 3.1 `.github/workflows/deadline-check.yml`: schedule + dispatch,
      digest, commit, issue.
- [ ] 3.2 Label `deadline-warning` wird erstellt falls fehlt.
- [ ] 3.3 Issue bei `neu_urgent > 0`; vorhandenes offenes Issue per Kommentar
      aktualisieren.

## 4. Dashboard

- [ ] 4.1 `dashboard/index.html`: Frist-Radar-Sektion (Tabelle).
- [ ] 4.2 `dashboard/app.js`: `deadlineDays()`, `deadlineClass()`,
      `urgentDeadlines` computed.
- [ ] 4.3 `dashboard/style.css`: urgency-Farbklassen.
- [ ] 4.4 `dashboard/sync-data.sh`: `deadline-digest.json` kopieren.

## 5. Cron-Wrapper

- [ ] 5.1 `mcp/cron_check_expired.sh`: zusätzlich `deadline_digest.py`
      aufrufen.

## 6. Doku

- [ ] 6.1 `docs/Roadmap.md`: Deadline-Pipeline als erledigt markieren.
- [ ] 6.2 `docs/Dashboard.md`: Frist-Radar-Panel dokumentieren.
- [ ] 6.3 `CHANGELOG.md`: Eintrag.

## 7. Qualitätssicherung

- [ ] 7.1 `openspec validate activate-deadline-pipeline` grün.
- [ ] 7.2 Workflow manuell auslösen und grün verifizieren.
- [ ] 7.3 Dashboard lokal rendern (Frist-Radar sichtbar).
