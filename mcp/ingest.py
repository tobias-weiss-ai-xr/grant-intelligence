"""Förder-Radar – Extensible Ingestion Pipeline.

Registry-based ingestion: each source is a function decorated with @register.
Adding a source = writing one function. The pipeline is:

  1. Repeatable: deterministic IDs (slug-based), idempotent upsert, audit log
  2. Extensible: @register("key", "Name", "desc", "api") on a fetch function
  3. Safe: --dry-run by default, --apply to write to catalog

Usage:
  python ingest.py --list                     # List all registered fetchers
  python ingest.py --source openaire          # Dry-run one fetcher
  python ingest.py --source openaire --apply  # Run and merge into catalog
  python ingest.py --all                      # Dry-run all fetchers
  python ingest.py --all --apply              # Run all and merge
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable

import httpx

from fetchers import ProgrammeUpdate, _enrich_programme, _slug_id, apply_fetch_updates
from grant_types import Programm

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
log = logging.getLogger(__name__)

CATALOG_JSON = Path(__file__).parent / "catalog.json"
AUDIT_LOG = Path(__file__).parent.parent / "docs" / "update_log.md"
UA = "Foerder-Radar/1.0"  # ASCII-only for HTTP headers

# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_REGISTRY: dict[str, FetcherEntry] = {}


@dataclass
class FetcherEntry:
    key: str
    name: str
    description: str
    category: str
    fetch_fn: Callable[[], ProgrammeUpdate]


def register(key: str, name: str, description: str = "", category: str = "api"):
    """Decorator: register a fetcher in the global registry."""

    def decorator(fn: Callable[[], ProgrammeUpdate]) -> Callable[[], ProgrammeUpdate]:
        _REGISTRY[key] = FetcherEntry(key, name, description or "", category, fn)
        return fn

    return decorator


def list_fetchers() -> list[FetcherEntry]:
    return sorted(_REGISTRY.values(), key=lambda e: e.key)


def ingest_source(key: str) -> ProgrammeUpdate:
    """Run a single registered fetcher. Raises KeyError if unknown."""
    entry = _REGISTRY.get(key)
    if not entry:
        raise KeyError(f"Unknown fetcher: {key}. Available: {', '.join(sorted(_REGISTRY))}")
    log.info(f"Fetching: {entry.name} ({key})")
    return entry.fetch_fn()


def ingest_all() -> list[ProgrammeUpdate]:
    """Run all registered fetchers, collecting errors per-source."""
    results: list[ProgrammeUpdate] = []
    for entry in list_fetchers():
        try:
            r = entry.fetch_fn()
            results.append(r)
            log.info(f"  {entry.key}: {len(r.programmes)} programmes, {len(r.errors)} errors")
        except Exception as e:
            log.error(f"  {entry.key}: FAILED — {e}")
            results.append(ProgrammeUpdate(entry.key, [], [str(e)], datetime.now().isoformat(), []))
    return results


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_CATEGORY_MAP = {
    "openaire": "EU", "crossref": "International", "nih": "International",
    "nsf": "International", "cost": "EU", "eu": "EU",
    "bmbf": "BMBF", "dfg": "DFG", "erc": "ERC",
}


def _oa_get(obj: Any, *path: str) -> str | None:
    """Extract a value from OpenAIRE's nested JSON (handles {"$": "value"} wrapping)."""
    for key in path:
        if not isinstance(obj, dict):
            return None
        obj = obj.get(key)
    if isinstance(obj, dict):
        return obj.get("$")
    return obj if isinstance(obj, str) else None


def _make_prog(
    source: str, pid: str, name: str, quelle: str, hinweis: str,
    frist: str | None = None, rolling: bool | None = None,
) -> dict[str, Any]:
    """Build a programme dict with sensible defaults for auto-imported entries."""
    if rolling is None:
        rolling = frist is None
    return {
        "id": pid,
        "name": name[:200],
        "kategorie": _CATEGORY_MAP.get(source, "International"),
        "themen": ["thematisch-offen"],
        "karriere": [],
        "rolle": ["lead"],
        "frist": frist,
        "rolling": rolling,
        "status": "zu-pruefen",
        "quelle": quelle,
        "standDatum": date.today().isoformat(),
        "hinweis": hinweis,
    }


def _api_fetch(
    source: str, url: str, params: dict | None, method: str = "GET",
    json_body: dict | None = None,
) -> tuple[list[dict[str, Any]], list[str], list[str], dict | None]:
    """Generic HTTP fetch with error handling.

    Returns (programmes, errors, suggestions, data). On success, data is the
    parsed JSON response. On failure, data is None and errors is populated.
    """
    programmes: list[dict[str, Any]] = []
    errors: list[str] = []
    suggestions: list[str] = []
    try:
        if method == "POST":
            resp = httpx.post(url, json=json_body, timeout=30, headers={"User-Agent": UA})
        else:
            resp = httpx.get(url, params=params, timeout=30, headers={"Accept": "application/json", "User-Agent": UA})
        resp.raise_for_status()
        data = resp.json()
        return programmes, errors, suggestions, data
    except httpx.HTTPStatusError as e:
        errors.append(f"HTTP {e.response.status_code}: {e}")
    except httpx.RequestError as e:
        errors.append(f"Network error: {e}")
    except json.JSONDecodeError as e:
        errors.append(f"JSON parse error: {e}")
    except Exception as e:
        errors.append(f"Unexpected error: {e}")
    return programmes, errors, suggestions, None


# ---------------------------------------------------------------------------
# Existing fetchers (re-registered for unified pipeline)
# ---------------------------------------------------------------------------


@register("cost", "COST", "COST European Cooperation portal check", "portal")
def fetch_cost_portal() -> ProgrammeUpdate:
    from fetchers import fetch_cost
    return fetch_cost()


@register("eu", "EU Horizon", "EU Horizon Europe portal check", "portal")
def fetch_eu_horizon_portal() -> ProgrammeUpdate:
    from fetchers import fetch_eu_horizon
    return fetch_eu_horizon()


@register("bmbf", "BMBF", "BMBF RSS feed (Bekanntmachungen)", "rss")
def fetch_bmbf_feed() -> ProgrammeUpdate:
    from fetchers import fetch_bmbf_rss
    return fetch_bmbf_rss()


# ---------------------------------------------------------------------------
# API-based fetchers
# ---------------------------------------------------------------------------


@register("openaire", "OpenAIRE", "EU research projects (3.9M projects, all EU funders)", "api")
def fetch_openaire() -> ProgrammeUpdate:
    """Fetch recent EU research projects from OpenAIRE API."""
    source = "openaire"
    programmes, errors, suggestions, data = _api_fetch(
        source, "https://api.openaire.eu/search/projects",
        params={"size": "50", "format": "json"},
    )
    if data:
        # OpenAIRE returns {"response": {"results": {"result": [...]}}}
        results_wrapper = data.get("response", {}).get("results", {})
        results = results_wrapper.get("result", []) if isinstance(results_wrapper, dict) else results_wrapper
        total = _oa_get(data.get("response", {}).get("header", {}), "total") or "?"
        seen: set[str] = set()
        for result in results:
            try:
                proj = result["metadata"]["oaf:entity"]["oaf:project"]
            except (KeyError, TypeError):
                continue
            code = _oa_get(proj, "code")
            title = _oa_get(proj, "title")
            funder = _oa_get(proj, "fundingtree", "funder", "name")
            funding_level = _oa_get(proj, "fundingtree", "funding_level_0", "name")
            if not code or not title:
                continue
            prog_name = funding_level or f"{funder or 'EU'}: {title[:80]}"
            pid = _slug_id(source, f"{code}-{prog_name}")
            if pid in seen:
                continue
            seen.add(pid)
            programmes.append(_make_prog(
                source, pid, prog_name,
                f"https://cordis.europa.eu/project/id/{code}",
                f"Auto-importiert aus OpenAIRE (Funder: {funder or '?'}). Verifikation erforderlich.",
            ))
        suggestions.append(f"{source}: {len(programmes)} programmes from {len(results)} projects (total: {total})")
    return ProgrammeUpdate(source, programmes, errors, datetime.now().isoformat(), suggestions)


@register("nih", "NIH RePORTER", "US biomedical grants (76K projects)", "api")
def fetch_nih_reporter() -> ProgrammeUpdate:
    """Fetch active NIH grants from NIH RePORTER API."""
    source = "nih"
    year = date.today().year
    programmes, errors, suggestions, data = _api_fetch(
        source, "https://api.reporter.nih.gov/v2/projects/search",
        params=None, method="POST",
        json_body={"criteria": {"fiscal_years": [year, year - 1]}, "limit": 50},
    )
    if data:
        total = data.get("meta", {}).get("total", "?")
        results = data.get("results", [])
        seen: set[str] = set()
        for proj in results:
            project_num = proj.get("project_num", "")
            title = proj.get("project_title", "")
            agency = proj.get("agency", "NIH")
            program_name = proj.get("fundProgramName", "")
            if not project_num or not title:
                continue
            prog_name = program_name or f"NIH: {title[:80]}"
            pid = _slug_id(source, f"{project_num}-{prog_name}")
            if pid in seen:
                continue
            seen.add(pid)
            programmes.append(_make_prog(
                source, pid, prog_name,
                f"https://reporter.nih.gov/project/{project_num}",
                f"Auto-importiert aus NIH RePORTER (Agency: {agency}). Verifikation erforderlich.",
            ))
        suggestions.append(f"{source}: {len(programmes)} programmes from {len(results)} projects (total: {total})")
    return ProgrammeUpdate(source, programmes, errors, datetime.now().isoformat(), suggestions)


@register("nsf", "NSF Awards", "US science grants (active awards)", "api")
def fetch_nsf_awards() -> ProgrammeUpdate:
    """Fetch active NSF awards from NSF Awards API."""
    source = "nsf"
    programmes, errors, suggestions, data = _api_fetch(
        source, "https://api.nsf.gov/services/v1/awards.json",
        params={"rpp": "50"},
    )
    if data:
        awards = data.get("response", {}).get("award", [])
        seen: set[str] = set()
        for award in awards:
            award_id = award.get("id", "")
            title = award.get("title", "")
            agency = award.get("agency", "NSF")
            program_name = award.get("fundProgramName", "")
            exp_date = award.get("expDate", "")
            if not award_id or not title:
                continue
            prog_name = program_name or f"NSF: {title[:80]}"
            pid = _slug_id(source, f"{award_id}-{prog_name}")
            if pid in seen:
                continue
            seen.add(pid)
            # Parse MM/DD/YYYY → YYYY-MM-DD
            frist = None
            if exp_date:
                try:
                    parts = exp_date.split("/")
                    if len(parts) == 3:
                        frist = f"{parts[2]}-{int(parts[0]):02d}-{int(parts[1]):02d}"
                except (ValueError, IndexError):
                    pass
            programmes.append(_make_prog(
                source, pid, prog_name,
                f"https://www.nsf.gov/awardsearch/?AwardID={award_id}",
                f"Auto-importiert aus NSF Awards (Agency: {agency}). Verifikation erforderlich.",
                frist=frist,
            ))
        suggestions.append(f"{source}: {len(programmes)} programmes from {len(awards)} awards")
    return ProgrammeUpdate(source, programmes, errors, datetime.now().isoformat(), suggestions)


@register("crossref", "Crossref Funder Registry", "45K funders with DOIs (metadata enrichment)", "registry")
def fetch_crossref_funders() -> ProgrammeUpdate:
    """Fetch German funder metadata from Crossref Funder Registry."""
    source = "crossref"
    programmes, errors, suggestions, data = _api_fetch(
        source, "https://api.crossref.org/funders",
        params={"filter": "location:Germany", "rows": "50"},
    )
    if data:
        items = data.get("message", {}).get("items", [])
        total = data.get("message", {}).get("total-results", "?")
        seen: set[str] = set()
        for funder in items:
            funder_id = funder.get("id", "")
            name = funder.get("name", "")
            location = funder.get("location", "")
            work_count = funder.get("count", 0)
            if not funder_id or not name:
                continue
            pid = _slug_id(source, funder_id)
            if pid in seen:
                continue
            seen.add(pid)
            programmes.append(_make_prog(
                source, pid, f"Crossref: {name}",
                f"https://api.crossref.org/funders/{funder_id}",
                f"Crossref Funder Registry ({location}, {work_count} works). Metadata only.",
            ))
        suggestions.append(f"{source}: {len(programmes)} German funders (total: {total})")
    return ProgrammeUpdate(source, programmes, errors, datetime.now().isoformat(), suggestions)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _print_results(updates: list[ProgrammeUpdate]) -> None:
    """Print fetch results table."""
    print(f"\n{'='*80}")
    print(f"{'Source':<15} {'Programmes':>10} {'Errors':>8} {'Suggestions':>12}")
    print(f"{'-'*80}")
    for u in updates:
        print(f"{u.source:<15} {len(u.programmes):>10} {len(u.errors):>8} {len(u.suggestions):>12}")
        for e in u.errors:
            print(f"  ERROR: {e}")
        for s in u.suggestions:
            print(f"  INFO: {s}")
    print(f"{'='*80}")


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Förder-Radar – Extensible Ingestion Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n  python ingest.py --list\n  python ingest.py --source openaire --apply\n  python ingest.py --all --apply",
    )
    ap.add_argument("--list", action="store_true", help="List all registered fetchers")
    ap.add_argument("--source", type=str, help="Run a specific fetcher by key")
    ap.add_argument("--all", action="store_true", help="Run all registered fetchers")
    ap.add_argument("--apply", action="store_true", help="Merge results into catalog (default: dry-run)")
    args = ap.parse_args()

    if args.list:
        print(f"\n{'Key':<15} {'Category':<10} {'Name':<30} Description")
        print("-" * 80)
        for e in list_fetchers():
            print(f"{e.key:<15} {e.category:<10} {e.name:<30} {e.description[:50]}")
        print(f"\nTotal: {len(_REGISTRY)} fetchers")
        return

    if args.source:
        try:
            updates = [ingest_source(args.source)]
        except KeyError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.all:
        updates = ingest_all()
    else:
        ap.print_help()
        return

    _print_results(updates)

    has_programmes = any(u.programmes for u in updates)
    if not has_programmes:
        print("\nNo programmes fetched. Nothing to merge.")
        return

    if not args.apply:
        # Dry-run: count what would be added/updated without writing
        existing_ids = set()
        try:
            with open(CATALOG_JSON, encoding="utf-8") as fh:
                existing_ids = {p.get("id") for p in json.load(fh).get("programme", []) if p.get("id")}
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        would_add = 0
        would_update = 0
        for u in updates:
            for p in u.programmes:
                pid = p.get("id", "")
                if pid in existing_ids:
                    would_update += 1
                else:
                    would_add += 1
        print(f"\n[DRY-RUN] Would add: {would_add}, Would update: {would_update}")
        print("  Run with --apply to merge into catalog.")
        return

    # Apply: merge into catalog
    result = apply_fetch_updates(updates, catalog_path=CATALOG_JSON, audit_path=AUDIT_LOG)
    print(f"\nResult [{result.get('status', '?')}]:")
    print(f"  New:       {result.get('gesamt_neu', 0)}")
    print(f"  Updated:   {result.get('gesamt_aktualisiert', 0)}")
    print(f"  Rejected:  {result.get('gesamt_abgelehnt', 0)}")
    if result.get("fehler"):
        print(f"  Errors:    {len(result['fehler'])}")
        for err in result["fehler"][:5]:
            print(f"    - {err}")
        if len(result["fehler"]) > 5:
            print(f"    ... and {len(result['fehler']) - 5} more")


if __name__ == "__main__":
    main()
