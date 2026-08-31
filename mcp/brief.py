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
from profile import get_profile_by_id

from grant_types import MatchResult
from match import load_catalog, match_profile, next_deadline
from saia import erweiterte_begruendung


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
    # Score transparenter machen: echte Maxima + Komponenten (wenn vorhanden)
    if r.punkte:
        max_ges = sum(c.get("max", 0) for c in r.punkte)
        teile = " · ".join(f"{c['name']} {c['punkte']}/{c['max']}" for c in r.punkte)
        score = f"{r.score}/{max_ges} ({teile})"
    else:
        score = f"{r.score}/4"
    return f"| {r.name} | {r.kategorie} | {score} | {frist} | {r.begruendung} |"


def generate(
    felder: list[str] | None = None,
    karriere: str | None = None,
    top: int = 5,
    tage: int = 60,
    saia: bool = False,
    profil_id: str | None = None,
) -> str:
    """Generate a weekly brief in Markdown format.

    Args:
        felder: Research fields. If None, uses profile.themen (requires profil_id).
        karriere: Career level. If None, uses profile.karriere (requires profil_id).
        top: Number of top matches to show.
        tage: Warning window in days.
        saia: Optional: KI-Begruendungen via SAIA (nur wenn konfiguriert).
        profil_id: Optional profile ID for profile-based matching.
            Requires einwilligung=True for matching.

    Returns:
        Markdown string with brief content.
    """
    # Load profile if profil_id is given
    profil = None
    if profil_id:
        profil = get_profile_by_id(profil_id)
        if profil is None:
            return f"# Fehler\n\nProfil nicht gefunden: {profil_id}\n"
        if not profil.einwilligung:
            return f"# Fehler\n\nProfil '{profil.name}' hat keine Einwilligung – Matching deaktiviert.\n"
        # Use profile defaults if no explicit args
        if felder is None:
            felder = profil.themen
        if karriere is None:
            karriere = profil.karriere

    # Ensure felder is a list (may be None if no profil_id and no explicit args)
    if felder is None:
        felder = []

    programmes = load_catalog()
    matches = match_profile(programmes, felder, karriere, top=top, profil=profil)
    fristen = next_deadline(programmes, felder, karriere, top=len(programmes), profil=profil)

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

    # Optional: SAIA-KI-Begruendungen (nur wenn konfiguriert und gewuenscht)
    if saia:
        zusatz_zeilen: list[str] = []
        for r in matches:
            prog = next((p for p in programmes if p["id"] == r.id), None)
            if prog is None:
                continue  # pragma: no cover – Matches stammen immer aus dem Katalog
            zusatz = erweiterte_begruendung(prog, felder if felder is not None else [], karriere)
            if zusatz:
                zusatz_zeilen.append(f"- **{r.name}:** {zusatz}")
        if zusatz_zeilen:
            lines += ["## KI-Begruendungen (SAIA)", "", *zusatz_zeilen, ""]

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
        default=None,
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
    ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--tage", type=int, default=60, help="Warnfenster in Tagen")
    ap.add_argument(
        "--saia",
        action="store_true",
        help="Optional: KI-Begruendungen via SAIA-KI-API (benoetigt SAIA_API_URL + SAIA_API_KEY)",
    )
    ap.add_argument(
        "--profil-id",
        default=None,
        help="Profil-ID aus profiles.json (übernimmt Felder & Karriere, erfordert Einwilligung)",
    )
    ap.add_argument("--out", default=None, help="Zieldatei (sonst stdout)")
    args = ap.parse_args()

    # Handle comma-separated single arguments ("Biologie, Nachhaltigkeit")
    felder: list[str] | None = None
    if args.felder:
        felder = []
        for token in args.felder:
            felder.extend(f.strip() for f in token.split(",") if f.strip())

    text = generate(
        felder=felder,
        karriere=args.karriere,
        top=args.top,
        tage=args.tage,
        saia=args.saia,
        profil_id=args.profil_id,
    )

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"Brief geschrieben: {args.out}", file=sys.stderr)
    else:
        print(text)


if __name__ == "__main__":
    main()
