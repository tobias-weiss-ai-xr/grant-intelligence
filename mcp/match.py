"""Förder-Radar – Daten-, Matching- und Begründungs-Schicht.

Reine Logik ohne MCP-/Web-Abhaengigkeit: Katalog laden/speichern,
gewichteter Matching-Score, menschenlesbare Begruendung (deutsch, regelbasiert),
naechste Fristen.
"""
from __future__ import annotations
import json
from datetime import date, datetime
from pathlib import Path

CATALOG = Path(__file__).with_name("catalog.json")


# --------------------------------------------------------------------------- Daten
def load_catalog(path: Path = CATALOG) -> list[dict]:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh).get("programme", [])


def save_catalog(programme: list[dict], path: Path = CATALOG) -> None:
    """Katalog persistieren: Inhalte + Stand-Datum neu setzen (Governance)."""
    doc = {
        "stand": date.today().isoformat(),
        "quelleHinweis": (
            "Kuratierter Katalog. status = verifiziert (live geprueft am standDatum) | "
            "laufend (keine Frist, rolling) | zu-pruefen (bekanntes Programm, Frist vor "
            "Nutzung gegen Portal pruefen). Keine rechtliche Bindung; fuer produktive "
            "Nutzung gegen offizielle Stellen pruefen."
        ),
        "programme": programme,
    }
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# ----------------------------------------------------------------------- Matching
def _fits(theme_defs: list[str], field: str) -> bool:
    """'alle'/'frei' passt immer; sonst Substring-Match (case-insensitive)."""
    f = field.lower()
    return any(
        t.lower() in ("alle", "frei") or t.lower() in f or f in t.lower()
        for t in theme_defs
    )


def _theme_score(prog: dict, fields: list[str]) -> tuple[int, list[str]]:
    """Gewichtete Themen-Ueberlappung (max 3) + getroffene Felder."""
    hits = [f for f in fields if _fits(prog.get("themen", []), f)]
    return min(len(hits), 3), hits


def _score(prog: dict, fields: list[str], karriere: str | None) -> dict:
    """Gewichteter Score (0..5) + Teilscores fuer die Begruendung."""
    t, hits = _theme_score(prog, fields)
    k = 1 if (karriere and karriere in prog.get("karriere", [])) else 0
    s = t + k
    return {"gesamt": s, "thema": t, "karriere": k, "felder": hits}


def _frist_text(frist: str | None, rolling: bool) -> str:
    if rolling:
        return "Rolling – jederzeit einreichbar, keine feste Frist"
    if not frist:
        return "Frist noch offen – vor Nutzung gegen Portal pruefen"
    try:
        d = datetime.strptime(frist, "%Y-%m-%d").date()
        delta = (d - date.today()).days
        if delta < 0:
            return f"Frist {d.strftime('%d.%m.%Y')} – bereits abgelaufen ({-delta} Tage)"
        return f"Frist {d.strftime('%d.%m.%Y')} – noch {delta} Tage"
    except Exception:
        return f"Frist {frist} (Format unklar, pruefen)"


def _begruendung(prog: dict, parts: dict, score: int) -> str:
    """Regelbasierte, menschenlesbare Begruendung (deutsch)."""
    bits: list[str] = []
    if parts["felder"]:
        bits.append("Themen-Ueberlappung: " + ", ".join(parts["felder"]))
    if prog.get("themen") in (["frei"], ["alle"]) or "frei" in (prog.get("themen") or []):
        bits.append("offen fuer alle Fachrichtungen")
    if parts["karriere"]:
        bits.append("Karrierestufe passt zum Programm")
    elif not (prog.get("karriere") or []):
        bits.append("Karrierestufe nicht gelistet – Eignung im Einzelfall pruefen")
    bits.append(_frist_text(prog.get("frist"), prog.get("rolling", False)))
    budget = prog.get("budget_max")
    if budget:
        bits.append(f"bis ca. {budget/1e6:.1f} Mio. Euro" if budget >= 1e6 else f"bis ca. {budget/1000:.0f} Tausend Euro")
    if prog.get("status") == "zu-pruefen":
        bits.append("Achtung: Details/Frist vor Antrag gegen Portal pruefen")
    return "; ".join(bits)


# ------------------------------------------------------------------ Abfrage-Ebene
def match_profile(programme, fields, karriere=None, rolle=None, top=3):
    """Top-Treffer mit Begruendung, sortiert nach Score und Frist.

    Karrierestufe ist ein harter Filter: Programme ohne passende Stufe
    werden nicht gelistet."""
    scored = []
    for p in programme:
        # Karrierestufe als harter Filter: Programm muss die Stufe explizit fuehren
        if karriere and (prog_karriere := p.get("karriere")):
            if karriere not in prog_karriere:
                continue
        parts = _score(p, fields, karriere)
        if parts["gesamt"] <= 0:
            continue
        if rolle and rolle not in p.get("rolle", []):
            continue
        scored.append({
            "id": p.get("id"),
            "name": p.get("name"),
            "kategorie": p.get("kategorie"),
            "score": parts["gesamt"],
            "frist": p.get("frist"),
            "rolling": p.get("rolling", False),
            "status": p.get("status"),
            "quelle": p.get("quelle", ""),
            "standDatum": p.get("standDatum"),
            "begruendung": _begruendung(p, parts, parts["gesamt"]),
        })
    scored.sort(key=lambda x: (-x["score"], x["frist"] or "9999-99-99"))
    return scored[:top]


def next_deadline(programs, fields, karriere=None, rolle=None, top=2, today=None):
    """Wie match_profile, zusaetzlich Tage bis zur Frist (oder None)."""
    today = today or date.today()
    out = []
    for r in match_profile(programs, fields, karriere, rolle=rolle, top=top):
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
