"""Förder-Radar – Forscherprofil-Modell und Persistenz.

Type-safe Profile dataclass with ORCID Public API adapter.
Analog zu grant_types.Programm: from_dict/to_dict (camelCase),
Validierung in __post_init__.

DSGVO: Matching nur mit einwilligung=True. ORCID-Abruf nur mit Einwilligung.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Any, ClassVar

import httpx

from grant_types import Karrierestufe

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

PROFILES = Path(__file__).with_name("profiles.json")
ORCID_API = "https://pub.orcid.org/v3.0"

_PROFILE_KEY_MAP: dict[str, str] = {
    "standDatum": "stand_datum",
}
"""Mapping from profiles.json (camelCase) keys to dataclass fields."""

_PROFILE_REVERSE_MAP = {v: k for k, v in _PROFILE_KEY_MAP.items()}

# Kuratierte Keywords zur Themen-Ableitung aus Publikationstiteln.
_FIELD_KEYWORDS: dict[str, list[str]] = {
    "Künstliche Intelligenz": ["künstliche intelligenz", "artificial intelligence", "machine learning", "deep learning", "neural network"],
    "Maschinelles Lernen": ["machine learning", "deep learning", "neural network"],
    "Graphen": ["graph", "graphen"],
    "GraphRAG": ["graphrag", "graph rag", "knowledge graph"],
    "Mathematik": ["mathematik", "mathematics"],
    "Algebra": ["algebra"],
    "Topologie": ["topologie", "topology", "mannigfaltigkeit"],
    "Analysis": ["analysis", "differential", "integral", "funktionalanalysis"],
    "Zahlentheorie": ["zahlentheorie", "number theory", "primzahl"],
    "Geometrie": ["geometrie", "geometry"],
    "Stochastik": ["stochastik", "wahrscheinlichkeit", "probability", "statistik"],
    "Numerik": ["numerik", "numerical", "approximation"],
    "Biologie": ["biologie", "biology"],
    "Medizin": ["medizin", "medical", "clinical"],
    "Physik": ["physik", "physics"],
    "Chemie": ["chemie", "chemistry"],
}


@dataclass
class Profile:
    """Forscherprofil mit DSGVO-Einwilligung.

    Persistiert in profiles.json. Matching nur mit einwilligung=True.
    ORCID-Abruf nur mit einwilligung=True und nicht-leerem orcid.

    Attributes:
        id: Eindeutige Profil-ID (z.B. "pilot-01-tobias").
        name: Vollständiger Name.
        karriere: Karrierestufe (postdoc, junior, prof, ...).
        themen: Forschungsfelder / Themen.
        orcid: ORCID iD (z.B. "0000-0001-2345-6789") oder leerer String.
        publikationen: Liste von Publikationstiteln (optional, via ORCID).
        einwilligung: DSGVO-Einwilligung (True = Matching erlaubt).
        status: Aktiv/Inaktiv-Status ("aktiv", "inaktiv").
        stand_datum: ISO-Datum der letzten Aktualisierung.
        hinweis: Freitext-Hinweis.
    """

    id: str
    name: str
    karriere: str
    themen: list[str] = field(default_factory=list)
    orcid: str = ""
    publikationen: list[str] = field(default_factory=list)
    einwilligung: bool = False
    status: str = "aktiv"
    stand_datum: str = ""
    hinweis: str = ""

    # Valid profile status values (distinct from programme Status enum)
    _VALID_STATUS: ClassVar[set[str]] = {"aktiv", "inaktiv"}

    def __post_init__(self) -> None:
        """Validate required fields and enum membership.

        Raises:
            ValueError: If id, name, or karriere is missing, or karriere
                is not a valid career level, or status is invalid.
        """
        missing = [
            label
            for label, value in (("id", self.id), ("name", self.name), ("karriere", self.karriere))
            if not value
        ]
        if missing:
            raise ValueError(f"Profil fehlen Pflichtfelder: {', '.join(missing)}")
        if not Karrierestufe.is_valid(self.karriere):
            raise ValueError(f"Ungültige Karrierestufe: {self.karriere}")
        if self.status not in self._VALID_STATUS:
            raise ValueError(f"Ungültiger status: {self.status}")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Profile:
        """Build a Profile from a profiles.json dict (camelCase keys).

        Args:
            data: Profile dictionary (camelCase keys like standDatum).

        Returns:
            Validated Profile instance.

        Raises:
            ValueError: If required fields are missing or values are invalid.
        """
        mapped = {_PROFILE_KEY_MAP.get(k, k): v for k, v in data.items()}
        # Check required fields before constructor to raise ValueError, not TypeError
        for field_name in ("id", "name", "karriere"):
            if not mapped.get(field_name):
                raise ValueError(f"Profil fehlen Pflichtfelder: {field_name}")
        return cls(**mapped)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to profiles.json format (camelCase keys).

        Returns:
            Dictionary compatible with profiles.json entries.
        """
        data = asdict(self)
        return {_PROFILE_REVERSE_MAP.get(k, k): v for k, v in data.items()}


# ---------------------------------------------------------------------------
# Persistenz
# ---------------------------------------------------------------------------


def load_profiles(path: Path | None = None) -> list[Profile]:
    """Load researcher profiles from profiles.json.

    Args:
        path: Path to profiles file. Defaults to profiles.json in same directory.

    Returns:
        List of Profile objects. Returns empty list if file does not exist.
    """
    path = path or PROFILES
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except FileNotFoundError:
        log.info(f"Profiles file not found: {path}")
        return []
    except json.JSONDecodeError as e:
        log.error(f"Invalid JSON in profiles: {path} - {e}")
        return []

    raw = data.get("profile", [])
    profiles: list[Profile] = []
    for entry in raw:
        try:
            profiles.append(Profile.from_dict(entry))
        except (ValueError, TypeError) as e:
            log.warning(f"Skipping invalid profile: {e}")
    return profiles


def save_profiles(profiles: list[Profile], path: Path | None = None) -> None:
    """Persist profiles to profiles.json with updated stand date.

    Args:
        profiles: List of Profile objects to save.
        path: Output path. Defaults to profiles.json in same directory.
    """
    path = path or PROFILES
    doc = {
        "stand": date.today().isoformat(),
        "quelleHinweis": (
            "Pilot- und Nutzer-Profile. Einwilligung erteilt = Profil wird "
            "im Matching verwendet. Weitere Profile koennen hier per Merge "
            "Request hinzugefuegt oder lokal als profiles.local gepflegt werden."
        ),
        "profile": [p.to_dict() for p in profiles],
    }
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    log.info(f"Profiles saved: {path} ({len(profiles)} profiles)")


def get_profile_by_id(profile_id: str, path: Path | None = None) -> Profile | None:
    """Load a single profile by ID.

    Args:
        profile_id: Profile ID to search for.
        path: Path to profiles file.

    Returns:
        Profile or None if not found.
    """
    for p in load_profiles(path):
        if p.id == profile_id:
            return p
    return None


# ---------------------------------------------------------------------------
# ORCID Public API Adapter
# ---------------------------------------------------------------------------


def fetch_orcid(
    orcid_id: str, einwilligung: bool = True, timeout: float = 10.0
) -> list[str]:
    """Fetch publication titles from ORCID Public API.

    Queries https://pub.orcid.org/v3.0/{orcid}/works and extracts titles.
    Only called when einwilligung=True and orcid_id is non-empty.

    Args:
        orcid_id: ORCID iD (e.g. "0000-0001-2345-6789").
        einwilligung: DSGVO consent flag. If False, returns empty list.
        timeout: HTTP timeout in seconds.

    Returns:
        List of publication titles. Empty list on error, missing consent,
        or non-200 response. Never raises.
    """
    if not einwilligung:
        log.info("ORCID fetch skipped: missing consent")
        return []

    if not orcid_id:
        log.info("ORCID fetch skipped: no ORCID iD")
        return []

    try:
        resp = httpx.get(
            f"{ORCID_API}/{orcid_id}/works",
            headers={"Accept": "application/json"},
            timeout=timeout,
        )
        if resp.status_code != 200:
            log.warning(f"ORCID API returned {resp.status_code} for {orcid_id}")
            return []

        data = resp.json()
        titles: list[str] = []
        for group in data.get("group", []):
            for work in group.get("work-summary", []):
                title = work.get("title", {}).get("title", {})
                content = title.get("content", "")
                if content:
                    titles.append(content)
        log.info(f"ORCID fetch: {len(titles)} publications for {orcid_id}")
        return titles

    except httpx.HTTPError as e:
        log.warning(f"ORCID fetch failed (HTTP): {e}")
        return []
    except (json.JSONDecodeError, KeyError) as e:
        log.warning(f"ORCID fetch failed (parse): {e}")
        return []
    except Exception as e:  # pragma: no cover
        log.warning(f"ORCID fetch failed (unexpected): {e}")
        return []


def derive_themen(titles: list[str]) -> list[str]:
    """Derate theme keywords from publication titles.

    Simple keyword extraction: looks for known research fields in titles.
    This is intentionally simple — no NLP, just substring matching against
    a curated list. Manual themen always take precedence.

    Args:
        titles: List of publication titles.

    Returns:
        List of derived theme keywords (deduplicated).
    """
    # Left word-boundary matching avoids false positives (e.g. "ki" in
    # "cooking") while still matching plurals/derivatives (e.g. "graph" in
    # "graphs", "algebra" in "algebraic")
    lower_titles = " ".join(t.lower() for t in titles)
    found: list[str] = []
    for field_name, keywords in _FIELD_KEYWORDS.items():
        for kw in keywords:
            if re.search(rf"\b{re.escape(kw)}", lower_titles):
                if field_name not in found:
                    found.append(field_name)
                break
    return found
