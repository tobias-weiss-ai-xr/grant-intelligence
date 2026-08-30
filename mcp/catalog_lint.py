#!/usr/bin/env python3
"""Förder-Radar – Katalog-Qualitätsgate (Lint).

Prüft den Katalog auf Datenintegritäts-Regeln (Nebenläufer zur Link-Prüfung
durch verify_sources.py: dort werden Quell-URLs geprüft, hier die Datenqualität).

Regeln:
  FAIL (Exit 1 mit --fail):
    id-fehlt            – id fehlt/leer
    name-fehlt          – name fehlt/leer
    kategorie-ungueltig – kategorie nicht im Kategorie-Enum
    status-ungueltig    – status nicht im Status-Enum
    frist-ungueltig     – frist ist kein ISO-Datum
    hinweis-fehlt       – hinweis fehlt/leer (Projektregel: immer angeben)
    budget-null-statt-0 – budget ist 0 statt null (Projektregel)
    rolling-mit-frist   – rolling=True UND frist gesetzt (Widerspruch)
    quelle-fehlt        – quelle fehlt/leer
    duplicate-ids       – id kommt mehrfach vor

  WARN:
    frist-abgelaufen    – frist liegt in der Vergangenheit
    stand-datum-alt     – standDatum älter als 60 Tage (status==verifiziert)

Unix-Philosophie: eine Sache (Katalog prüfen), textbasiert, nur Stdlib +
grant_types/match. Läuft lokal und in CI (catalog-lint.yml).

Beispiel:
    python mcp/catalog_lint.py                       # prüfen, Exit 0
    python mcp/catalog_lint.py --fail                # Exit 1 bei FAIL-Findings
    python mcp/catalog_lint.py --report catalog-lint-report.json
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from grant_types import Kategorie, Status, parse_frist
from match import load_catalog_doc as _load_catalog_doc

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
log = logging.getLogger(__name__)

CATALOG = Path(__file__).with_name("catalog.json")
STALE_STAND_DAYS = 60


@dataclass
class Finding:
    """Ein Lint-Befund.

    Attributes:
        pid: Programm-id (oder None für katalogweite Befunde).
        rule: Regelname (z. B. "hinweis-fehlt").
        severity: "fail" oder "warn".
        message: Menschenlesbare Beschreibung.
    """

    pid: str | None
    rule: str
    severity: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.pid, "rule": self.rule, "severity": self.severity, "message": self.message}


def _add(findings: list[Finding], finding: Finding) -> None:
    findings.append(finding)


def lint_catalog(
    programme: list[dict[str, Any]],
    today: date | None = None,
) -> list[Finding]:
    """Prüfe den Katalog auf Datenintegritäts-Regeln.

    Args:
        programme: Liste der Programm-Dicts.
        today: Referenzdatum (Standard: heute) für Frist-/Stand-Prüfungen.

    Returns:
        Liste von Finding-Objekten (leer wenn sauber).
    """
    today = today or date.today()
    findings: list[Finding] = []

    # Katalogweite Regel: doppelte ids
    seen: dict[str, int] = {}
    for p in programme:
        pid = p.get("id")
        if isinstance(pid, str) and pid:
            seen[pid] = seen.get(pid, 0) + 1
    for pid, count in seen.items():
        if count > 1:
            _add(findings, Finding(pid, "duplicate-ids", "fail", f"id '{pid}' kommt {count}x vor"))

    for p in programme:
        raw_id = p.get("id")
        pid = raw_id or "?"
        name = p.get("name")

        if not raw_id:
            _add(findings, Finding(None, "id-fehlt", "fail", "Programm ohne id"))
        if not name:
            _add(findings, Finding(pid, "name-fehlt", "fail", "name fehlt/leer"))

        if not Kategorie.is_valid(p.get("kategorie")):
            _add(findings, Finding(pid, "kategorie-ungueltig", "fail",
                                   f"unbekannte kategorie: {p.get('kategorie')!r}"))
        if not Status.is_valid(p.get("status")):
            _add(findings, Finding(pid, "status-ungueltig", "fail",
                                   f"unbekannter status: {p.get('status')!r}"))

        frist = p.get("frist")
        if frist:
            if parse_frist(frist) is None:
                _add(findings, Finding(pid, "frist-ungueltig", "fail",
                                       f"frist ist kein ISO-Datum: {frist!r}"))
            elif not p.get("rolling"):
                d = parse_frist(frist)
                if d is not None and d < today:
                    _add(findings, Finding(pid, "frist-abgelaufen", "warn",
                                           f"Frist {frist} liegt in der Vergangenheit ({days_ago(d, today)} Tage)"))

        if p.get("rolling") and frist:
            _add(findings, Finding(pid, "rolling-mit-frist", "fail",
                                   f"rolling=True aber frist gesetzt: {frist}"))

        if not p.get("hinweis"):
            _add(findings, Finding(pid, "hinweis-fehlt", "fail", "hinweis fehlt/leer"))

        for key in ("budget_min", "budget_max"):
            if p.get(key) == 0:
                _add(findings, Finding(pid, "budget-null-statt-0", "fail",
                                       f"{key} ist 0 – bitte null verwenden"))

        if not p.get("quelle"):
            _add(findings, Finding(pid, "quelle-fehlt", "fail", "quelle fehlt/leer"))

        # WARN: standDatum alt für verifizierte Programme
        if p.get("status") == "verifiziert":
            stand = p.get("standDatum")
            d = parse_frist(stand) if stand else None
            if d is not None and (today - d).days > STALE_STAND_DAYS:
                _add(findings, Finding(pid, "stand-datum-alt", "warn",
                                       f"standDatum {stand} ist {(today - d).days} Tage alt "
                                       f"(> {STALE_STAND_DAYS})"))

    return findings


def days_ago(d: date, today: date) -> int:
    """Tage seit d (nur fürs Message-Format)."""
    return (today - d).days


def build_report(
    findings: list[Finding],
    geprueft: int,
    today: date | None = None,
) -> dict[str, Any]:
    """Baue den strukturierten Report aus den Findings.

    Args:
        findings: Liste der Findings.
        geprueft: Anzahl geprüfter Programme.
        today: Referenzdatum.

    Returns:
        Report-Dict mit stand, geprueft, ergebnis, counts, findings.
    """
    today = today or date.today()
    fail = [f for f in findings if f.severity == "fail"]
    warn = [f for f in findings if f.severity == "warn"]
    if fail:
        ergebnis = "problems"
    elif warn:
        ergebnis = "warn"
    else:
        ergebnis = "clean"
    return {
        "stand": today.isoformat(),
        "geprueft": geprueft,
        "ergebnis": ergebnis,
        "counts": {"fail": len(fail), "warn": len(warn)},
        "findings": [f.to_dict() for f in findings],
    }


def main() -> None:
    """CLI: Katalog prüfen, Report ausgeben und (optional) als JSON speichern."""
    ap = argparse.ArgumentParser(description="Förder-Radar Katalog-Lint")
    ap.add_argument("--catalog", type=Path, default=CATALOG, help="Katalog-Datei")
    ap.add_argument("--report", type=Path, default=None,
                    help="Report-Datei (JSON) schreiben")
    ap.add_argument("--fail", action="store_true",
                    help="Exit 1 bei FAIL-Findings (für CI)")
    args = ap.parse_args()

    doc = _load_catalog_doc(args.catalog)
    programme = doc.get("programme", [])
    findings = lint_catalog(programme)
    fail = [f for f in findings if f.severity == "fail"]
    warn = [f for f in findings if f.severity == "warn"]
    report = build_report(findings, len(programme))

    # Ausgabe
    print(f"Katalog: {args.catalog} ({len(programme)} Programme)")
    print(f"Ergebnis: {report['ergebnis']} (fail={len(fail)}, warn={len(warn)})")
    for f in findings:
        sev = "F" if f.severity == "fail" else "W"
        pid = f.pid or "(katalog)"
        print(f"  [{sev}] {pid}: {f.rule} – {f.message}")
    if not findings:
        print("  Keine Befunde – Katalog sauber.")

    if args.report:
        _write_report(report, args.report)

    if args.fail and fail:
        sys.exit(1)


def _write_report(report: dict[str, Any], path: Path) -> None:
    """Report als JSON schreiben (UTF-8, indent 2, Trailing-Newline)."""
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    log.info(f"Report geschrieben: {path}")


if __name__ == "__main__":
    main()
