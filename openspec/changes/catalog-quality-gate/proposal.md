# Change: catalog-quality-gate

## Problem

Der Katalog ist durch `verify_sources` (Link-Check) und `Programm.from_dict`
(Pflichtfelder) abgesichert, aber es gibt **keine Durchsetzung der
Datenqualitäts-Regeln** des Projekts:

- `hinweis` muss immer gefüllt sein (Projektregel),
- `budget_*` muss `null` statt `0` sein,
- `frist` darf nicht abgelaufen sein (ohne Kennzeichnung),
- `rolling=True` widerspricht einem gesetzten `frist`,
- `standDatum` altert bei `status=verifiziert` (>60 Tage).

Die Lücke wurde real sichtbar: `erc-adg-2027` war `status=verifiziert`, hatte
aber eine bereits abgelaufene Frist (2026-08-27) und einen Hinweis, der
fälschlich „Rolling" behauptete – trotz grünem Link-Check.

## Proposal

Ein **Katalog-Qualitätsgate** als Nebenläufer zur Link-Prüfung:

1. **`catalog_lint.py`** – kleines Lint-Modul (Unix: eine Sache – Katalog
   prüfen). Regeln in `fail` (strukturell) und `warn` (Alterung) unterteilt.
   CLI: `--catalog`, `--report PATH` (JSON), `--fail` (Exit 1 bei fail-Findings).
2. **GitHub Action `catalog-lint.yml`** – wöchentlich (So 08:00 UTC) +
   bei Änderungen an `catalog.json`/`catalog_lint.py` + manuell; Report als
   Artifact; Exit 1 (rot) nur bei strukturellen Fehlern.
3. **Daten-Fix:** `erc-adg-2027` – abgelaufene Frist korrigiert
   (`frist=null`, `status=zu-pruefen`, frisches `standDatum`, korrigierter
   Hinweis ohne „Rolling"-Fehlangabe); kein Datum erfunden (Projektregel).
4. **Tests** für alle Lint-Regeln (fail + warn) und CLI-Exit-Codes.
5. **Doku** – CHANGELOG, README (Update-Pipeline), OpenSpec-Change.

## Keine Breaking Changes

- `catalog_lint.py` ist rein additiv; `update_catalog.py --validate` bleibt
  unverändert (Pflichtfelder) und der Lint ergänzt die Business-Regeln.
- Keine Änderung an `verify_sources`, `server`, `match`, `update_catalog`.
