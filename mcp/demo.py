"""Grant-Agent – Demo der Agent-Schleife (ingest -> search -> match -> fristen -> notify).

Laufend & reproduzierbar ohne interaktiven MCP-Server:
    python mcp/demo.py

Nur Demo-Daten, bewusst grob und nicht verbindlich.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from match import load_catalog, match_profile, next_deadline

PROGRAMME = load_catalog()


def search(kategorie: str | None = None, stichwort: str | None = None) -> list[dict[str, Any]]:
    out = PROGRAMME
    if kategorie:
        out = [p for p in out if p.get("kategorie") == kategorie]
    sk = (stichwort or "").lower()
    if sk:
        out = [
            p
            for p in out
            if sk in (p.get("name") or "").lower()
            or sk in " ".join(p.get("themen") or []).lower()
            or sk in (p.get("quelle") or "").lower()
        ]
    return out


def notify(felder: list[str], karriere: str | None = None, tage: int = 60) -> list[Any]:
    out: list[Any] = []
    for r in next_deadline(PROGRAMME, felder, karriere, top=len(PROGRAMME)):
        if r.rolling or (r.tage_bis_frist is not None and r.tage_bis_frist <= tage):
            out.append(r)
    return out


def _line(r: Any) -> str:
    f = r.tage_bis_frist
    frist = f"{f} Tage" if f is not None else "—"
    return f"  {r.score:>2} | {r.name[:38]:<38} | {r.kategorie:<5} | {frist}"


def main() -> None:
    print(f"# Grant-Agent – Agent-Schleife (Demo)  Stand: {date.today()}")
    print(f"Katalog: {len(PROGRAMME)} Programme\n")

    prof = ["Biologie", "Nachhaltigkeit"]
    karr = "postdoc"

    print("1) search(kategorie='DFG')")
    for p in search(kategorie="DFG"):
        print("   -", p.get("name"))

    print("2) match_best")
    for r in match_profile(PROGRAMME, prof, karr, top=3):
        print(_line(r))

    print("3) naechste_fristen")
    for r in next_deadline(PROGRAMME, prof, karr, top=2):
        print(_line(r))

    print("4) notify (Fristen <= 60 Tage / Rolling)")
    for r in notify(prof, karr, tage=60):
        print(_line(r))

    print("5) brief (Wochen-Brief in einem Aufruf)")
    fristen = next_deadline(PROGRAMME, prof, karr, top=1)
    top_matches = match_profile(PROGRAMME, prof, karr, top=2)
    nf = fristen[0] if fristen else None
    warnungen = notify(prof, karr, tage=60)
    print(f"   Top 2: {', '.join(r.name for r in top_matches)}")
    print(
        f"   Naechste Frist: {nf.name if nf else 'keine'} ({nf.tage_bis_frist if nf else '-'} Tage)"
    )
    print(f"   Warnungen: {len(warnungen)} Programme")

    print(
        "Fertig. Katalog/Daten: offizielle Quellen (ERC verifiziert 2026-08-03), "
        "DFG/LOEWE strukturell; Scores nur Orientierung."
    )


if __name__ == "__main__":
    main()
