"""Tests für catalog_lint.py (Katalog-Qualitätsgate)."""

from __future__ import annotations

import pytest

import json
import sys
from datetime import date, timedelta

import catalog_lint as cl

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
    "frist": None,
    "rolling": False,
    "budget_min": None,
    "budget_max": None,
    "hinweis": "Test-Hinweis.",
}

TODAY = date(2026, 9, 1)


def _rules(programmes, **kw) -> set[str]:
    return {f.rule for f in cl.lint_catalog(programmes, TODAY, **kw)}


def _findings(programmes) -> list[cl.Finding]:
    return cl.lint_catalog(programmes, TODAY)


class TestHardRules:
    def test_sauber_keine_befunde(self):
        assert _rules([dict(VOLL)]) == set()

    def test_id_fehlt(self):
        assert "id-fehlt" in _rules([{k: v for k, v in VOLL.items() if k != "id"}])

    def test_name_fehlt(self):
        assert "name-fehlt" in _rules([{**VOLL, "name": ""}])

    def test_kategorie_ungueltig(self):
        assert "kategorie-ungueltig" in _rules([{**VOLL, "kategorie": "Mars"}])

    def test_status_ungueltig(self):
        assert "status-ungueltig" in _rules([{**VOLL, "status": "kaputt"}])

    def test_frist_ungueltig(self):
        assert "frist-ungueltig" in _rules([{**VOLL, "frist": "bald"}])

    def test_hinweis_fehlt(self):
        assert "hinweis-fehlt" in _rules([{**VOLL, "hinweis": ""}])

    def test_budget_null_statt_0(self):
        assert "budget-null-statt-0" in _rules([{**VOLL, "budget_max": 0}])

    def test_rolling_mit_frist(self):
        assert "rolling-mit-frist" in _rules([{**VOLL, "rolling": True, "frist": "2027-01-01"}])

    def test_quelle_fehlt(self):
        assert "quelle-fehlt" in _rules([{**VOLL, "quelle": ""}])

    def test_duplicate_ids(self):
        assert "duplicate-ids" in _rules([dict(VOLL), dict(VOLL)])


class TestWarnRules:
    def test_frist_abgelaufen(self):
        f = _findings([{**VOLL, "frist": (TODAY - timedelta(days=3)).isoformat()}])
        assert any(x.rule == "frist-abgelaufen" and x.severity == "warn" for x in f)

    def test_zukuenftige_frist_kein_warn(self):
        assert not any(x.rule == "frist-abgelaufen"
                       for x in _findings([{**VOLL, "frist": (TODAY + timedelta(days=10)).isoformat()}]))

    def test_stand_datum_alt_verifiziert(self):
        f = _findings([{**VOLL, "status": "verifiziert",
                        "standDatum": (TODAY - timedelta(days=90)).isoformat()}])
        assert any(x.rule == "stand-datum-alt" and x.severity == "warn" for x in f)

    def test_stand_datum_frisch_kein_warn(self):
        f = _findings([{**VOLL, "status": "verifiziert", "standDatum": TODAY.isoformat()}])
        assert not any(x.rule == "stand-datum-alt" for x in f)

    def test_stand_datum_alt_nur_verifiziert(self):
        # Nicht-verifizierte Einträge bekommen kein stand-datum-alt
        f = _findings([{**VOLL, "status": "zu-pruefen",
                        "standDatum": (TODAY - timedelta(days=200)).isoformat()}])
        assert not any(x.rule == "stand-datum-alt" for x in f)


class TestBuildReport:
    def test_clean(self):
        r = cl.build_report([], 10, TODAY)
        assert r["ergebnis"] == "clean"
        assert r["counts"] == {"fail": 0, "warn": 0}
        assert r["geprueft"] == 10

    def test_warn(self):
        w = [cl.Finding("x", "frist-abgelaufen", "warn", "msg")]
        r = cl.build_report(w, 1, TODAY)
        assert r["ergebnis"] == "warn"
        assert r["counts"]["warn"] == 1

    def test_problems(self):
        f = [cl.Finding("x", "hinweis-fehlt", "fail", "msg")]
        r = cl.build_report(f, 1, TODAY)
        assert r["ergebnis"] == "problems"
        assert r["counts"]["fail"] == 1

    def test_findings_serialisierbar(self):
        r = cl.build_report([cl.Finding("x", "hinweis-fehlt", "fail", "msg")], 1, TODAY)
        json.dumps(r)  # kein Fehler


class TestMain:
    def test_main_bericht_und_fail_exit(self, tmp_path, monkeypatch):
        cat = tmp_path / "catalog.json"
        cat.write_text(json.dumps({"programme": [{**VOLL, "hinweis": ""}]}), encoding="utf-8")
        out = tmp_path / "lint.json"
        monkeypatch.setattr(sys, "argv",
                            ["catalog_lint", "--catalog", str(cat), "--report", str(out), "--fail"])
        with pytest.raises(SystemExit) as ex:
            cl.main()
        assert ex.value.code == 1
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["ergebnis"] == "problems"
        assert data["counts"]["fail"] >= 1

    def test_main_ohne_fail_exit_0(self, tmp_path, monkeypatch):
        cat = tmp_path / "catalog.json"
        cat.write_text(json.dumps({"programme": [dict(VOLL)]}), encoding="utf-8")
        monkeypatch.setattr(sys, "argv", ["catalog_lint", "--catalog", str(cat)])
        cl.main()  # kein SystemExit
