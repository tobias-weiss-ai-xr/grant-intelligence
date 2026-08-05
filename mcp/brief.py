"""Förder-Radar – Wochen-Brief (automatisierbar per Cron).

Generates a weekly brief in Markdown format with top matches and deadline warnings.

Usage:
    python mcp/brief.py --felder Biologie Nachhaltigkeit --karriere postdoc
    python mcp/brief.py --felder "Biologie, Nachhaltigkeit" --karriere prof --out docs/brief.md

Writes Markdown to stdout or file. No email in MVP; brief is placed in shared folder.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date

from grant_types import MatchResult
from match import load_catalog, match_profile, next_deadline


def _zeile(r: MatchResult) -> str:
    """Generate a table row for a match result.

    Args:
        r: Match result.

    Returns:
        Markdown table row string.
    """
    frist = (
        f"{r.tage_bis_frist} Tage"
        if r.tage_bis_frist is not None
        else ("Rolling" if r.rolling else "—")
    )
    return f"| {r.name} | {r.kategorie} | {r.score}/5 | {frist} | {r.begruendung} |"


def generate(felder: list[str], karriere: str | None, top: int = 3, tage: int = 60) -> str:
    """Generate a weekly brief in Markdown format.

    Args:
        felder: Research fields.
        karriere: Career level.
        top: Number of top matches to show.
        tage: Warning window in days.

    Returns:
        Markdown string with brief content.
    """
    programmes = load_catalog()
    matches = match_profile(programmes, felder, karriere, top=top)
    fristen = next_deadline(programmes, felder, karriere, top=len(programmes))

    # Filter warnings (rolling or within tage days)
    warn = [
        r
        for r in fristen
        if r.rolling or (r.tage_bis_frist is not None and r.tage_bis_frist <= tage)
    ]

    # Build markdown
    lines = [
        "# Förder-Radar – Wochen-Brief",
        "",
        f"**Stand:** {date.today().isoformat()} · Profil: {', '.join(felder)}",
        f"{' · Karriere: ' + karriere if karriere else ''}",
        "",
        f"Katalog: {len(programmes)} Programme.",
        "",
    ]

    # Top matches section
    lines += [
        "## Top-Matches",
        "",
        "| Programm | Kategorie | Score | Frist | Begründung |",
        "|---|---|---|---|---|",
    ]
    lines += [_zeile(r) for r in matches] + [""]

    # Warnings section
    if warn:
        lines += [
            f"## Frist-Warnungen (≤ {tage} Tage / Rolling)",
            "",
            "| Programm | Kategorie | Score | Frist | Begründung |",
            "|---|---|---|---|---|",
        ]
        lines += [_zeile(r) for r in warn] + [""]
    else:
        lines += [
            "## Frist-Warnungen",
            "",
            f"_Keine Fristen unter {tage} Tagen._",
            "",
        ]

    # Footer
    lines += [
        "---",
        "",
        "_Scores sind Orientierung, keine Zusage. Quellen und Stand-Datum je Programm ",
        "im Katalog prüfen. Automatisch erzeugt – vor Nutzung gegen offizielle Stellen ",
        "prüfen._",
    ]

    return "\n".join(lines)


def main() -> None:
    """CLI entry point."""
    ap = argparse.ArgumentParser(description="Förder-Radar Wochen-Brief")
    ap.add_argument(
        "--felder",
        nargs="+",
        required=True,
        help='Forschungsfelder (z.B. Biologie Nachhaltigkeit oder "Biologie, Nachhaltigkeit")',
    )
    ap.add_argument(
        "--karriere",
        choices=[
            "postdoc",
            "junior",
            "prof",
            "verwaltung",
            "service",
            "IT",
            "bibliothek",
            "student",
            "senior",
        ],
        default=None,
    )
    ap.add_argument("--top", type=int, default=3)
    ap.add_argument("--tage", type=int, default=60, help="Warnfenster in Tagen")
    ap.add_argument("--out", default=None, help="Zieldatei (sonst stdout)")
    args = ap.parse_args()

    # Handle comma-separated single arguments ("Biologie, Nachhaltigkeit")
    felder: list[str] = []
    for token in args.felder:
        felder.extend(f.strip() for f in token.split(",") if f.strip())

    text = generate(felder, args.karriere, top=args.top, tage=args.tage)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"Brief geschrieben: {args.out}", file=sys.stderr)
    else:
        print(text)


if __name__ == "__main__":
    main()
