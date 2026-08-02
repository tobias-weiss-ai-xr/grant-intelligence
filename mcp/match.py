"""Förder-Radar – Daten- und Matching-Schichten (Demo).

Reine Logik ohne MCP-Abhängigkeit: Katalog laden, einfacher Matching-Score,
nächste Fristen. Hinweis: Nur Demo-Daten zu Entwicklungszwecken, nicht
verbindlich.
"""
from __future__ import annotations
import json
from datetime import date, datetime
from pathlib import Path

CATALOG = Path(__file__).with_name("catalog.json")


def load_catalog(path: Path = CATALOG) -> list[dict]:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh).get("programme", [])


def _fits(theme_defs: list[str], field: str) -> bool:
    """'alle'/'frei' passt immer; sonst Substring-Match (case-insensitive)."""
    f = field.lower()
    return any(
        t.lower() in ("alle", "frei") or t.lower() in f or f in t.lower()
        for t in theme_defs
    )


def _score(prog: dict, fields: list[str], karriere: str | None) -> int:
    """Sehr einfacher Demo-Score: maximal für Themen-Überlapp und Karrierefit."""
    s = 0
    s += min(sum(1 for f in fields if _fits(prog.get("themen", []), f)), 3)
    if karriere and karriere in prog.get("karriere", []):
        s += 1
    return s


def match_profile(programme, fields, karriere=None, top=3):
    """Top-Treffer mit Begründung, sortiert nach Score und Frist."""
    scored = []
    for p in programme:
        sc = _score(p, fields, karriere)
        if sc <= 0:
            continue
        scored.append({
            "id": p.get("id"),
            "name": p.get("name"),
            "kategorie": p.get("kategorie"),
            "score": sc,
            "frist": p.get("frist"),
            "rolling": p.get("rolling", False),
            "quelle": p.get("quelle", ""),
            "standDatum": p.get("standDatum"),
            "begruendung": f"Themen-Überlappung: {sc} Punkte (Demo-Regel)",
        })
    scored.sort(key=lambda x: (-x["score"], x["frist"] or ""))
    return scored[:top]


def next_deadline(programs, fields, karriere=None, top=2, today=None):
    """Wie match_profile, zusätzlich Tage bis zur Frist (oder None)."""
    today = today or date.today()
    out = []
    for r in match_profile(programs, fields, karriere, top):
        delta = None
        try:
            d = datetime.strptime(r["frist"], "%Y-%m-%d").date()
            delta = (d - today).days
        except Exception:
            delta = None
        out.append({**r, "tageBisFrist": delta})
    return out


if __name__ == "__main__":
    progs = load_catalog()
    print(json.dumps(match_profile(progs, ["Biologie", "Nachhaltigkeit"], "postdoc"),
                     ensure_ascii=False, indent=2))
    print(json.dumps(next_deadline(progs, ["Biologie"], "postdoc"),
                     ensure_ascii=False, indent=2))