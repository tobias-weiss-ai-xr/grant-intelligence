# Change: activate-deadline-pipeline

## Problem

Der Förder-Radar hat eine Frist-Logik (`naechste_fristen`, `notify`,
`check_expired`) und einen unverbundenen Cron-Wrapper
(`cron_check_expired.sh`), der aber **nicht deployed** ist und nur abgelaufene
Fristen als Log-Zeilen ausgibt. Es gibt:

- keinen strukturierten, maschinenlesbaren Frist-Digest,
- keine Deduplizierung (jeder Lauf meldet alle Fristen erneut),
- keine automatische Benachrichtigung (Issue/E-Mail) bei neuen dringenden
  Fristen,
- keinen wiederkehrenden, portablen Lauf (GitHub Action),
- keine Frist-Übersicht im Dashboard (nur ein Chart, keine Tabelle).

## Proposal

Eine end-to-end Frist-Benachrichtigungs-Pipeline:

1. **`deadline_digest.py`** – kleines, fokussiertes Modul (Unix-Philosophie:
   eine Sache – Frist-Übersicht erzeugen). Liest den Katalog, erzeugt einen
   strukturierten Digest (dringend ≤30d, anstehend ≤90d, abgelaufen, rolling),
   persistiert `deadline-digest.json` und dedupliziert gegen den vorherigen
   Lauf (nur *neue* dringende Fristen werden gemeldet).
2. **GitHub Action `deadline-check.yml`** – wöchentlich (So 06:00 UTC) +
   manuell; berechnet den Digest, committet ihn, und öffnet/aktualisiert ein
   GitHub Issue (Label `deadline-warning`) bei neuen dringenden Fristen.
3. **Dashboard-Panel "Frist-Radar"** – Tabelle der anstehenden Fristen (≤90d),
   farbcodiert nach Dringlichkeit (≤14d rot, ≤30d orange, >30d grün).
4. **`sync-data.sh`** – kopiert `deadline-digest.json` ins Dashboard-Daten-
   Verzeichnis.
5. **`cron_check_expired.sh`** – ruft zusätzlich `deadline_digest.py` auf,
   damit ein lokaler/systemd-Lauf ebenfalls den Digest erzeugt.
6. **Tests** für `deadline_digest.py` (compute, diff, save/load, CLI).
7. **Doku** – Roadmap, Dashboard.md, CHANGELOG.

## Keine Breaking Changes

- Bestehende Module (`update_catalog.py`, `match.py`, `server.py`) werden
  nicht geändert. `deadline_digest.py` ist ein neues, rein additivses Modul.
- `cron_check_expired.sh` erhält einen zusätzlichen Aufruf, bleibt
  abwärtskompatibel.
- Dashboard-Änderungen sind rein additiv (neue Sektion).
