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
from match import load_catalog, match_profile, next_deadline

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
    """Neue Quellen/Programme per Upsert (id) in den laufenden Katalog aufnehmen."""
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
    return {"status": "ok", "neu": added, "aktualisiert": updated, "gesamt": len(PROGRAMME)}


@mcp.tool()
def match_best(felder: list[str], karriere: str | None = None, top: int = 3) -> list[dict]:
    """Beste Programme zu einem Profil (Themen-Felder + Karriere) mit Begruendung."""
    return match_profile(PROGRAMME, felder, karriere, top=top)


@mcp.tool()
def naechste_fristen(felder: list[str], karriere: str | None = None, top: int = 2) -> list[dict]:
    """Wie match_best, zusaechlich Tage bis zur naechsten Frist (Rolling wird mitgezaehlt)."""
    return next_deadline(PROGRAMME, felder, karriere, top=top)


@mcp.tool()
def notify(felder: list[str], karriere: str | None = None, tage: int = 60) -> list[dict]:
    """Benoetigte Aktivierungs-Warnungen: Fristen innerhalb `tage` Tagen; Rolling immer relevant."""
    out = []
    for r in next_deadline(PROGRAMME, felder, karriere, top=len(PROGRAMME)):
        if r.get("rolling"):
            out.append(r)
        elif r.get("tageBisFrist") is not None and r["tageBisFrist"] <= tage:
            out.append(r)
    return out


if __name__ == "__main__":
    mcp.run(transport="stdio")