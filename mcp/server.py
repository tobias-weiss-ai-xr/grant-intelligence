"""Grant-Agent (Förder-Radar) - MCP-Server (offizielles MCP-SDK, FastMCP).

Voll agentisch ausgerichtet: Mindest-Loop -> ingest, search, notify.
  - ingest   : Quellen/Programme in den Katalog aufnehmen (Upsert)
  - search   : Katalog durchsuchen (Kategorie-Filter + Stichwort)
  - match_best / naechste_fristen: Profil-Fit + Fristen
  - notify   : fristige Aktivierung (Deadline-Warnungen), Rolling immer

Ablauf: python server.py -> laeuft ueber MCP-Transport stdio.
"""
from __future__ import annotations

from mcp.server.fastmcp import FastMCP
from match import load_catalog, save_catalog, match_profile, next_deadline

# Laufender, erweiterbarer Katalog (ingest mutiert ihn im Speicher).
PROGRAMME = load_catalog()

mcp = FastMCP("grant-agent")


@mcp.tool()
def programs(kategorie: str | None = None) -> list[dict]:
    """Kuratierter Foerderkatalog; optional nach kategorie (DFG|ERC|BMBF|Land|Stiftung) filtern."""
    if not kategorie:
        return PROGRAMME
    return [p for p in PROGRAMME if p.get("kategorie") == kategorie]


@mcp.tool()
def search(kategorie: str | None = None, stichwort: str | None = None) -> list[dict]:
    """Stichwort-Suche ueber Name/Themen/Quelle; optional nach Kategorie eingeschraenkt."""
    out = PROGRAMME
    if kategorie:
        out = [p for p in out if p.get("kategorie") == kategorie]
    sk = (stichwort or "").lower()
    if sk:
        out = [
            p for p in out
            if sk in (p.get("name") or "").lower()
            or sk in " ".join(p.get("themen") or []).lower()
            or sk in (p.get("quelle") or "").lower()
        ]
    return out


@mcp.tool()
def ingest(programme: list[dict]) -> dict:
    """Neue Quellen/Programme per Upsert (id) in den Katalog aufnehmen und persistieren.

    Aenderungen werden sofort nach catalog.json geschrieben (Stand-Datum neu)."""
    added, updated = 0, 0
    ids = {p.get("id") for p in PROGRAMME}
    for p in programme:
        pid = p.get("id")
        if not pid:
            continue
        if pid in ids:
            updated += 1
            for i, old in enumerate(PROGRAMME):
                if old.get("id") == pid:
                    PROGRAMME[i] = p
        else:
            added += 1
            PROGRAMME.append(p)
            ids.add(pid)
    if added or updated:
        # Nur bei echter Aenderung persistieren (kein No-op-Rewrite)
        save_catalog(PROGRAMME)
    return {"status": "ok", "neu": added, "aktualisiert": updated, "gesamt": len(PROGRAMME)}


@mcp.tool()
def loeschen(programm_id: str) -> dict:
    """Programm per id aus dem Katalog entfernen und persistieren."""
    before = len(PROGRAMME)
    PROGRAMME[:] = [p for p in PROGRAMME if p.get("id") != programm_id]
    removed = before - len(PROGRAMME)
    if removed:
        save_catalog(PROGRAMME)
    return {"status": "ok" if removed else "nicht gefunden", "entfernt": removed, "gesamt": len(PROGRAMME)}


@mcp.tool()
def match_best(felder: list[str], karriere: str | None = None, rolle: str | None = None, top: int = 3) -> list[dict]:
    """Beste Programme zu einem Profil (Themen-Felder + Karriere + optional Rolle) mit Begruendung."""
    return match_profile(PROGRAMME, felder, karriere, rolle=rolle, top=top)


@mcp.tool()
def naechste_fristen(felder: list[str], karriere: str | None = None, top: int = 2) -> list[dict]:
    """Wie match_best, zusaechlich Tage bis zur naechsten Frist (Rolling wird mitgezaehlt)."""
    return next_deadline(PROGRAMME, felder, karriere, top=top)


@mcp.tool()
def notify(felder: list[str], karriere: str | None = None, rolle: str | None = None, tage: int = 60) -> list[dict]:
    """Benoetigte Aktivierungs-Warnungen: Fristen innerhalb `tage` Tagen; Rolling immer relevant."""
    out = []
    for r in next_deadline(PROGRAMME, felder, karriere, rolle=rolle, top=len(PROGRAMME)):
        if r.get("rolling"):
            out.append(r)
        elif r.get("tageBisFrist") is not None and r["tageBisFrist"] <= tage:
            out.append(r)
    return out


@mcp.tool()
def brief(felder: list[str], karriere: str | None = None, rolle: str | None = None, top: int = 3, tage: int = 60) -> dict:
    """Wochen-Brief in einem Aufruf: Top-Matches, naechste Frist, Warnungen."""
    fristen = next_deadline(PROGRAMME, felder, karriere, rolle=rolle, top=1)
    return {
        "top_matches": match_profile(PROGRAMME, felder, karriere, rolle=rolle, top=top),
        "naechste_frist": fristen[0] if fristen else None,
        "warnungen": notify(felder, karriere, rolle=rolle, tage=tage),
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")