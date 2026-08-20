"""Förder-Radar – Automatisches Fetching von Quellen.

Implements HTTP clients for sources with RSS/API support.
Checks current deadlines against sources.json and generates update suggestions.

Usage:
    python mcp/fetchers.py --source all --check-deadlines
    python mcp/fetchers.py --source bmbf --rss
"""

from __future__ import annotations

import argparse
import json
import logging
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

import httpx

from grant_types import parse_frist

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
log = logging.getLogger(__name__)

SOURCES_JSON = Path(__file__).parent / "sources.json"
CATALOG_JSON = Path(__file__).parent / "catalog.json"


@dataclass
class ProgrammeUpdate:
    """Update result from a source.

    Attributes:
        source: Source identifier.
        programmes: List of newly fetched programmes.
        errors: List of error messages.
        fetched_at: Timestamp of fetch.
        suggestions: Manual update suggestions.
    """

    source: str
    programmes: list[dict[str, Any]]
    errors: list[str]
    fetched_at: str
    suggestions: list[str]


def load_sources() -> dict[str, Any]:
    """Load source definitions from sources.json.

    Returns:
        Dictionary of source configurations.
    """
    with open(SOURCES_JSON, encoding="utf-8") as fh:
        return json.load(fh)


def load_catalog() -> list[dict[str, Any]]:
    """Load current catalog.

    Returns:
        List of programme dictionaries.
    """
    with open(CATALOG_JSON, encoding="utf-8") as fh:
        return json.load(fh).get("programme", [])


def check_deadline(programme: dict[str, Any], today: date) -> str | None:
    """Check deadline and return warning if urgent or expired.

    Args:
        programme: Programme dictionary.
        today: Reference date.

    Returns:
        Warning string or None.
    """
    if programme.get("rolling"):
        return None
    frist_str = programme.get("frist")
    if not frist_str:
        return None
    frist = parse_frist(frist_str)
    if frist is None:
        return f"UNGÜLTIGES DATUM: {frist_str}"
    days_left = (frist - today).days
    if days_left < 0:
        return f"ABGELAUFEN: {days_left} Tage alt"
    elif days_left <= 14:
        return f"BALD: {days_left} Tage bis Frist"
    elif days_left <= 30:
        return f"ACHTUNG: {days_left} Tage bis Frist"
    return None


def fetch_cost() -> ProgrammeUpdate:
    """Check COST portal and generate update suggestions.

    Returns:
        ProgrammeUpdate with suggestions for manual check.
    """
    source = "cost"
    programmes: list[dict[str, Any]] = []
    errors: list[str] = []
    suggestions: list[str] = []

    try:
        # COST portal check (302 redirect, no API)
        resp = httpx.get("https://www.cost.eu/funding/", timeout=10, follow_redirects=False)
        log.info(f"{source}: Portal reachable (Status {resp.status_code})")

        suggestions.append(
            f"{source}: Check COST Actions at portal (cost.eu/funding/) - "
            f"current calls: COST CA (Actions), COST Open Calls"
        )

    except Exception as e:
        errors.append(str(e))

    return ProgrammeUpdate(source, programmes, errors, datetime.now().isoformat(), suggestions)


def fetch_eu_horizon() -> ProgrammeUpdate:
    """Check EU Horizon portal and generate update suggestions.

    Returns:
        ProgrammeUpdate with suggestions for manual check.
    """
    source = "eu_horizon"
    programmes: list[dict[str, Any]] = []
    errors: list[str] = []
    suggestions: list[str] = []

    try:
        # EU Horizon portal (301 redirect, no API)
        resp = httpx.get(
            "https://ec.europa.eu/info/funding-tenders", timeout=10, follow_redirects=False
        )
        log.info(f"{source}: Portal reachable (Status {resp.status_code})")

        suggestions.append(
            f"{source}: Check Horizon Europe calls at portal (ec.europa.eu/funding) - "
            f"Cluster 4 (Digital), Cluster 5 (Climate/Energy), Cluster 6 (Biodiversity)"
        )

    except Exception as e:
        errors.append(str(e))

    return ProgrammeUpdate(source, programmes, errors, datetime.now().isoformat(), suggestions)


def _slug_id(source: str, title: str) -> str:
    """Deterministic programme id from source and title.

    Re-fetching the same RSS item produces the same id (upsert-safe),
    unlike timestamp-based ids which would duplicate entries.

    Args:
        source: Source identifier (e.g. "bmbf").
        title: Item title.

    Returns:
        Slugified id like "bmbf-<slug>".
    """
    slug = "".join(c if c.isalnum() else "-" for c in title.lower()).strip("-")
    slug = "-".join(part for part in slug.split("--") if part)[:60].rstrip("-")
    return f"{source}-{slug}"


def fetch_bmbf_rss() -> ProgrammeUpdate:
    """Attempt to fetch BMBF RSS feed if available.

    Returns:
        ProgrammeUpdate with programmes or suggestions.
    """
    source = "bmbf"
    programmes: list[dict[str, Any]] = []
    errors: list[str] = []
    suggestions: list[str] = []

    rss_url = "https://www.bmbf.de/bmbf/de/forschung/foerderung/bekanntmachungen/rss.xml"

    try:
        log.info(f"{source}: Attempting RSS from {rss_url}")
        resp = httpx.get(rss_url, timeout=10)
        if resp.status_code == 200:
            root = ET.fromstring(resp.content)
            for item in root.findall(".//item"):
                title = item.find("title")
                link = item.find("link")
                if title is not None and title.text:
                    programmes.append(
                        {
                            "id": _slug_id(source, title.text),
                            "name": title.text,
                            "quelle": link.text if link is not None else rss_url,
                            "standDatum": datetime.now().isoformat()[:10],
                            "hinweis": "Automatically imported from RSS - manual verification required",
                        }
                    )
            log.info(f"{source}: {len(programmes)} items in RSS feed")
        else:
            log.info(f"{source}: RSS not available (Status {resp.status_code})")
            suggestions.append(
                f"{source}: No RSS feed available. Manual portal check: "
                f"bmbf.de/forschung/foerderung/bekanntmachungen"
            )
    except Exception as e:
        errors.append(str(e))
        suggestions.append(f"{source}: RSS error - manual check required")

    return ProgrammeUpdate(source, programmes, errors, datetime.now().isoformat(), suggestions)


def check_catalog_deadlines(catalog: list[dict[str, Any]]) -> list[str]:
    """Check all programmes in catalog for expired/urgent deadlines.

    Args:
        catalog: List of programme dictionaries.

    Returns:
        List of warning strings.
    """
    today = date.today()
    warnings: list[str] = []

    for p in catalog:
        warning = check_deadline(p, today)
        if warning:
            warnings.append(f"{p.get('id', 'unknown')}: {p.get('name', '')} - {warning}")

    return warnings


def generate_update_suggestions(
    catalog: list[dict[str, Any]], sources: dict[str, Any]
) -> list[str]:
    """Generate update suggestions based on source status.

    Args:
        catalog: List of programme dictionaries.
        sources: Source configurations from sources.json.

    Returns:
        List of suggestion strings.
    """
    suggestions: list[str] = []
    today = date.today()

    # Check for old standDatum
    for p in catalog:
        stand = p.get("standDatum", "")
        if not stand:
            continue
        stand_date = parse_frist(stand)
        if stand_date is None:
            continue
        days_old = (today - stand_date).days
        if days_old > 60 and p.get("status") == "verifiziert":
            suggestions.append(
                f"{p.get('id', 'unknown')}: standDatum older than 60 days ({days_old} days) - "
                f"portal check recommended"
            )

    # Source-specific hints
    for source_key, source_data in sources.items():
        if not isinstance(source_data, dict) or source_data.get("type") != "manual":
            continue
        last_check = source_data.get("last_check", "")
        if not last_check:
            continue
        check_date = parse_frist(last_check)
        if check_date is None:
            continue
        days_old = (today - check_date).days
        freq = source_data.get("update_frequency", "monthly")
        if (freq == "weekly" and days_old > 7) or (freq == "monthly" and days_old > 30):
            suggestions.append(
                f"{source_key}: Last check {days_old} days ago ({freq} recommended) - portal check"
            )

    return suggestions


def _enrich_programme(partial: dict[str, Any], source: str) -> dict[str, Any] | None:
    """Fill missing required fields for a fetched programme.

    Fetched data is often incomplete (only id, name, quelle). This adds
    sensible defaults so the programme passes Programm.from_dict() validation.
    Returns None if essential fields are missing.

    Args:
        partial: Partial programme dict from a fetcher.
        source: Source identifier (e.g. "bmbf", "cost").

    Returns:
        Complete programme dict, or None if unenrichable.
    """
    if not partial.get("id") or not partial.get("name"):
        return None

    _CATEGORY_MAP = {
        "bmbf": "BMBF",
        "cost": "EU",
        "eu": "EU",
        "erc": "ERC",
        "dfg": "DFG",
    }

    return {
        "id": partial["id"],
        "name": partial["name"],
        "kategorie": _CATEGORY_MAP.get(source, source),
        "themen": partial.get("themen", ["thematisch-offen"]),
        "karriere": partial.get("karriere", []),
        "rolle": partial.get("rolle", ["lead"]),
        "budget_min": partial.get("budget_min"),
        "budget_max": partial.get("budget_max"),
        "dauerJahre": partial.get("dauerJahre"),
        "frist": partial.get("frist"),
        "rolling": partial.get("rolling", False),
        "status": "zu-pruefen",
        "quelle": partial.get("quelle", ""),
        "standDatum": partial.get("standDatum", date.today().isoformat()),
        "hinweis": partial.get("hinweis", "Auto-importiert, manuelle Verifikation erforderlich"),
    }


def apply_fetch_updates(
    updates: list[ProgrammeUpdate],
    catalog_path: Path = CATALOG_JSON,
    audit_path: Path | None = None,
) -> dict[str, Any]:
    """Validate fetched programmes, merge into catalog, write audit log.

    Each programme in each update is validated via Programm.from_dict().
    Invalid programmes are rejected and logged but do not block others.

    Args:
        updates: List of ProgrammeUpdate results from fetchers.
        catalog_path: Path to catalog.json.
        audit_path: Path to audit log. Defaults to docs/update_log.md.

    Returns:
        Summary dict with source, added, updated, rejected counts.
    """
    from grant_types import Programm

    if audit_path is None:
        audit_path = Path(__file__).parent.parent / "docs" / "update_log.md"

    # Load catalog
    try:
        with open(catalog_path, encoding="utf-8") as fh:
            doc = json.load(fh)
        catalogue = doc.get("programme", [])
    except (FileNotFoundError, json.JSONDecodeError) as e:
        log.error(f"Cannot load catalog {catalog_path}: {e}")
        return {"status": "error", "fehler": str(e)}

    total_added, total_updated, total_rejected = 0, 0, 0
    all_errors: list[str] = []
    source_reports: list[str] = []

    existing_ids = {p.get("id") for p in catalogue if p.get("id")}

    for update in updates:
        added, updated, rejected = 0, 0, 0
        source_errors: list[str] = []

        for partial in update.programmes:
            enriched = _enrich_programme(partial, update.source)
            if enriched is None:
                rejected += 1
                source_errors.append(f"Missing id/name: {partial.get('id', '?')}")
                continue

            # Validate
            try:
                Programm.from_dict(enriched)
            except (ValueError, TypeError) as e:
                rejected += 1
                source_errors.append(f"{enriched['id']}: {e}")
                log.warning(f"Rejected {enriched['id']}: {e}")
                continue

            # Upsert
            pid = enriched["id"]
            if pid in existing_ids:
                for i, old in enumerate(catalogue):
                    if old.get("id") == pid:
                        catalogue[i] = enriched
                        break
                updated += 1
                log.info(f"  Updated: {pid}")
            else:
                catalogue.append(enriched)
                existing_ids.add(pid)
                added += 1
                log.info(f"  Added: {pid}")

        total_added += added
        total_updated += updated
        total_rejected += rejected
        all_errors.extend(source_errors)

        if added or updated or rejected:
            source_reports.append(
                f"{update.source}: +{added} / ~{updated} / x{rejected}"
            )

    # Save catalog
    if total_added or total_updated:
        doc["stand"] = date.today().isoformat()
        doc["programme"] = catalogue
        with open(catalog_path, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        log.info(f"Catalog saved: {catalog_path} ({len(catalogue)} programmes)")

    # Audit log
    if source_reports:
        audit_entry = (
            f"## {datetime.now().isoformat()} – Fetch Pipeline\n\n"
            + "\n".join(f"- {r}" for r in source_reports)
            + (f"\n\nErrors:\n" + "\n".join(f"- {e}" for e in all_errors) if all_errors else "")
            + "\n"
        )
        try:
            with open(audit_path, "a", encoding="utf-8") as fh:
                fh.write(audit_entry)
        except OSError as e:
            log.warning(f"Cannot write audit log: {e}")

    return {
        "status": "ok",
        "gesamt_neu": total_added,
        "gesamt_aktualisiert": total_updated,
        "gesamt_abgelehnt": total_rejected,
        "fehler": all_errors,
        "quellen": source_reports,
    }


def fetch_all(check_deadlines_flag: bool = False) -> list[ProgrammeUpdate]:
    """Query all sources.

    Args:
        check_deadlines: Whether to check catalog deadlines.

    Returns:
        List of ProgrammeUpdate results.
    """
    results = []
    catalog = load_catalog() if check_deadlines_flag else []
    sources = load_sources()

    log.info("=== Manual Sources (no automatic fetching) ===")
    for source in sources:
        if isinstance(sources[source], dict) and sources[source].get("type") == "manual":
            log.info(f"  {source}: Manual maintenance")

    log.info("\n=== Sources with potential automatic fetching ===")
    results.append(fetch_cost())
    results.append(fetch_eu_horizon())

    # BMBF RSS (produces programme records)
    results.append(fetch_bmbf_rss())

    # Deadline check
    if check_deadlines_flag:
        log.info("\n=== Deadline Check ===")
        warnings = check_catalog_deadlines(catalog)
        if warnings:
            for w in warnings:
                log.warning(f"  {w}")
        else:
            log.info("  No expired or urgent deadlines")

        # Update suggestions
        log.info("\n=== Update Suggestions ===")
        suggestions = generate_update_suggestions(catalog, sources)
        for s in suggestions[:10]:
            log.info(f"  {s}")
        if len(suggestions) > 10:
            log.info(f"  ... and {len(suggestions) - 10} more")

    return results


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description="Förder-Radar – Automatic Fetching")
    ap.add_argument(
        "--source", choices=["cost", "eu", "bmbf", "all"], default="all", help="Source to query"
    )
    ap.add_argument("--check-deadlines", action="store_true", help="Check deadlines in catalog")
    args = ap.parse_args()

    if args.source == "all":
        results = fetch_all(check_deadlines_flag=args.check_deadlines)
    elif args.source == "cost":
        results = [fetch_cost()]
    elif args.source == "eu":
        results = [fetch_eu_horizon()]
    elif args.source == "bmbf":
        results = [fetch_bmbf_rss()]

    log.info("\n=== Fetch Results ===")
    for r in results:
        log.info(
            f"{r.source}: {len(r.programmes)} programmes, {len(r.errors)} errors, {len(r.suggestions)} suggestions"
        )
        for e in r.errors:
            log.warning(f"  Error: {e}")
        for s in r.suggestions:
            log.info(f"  Suggestion: {s}")

    # Apply fetch updates if any programmes were fetched
    programmes_fetched = [r for r in results if r.programmes]
    if programmes_fetched:
        log.info("\n=== Applying Fetch Updates ===")
        summary = apply_fetch_updates(programmes_fetched)
        log.info(f"  Result: +{summary.get('gesamt_neu', 0)} / ~{summary.get('gesamt_aktualisiert', 0)} / x{summary.get('gesamt_abgelehnt', 0)}")
        if summary.get("fehler"):
            for e in summary["fehler"]:
                log.warning(f"  {e}")


if __name__ == "__main__":
    main()
