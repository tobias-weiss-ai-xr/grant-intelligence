#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ideen-Batch-250 (ASCII-sicher, deterministisch) + Batch-Score.
Score = 0.20*A + 0.25*D + 0.30*Ak + 0.25*N   (0-5)
A=Machbarkeit(solo), D=Demo, Ak=Aktualitaet+Persistenz, N=Neuheit (1-5)
"""
from __future__ import annotations

# 25 Kategorien x 10 Formate = 250 Ideen. (Kategorien-Token, A, D, Ak, N)
CATS = [
    ("Barrierefreiheit",       3,4,5,4),
    ("Sprache",                5,4,4,3),
    ("Umwelt-Energie",         3,4,5,3),
    ("Klima-Campus",           3,4,4,3),
    ("Wohlbefinden",           4,4,3,4),
    ("Community",              4,4,3,2),
    ("Wohnen",                 5,4,3,2),
    ("Mobilitaet",             4,4,3,3),
    ("Sharing-Economy",        4,4,3,3),
    ("Verpflegung",            4,4,3,3),
    ("Freizeit-Kultur",        4,3,3,2),
    ("Sport",                  4,4,3,3),
    ("Sicherheit",             4,4,3,4),
    ("Digitale-Dienste",       4,4,4,3),
    ("Verwaltung",             4,4,4,3),
    ("Forschungspraxis",       4,4,4,4),
    ("Lehre-Pruefung",         4,4,4,3),
    ("Karriere",               4,4,4,3),
    ("Gesundheit",             4,4,4,4),
    ("Familie-Eltern",         4,4,4,3),
    ("OpenData-Transparenz",   4,4,4,3),
    ("KI-Automation",          4,5,5,5),
    ("Geschichte-Ort",         4,4,4,4),
    ("Kommunikation",          4,4,3,3),
]
# 10 Form-/Funktionstypen je Kategorie
FORMS = [
    ("-Karte",        0.2,  0.3,  0.0,  0.1),
    ("-Navigator",    0.2,  0.3,  0.1,  0.2),
    ("-Matcher",      0.3,  0.2,  0.1,  0.2),
    ("-Alarm",        0.3,  0.2,  0.2,  0.1),
    ("-Dashboard",    0.1,  0.4,  0.2,  0.0),
    ("-Tool",         0.3,  0.2,  0.1,  0.1),
    ("-Guide",        0.3,  0.2,  0.0,  0.1),
    ("-Boerse",       0.2,  0.2,  0.1,  0.0),
    ("-Wiki",         0.1,  0.2,  0.0,  0.3),
    ("-Kalender",     0.3,  0.3,  0.1,  0.0),
]
# 10 extra hand-worked Ideen -> insg. 24*10+10 = 250 (noch 10)
EXTRAS = [
    ("KI-Automation",      "Lokaler souveraener Agent-Playground",    3,5,5,5),
    ("Barrierefreiheit",   "Live-Untertitel + Simultanuebersetzung",  4,5,5,4),
    ("Barrierefreiheit",   "a11y-Audit-Report Uni-Webseiten (BitV)",  3,5,5,3),
    ("Umwelt-Energie",     "CO2-Label je Gebaeude & Rechenzentrum",   3,5,5,3),
    ("Forschungspraxis",   "offene Forschungsdaten-Plattform (FAIR)", 4,4,5,4),
    ("OpenData-Transparenz","Transparenz-Dashboard der Antraege",      4,4,4,3),
    ("Community",          "Babysitter-/Nachbarschafts-Pool (Tausch)",5,5,4,3),
    ("Verpflegung",        "Food-Sharing unverkauft (Mensa-Transfer)", 4,5,4,3),
    ("Geschichte-Ort",     "Stadtteil-Erzaehlpfad in AR/Geolayer",    4,4,4,4),
    ("Wohnen",             "WG/Zimmer-Planer im 10-Minuten-Radius",   5,5,4,3),
]

def build() -> list[tuple[str, str, int, int, int, int]]:
    out: list[tuple[str,str,int,int,int,int]] = []
    for ci,(cat,a,d,ak,n) in enumerate(CATS):
        for fi,(suf,da,dd,dk,dn) in enumerate(FORMS):
            out.append((cat, cat + suf, clamp(a+da), clamp(d+dd), clamp(ak+dk), clamp(n+dn)))
    for cat,title,a,d,ak,n in EXTRAS:
        out.append((cat, title, a, d, ak, n))
    return out

def clamp(x: float) -> int:
    return int(max(1.0, min(5.0, round(x))))

def score(a,d,ak,n) -> float:
    return 0.20*a + 0.25*d + 0.30*ak + 0.25*n

def verify(rows) -> None:
    for cat,title,a,d,ak,n in rows:
        assert all(ord(c) < 128 for c in title), f"non-ascii: {title}"
        assert isinstance(a,int) and 1<=a<=5, a
    assert len(rows)==250, len(rows)

def main():
    rows = build()
    verify(rows)
    scored = sorted([(score(r[2],r[3],r[4],r[5]), i, r) for i,r in enumerate(rows,1)],
                    key=lambda x: -x[0])
    with open("Batch-Ideen-250.md","w",encoding="ascii") as f:
        f.write("# Ideen-Batch (250) + Batch-Score\n\n")
        f.write("Score = 0.20A + 0.25D + 0.30Ak + 0.25N (0-5). ASCII-sicher generiert.\n\n")
        f.write("| Nr | Kategorie | Idee | A | D | Ak | N | Score |\n|---|---|---|---|---|---|---|---|\n")
        for i,r in enumerate(rows,1):
            cat,title,a,d,ak,n = r
            f.write(f"| {i} | {cat} | {title} | {a} | {d} | {ak} | {n} | {score(a,d,ak,n):.2f} |\n")
        f.write("\n## Top 10\n")
        for rank,(sc,i,r) in enumerate(scored[:10],1):
            cat,title,a,d,ak,n = r
            f.write(f"{rank}. **{title}** [{cat}]  Score {sc:.2f} (A{d} D{d} Ak{ak} N{n})\n")
        f.write(f"\nErzeugt {len(rows)} Ideen.\n")
    print("OK 250 Ideen geschrieben.")
    print("\nTOP 10:")
    for rank,(sc,i,r) in enumerate(scored[:10],1):
        cat,title,a,d,ak,n = r
        print(f"  {rank}. {title}  Score {sc:.2f}")

if __name__ == "__main__":
    main()