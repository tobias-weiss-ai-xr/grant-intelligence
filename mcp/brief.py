"""Förder-Radar – Wochen-Brief (automatisierbar per Cron).

Beispiel:
    python mcp/brief.py --felder Biologie Nachhaltigkeit --karriere postdoc
    python mcp/brief.py --felder "Biologie, Nachhaltigkeit" --karriere prof --out docs/brief.md

Schreibt Markdown nach stdout oder in eine Datei. Kein Mailversand im MVP;
der Brief liegt dann z.B. in einem geteilten Ordner.
"""
from __future__ import annotations

import argparse
import sys
from datetime import date

from match import load_catalog, match_profile, next_deadline

def _zeile(r: dict) -> str:
    f = r.get("tageBisFrist")
    frist = f"{f} Tage" if f is not None else ("Rolling" if r.get("rolling") else "—")
    return (f"| {r['name']} | {r['kategorie']} | {r['score']}/5 | {frist} | "
            f"{r['begruendung']} |")


def generate(felder: list[str], karriere: str | None, top: int = 3, tage: int = 60) -> str:
    programmes = load_catalog()
    matches = match_profile(programmes, felder, karriere, top=top)
    fristen = next_deadline(programmes, felder, karriere, top=len(programmes))
    warn = [r for r in fristen
            if r.get("rolling") or (r.get("tageBisFrist") is not None and r["tageBisFrist"] <= tage)]

    lines = [f"# Förder-Radar – Wochen-Brief", "",
             f"**Stand:** {date.today().isoformat()} · Profil: {', '.join(felder)}"
             + (f" · Karriere: {karriere}" if karriere else ""), "",
             f"Katalog: {len(programmes)} Programme.", ""]

    lines += ["## Top-Matches", "", "| Programm | Kategorie | Score | Frist | Begründung |",
              "|---|---|---|---|---|"]
    lines += [_zeile(r) for r in matches] + [""]

    if warn:
        lines += ["## Frist-Warnungen (≤ %d Tage / Rolling)" % tage, "",
                  "| Programm | Kategorie | Score | Frist | Begründung |",
                  "|---|---|---|---|---|"]
        lines += [_zeile(r) for r in warn] + [""]
    else:
        lines += ["## Frist-Warnungen", "", "_Keine Fristen unter %d Tagen._" % tage, ""]

    lines += ["---", "",
              "_Scores sind Orientierung, keine Zusage. Quellen und Stand-Datum je Programm "
              "im Katalog prüfen. Automatisch erzeugt – vor Nutzung gegen offizielle Stellen "
              "prüfen._"]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description="Förder-Radar Wochen-Brief")
    ap.add_argument("--felder", nargs="+", required=True, help="Forschungsfelder (z.B. Biologie Nachhaltigkeit oder \"Biologie, Nachhaltigkeit\")")
    ap.add_argument("--karriere", choices=["postdoc", "junior", "prof"], default=None)
    ap.add_argument("--top", type=int, default=3)
    ap.add_argument("--tage", type=int, default=60, help="Warnfenster in Tagen")
    ap.add_argument("--out", default=None, help="Zieldatei (sonst stdout)")
    args = ap.parse_args()

    # Kommagetrennte Einzelargumente wie im UI behandeln ("Biologie, Nachhaltigkeit")
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
