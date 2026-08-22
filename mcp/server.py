"""Grant-Agent (Förder-Radar) - MCP-Server.

Official MCP-SDK FastMCP server providing grant discovery tools:
  - programs   : List catalogued programs (optional category filter)
  - search     : Keyword search across name/themes/source
  - ingest     : Add/update programs (persisted immediately)
  - loeschen   : Remove programs by ID
  - match_best : Find best matches for a profile
  - naechste_fristen : Programs with upcoming deadlines
  - notify     : Deadline warnings (within N days, rolling always)
  - brief      : Complete weekly brief in one call

Usage:
    python server.py  # Runs over stdio transport
"""

from __future__ import annotations

import logging
from typing import Any

from mcp.server.fastmcp import FastMCP

from grant_types import MatchResult, Programm
from match import load_catalog, match_profile, next_deadline, save_catalog
from profile import Profile, get_profile_by_id, load_profiles

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# Load catalog at startup (mutable in-memory state for ingest)
PROGRAMME = load_catalog()

mcp = FastMCP("grant-agent")


def _serialize(r: MatchResult) -> dict[str, Any]:
    """Serialize a MatchResult to the catalog's camelCase API format.

    Args:
        r: Match result.

    Returns:
        Dictionary with camelCase keys (standDatum, tageBisFrist) matching
        the catalog convention used across the MCP API.
    """
    return {
        "id": r.id,
        "name": r.name,
        "kategorie": r.kategorie,
        "score": r.score,
        "frist": r.frist,
        "rolling": r.rolling,
        "status": r.status,
        "quelle": r.quelle,
        "standDatum": r.stand_datum,
        "begruendung": r.begruendung,
        "tageBisFrist": r.tage_bis_frist,
    }


@mcp.tool()
def programs(kategorie: str | None = None) -> list[dict[str, Any]]:
    """List curated grant programs, optionally filtered by category.

    Args:
        kategorie: Optional category filter (DFG, ERC, BMBF, Land, Stiftung, Industrie, EU, Bund, International).

    Returns:
        List of program dictionaries.
    """
    if not kategorie:
        return PROGRAMME
    return [p for p in PROGRAMME if p.get("kategorie") == kategorie]


@mcp.tool()
def search(kategorie: str | None = None, stichwort: str | None = None) -> list[dict[str, Any]]:
    """Search catalog by keyword across name, themes, and source URL.

    Args:
        kategorie: Optional category filter.
        stichwort: Search keyword (case-insensitive).

    Returns:
        List of matching program dictionaries.
    """
    out = PROGRAMME
    if kategorie:
        out = [p for p in out if p.get("kategorie") == kategorie]
    if stichwort:
        sk = stichwort.lower()
        out = [
            p
            for p in out
            if sk in (p.get("name") or "").lower()
            or sk in " ".join(p.get("themen") or []).lower()
            or sk in (p.get("quelle") or "").lower()
        ]
    return out


@mcp.tool()
def ingest(programme: list[dict[str, Any]]) -> dict[str, Any]:
    """Add or update programs in the catalog (persisted immediately).

    Uses ID-based upsert: programs with existing IDs are updated,
    new IDs are appended. Every program is validated against the
    type-safe Programm model before it is accepted; invalid entries
    are rejected with error details and nothing is persisted.

    Args:
        programme: List of program dictionaries with required 'id' field.

    Returns:
        Dictionary with status, counts (neu, aktualisiert, abgelehnt,
        fehler) and total.
    """
    added, updated, abgelehnt = 0, 0, 0
    fehler: list[str] = []
    ids = {p.get("id") for p in PROGRAMME if p.get("id")}

    for p in programme:
        pid = p.get("id")
        if not pid:
            abgelehnt += 1
            fehler.append("Programm ohne id")
            log.warning("Skipping program without ID")
            continue

        # Validierung: nur valide Programme duerfen in den Katalog
        try:
            Programm.from_dict(p)
        except (ValueError, TypeError) as e:
            abgelehnt += 1
            fehler.append(f"{pid}: {e}")
            log.warning(f"Rejected invalid program {pid}: {e}")
            continue

        if pid in ids:
            # Update existing
            updated += 1
            for i, old in enumerate(PROGRAMME):
                if old.get("id") == pid:
                    PROGRAMME[i] = p
                    break
        else:
            # Add new
            added += 1
            PROGRAMME.append(p)
            ids.add(pid)

    # Persist only if changes were made
    if added or updated:
        save_catalog(PROGRAMME)

    return {
        "status": "ok" if not abgelehnt else "teilweise abgelehnt",
        "neu": added,
        "aktualisiert": updated,
        "abgelehnt": abgelehnt,
        "fehler": fehler,
        "gesamt": len(PROGRAMME),
    }


@mcp.tool()
def loeschen(programm_id: str) -> dict[str, Any]:
    """Remove a program from the catalog by ID (persisted immediately).

    Args:
        programm_id: ID of program to remove.

    Returns:
        Dictionary with status, count of removed programs, and total.
    """
    before = len(PROGRAMME)
    PROGRAMME[:] = [p for p in PROGRAMME if p.get("id") != programm_id]
    removed = before - len(PROGRAMME)

    if removed:
        save_catalog(PROGRAMME)
        log.info(f"Removed program: {programm_id}")

    return {
        "status": "ok" if removed else "nicht gefunden",
        "entfernt": removed,
        "gesamt": len(PROGRAMME),
    }


@mcp.tool()
def profile(profil_id: str | None = None) -> dict[str, Any] | list[dict[str, Any]]:
    """Load a researcher profile by ID, or list all profiles.

    Args:
        profil_id: Profile ID to load. If None, lists all profiles.

    Returns:
        Profile dict (if profil_id given) or list of all profile dicts.
        If profil_id not found, returns an error dict.
    """
    if profil_id is None:
        return [p.to_dict() for p in load_profiles()]
    p = get_profile_by_id(profil_id)
    if p is None:
        return {"fehler": f"Profil nicht gefunden: {profil_id}"}
    return p.to_dict()


@mcp.tool()
def match_best(
    felder: list[str] | None = None,
    karriere: str | None = None,
    rolle: str | None = None,
    top: int = 3,
    profil_id: str | None = None,
) -> list[dict[str, Any]]:
    """Find best matching programs for a profile.

    Career level is a hard filter. Results sorted by score and deadline.

    Args:
        felder: Research fields (e.g., ["Medizin", "Onkologie"]).
            If None, uses profile.themen (requires profil_id).
        karriere: Career level (e.g., "postdoc", "prof").
            If None, uses profile.karriere (requires profil_id).
        rolle: Optional role filter ("lead" or "partner").
        top: Maximum number of results (clamped to >= 1).
        profil_id: Optional profile ID. Loads profile from profiles.json.
            Requires einwilligung=True for matching.

    Returns:
        List of matching programs with scores and explanations.
        Empty list if profile lacks consent.
    """
    profil = None
    if profil_id:
        profil = get_profile_by_id(profil_id)
        if profil is None:
            return []
        if not profil.einwilligung:
            return []
    return [
        _serialize(r)
        for r in match_profile(PROGRAMME, felder, karriere, rolle=rolle, top=max(1, top), profil=profil)
    ]


@mcp.tool()
def naechste_fristen(
    felder: list[str] | None = None,
    karriere: str | None = None,
    top: int = 2,
    profil_id: str | None = None,
) -> list[dict[str, Any]]:
    """Find programs with upcoming deadlines.

    Includes days until deadline (None for rolling programs).

    Args:
        felder: Research fields. If None, uses profile.themen.
        karriere: Career level. If None, uses profile.karriere.
        top: Maximum number of results (clamped to >= 1).
        profil_id: Optional profile ID for profile-based matching.

    Returns:
        List of programs with deadline information.
    """
    profil = None
    if profil_id:
        profil = get_profile_by_id(profil_id)
        if profil is None:
            return []
        if not profil.einwilligung:
            return []
    return [
        _serialize(r)
        for r in next_deadline(PROGRAMME, felder, karriere, top=max(1, top), profil=profil)
    ]


@mcp.tool()
def notify(
    felder: list[str] | None = None,
    karriere: str | None = None,
    rolle: str | None = None,
    tage: int = 60,
    profil_id: str | None = None,
) -> list[dict[str, Any]]:
    """Get deadline warnings for programs requiring action.

    Includes:
        - Rolling programs (always relevant)
        - Programs with deadlines within `tage` days

    Args:
        felder: Research fields. If None, uses profile.themen.
        karriere: Career level. If None, uses profile.karriere.
        rolle: Optional role filter.
        tage: Warning window in days (default 60).
        profil_id: Optional profile ID for profile-based matching.

    Returns:
        List of programs requiring attention.
    """
    profil = None
    if profil_id:
        profil = get_profile_by_id(profil_id)
        if profil is None:
            return []
        if not profil.einwilligung:
            return []
    results = next_deadline(PROGRAMME, felder, karriere, rolle=rolle, top=len(PROGRAMME), profil=profil)
    out = []
    for r in results:
        if r.rolling or (r.tage_bis_frist is not None and r.tage_bis_frist <= tage):
            out.append(_serialize(r))
    return out


@mcp.tool()
def brief(
    felder: list[str] | None = None,
    karriere: str | None = None,
    rolle: str | None = None,
    top: int = 3,
    tage: int = 60,
    profil_id: str | None = None,
) -> dict[str, Any]:
    """Generate a complete weekly brief in one call.

    Combines:
        - Top matches (best fitting programs)
        - Next deadline (soonest upcoming)
        - Warnings (programs requiring attention)

    Args:
        felder: Research fields. If None, uses profile.themen.
        karriere: Career level. If None, uses profile.karriere.
        rolle: Optional role filter.
        top: Number of top matches.
        tage: Warning window in days.
        profil_id: Optional profile ID for profile-based matching.
            If profile lacks consent, returns error dict.

    Returns:
        Dictionary with top_matches, naechste_frist, warnungen.
        If profil_id is given but not found, includes a fehler field.
        If profile lacks consent, includes fehler and empty lists.
    """
    profil = None
    if profil_id:
        profil = get_profile_by_id(profil_id)
        if profil is None:
            return {
                "fehler": f"Profil nicht gefunden: {profil_id}",
                "top_matches": [],
                "naechste_frist": None,
                "warnungen": [],
            }
        if not profil.einwilligung:
            return {
                "fehler": "Einwilligung fehlt – Profil kann nicht gematcht werden",
                "top_matches": [],
                "naechste_frist": None,
                "warnungen": [],
            }
    fristen = next_deadline(PROGRAMME, felder, karriere, rolle=rolle, top=1, profil=profil)
    return {
        "top_matches": [
            _serialize(r)
            for r in match_profile(PROGRAMME, felder, karriere, rolle=rolle, top=top, profil=profil)
        ],
        "naechste_frist": _serialize(fristen[0]) if fristen else None,
        "warnungen": notify(felder, karriere, rolle=rolle, tage=tage, profil_id=profil_id),
    }


if __name__ == "__main__":
    log.info("Starting grant-agent MCP server...")
    mcp.run(transport="stdio")
