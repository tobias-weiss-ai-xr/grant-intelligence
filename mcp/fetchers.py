#!/usr/bin/env python3
"""Förder-Radar – Automatisches Fetching von Quellen.

Implementiert HTTP-Clients für Quellen mit RSS/API-Unterstützung.
Aktuell: COST, EU Horizon (manuell >80%, automatisierte Teile hier).

Beispiel:
    python mcp/fetchers.py --source cost
    python mcp/fetchers.py --source all
"""
from __future__ import annotations

import argparse
import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
log = logging.getLogger(__name__)


@dataclass
class ProgrammeUpdate:
    """Update-Ergebnis aus einer Quelle."""
    source: str
    programmes: list[dict[str, Any]]
    errors: list[str]
    fetched_at: str


def fetch_cost() -> ProgrammeUpdate:
    """COST Actions per RSS/API abrufen."""
    source = "cost"
    programmes: list[dict[str, Any]] = []
    errors: list[str] = []

    try:
        log.info(f"{source}: Kein automatischer Feed verfügbar (manuell pflegen)")
        return ProgrammeUpdate(source, programmes, errors, datetime.now().isoformat())

    except Exception as e:
        errors.append(str(e))
        return ProgrammeUpdate(source, programmes, errors, datetime.now().isoformat())


def fetch_eu_horizon() -> ProgrammeUpdate:
    """EU Horizon Calls per HTTP abrufen."""
    source = "eu_horizon"
    programmes: list[dict[str, Any]] = []
    errors: list[str] = []

    log.info(f"{source}: Kein automatischer Feed verfügbar (manuell pflegen)")
    return ProgrammeUpdate(source, programmes, errors, datetime.now().isoformat())


def fetch_rss(url: str, source: str) -> ProgrammeUpdate:
    """Generic RSS-Feed Parser für Quellen mit RSS-Unterstützung."""
    programmes: list[dict[str, Any]] = []
    errors: list[str] = []

    try:
        log.info(f"{source}: Fetching RSS from {url}")
        resp = httpx.get(url, timeout=10)
        resp.raise_for_status()

        root = ET.fromstring(resp.content)
        for item in root.findall(".//item"):
            title = item.find("title")
            link = item.find("link")
            pub_date = item.find("pubDate")

            if title is not None:
                programmes.append({
                    "id": f"{source}-{datetime.now().strftime('%Y%m%d')}",
                    "name": title.text or "",
                    "quelle": link.text if link is not None else url,
                    "standDatum": datetime.now().isoformat()[:10],
                    "hinweis": f"Automatisch aus RSS importiert",
                })

        log.info(f"{source}: Found {len(programmes)} items in RSS feed")

    except httpx.HTTPError as e:
        errors.append(f"HTTP error: {e}")
    except ET.ParseError as e:
        errors.append(f"XML parse error: {e}")
    except Exception as e:
        errors.append(f"Unexpected error: {e}")

    return ProgrammeUpdate(source, programmes, errors, datetime.now().isoformat())


def fetch_bmbf_rss() -> ProgrammeUpdate:
    """BMBF bekanntmachungen RSS (falls verfügbar)."""
    url = "https://www.bmbf.de/bmbf/de/forschung/foerderung/bekanntmachungen/rss.xml"
    return fetch_rss(url, "bmbf")


def fetch_all() -> list[ProgrammeUpdate]:
    """Alle Quellen abfragen."""
    results = []

    log.info("=== Manuelle Quellen (kein automatisches Fetching) ===")
    for source in ["erc", "dfg", "bmbf", "loewe", "stiftungen", "industrie"]:
        log.info(f"  {source}: Manuell pflegen")

    log.info("\n=== Quellen mit potentiellem automatischem Fetching ===")
    results.append(fetch_cost())
    results.append(fetch_eu_horizon())

    return results


def main() -> None:
    ap = argparse.ArgumentParser(description="Förder-Radar – Automatisches Fetching")
    ap.add_argument("--source", choices=["cost", "eu", "bmbf", "all"], default="all",
                    help="Quelle abfragen")
    args = ap.parse_args()

    if args.source == "all":
        results = fetch_all()
    elif args.source == "cost":
        results = [fetch_cost()]
    elif args.source == "eu":
        results = [fetch_eu_horizon()]
    elif args.source == "bmbf":
        results = [fetch_bmbf_rss()]

    log.info("\n=== Fetch-Ergebnisse ===")
    for r in results:
        log.info(f"{r.source}: {len(r.programmes)} Programme, {len(r.errors)} Fehler")
        for e in r.errors:
            log.warning(f"  Error: {e}")


if __name__ == "__main__":
    main()
