#!/usr/bin/env python3
"""Förder-Radar – Pilot-Demonstration (Fachbereich Mathematik).

Generiert Match-Ergebnisse für alle Pilot-Profile und schreibt
docs/pilot-ergebnisse.md.

Usage:
    python3 mcp/pilot_demo.py
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

# Ensure mcp/ is on the path
sys.path.insert(0, str(Path(__file__).parent))

from profile import load_profiles

from match import load_catalog, match_profile, next_deadline


def generate_pilot_results() -> str:
    """Generate pilot results markdown for all profiles.

    Returns:
        Markdown string with match results for each profile.
    """
    programmes = load_catalog()
    profiles = load_profiles()
    today = date.today().isoformat()

    lines = [
        "# Pilot-Ergebnisse – Förder-Radar",
        "",
        f"**Stand:** {today} · Katalog: {len(programmes)} Programme",
        "**Pilot-Fakultät:** Philipps-Universität Marburg, Fachbereich Mathematik",
        f"**Profile:** {len(profiles)} ({sum(1 for p in profiles if p.einwilligung)} mit Einwilligung)",
        "",
        "---",
        "",
    ]

    for p in profiles:
        lines.append(f"## Profil: {p.name}")
        lines.append("")
        lines.append(f"- **ID:** {p.id}")
        lines.append(f"- **Karriere:** {p.karriere}")
        lines.append(f"- **Themen:** {', '.join(p.themen) if p.themen else '—'}")
        lines.append(f"- **ORCID:** {p.orcid or '—'}")
        lines.append(f"- **Einwilligung:** {'ja' if p.einwilligung else 'nein'}")
        lines.append("")

        if not p.einwilligung:
            lines.append("> ⚠️ Keine Einwilligung erteilt – Matching übersprungen.")
            lines.append("")
            continue

        # Top matches
        matches = match_profile(programmes, profil=p, top=5)
        lines.append("### Top-Matches")
        lines.append("")
        if not matches:
            lines.append("_Keine Treffer._")
            lines.append("")
            continue

        lines.append("| # | Programm | Kategorie | Score | Frist | Begründung |")
        lines.append("|---|---|---|---|---|---|")
        for i, m in enumerate(matches, 1):
            frist = m.frist or ("Rolling" if m.rolling else "—")
            lines.append(
                f"| {i} | {m.name} | {m.kategorie} | {m.score}/5 | {frist} | {m.begruendung} |"
            )
        lines.append("")

        # Next deadline
        fristen = next_deadline(programmes, profil=p, top=3)
        if fristen:
            lines.append("### Nächste Fristen")
            lines.append("")
            lines.append("| Programm | Frist | Tage | Begründung |")
            lines.append("|---|---|---|---|")
            for r in fristen:
                tage = (
                    f"{r.tage_bis_frist}"
                    if r.tage_bis_frist is not None
                    else ("Rolling" if r.rolling else "—")
                )
                lines.append(f"| {r.name} | {r.frist or '—'} | {tage} | {r.begruendung} |")
            lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(
        "_Automatisch generiert von `pilot_demo.py`. Scores sind Orientierung, "
        "keine Zusage. Quellen und Stand-Datum je Programm im Katalog prüfen._"
    )

    return "\n".join(lines)


def main() -> None:
    """Generate pilot results and write to docs/pilot-ergebnisse.md."""
    output = generate_pilot_results()
    out_path = Path(__file__).parent.parent / "docs" / "pilot-ergebnisse.md"
    out_path.write_text(output, encoding="utf-8")
    print(f"Pilot-Ergebnisse geschrieben: {out_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
