from __future__ import annotations

"""Förder-Radar – Daten-, Matching- und Begründungs-Schicht.

Reine, side-effect-arme Logik ohne MCP-/Web-Abhängigkeit: Katalog laden/speichern,
gewichteter Matching-Score (Thema + Karriere), menschenlesbare Begründung
(deutsch, regelbasiert), nächste Fristen. Die Module `app`/`server`/`brief` bauen
auf dieser Schicht auf; Tests und der JS-Port `dashboard/app.js` müssen zu
identischen Ergebnissen kommen.

Public API:
    - load_catalog / save_catalog: JSON-Persistenz des Programmkatalogs.
    - match_profile / next_deadline: zentrale Matching-Einstiegspunkte.
    - _score / _theme_score / _fits: Score-Bausteine, auch einzeln testbar.

Konventionen:
    - Matching ist case-insensitive und substring-basiert (bidirektional).
    - Die Wildcards 'alle', 'frei' und 'thematisch-offen' matchen jedes Feld.
    - Karriere ist ein harter Filter, sofern das Programm Karrierestufen listet.
"""


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
    """Clear the in-memory catalog cache.

    Needed for test isolation and after `save_catalog`, so subsequent
    `load_catalog` calls read fresh data from disk.

    Args:
        path: Optional specific catalog path to evict from the cache. If None,
            the entire cache is cleared.

    Returns:
        None.
    """
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
    """Check if a research field matches the programme's theme definitions.

    Matching rules:
        - The wildcards 'alle', 'frei' and 'thematisch-offen' match any
          non-empty field (open-ended programmes are visible to every search).
        - Otherwise the match is case-insensitive and bidirectional substring:
          the definition matches if it is contained in the field OR the field
          is contained in the definition, e.g. 'Physik' matches
          'Astroteilchenphysik' and vice versa.
        - Empty or whitespace-only fields never match.

    Args:
        theme_defs: List of theme definitions from the programme (``themen``).
        field: User-provided research field.

    Returns:
        True if the field matches at least one theme definition, else False.
    """
    wildcards = ("alle", "frei", "thematisch-offen")
    f = field.lower().strip()
    if not f:
        return False
    return any(
        t.lower() in wildcards or t.lower() in f or f in t.lower() for t in theme_defs
    )


def _theme_score(prog: dict[str, Any], fields: list[str]) -> tuple[int, list[str]]:
    """Calculate the theme-overlap score for a programme.

    Iterates the user's fields and counts how many match the programme's
    themes. The score is capped at 3 so the theme contribution to the total
    match score stays bounded, independent of how many fields were supplied.

    Args:
        prog: Programme dictionary (uses the ``themen`` key).
        fields: User-provided research fields.

    Returns:
        Tuple of (score, matched_fields): score is at most 3; matched_fields
        lists every field that matched (not truncated to 3), so the
        justification can name all of them.
    """
    hits = [f for f in fields if _fits(prog.get("themen", []), f)]
    return min(len(hits), 3), hits


def _score(prog: dict[str, Any], fields: list[str], karriere: str | None) -> dict[str, Any]:
    """Calculate weighted match score (0-5) with component breakdown.

    Components:
        - Thema: 0-3 points for theme overlap (`_theme_score`).
        - Karriere: 1 point if the career level is listed in the programme.
          No penalty is applied when the programme declares no careers.

    Args:
        prog: Programme dictionary (uses ``themen`` and ``karriere`` keys).
        fields: User-provided research fields.
        karriere: User's career level, or None to skip the career component.

    Returns:
        Dictionary with the keys:
            - ``gesamt``: total score 0-5 (theme + career).
            - ``thema``: theme sub-score 0-3.
            - ``karriere``: career sub-score 0 or 1.
            - ``felder``: list of matched research fields.
    """
    t, hits = _theme_score(prog, fields)
    k = 1 if (karriere and karriere in prog.get("karriere", [])) else 0
    return {"gesamt": t + k, "thema": t, "karriere": k, "felder": hits}


def _punkte_teile(parts: dict[str, Any]) -> list[dict[str, Any]]:
    """Strukturierte Punkte-Aufschlüsselung (Transparenz, ändert den Score nicht).

    Macht begründbar, woraus sich der Gesamt-Score zusammensetzt. Additiv zu
    `_score`: der berechnete Score bleibt unverändert, zusätzlich werden die
    Komponenten (Name, Punkte, Max, Detail) als strukturierte Daten exponiert.

    Args:
        parts: Score-Breakdown aus `_score`.

    Returns:
        Liste von Komponenten {"name", "punkte", "max", "detail"}.
    """
    thema_detail = ", ".join(parts.get("felder", [])) or None
    return [
        {
            "name": "Thema",
            "punkte": parts.get("thema", 0),
            "max": 3,
            "detail": thema_detail,
        },
        {
            "name": "Karriere",
            "punkte": parts.get("karriere", 0),
            "max": 1,
            "detail": "Karrierestufe im Programm gelistet"
            if parts.get("karriere")
            else None,
        },
    ]


def _frist_text(frist: str | None, rolling: bool) -> str:
    """Generate a human-readable, German deadline description.

    Priority: rolling admissions > missing/unparseable deadline > days until
    deadline (or how long it has expired). Used inside `_begruendung`.

    Args:
        frist: Deadline date in ISO format (YYYY-MM-DD) or None.
        rolling: Whether the programme has rolling admissions.

    Returns:
        Human-readable deadline description, e.g. "Frist 30.06.2027 – noch 120
        Tage".
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
    """Generate a human-readable, German explanation for a match.

    Combines the matched themes, open-to-all-fields signals, career fit,
    deadline, budget and status warnings into one ";".join()-ed sentence.
    Rule-based and deterministic, so it is testable and stays stable across
    identical inputs.

    Args:
        prog: Programme dictionary (uses ``themen``, ``karriere``, ``frist``,
            ``rolling``, ``budget_max``, ``budget_text``, ``status``).
        parts: Score breakdown from `_score`.

    Returns:
        An explanatory string in German.
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
    """Find the top matching programmes for a profile.

    Career level is a hard filter: a programme that lists careers is excluded
    when it does not contain the user's career level. Programmes that declare
    no careers at all are not filtered. Matches need a positive theme score,
    pure-career matches (no theme overlap) are dropped. Empty/whitespace-only
    fields or ``top <= 0`` return no results.

    Args:
        programme: List of programme dictionaries.
        fields: User's research fields. If None, ``profil.themen`` is used.
        karriere: User's career level (hard filter). If None,
            ``profil.karriere`` is used.
        rolle: Optional role filter (lead/partner); programmes not listing the
            role are excluded when set.
        top: Maximum number of results to return.
        profil: Optional Profile object. If provided, its themen and karriere
            are used as defaults. Explicit fields/karriere arguments take
            precedence over profile values. If ``profil.einwilligung`` is
            False, an empty list is returned (DSGVO consent gate).

    Returns:
        List of MatchResult objects, sorted by score (descending) and then by
        deadline (ascending, missing deadlines last), truncated to ``top``.
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
            punkte=_punkte_teile(parts),
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
    """Find noteworthy programmes with upcoming (or recent) deadlines.

    Delegates scoring and filtering to `match_profile` (same hard career
    filter, consent gate and sorting) and additionally computes the days
    until each deadline relative to `today`. Unparseable deadlines yield
    None for ``tage_bis_frist`` instead of failing.

    Args:
        programs: List of programme dictionaries.
        fields: User's research fields. If None, ``profil.themen`` is used.
        karriere: User's career level. If None, ``profil.karriere`` is used.
        rolle: Optional role filter (lead/partner).
        top: Maximum number of results (default 2, smaller than
            `match_profile` because only the imminent deadlines matter).
        today: Reference date for the day delta (defaults to date.today()).
        profil: Optional Profile object for defaults and consent gate.

    Returns:
        List of MatchResult objects, each with ``tage_bis_frist`` set (None
        when the deadline is missing or unparseable), sorted as in
        `match_profile`.
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
                punkte=r.punkte,
            )
        )
    return out
