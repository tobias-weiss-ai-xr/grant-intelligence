"""Tests für die type-safe Datenmodelle (grant_types.py)."""

from __future__ import annotations

from datetime import date

import pytest

from grant_types import (
    Karrierestufe,
    Programm,
    Status,
    budget_beschreibung,
    parse_frist,
)

VOLL = {
    "id": "test-1",
    "name": "Testprogramm",
    "kategorie": "DFG",
    "themen": ["frei"],
    "karriere": ["postdoc"],
    "rolle": ["lead"],
    "budget_max": 1_500_000,
    "frist": "2027-01-15",
    "rolling": False,
    "status": "verifiziert",
    "quelle": "https://example.org",
    "standDatum": "2026-08-03",
    "dauerJahre": 3,
}


class TestParseFrist:
    def test_gueltig(self):
        assert parse_frist("2027-01-15") == date(2027, 1, 15)

    def test_none(self):
        assert parse_frist(None) is None

    def test_leer(self):
        assert parse_frist("") is None

    def test_ungueltig(self):
        assert parse_frist("bald") is None
        assert parse_frist("15.01.2027") is None


class TestBudget:
    def test_mio(self):
        assert "Mio" in budget_beschreibung(1_500_000)

    def test_tausend(self):
        assert "Tausend" in budget_beschreibung(250_000)

    def test_none(self):
        assert budget_beschreibung(None) == ""

    def test_null(self):
        assert budget_beschreibung(0) == ""


class TestEnums:
    def test_status_is_valid(self):
        assert Status.is_valid("verifiziert")
        assert Status.is_valid("laufend")
        assert Status.is_valid("zu-pruefen")
        assert not Status.is_valid("kaputt")

    def test_karriere_is_valid(self):
        assert Karrierestufe.is_valid("postdoc")
        assert Karrierestufe.is_valid(None)
        assert not Karrierestufe.is_valid("abgelehnt")


class TestProgramm:
    def test_roundtrip_camelcase(self):
        p = Programm.from_dict(VOLL)
        assert p.stand_datum == "2026-08-03"
        assert p.dauer_jahre == 3
        back = p.to_dict()
        assert back["standDatum"] == "2026-08-03"
        assert back["dauerJahre"] == 3
        assert back["id"] == "test-1"

    def test_fehlende_pflichtfelder(self):
        with pytest.raises(ValueError):
            Programm.from_dict({**VOLL, "id": ""})

    def test_ungueltiger_status(self):
        with pytest.raises(ValueError):
            Programm.from_dict({**VOLL, "status": "kaputt"})

    def test_ungueltige_frist(self):
        with pytest.raises(ValueError):
            Programm.from_dict({**VOLL, "frist": "bald"})

    def test_days_until_deadline(self):
        p = Programm.from_dict({**VOLL, "frist": date.today().isoformat()})
        assert p.days_until_deadline == 0

    def test_rolling_keine_frist(self):
        p = Programm.from_dict({**VOLL, "rolling": True, "frist": None})
        assert p.days_until_deadline is None
        assert not p.is_expired
        assert not p.is_urgent()

    def test_is_expired(self):
        p = Programm.from_dict({**VOLL, "frist": "2020-01-01"})
        assert p.is_expired

    def test_is_urgent(self):
        p = Programm.from_dict({**VOLL, "frist": date.today().isoformat()})
        assert p.is_urgent(days=5)
        assert not p.is_urgent(days=-1)

    def test_budget_text_property(self):
        p = Programm.from_dict({**VOLL, "budget_max": 500_000})
        assert "Tausend" in p.budget_text
