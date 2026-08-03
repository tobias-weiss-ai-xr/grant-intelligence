"""Förder-Radar – Type definitions and data models.

Type hints and Pydantic models for consistent data validation across the codebase.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Any


class Status(Enum):
    """Programm-Verifikationsstatus."""
    VERIFIZIERT = "verifiziert"
    LAUFEND = "laufend"
    ZU_PRUEFEN = "zu-pruefen"


class Kategorie(Enum):
    """Förder-Kategorien."""
    DFG = "DFG"
    ERC = "ERC"
    BMBF = "BMBF"
    EU = "EU"
    LAND = "Land"
    STIFTUNG = "Stiftung"
    INDUSTRIE = "Industrie"


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


@dataclass
class Programm:
    """Ein Förderprogramm im Katalog."""
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
        """Validate required fields."""
        if not self.id:
            raise ValueError("Programm.id is required")
        if not self.name:
            raise ValueError("Programm.name is required")
        if not self.kategorie:
            raise ValueError("Programm.kategorie is required")
        if not self.themen:
            raise ValueError("Programm.themen is required")
        if not self.karriere:
            raise ValueError("Programm.karriere is required")
        if not self.rolle:
            raise ValueError("Programm.rolle is required")

    @property
    def budget_text(self) -> str:
        """Human-readable budget range."""
        if self.budget_max is None:
            return ""
        if self.budget_max >= 1_000_000:
            return f"bis ca. {self.budget_max / 1_000_000:.1f} Mio. Euro"
        return f"bis ca. {self.budget_max / 1_000:.0f} Tausend Euro"

    @property
    def days_until_deadline(self) -> int | None:
        """Days until deadline (None if rolling or no date)."""
        if self.rolling or not self.frist:
            return None
        try:
            deadline = date.fromisoformat(self.frist)
            return (deadline - date.today()).days
        except ValueError:
            return None

    @property
    def is_expired(self) -> bool:
        """Check if deadline has passed."""
        days = self.days_until_deadline
        return days is not None and days < 0

    @property
    def is_urgent(self, days: int = 60) -> bool:
        """Check if deadline is within `days` days."""
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
