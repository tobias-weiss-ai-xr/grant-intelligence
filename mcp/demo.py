"""Grant-Agent – Demo der Agent-Schleife (ingest -> search -> match -> fristen -> notify).

Laufend & reproduzierbar ohne interaktiven MCP-Server:
    python mcp/demo.py

Nur Demo-Daten, bewusst grob und nicht verbindlich.
"""
from __future__ import annotations

from datetime import date

from match import load_catalog, match_profile, next_deadline

PROGRAMME = load_catalog()


def search(kategorie=None, stichwort=None):
    out = PROGRAMME
    if kategorie:
        out = [p for p in out if p.get("kategorie") == kategorie]
    sk = (stichwort or "").lower()
    if sk:
        out = [p for p in out
               if sk in (p.get("name") or "").lower()
               or sk in " ".join(p.get("themen") or []).lower()
               or sk in (p.get("quelle") or "").lower()]
    return out


def notify(felder, karriere=None, tage=60):
    out = []
    for r in next_deadline(PROGRAMME, felder, karriere, top=len(PROGRAMME)):
        if r.get("rolling"):
            out.append(r)
        elif r.get("tageBisFrist") is not None and r["tageBisFrist"] <= tage:
            out.append(r)
    return out


def _line(r):
    f = r.get("tageBisFrist")
    frist = f"{f} Tage" if f is not None else "—"
    return (f"  {r.get('score'):>2} | {r.get('name','')[:38]:<38} | "
            f"{r.get('kategorie',''):<5} | {frist}")


def main():
    print(f"# Grant-Agent – Agent-Schleife (Demo)  Stand: {date.today()}")
    print(f"Katalog: {len(PROGRAMME)} Programme\n")

    prof = ["Biologie", "Nachhaltigkeit"]
    karr = "postdoc"

    print("1) search(kategorie='BMBF')")
    for p in search(kategorie="BMBF"):
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

    print("Fertig. Katalog/Daten: bewusst grob, Demo-Stand.")


if __name__ == "__main__":
    main()