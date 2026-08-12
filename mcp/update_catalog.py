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
from datetime import date
from pathlib import Path

import yaml

from grant_types import Programm, parse_frist

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
log = logging.getLogger(__name__)

CATALOG = Path(__file__).with_name("catalog.json")
SOURCES_YAML = Path(__file__).with_name("sources.yaml")


# ------------------------------------------------------------------ Hilfsfunktionen
def load_sources() -> dict:
    """Lade Quellen-Registrierung aus sources.yaml (Single Source of Truth).

    Returns:
        Quellen-Dictionary aus sources.yaml.
    """
    with open(SOURCES_YAML, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_catalog(path: Path = CATALOG) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def save_catalog(doc: dict, path: Path = CATALOG) -> None:
    doc["stand"] = date.today().isoformat()
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=2)
    log.info(f"Katalog gespeichert: {path} ({len(doc.get('programme', []))} Programme)")


def validate_programme(p: dict) -> list[str]:
    """Prüfe Programm auf Pflichtfelder und Format.

    Nutzt die type-safe Programm-Dataclass inkl. Status-Enum und
    Frist-Format-Validierung.

    Args:
        p: Programm-Dictionary im Katalogformat (camelCase).

    Returns:
        Liste von Fehlermeldungen (leer wenn gültig).
    """
    errors: list[str] = []
    required = ["id", "name", "kategorie", "themen", "karriere", "rolle", "quelle", "standDatum"]
    for k in required:
        if k not in p:
            errors.append(f"Fehlt: {k}")
    try:
        Programm.from_dict(p)
    except (ValueError, TypeError) as e:
        errors.append(str(e))
    if "frist" in p and p["frist"] and parse_frist(p["frist"]) is None:
        errors.append(f"Ungültiges frist-Format: {p['frist']}")
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
        frist = parse_frist(p["frist"])
        if frist is None:
            continue
        if frist < today:
            expired.append(
                {
                    "id": p["id"],
                    "name": p["name"],
                    "frist": p["frist"],
                    "tage_abgelaufen": (today - frist).days,
                }
            )
    return expired


def update_stand_datum(programme: list[dict]) -> list[dict]:
    """Setze standDatum auf heute für alle Programme."""
    today = date.today().isoformat()
    for p in programme:
        p["standDatum"] = today
    return programme


# ------------------------------------------------------------------ Update-Operationen
def fetch_manual(source: str) -> list[dict] | None:
    """Quellen-Prüfung via Fetcher (falls vorhanden) oder manuell.

    Nutzt die Fetcher aus fetchers.py, falls eine Funktion fuer die Quelle
    existiert. Liefert validierte Programme zurueck, die in den Katalog
    gemergt werden koennen.

    Args:
        source: Quell-Bezeichner (erc, dfg, bmbf, eu, cost, …).

    Returns:
        Liste von Programm-Dicts oder None (fuer rein manuelle Quellen).
    """
    _FETCHER_MAP = {
        "cost": lambda: __import__("fetchers", fromlist=["fetch_cost"]).fetch_cost(),
        "eu": lambda: __import__("fetchers", fromlist=["fetch_eu_horizon"]).fetch_eu_horizon(),
        "bmbf": lambda: __import__("fetchers", fromlist=["fetch_bmbf_rss"]).fetch_bmbf_rss(),
    }

    sources = load_sources()
    src = sources.get(source)
    if not isinstance(src, dict):
        log.warning(f"Unbekannte Quelle: {source}")
        return None

    # Try fetcher if available
    fetcher_fn = _FETCHER_MAP.get(source)
    if fetcher_fn:
        log.info(f"Fetch via Fetcher: {src.get('name', source)}")
        update = fetcher_fn()
        if update.programmes:
            log.info(f"  {len(update.programmes)} Programme von {source}")
            for e in update.errors:
                log.warning(f"  Fehler: {e}")
            return update.programmes
        if update.suggestions:
            for s in update.suggestions:
                log.info(f"  {s}")
        return None

    # Manual source: log hint
    log.info(f"Manuelle Prüfung: {src.get('name', source)} ({src.get('url', '?')})")
    hinweis = src.get("hinweis")
    if hinweis:
        log.info(f"  Hinweis: {hinweis}")
    return None


def merge_programmes(new: list[dict], existing: list[dict]) -> tuple[list[dict], int, int]:
    """Upsert: neue Programme hinzufügen/aktualisieren.

    Args:
        new: Neue Programme (ohne id werden übersprungen).
        existing: Bestehender Katalog (in-place erweitert).

    Returns:
        (Katalog, Anzahl neu, Anzahl aktualisiert).
    """
    ids = {p["id"] for p in existing if p.get("id")}
    added, updated = 0, 0
    for p in new:
        pid = p.get("id")
        if not pid:
            log.warning("Überspringe Programm ohne id")
            continue
        if pid in ids:
            # Update: alte Daten behalten, neue überschreiben
            for i, old in enumerate(existing):
                if old.get("id") == pid:
                    existing[i] = p
                    break
            updated += 1
            log.info(f"Update: {pid}")
        else:
            existing.append(p)
            ids.add(pid)
            added += 1
            log.info(f"Neu: {pid}")
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
            for ex in expired:
                log.warning(
                    f"  {ex['id']}: {ex['name']} ({ex['frist']}, {ex['tage_abgelaufen']} Tage alt)"
                )
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
            for err in errors[:10]:
                log.error(f"  {err}")
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
