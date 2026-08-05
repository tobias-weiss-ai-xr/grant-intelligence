"""Tests für update_catalog.py (Update-Pipeline, Validierung, Merge)."""

from __future__ import annotations

from datetime import date, timedelta

import update_catalog as uc

VOLL = {
    "id": "test-1",
    "name": "Testprogramm",
    "kategorie": "DFG",
    "themen": ["frei"],
    "karriere": ["postdoc"],
    "rolle": ["lead"],
    "quelle": "https://example.org",
    "standDatum": "2026-08-03",
    "status": "zu-pruefen",
    "frist": "2027-01-15",
}


class TestValidate:
    def test_gueltig(self):
        assert uc.validate_programme(VOLL) == []

    def test_fehlt_id(self):
        errs = uc.validate_programme({k: v for k, v in VOLL.items() if k != "id"})
        assert any("Fehlt: id" in e for e in errs)

    def test_ungueltige_frist(self):
        errs = uc.validate_programme({**VOLL, "frist": "bald"})
        assert any("frist" in e for e in errs)

    def test_ungueltiger_status(self):
        errs = uc.validate_programme({**VOLL, "status": "kaputt"})
        assert errs

    def test_ungueltige_karriere(self):
        errs = uc.validate_programme({**VOLL, "karriere": ["abgelehnt"]})
        assert not errs  # karriere-Werte sind freie Liste; nur Pflichtfelder


class TestCheckExpired:
    def test_abgelaufene_frist(self):
        p = [{**VOLL, "frist": (date.today() - timedelta(days=3)).isoformat()}]
        expired = uc.check_expired(p, date.today())
        assert len(expired) == 1
        assert expired[0]["tage_abgelaufen"] == 3

    def test_rolling_ignoriert(self):
        p = [{**VOLL, "rolling": True, "frist": "2020-01-01"}]
        assert uc.check_expired(p, date.today()) == []

    def test_zukuenftige_frist(self):
        p = [{**VOLL, "frist": (date.today() + timedelta(days=10)).isoformat()}]
        assert uc.check_expired(p, date.today()) == []

    def test_kaputte_frist_kein_crash(self):
        assert uc.check_expired([{**VOLL, "frist": "bald"}], date.today()) == []


class TestMerge:
    def test_neu_und_update(self):
        existing = [dict(VOLL)]
        neu = [dict(VOLL), {**VOLL, "id": "test-2", "name": "Zweites"}]
        merged, added, updated = uc.merge_programmes(neu, existing)
        assert added == 1 and updated == 1
        assert len(merged) == 2

    def test_ohne_id_uebersprungen(self):
        existing: list[dict] = []
        merged, added, updated = uc.merge_programmes([{"name": "kein id"}], existing)
        assert added == 0 and updated == 0 and merged == []


class TestUpdateStand:
    def test_setzt_heute(self):
        p = uc.update_stand_datum([dict(VOLL)])
        assert p[0]["standDatum"] == date.today().isoformat()
