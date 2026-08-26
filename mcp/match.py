"""Förder-Radar – Daten-, Matching- und Begründungs-Schicht.

Reine Logik ohne MCP-/Web-Abhaengigkeit: Katalog laden/speichern,
gewichteter Matching-Score, menschenlesbare Begruendung (deutsch, regelbasiert),
naechste Fristen.

Type-safe, well-documented, and testable.
"""

from __future__ import annotations

import json
import logging
from datetime import date
from pathlib import Path
from typing import Any

from grant_types import MatchResult, budget_beschreibung, parse_frist

try:
    from profile import Profile
except ImportError:  # pragma: no cover
    Profile = None  # type: ignore[assignment, misc]

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

CATALOG = Path(__file__).with_name("catalog.json")
SOURCES = Path(__file__).with_name("sources.json")

# Performance: pfad-basierter in-memory Cache für Catalog-Loads
_CATALOG_CACHE: dict[str, list[dict[str, Any]]] = {}


def _clear_catalog_cache(path: Path | None = None) -> None:
    """Cache leeren (für Pfad oder komplett)."""
    global _CATALOG_CACHE
    if path is not None:
        key = str(path.resolve())
        _CATALOG_CACHE.pop(key, None)
    else:
        _CATALOG_CACHE.clear()


class CatalogError(Exception):
    """Raised when catalog operations fail."""

    pass


def load_sources(path: Path | None = None) -> dict[str, Any]:
    """Load source definitions from sources.json.

    Args:
        path: Path to sources file. Defaults to sources.json in same directory.

    Returns:
        Dictionary of source configurations.
    """
    path = path or SOURCES
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def load_catalog_doc(path: Path | None = None) -> dict[str, Any]:
    """Load the full catalog document (dict with 'programme' key).

    Single source of truth for reading the raw catalog JSON. Returns the
    entire document (stand, quelleHinweis, programme) so callers that need
    the metadata can use it directly.

    Args:
        path: Path to catalog file. Defaults to catalog.json in same directory.

    Returns:
        The parsed JSON document as a dict.
    """
    path = path or CATALOG
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def load_catalog(path: Path | None = None) -> list[dict[str, Any]]:
    """Load the program catalog from JSON.

    Args:
        path: Path to catalog file. Defaults to catalog.json in same directory.

    Returns:
        List of program dictionaries.

    Raises:
        CatalogError: If file cannot be read or parsed.
    """
    global _CATALOG_CACHE
    path = path or CATALOG
    # Cache-Hit
    key = str(path.resolve())
    if key in _CATALOG_CACHE:
        return _CATALOG_CACHE[key]
    try:
        data = load_catalog_doc(path)
        if not isinstance(data, dict):
            raise CatalogError(
                f"Invalid catalog structure: expected object, got {type(data).__name__}"
            )
        result = data.get("programme", [])
        _CATALOG_CACHE[key] = result
        return result
    except FileNotFoundError:
        log.error(f"Catalog file not found: {path}")
        raise CatalogError(f"Catalog file not found: {path}") from None
    except json.JSONDecodeError as e:
        log.error(f"Invalid JSON in catalog: {path} - {e}")
        raise CatalogError(f"Invalid JSON in catalog: {e}") from e


def save_catalog(programme: list[dict[str, Any]], path: Path | None = None) -> None:
    """Persist the catalog with updated metadata.

    Sets the 'stand' date to today and includes governance information.

    Args:
        programme: List of program dictionaries to save.
        path: Output path. Defaults to catalog.json in same directory.

    Raises:
        CatalogError: If file cannot be written.
    """
    path = path or CATALOG
    doc = {
        "stand": date.today().isoformat(),
        "quelleHinweis": (
            "Kuratierter Katalog. status = verifiziert (live geprüft am standDatum) | "
            "laufend (keine Frist, rolling) | zu-pruefen (bekanntes Programm, Frist vor "
            "Nutzung gegen Portal prüfen). Keine rechtliche Bindung; für produktive "
            "Nutzung gegen offizielle Stellen prüfen."
        ),
        "programme": programme,
    }
    try:
        path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        log.info(f"Catalog saved: {path} ({len(programme)} programmes)")
        # Cache invalidieren
        _clear_catalog_cache(path)
    except OSError as e:
        log.error(f"Failed to write catalog: {path} - {e}")
        raise CatalogError(f"Failed to write catalog: {e}") from e


# =============================================================================
# Matching Logic
# =============================================================================


def _fits(theme_defs: list[str], field: str) -> bool:
    """Check if a field matches the program's theme definitions.

    'alle'/'frei' matches everything. Otherwise, case-insensitive substring match.

    Args:
        theme_defs: List of theme definitions from the program.
        field: User-provided research field.

    Returns:
        True if field matches any theme definition.
    """
    f = field.lower().strip()
    if not f:
        return False
    return any(
        t.lower() in ("alle", "frei") or t.lower() in f or f in t.lower() for t in theme_defs
    )


def _theme_score(prog: dict[str, Any], fields: list[str]) -> tuple[int, list[str]]:
    """Calculate weighted theme overlap score.

    Maximum score of 3, with list of matched fields.

    Args:
        prog: Program dictionary.
        fields: User-provided research fields.

    Returns:
        Tuple of (score, list of matched fields).
    """
    hits = [f for f in fields if _fits(prog.get("themen", []), f)]
    return min(len(hits), 3), hits


def _score(prog: dict[str, Any], fields: list[str], karriere: str | None) -> dict[str, Any]:
    """Calculate weighted match score (0-5) with component breakdown.

    Components:
        - Thema: 0-3 points for theme overlap
        - Karriere: 1 point if career level matches

    Args:
        prog: Program dictionary.
        fields: User-provided research fields.
        karriere: User's career level.

    Returns:
        Dictionary with total score, theme score, career score, and matched fields.
    """
    t, hits = _theme_score(prog, fields)
    k = 1 if (karriere and karriere in prog.get("karriere", [])) else 0
    return {"gesamt": t + k, "thema": t, "karriere": k, "felder": hits}


def _frist_text(frist: str | None, rolling: bool) -> str:
    """Generate human-readable deadline text.

    Args:
        frist: Deadline date in ISO format (YYYY-MM-DD) or None.
        rolling: Whether the program has rolling admissions.

    Returns:
        Human-readable deadline description.
    """
    if rolling:
        return "Rolling – jederzeit einreichbar, keine feste Frist"
    if not frist:
        return "Frist noch offen – vor Nutzung gegen Portal prüfen"
    d = parse_frist(frist)
    if d is None:
        return f"Frist {frist} (Format unklar, prüfen)"
    delta = (d - date.today()).days
    if delta < 0:
        return f"Frist {d.strftime('%d.%m.%Y')} – bereits abgelaufen ({-delta} Tage)"
    return f"Frist {d.strftime('%d.%m.%Y')} – noch {delta} Tage"


def _begruendung(prog: dict[str, Any], parts: dict[str, Any]) -> str:
    """Generate human-readable explanation for match score.

    Args:
        prog: Program dictionary.
        parts: Score breakdown from _score().

    Returns:
        German explanation string.
    """
    bits: list[str] = []

    # Theme overlap
    if parts["felder"]:
        bits.append("Themen-Ueberlappung: " + ", ".join(parts["felder"]))

    # Open to all fields
    if prog.get("themen") in (["frei"], ["alle"]) or "frei" in (prog.get("themen") or []):
        bits.append("offen fuer alle Fachrichtungen")

    # Career level
    if parts["karriere"]:
        bits.append("Karrierestufe passt zum Programm")
    elif not (prog.get("karriere") or []):
        bits.append("Karrierestufe nicht gelistet – Eignung im Einzelfall prüfen")

    # Deadline
    bits.append(_frist_text(prog.get("frist"), prog.get("rolling", False)))

    # Budget
    budget = prog.get("budget_max")
    if budget:
        bits.append(prog.get("budget_text") or budget_beschreibung(budget))

    # Status warning
    if prog.get("status") == "zu-pruefen":
        bits.append("Achtung: Details/Frist vor Antrag gegen Portal prüfen")

    return "; ".join(bits)


# =============================================================================
# Query Layer
# =============================================================================


def match_profile(
    programme: list[dict[str, Any]],
    fields: list[str] | None = None,
    karriere: str | None = None,
    rolle: str | None = None,
    top: int = 3,
    profil: Profile | None = None,
) -> list[MatchResult]:
    """Find top matching programs for a profile.

    Career level is a hard filter: programs without the specified career level
    are excluded. Empty fields return no results.

    Args:
        programme: List of program dictionaries.
        fields: User's research fields. If None, profile.themen is used.
        karriere: User's career level (hard filter). If None, profile.karriere is used.
        rolle: Optional role filter (lead/partner).
        top: Maximum number of results to return.
        profil: Optional Profile object. If provided, its themen and karriere
            are used as defaults. Explicit fields/karriere arguments take
            precedence over profile values. If profil.einwilligung is False,
            returns an empty list (DSGVO consent gate).

    Returns:
        List of MatchResult objects, sorted by score and deadline.
    """
    # DSGVO consent gate
    if profil is not None and not profil.einwilligung:
        log.info(f"Matching refused: profile '{profil.id}' has no consent")
        return []

    # Profile defaults: explicit args take precedence over profile values
    if profil is not None:
        if fields is None:
            fields = profil.themen
        if karriere is None:
            karriere = profil.karriere

    if not fields or not any(f.strip() for f in fields):
        log.debug("Empty or whitespace-only fields, returning no matches")
        return []

    if top <= 0:
        log.debug(f"top <= 0 ({top}), returning no matches")
        return []

    scored: list[MatchResult] = []
    for p in programme:
        # Hard career filter
        prog_karriere = p.get("karriere", [])
        if karriere and prog_karriere and karriere not in prog_karriere:
            continue

        # Calculate score
        parts = _score(p, fields, karriere)
        if parts["gesamt"] <= 0 or parts["thema"] <= 0:
            continue

        # Role filter
        if rolle and rolle not in p.get("rolle", []):
            continue

        # Build result
        begruendung = _begruendung(p, parts)
        result = MatchResult(
            id=p.get("id", ""),
            name=p.get("name", ""),
            kategorie=p.get("kategorie", ""),
            score=parts["gesamt"],
            frist=p.get("frist"),
            rolling=bool(p.get("rolling", False)),
            status=p.get("status", ""),
            quelle=p.get("quelle", ""),
            stand_datum=p.get("standDatum", ""),
            begruendung=begruendung,
        )
        scored.append(result)

    # Sort by score (desc) then deadline (asc, None last)
    scored.sort(key=lambda x: (-x.score, x.frist or "9999-99-99"))
    return scored[:top]


def next_deadline(
    programs: list[dict[str, Any]],
    fields: list[str] | None = None,
    karriere: str | None = None,
    rolle: str | None = None,
    top: int = 2,
    today: date | None = None,
    profil: Profile | None = None,
) -> list[MatchResult]:
    """Find programs with upcoming deadlines.

    Like match_profile, but includes days until deadline.

    Args:
        programs: List of program dictionaries.
        fields: User's research fields. If None, profile.themen is used.
        karriere: User's career level. If None, profile.karriere is used.
        rolle: Optional role filter.
        top: Maximum number of results.
        today: Reference date (defaults to today).
        profil: Optional Profile object for defaults and consent gate.

    Returns:
        List of MatchResult objects with tage_bis_frist set.
    """
    today = today or date.today()
    results = match_profile(programs, fields, karriere, rolle=rolle, top=top, profil=profil)

    out: list[MatchResult] = []
    for r in results:
        delta = None
        if r.frist:
            d = parse_frist(r.frist)
            if d is not None:
                delta = (d - today).days
        out.append(
            MatchResult(
                id=r.id,
                name=r.name,
                kategorie=r.kategorie,
                score=r.score,
                frist=r.frist,
                rolling=r.rolling,
                status=r.status,
                quelle=r.quelle,
                stand_datum=r.stand_datum,
                begruendung=r.begruendung,
                tage_bis_frist=delta,
            )
        )
    return out
