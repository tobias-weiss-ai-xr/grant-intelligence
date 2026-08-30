# Tasks: catalog-quality-gate

## 1. Lint-Modul

- [x] 1.1 `mcp/catalog_lint.py` erstellen: `lint_catalog()`, `build_report()`,
      CLI `main()` mit `--catalog`, `--report`, `--fail`.
- [x] 1.2 FAIL-Regeln: id/name/kategorie/status/frist/hinweis/budget/rolling/
      quelle/duplicate-ids.
- [x] 1.3 WARN-Regeln: frist-abgelaufen, stand-datum-alt (verifiziert > 60d).

## 2. Tests

- [x] 2.1 `mcp/test_catalog_lint.py`: alle FAIL-Regeln.
- [x] 2.2 WARN-Regeln (abgelaufen, stand-datum-alt, nur bei verifiziert).
- [x] 2.3 `build_report` (clean/warn/problems, Serialisierbarkeit).
- [x] 2.4 CLI: `--fail` → Exit 1 bei fail-Findings; ohne `--fail` → Exit 0.
- [x] 2.5 `pytest` grün (bestehend + neu), `mypy` grün.

## 3. Daten-Fix

- [x] 3.1 `erc-adg-2027`: `frist=null`, `status=zu-pruefen`, frisches
      `standDatum`, korrigierter `hinweis` (kein „Rolling"-Fehler).
- [x] 3.2 Lint auf echtem Katalog: Ergebnis `clean` (fail=0, warn=0).

## 4. CI-Workflow

- [x] 4.1 `.github/workflows/catalog-lint.yml`: schedule + dispatch + push
      (catalog.json/catalog_lint.py/workflow).
- [x] 4.2 Report als Artifact (`if: always()`).
- [x] 4.3 `--fail` Gate (Exit 1 nur bei strukturellen Fehlern).

## 5. Doku

- [x] 5.1 `CHANGELOG.md`: Eintrag.
- [x] 5.2 `README.md`: Update-Pipeline um `catalog_lint.py` ergänzen.
- [x] 5.3 `.gitignore`: `catalog-lint-report.json`.

## 6. Qualitätssicherung

- [x] 6.1 `openspec validate catalog-quality-gate` grün.
- [x] 6.2 Workflow manuell auslösen und grün verifizieren.
