#!/usr/bin/env python3
"""Förder-Radar – Export-Funktionen.

Exportiert Katalog in verschiedene Formate:
- CSV (für Excel/Sheets)
- JSON (für weitere Verarbeitung)
- Markdown (für Dokumentation)

Beispiel:
    python mcp/export.py --format csv --out docs/export.csv
    python mcp/export.py --format json --out docs/export.json
    python mcp/export.py --format markdown --out docs/export.md
"""
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from match import load_catalog


def export_csv(programme: list[dict[str, Any]], out: Path) -> None:
    """Export to CSV."""
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

    with open(out, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"CSV exportiert: {out} ({len(rows)} Zeilen)")


def export_json(programme: list[dict[str, Any]], out: Path) -> None:
    """Export to JSON."""
    doc = {
        "stand": datetime.now().isoformat()[:10],
        "exportiert_am": datetime.now().isoformat(),
        "programme": programme,
    }

    with open(out, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=2)

    print(f"JSON exportiert: {out} ({len(programme)} Programme)")


def export_markdown(programme: list[dict[str, Any]], out: Path) -> None:
    """Export to Markdown table."""
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
        name = p.get("name", "")[:40]
        kategorie = p.get("kategorie", "")
        themen = "; ".join(p.get("themen", [])[:3])
        karriere = "; ".join(p.get("karriere", [])[:2])
        frist = p.get("frist") or ("Rolling" if p.get("rolling") else "-")
        status = p.get("status", "")

        lines.append(f"| {id_} | {name} | {kategorie} | {themen} | {karriere} | {frist} | {status} |")

    lines.extend(["", "## Nach Kategorie", ""])

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
            lines.append(f"- **{p.get('name', '')}** ({frist})")
        lines.append("")

    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))

    print(f"Markdown exportiert: {out} ({len(programme)} Programme)")


def main() -> None:
    ap = argparse.ArgumentParser(description="Förder-Radar – Export")
    ap.add_argument("--format", choices=["csv", "json", "markdown"], required=True,
                    help="Export-Format")
    ap.add_argument("--out", type=Path, required=True, help="Ausgabedatei")
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
