"""Förder-Radar – Export-Funktionen.

Exports the grant catalog in various formats (CSV, JSON, Markdown).

Usage:
    python mcp/export.py --format csv --out docs/export.csv
    python mcp/export.py --format json --out docs/export.json
    python mcp/export.py --format markdown --out docs/export.md
    python mcp/export.py --format csv --out -          # stdout
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from match import load_catalog

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def _to_stream(out: Path | str):
    """Return a file handle and whether to close it.

    If out is '-' or Path('-'), writes to stdout.
    """
    if isinstance(out, str) and out == "-":
        return sys.stdout, False
    if isinstance(out, Path) and str(out) == "-":
        return sys.stdout, False
    return open(out, "w", encoding="utf-8", newline=""), True


def export_csv(programme: list[dict[str, Any]], out: Path | str) -> None:
    """Export catalog to CSV format.

    Args:
        programme: List of program dictionaries.
        out: Output file path, or '-' for stdout.
    """
    rows = []
    for p in programme:
        row = {
            "id": p.get("id", ""),
            "name": p.get("name", ""),
            "kategorie": p.get("kategorie", ""),
            "themen": "; ".join(p.get("themen", [])),
            "karriere": "; ".join(p.get("karriere", [])),
            "rolle": "; ".join(p.get("rolle", [])),
            "budget_min": p.get("budget_min", ""),
            "budget_max": p.get("budget_max", ""),
            "dauerJahre": p.get("dauerJahre", ""),
            "frist": p.get("frist", ""),
            "rolling": p.get("rolling", False),
            "status": p.get("status", ""),
            "quelle": p.get("quelle", ""),
            "standDatum": p.get("standDatum", ""),
            "hinweis": p.get("hinweis", ""),
        }
        rows.append(row)

    fieldnames = list(rows[0].keys()) if rows else []

    fh, close = _to_stream(out)
    try:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    finally:
        if close:
            fh.close()

    if close:
        log.info(f"CSV exported: {out} ({len(rows)} rows)")


def export_json(programme: list[dict[str, Any]], out: Path | str) -> None:
    """Export catalog to JSON format.

    Args:
        programme: List of program dictionaries.
        out: Output file path, or '-' for stdout.
    """
    doc = {
        "stand": datetime.now().isoformat()[:10],
        "exportiert_am": datetime.now().isoformat(),
        "programme": programme,
    }

    fh, close = _to_stream(out)
    try:
        json.dump(doc, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    finally:
        if close:
            fh.close()

    if close:
        log.info(f"JSON exported: {out} ({len(programme)} programmes)")


def export_markdown(programme: list[dict[str, Any]], out: Path | str) -> None:
    """Export catalog to Markdown format.

    Args:
        programme: List of program dictionaries.
        out: Output file path, or '-' for stdout.
    """
    lines = [
        "# Förder-Radar – Programm-Übersicht",
        "",
        f"**Exportiert:** {datetime.now().isoformat()}",
        f"**Gesamt:** {len(programme)} Programme",
        "",
        "## Alle Programme",
        "",
        "| ID | Name | Kategorie | Themen | Karriere | Frist | Status |",
        "|---|---|---|---|---|---|---|",
    ]

    for p in sorted(programme, key=lambda x: x.get("kategorie", "")):
        id_ = p.get("id", "")
        name = (p.get("name", "") or "")[:40]
        kategorie = p.get("kategorie", "")
        themen = "; ".join((p.get("themen", []) or [])[:3])
        karriere = "; ".join((p.get("karriere", []) or [])[:2])
        frist = p.get("frist") or ("Rolling" if p.get("rolling") else "-")
        status = p.get("status", "")

        lines.append(
            f"| {id_} | {name} | {kategorie} | {themen} | {karriere} | {frist} | {status} |"
        )

    lines.extend(["", "## Nach Kategorie", ""])

    # Group by category
    categories: dict[str, list[dict]] = {}
    for p in programme:
        cat = p.get("kategorie", "Unknown")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(p)

    for cat in sorted(categories.keys()):
        progs = categories[cat]
        lines.append(f"### {cat} ({len(progs)})")
        lines.append("")
        for p in progs:
            frist = p.get("frist") or ("Rolling" if p.get("rolling") else "-")
            name = p.get("name", "") or ""
            lines.append(f"- **{name}** ({frist})")
        lines.append("")

    fh, close = _to_stream(out)
    try:
        fh.write("\n".join(lines))
        fh.write("\n")
    finally:
        if close:
            fh.close()

    if close:
        log.info(f"Markdown exported: {out} ({len(programme)} programmes)")


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description="Förder-Radar – Export")
    ap.add_argument(
        "--format", choices=["csv", "json", "markdown"], required=True, help="Export format"
    )
    ap.add_argument("--out", type=Path, required=True, help="Output file path (or '-' for stdout)")
    args = ap.parse_args()

    programme = load_catalog()

    if args.format == "csv":
        export_csv(programme, args.out)
    elif args.format == "json":
        export_json(programme, args.out)
    elif args.format == "markdown":
        export_markdown(programme, args.out)


if __name__ == "__main__":
    main()
