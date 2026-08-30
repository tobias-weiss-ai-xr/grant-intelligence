"""Förder-Radar – Type definitions and data models.

Type hints and dataclass models for consistent data validation across the codebase.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from enum import Enum
from typing import Any


class Status(Enum):
    """Programm-Verifikationsstatus."""

    VERIFIZIERT = "verifiziert"
    LAUFEND = "laufend"
    ZU_PRUEFEN = "zu-pruefen"

    @classmethod
    def is_valid(cls, value: str | None) -> bool:
        """Check whether a string is a known status value.

        Args:
            value: Status string or None.

        Returns:
            True if value is a known status value.
        """
        return value in cls._value2member_map_


class Kategorie(Enum):
    """Förder-Kategorien."""

    DFG = "DFG"
    ERC = "ERC"
    BMBF = "BMBF"
    EU = "EU"
    LAND = "Land"
    STIFTUNG = "Stiftung"
    INDUSTRIE = "Industrie"
    BUND = "Bund"
    INTERNATIONAL = "International"

    @classmethod
    def is_valid(cls, value: str | None) -> bool:
        """Check whether a string is a known category.

        Args:
            value: Category string or None.

        Returns:
            True if value is a known category value.
        """
        return value in cls._value2member_map_


class Karrierestufe(Enum):
    """Ziel-Karrierestufen."""

    POSTDOC = "postdoc"
    JUNIOR = "junior"
    PROF = "prof"
    SENIOR = "senior"
    STUDENT = "student"
    VERWALTUNG = "verwaltung"
    SERVICE = "service"
    IT = "IT"
    BIBLIOTHEK = "bibliothek"

    @classmethod
    def is_valid(cls, value: str | None) -> bool:
        """Check whether a string is a known career level.

        Args:
            value: Career level string (e.g. "postdoc") or None.

        Returns:
            True if value is None or a known career level.
        """
        return value is None or value in cls._value2member_map_


# ---------------------------------------------------------------------------
# Gemeinsame Helfer (Single Source of Truth)
# ---------------------------------------------------------------------------


def parse_frist(frist: str | None) -> date | None:
    """Parse an ISO 8601 date string (YYYY-MM-DD) safely.

    Central helper replacing ad-hoc ``strptime`` calls across modules.

    Args:
        frist: ISO 8601 date string or None.

    Returns:
        ``date`` object, or None if missing/invalid.
    """
    if not frist:
        return None
    try:
        return date.fromisoformat(frist)
    except ValueError:
        return None


def budget_beschreibung(budget_max: int | None) -> str:
    """Human-readable budget description from maximum budget.

    Args:
        budget_max: Maximum budget in Euro, or None.

    Returns:
        German description ("bis ca. 1.5 Mio. Euro"), empty if unknown.
    """
    if not budget_max:
        return ""
    if budget_max >= 1_000_000:
        return f"bis ca. {budget_max / 1_000_000:.1f} Mio. Euro"
    return f"bis ca. {budget_max / 1_000:.0f} Tausend Euro"


_KATALOG_KEY_MAP: dict[str, str] = {
    "standDatum": "stand_datum",
    "dauerJahre": "dauer_jahre",
}
"""Mapping from catalog (camelCase) keys to dataclass fields."""

_REVERSE_KEY_MAP = {v: k for k, v in _KATALOG_KEY_MAP.items()}


@dataclass
class Programm:
    """Ein Förderprogramm im Katalog.

    Validates required fields on construction. Use :meth:`from_dict` /
    :meth:`to_dict` to convert between the catalog's camelCase JSON format
    and this type-safe representation.
    """

    id: str
    name: str
    kategorie: str
    themen: list[str]
    karriere: list[str]
    rolle: list[str]
    budget_min: int | None = None
    budget_max: int | None = None
    dauer_jahre: int | None = None
    frist: str | None = None  # ISO 8601 date (YYYY-MM-DD)
    rolling: bool = False
    status: str = "zu-pruefen"
    quelle: str = ""
    stand_datum: str = ""
    hinweis: str = ""

    def __post_init__(self) -> None:
        """Validate required fields and enum membership.

        Only id, name, and kategorie are hard requirements.
        Empty themen/karriere/rolle lists are allowed (means "open to all").
        """
        missing = [
            label
            for label, value in (
                ("id", self.id),
                ("name", self.name),
                ("kategorie", self.kategorie),
            )
            if not value
        ]
        if missing:
            raise ValueError(f"Programm fehlen Pflichtfelder: {', '.join(missing)}")
        if not Status.is_valid(self.status):
            raise ValueError(f"Ungültiger status: {self.status}")
        if self.frist and parse_frist(self.frist) is None:
            raise ValueError(f"Ungültiges frist-Format: {self.frist}")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Programm:
        """Build a Programm from a catalog dict (camelCase keys).

        Args:
            data: Catalog programme dictionary.

        Returns:
            Validated Programm instance.

        Raises:
            ValueError: If required fields are missing or values are invalid.
        """
        mapped = {_KATALOG_KEY_MAP.get(k, k): v for k, v in data.items()}
        return cls(**mapped)

    def to_dict(self) -> dict[str, Any]:
        """Serialize back to catalog format (camelCase keys).

        Returns:
            Dictionary compatible with catalog.json entries.
        """
        data = asdict(self)
        return {_REVERSE_KEY_MAP.get(k, k): v for k, v in data.items()}

    @property
    def budget_text(self) -> str:
        """Human-readable budget range."""
        return budget_beschreibung(self.budget_max)

    @property
    def days_until_deadline(self) -> int | None:
        """Days until deadline (None if rolling or no date)."""
        if self.rolling or not self.frist:
            return None
        deadline = parse_frist(self.frist)
        if deadline is None:
            return None
        return (deadline - date.today()).days

    @property
    def is_expired(self) -> bool:
        """Check if deadline has passed."""
        days = self.days_until_deadline
        return days is not None and days < 0

    def is_urgent(self, days: int = 60) -> bool:
        """Check if deadline is within `days` days (parameterized, not a property).

        Args:
            days: Warning window in days.

        Returns:
            True if a deadline exists and is within `days` days.
        """
        deadline_days = self.days_until_deadline
        if deadline_days is None:
            return False
        return 0 <= deadline_days <= days


@dataclass
class MatchResult:
    """Ergebnis eines Matching-Vorgangs."""

    id: str
    name: str
    kategorie: str
    score: int
    frist: str | None
    rolling: bool
    status: str
    quelle: str
    stand_datum: str
    begruendung: str
    tage_bis_frist: int | None = None
    # Strukturierte Punkte-Aufschlüsselung (Transparenz, additiv):
    # [{"name": "Thema", "punkte": 2, "max": 3, "detail": ...}, ...]
    punkte: list[dict[str, Any]] | None = None


@dataclass
class BriefResult:
    """Ergebnis eines Wochen-Briefs."""

    top_matches: list[MatchResult]
    naechste_frist: MatchResult | None
    warnungen: list[MatchResult]


@dataclass
class CatalogMetadata:
    """Katalog-Metadaten."""

    stand: str
    quelle_hinweis: str = """
Kuratierter Katalog. status = verifiziert (live geprüft am standDatum) |
laufend (keine Frist, rolling) | zu-pruefen (bekanntes Programm, Frist vor
Nutzung gegen Portal prüfen). Keine rechtliche Bindung; für produktive
Nutzung gegen offizielle Stellen prüfen.
""".strip()
