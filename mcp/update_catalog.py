#!/usr/bin/env python3
"""Förder-Radar – Update-Pipeline für Katalog.

Automatisches Abziehen von offiziellen Quellen (RSS/API) + manuelle Updates.
Laufbar per Cron oder manuell.

Beispiel:
    python mcp/update_catalog.py --fetch dfg,erc,bmbf --out mcp/catalog.json
    python mcp/update_catalog.py --check-expired  # tote Fristen melden
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
log = logging.getLogger(__name__)

CATALOG = Path(__file__).with_name("catalog.json")

# ------------------------------------------------------------------ Quellen-Definitionen
SOURCES = {
    "erc": {
        "name": "ERC",
        "url": "https://erc.europa.eu/funding",
        "type": "manual",  # Kein RSS/API verfügbar, manuell pflegen
        "hinweis": "ERC-Fristen per Portal-Check aktualisieren (StG, AdG, SyG)",
    },
    "dfg": {
        "name": "DFG",
        "url": "https://www.dfg.de/foerderung/foerdermoeglichkeiten/",
        "type": "manual",
        "hinweis": "DFG-Stichtage (1.2./1.10.) strukturell bekannt, manuell prüfen",
    },
    "bmbf": {
        "name": "BMBF",
        "url": "https://www.bmbf.de/bmbf/de/forschung/foerderung/bekanntmachungen",
        "type": "manual",
        "hinweis": "BMBF-Bekanntmachungen per Portal-Check aktualisieren",
    },
    "eu": {
        "name": "EU Horizon",
        "url": "https://ec.europa.eu/info/funding-tenders",
        "type": "manual",
        "hinweis": "EU Horizon Calls per Portal-Check aktualisieren",
    },
    "cost": {
        "name": "COST",
        "url": "https://www.cost.eu/funding/",
        "type": "manual",
        "hinweis": "COST Actions per Portal-Check aktualisieren",
    },
}

# ------------------------------------------------------------------ Hilfsfunktionen
def load_catalog(path: Path = CATALOG) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def save_catalog(doc: dict, path: Path = CATALOG) -> None:
    doc["stand"] = date.today().isoformat()
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=2)
    log.info(f"Katalog gespeichert: {path} ({len(doc.get('programme', []))} Programme)")


def validate_programme(p: dict) -> list[str]:
    """Prüfe Programm auf Pflichtfelder und Format."""
    errors: list[str] = []
    required = ["id", "name", "kategorie", "themen", "karriere", "rolle", "quelle", "standDatum"]
    for k in required:
        if k not in p:
            errors.append(f"Fehlt: {k}")
    if "frist" in p and p["frist"]:
        try:
            datetime.strptime(p["frist"], "%Y-%m-%d")
        except ValueError:
            errors.append(f"Ungültiges frist-Format: {p['frist']}")
    if p.get("status") not in ("verifiziert", "laufend", "zu-pruefen"):
        errors.append(f"Ungültiger status: {p.get('status')}")
    return errors


def check_expired(programme: list[dict], today: date | None = None) -> list[dict]:
    """Melde abgelaufene Fristen (nicht Rolling)."""
    today = today or date.today()
    expired = []
    for p in programme:
        if p.get("rolling"):
            continue
        if not p.get("frist"):
            continue
        try:
            frist = datetime.strptime(p["frist"], "%Y-%m-%d").date()
            if frist < today:
                expired.append({
                    "id": p["id"],
                    "name": p["name"],
                    "frist": p["frist"],
                    "tage_abgelaufen": (today - frist).days,
                })
        except ValueError:
            pass
    return expired


def update_stand_datum(programme: list[dict]) -> list[dict]:
    """Setze standDatum auf heute für alle Programme."""
    today = date.today().isoformat()
    for p in programme:
        p["standDatum"] = today
    return programme


# ------------------------------------------------------------------ Update-Operationen
def fetch_manual(source: str) -> list[dict] | None:
    """Manuelle Quellen-Prüfung (Platzhalter für Portal-Check)."""
    if source not in SOURCES:
        log.warning(f"Unbekannte Quelle: {source}")
        return None
    src = SOURCES[source]
    log.info(f"Manuelle Prüfung: {src['name']} ({src['url']})")
    log.info(f"  Hinweis: {src['hinweis']}")
    return None  # Keine automatischen Updates für manuelle Quellen


def merge_programmes(new: list[dict], existing: list[dict]) -> tuple[list[dict], int, int]:
    """Upsert: neue Programme hinzufügen/aktualisieren."""
    ids = {p["id"] for p in existing}
    added, updated = 0, 0
    for p in new:
        if p["id"] in ids:
            # Update: alte Daten behalten, neue überschreiben
            for i, old in enumerate(existing):
                if old["id"] == p["id"]:
                    existing[i] = p
            updated += 1
            log.info(f"Update: {p['id']}")
        else:
            existing.append(p)
            added += 1
            log.info(f"Neu: {p['id']}")
    return existing, added, updated


# ------------------------------------------------------------------ CLI
def main() -> None:
    ap = argparse.ArgumentParser(description="Förder-Radar Katalog-Update")
    ap.add_argument("--fetch", nargs="+", help="Quellen abziehen (erc, dfg, bmbf, eu, cost)")
    ap.add_argument("--out", type=Path, default=CATALOG, help="Zieldatei")
    ap.add_argument("--check-expired", action="store_true", help="Tote Fristen melden")
    ap.add_argument("--update-stand", action="store_true", help="standDatum auf heute setzen")
    ap.add_argument("--validate", action="store_true", help="Validierung durchführen")
    args = ap.parse_args()

    doc = load_catalog(args.out)
    programme = doc.get("programme", [])
    today = date.today()

    # Check expired
    if args.check_expired:
        expired = check_expired(programme, today)
        if expired:
            log.warning(f"Abgelaufene Fristen ({len(expired)}):")
            for e in expired:
                log.warning(f"  {e['id']}: {e['name']} ({e['frist']}, {e['tage_abgelaufen']} Tage alt)")
        else:
            log.info("Keine abgelaufenen Fristen.")

    # Update standDatum
    if args.update_stand:
        programme = update_stand_datum(programme)
        log.info(f"standDatum auf {today.isoformat()} gesetzt")

    # Fetch from sources
    if args.fetch:
        all_new: list[dict] = []
        for src in args.fetch:
            new = fetch_manual(src)
            if new:
                all_new.extend(new)
        if all_new:
            programme, added, updated = merge_programmes(all_new, programme)
            log.info(f"Merge: {added} neu, {updated} aktualisiert")
        else:
            log.info("Keine automatischen Updates verfügbar (manuelle Quellen)")

    # Validate
    if args.validate:
        errors = []
        for p in programme:
            errs = validate_programme(p)
            if errs:
                errors.extend([f"{p['id']}: {e}" for e in errs])
        if errors:
            log.error(f"Validierungsfehler ({len(errors)}):")
            for e in errors[:10]:
                log.error(f"  {e}")
            if len(errors) > 10:
                log.error(f"  ... und {len(errors) - 10} weitere")
            sys.exit(1)
        else:
            log.info("Validierung OK")

    # Save
    doc["programme"] = programme
    save_catalog(doc, args.out)


if __name__ == "__main__":
    main()
