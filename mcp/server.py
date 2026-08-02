"""Förder-Radar – MCP-Server (offizielles MCP-SDK, FastMCP).

Stellt drei kuratierte Tools bereit:
  - `alle_programme`: Programmkatalog filtern
  - `match_besten`: beste 2-3 Programme zu einem Profil + Begründung
  - `naechste_fristen`: Fristen inkl. Tage bis Frist (auch Rolling)

Ablauf: python server.py  -> läuft über MCP-Transport stdio.
Zum Testen z. B. die offizielle MCP CLI / ein beliebiger MCP-Client.
"""
from __future__ import annotations
from mcp.server.fastmcp import FastMCP
from match import load_catalog, match_profile, next_deadline

PROGRAMME = load_catalog()

mcp = FastMCP("foerder-radar")


@mcp.tool()
def programs(kategorie: str | None = None) -> list[dict]:
    """Kuratierter Förderkatalog; optional nach kategorie (DFG|ERC|BMBF|Land|Stiftung) filtern."""
    if not kategorie:
        return PROGRAMME
    return [p for p in PROGRAMME if p.get("kategorie") == kategorie]


@mcp.tool()
def match_best(felder: list[str], karriere: str | None = None, top: int = 3) -> list[dict]:
    """Beste Programme zu einem Profil (Themen-Felder + Karrierestufe) mit Begründung."""
    return match_profile(PROGRAMME, felder, karriere, top=top)


@mcp.tool()
def naechste_fristen(felder: list[str], karriere: str | None = None, top: int = 2) -> list[dict]:
    """Wie match_best, zusatzlich Tage bis zur nächsten Frist (Rolling wird mitgezählt)."""
    return next_deadline(PROGRAMME, felder, karriere, top=top)


if __name__ == "__main__":
    mcp.run(transport="stdio")