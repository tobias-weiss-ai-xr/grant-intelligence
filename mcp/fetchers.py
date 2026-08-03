#!/usr/bin/env python3
"""Förder-Radar – Automatisches Fetching von Quellen.

Implementiert HTTP-Clients für Quellen mit RSS/API-Unterstützung.
Prüft aktuelle Fristen gegen sources.yaml und generiert Update-Vorschläge.

Beispiel:
    python mcp/fetchers.py --source all --check-deadlines
    python mcp/fetchers.py --source bmbf --rss
"""
from __future__ import annotations

import argparse
import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
import yaml

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
log = logging.getLogger(__name__)

SOURCES_YAML = Path(__file__).parent / "sources.yaml"
CATALOG_JSON = Path(__file__).parent / "catalog.json"


@dataclass
class ProgrammeUpdate:
    """Update-Ergebnis aus einer Quelle."""
    source: str
    programmes: list[dict[str, Any]]
    errors: list[str]
    fetched_at: str
    suggestions: list[str]  # Manuelle Update-Vorschläge


def load_sources() -> dict:
    """Lade Quellen-Definitionen aus sources.yaml."""
    with open(SOURCES_YAML, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_catalog() -> list[dict]:
    """Lade aktuellen Katalog."""
    import json
    with open(CATALOG_JSON, encoding="utf-8") as fh:
        return json.load(fh).get("programme", [])


def check_deadline(programme: dict, today: date) -> str | None:
    """Prüfe Frist und gib Warnung zurück wenn bald oder abgelaufen."""
    if programme.get("rolling"):
        return None
    frist_str = programme.get("frist")
    if not frist_str:
        return None
    try:
        frist = datetime.strptime(frist_str, "%Y-%m-%d").date()
        days_left = (frist - today).days
        if days_left < 0:
            return f"ABGELAUFEN: {days_left} Tage alt"
        elif days_left <= 14:
            return f"BALD: {days_left} Tage bis Frist"
        elif days_left <= 30:
            return f"ACHTUNG: {days_left} Tage bis Frist"
        return None
    except ValueError:
        return f"UNGÜLTIGES DATUM: {frist_str}"


def fetch_cost() -> ProgrammeUpdate:
    """COST Actions: Prüfe Portal und generiere Update-Vorschläge."""
    source = "cost"
    programmes: list[dict[str, Any]] = []
    errors: list[str] = []
    suggestions: list[str] = []

    try:
        # COST Portal check (302 redirect, kein API)
        resp = httpx.get("https://www.cost.eu/funding/", timeout=10, follow_redirects=False)
        log.info(f"{source}: Portal erreichbar (Status {resp.status_code})")

        # Update-Vorschlag: Manuelle Prüfung der COST Actions
        suggestions.append(
            f"{source}: COST Actions per Portal prüfen (cost.eu/funding/) - "
            f"aktuelle Calls: COST CA (Actions), COST Open Calls"
        )

    except Exception as e:
        errors.append(str(e))

    return ProgrammeUpdate(source, programmes, errors, datetime.now().isoformat(), suggestions)


def fetch_eu_horizon() -> ProgrammeUpdate:
    """EU Horizon: Prüfe Portal und generiere Update-Vorschläge."""
    source = "eu_horizon"
    programmes: list[dict[str, Any]] = []
    errors: list[str] = []
    suggestions: list[str] = []

    try:
        # EU Horizon Portal (301 redirect, kein API)
        resp = httpx.get("https://ec.europa.eu/info/funding-tenders", timeout=10, follow_redirects=False)
        log.info(f"{source}: Portal erreichbar (Status {resp.status_code})")

        # Update-Vorschlag: Horizon Europe Calls
        suggestions.append(
            f"{source}: Horizon Europe Calls per Portal prüfen (ec.europa.eu/funding) - "
            f"Cluster 4 (Digital), Cluster 5 (Klima/Energie), Cluster 6 (Biodiversität)"
        )

    except Exception as e:
        errors.append(str(e))

    return ProgrammeUpdate(source, programmes, errors, datetime.now().isoformat(), suggestions)


def fetch_bmbf_rss() -> ProgrammeUpdate:
    """BMBF: Versuche RSS-Feed, falls verfügbar."""
    source = "bmbf"
    programmes: list[dict[str, Any]] = []
    errors: list[str] = []
    suggestions: list[str] = []

    # BMBF RSS URL (falls verfügbar)
    rss_url = "https://www.bmbf.de/bmbf/de/forschung/foerderung/bekanntmachungen/rss.xml"

    try:
        log.info(f"{source}: Versuche RSS from {rss_url}")
        resp = httpx.get(rss_url, timeout=10)
        if resp.status_code == 200:
            root = ET.fromstring(resp.content)
            for item in root.findall(".//item"):
                title = item.find("title")
                link = item.find("link")
                if title is not None:
                    programmes.append({
                        "id": f"{source}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                        "name": title.text or "",
                        "quelle": link.text if link is not None else rss_url,
                        "standDatum": datetime.now().isoformat()[:10],
                        "hinweis": "Automatisch aus RSS importiert - manuell prüfen",
                    })
            log.info(f"{source}: {len(programmes)} Items im RSS-Feed")
        else:
            log.info(f"{source}: RSS nicht verfügbar (Status {resp.status_code})")
            suggestions.append(
                f"{source}: Kein RSS-Feed verfügbar. Manuelles Portal-Check: "
                f"bmbf.de/forschung/foerderung/bekanntmachungen"
            )
    except Exception as e:
        errors.append(str(e))
        suggestions.append(f"{source}: RSS-Fehler - manuell prüfen")

    return ProgrammeUpdate(source, programmes, errors, datetime.now().isoformat(), suggestions)


def check_catalog_deadlines(catalog: list[dict]) -> list[str]:
    """Prüfe alle Programme im Katalog auf baldige/abgelaufene Fristen."""
    today = date.today()
    warnings: list[str] = []

    for p in catalog:
        warning = check_deadline(p, today)
        if warning:
            warnings.append(f"{p['id']}: {p['name']} - {warning}")

    return warnings


def generate_update_suggestions(catalog: list[dict], sources: dict) -> list[str]:
    """Generiere Update-Vorschläge basierend auf Quellen-Status."""
    suggestions: list[str] = []
    today = date.today()

    # Prüfe ältere standDatum
    for p in catalog:
        stand = p.get("standDatum", "")
        if stand:
            try:
                stand_date = datetime.strptime(stand, "%Y-%m-%d").date()
                days_old = (today - stand_date).days
                if days_old > 60 and p.get("status") == "verifiziert":
                    suggestions.append(
                        f"{p['id']}: standDatum älter als 60 Tage ({days_old} Tage) - "
                        f"Portal-Check empfohlen"
                    )
            except ValueError:
                pass

    # Quellen-spezifische Hinweise
    for source_key, source_data in sources.items():
        if isinstance(source_data, dict) and source_data.get("type") == "manual":
            last_check = source_data.get("last_check", "")
            if last_check:
                try:
                    check_date = datetime.strptime(last_check, "%Y-%m-%d").date()
                    days_old = (today - check_date).days
                    freq = source_data.get("update_frequency", "monthly")
                    if freq == "weekly" and days_old > 7:
                        suggestions.append(
                            f"{source_key}: Letzte Prüfung vor {days_old} Tagen "
                            f"({freq} empfohlen) - Portal-Check"
                        )
                    elif freq == "monthly" and days_old > 30:
                        suggestions.append(
                            f"{source_key}: Letzte Prüfung vor {days_old} Tagen "
                            f"({freq} empfohlen) - Portal-Check"
                        )
                except (ValueError, TypeError):
                    pass

    return suggestions


def fetch_all(check_deadlines: bool = False) -> list[ProgrammeUpdate]:
    """Alle Quellen abfragen."""
    results = []
    catalog = load_catalog() if check_deadlines else []
    sources = load_sources()

    log.info("=== Manuelle Quellen (kein automatisches Fetching) ===")
    for source in ["erc", "dfg", "bmbf", "loewe", "stiftungen", "industrie"]:
        log.info(f"  {source}: Manuell pflegen")

    log.info("\n=== Quellen mit potentiellem automatischem Fetching ===")
    results.append(fetch_cost())
    results.append(fetch_eu_horizon())

    # Deadline-Check
    if check_deadlines:
        log.info("\n=== Fristen-Prüfung ===")
        warnings = check_catalog_deadlines(catalog)
        if warnings:
            for w in warnings:
                log.warning(f"  {w}")
        else:
            log.info("  Keine abgelaufenen oder baldigen Fristen")

        # Update-Suggestions
        log.info("\n=== Update-Vorschläge ===")
        suggestions = generate_update_suggestions(catalog, sources)
        for s in suggestions[:10]:
            log.info(f"  {s}")
        if len(suggestions) > 10:
            log.info(f"  ... und {len(suggestions) - 10} weitere")

    return results


def main() -> None:
    ap = argparse.ArgumentParser(description="Förder-Radar – Automatisches Fetching")
    ap.add_argument("--source", choices=["cost", "eu", "bmbf", "all"], default="all",
                    help="Quelle abfragen")
    ap.add_argument("--check-deadlines", action="store_true",
                    help="Fristen im Katalog prüfen")
    args = ap.parse_args()

    if args.source == "all":
        results = fetch_all(check_deadlines=args.check_deadlines)
    elif args.source == "cost":
        results = [fetch_cost()]
    elif args.source == "eu":
        results = [fetch_eu_horizon()]
    elif args.source == "bmbf":
        results = [fetch_bmbf_rss()]

    log.info("\n=== Fetch-Ergebnisse ===")
    for r in results:
        log.info(f"{r.source}: {len(r.programmes)} Programme, {len(r.errors)} Fehler, {len(r.suggestions)} Vorschläge")
        for e in r.errors:
            log.warning(f"  Error: {e}")
        for s in r.suggestions:
            log.info(f"  Suggestion: {s}")


if __name__ == "__main__":
    main()
