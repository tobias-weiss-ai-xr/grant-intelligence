"""Tests für deadline_digest.py (Frist-Digest + Deduplizierung)."""

from __future__ import annotations

import json
import sys
from datetime import date, timedelta

import deadline_digest as dd

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

TODAY = date(2026, 9, 1)


def _iso(days: int) -> str:
    """ISO-Datum relativ zu TODAY in Tagen (negativ = in der Vergangenheit)."""
    return (TODAY + timedelta(days=days)).isoformat()


class TestComputeDigest:
    def test_urgent_innerhalb_fenster(self):
        d = dd.compute_digest([{**VOLL, "id": "u1", "frist": _iso(10)}], TODAY)
        assert d["counts"] == {"urgent": 1, "upcoming": 1, "expired": 0, "rolling": 0}
        assert d["urgent"][0]["id"] == "u1"
        assert d["urgent"][0]["tage_bis_frist"] == 10
        assert d["upcoming"][0]["tage_bis_frist"] == 10

    def test_upcoming_ausserhalb_urgent(self):
        d = dd.compute_digest([{**VOLL, "id": "u2", "frist": _iso(60)}], TODAY)
        assert d["counts"]["urgent"] == 0
        assert d["counts"]["upcoming"] == 1

    def test_abgelaufen(self):
        d = dd.compute_digest([{**VOLL, "id": "e1", "frist": _iso(-5)}], TODAY)
        assert d["counts"]["expired"] == 1
        assert d["counts"]["upcoming"] == 0
        assert d["expired"][0]["tage_bis_frist"] == -5

    def test_rolling_zaehlt_nicht_als_frist(self):
        d = dd.compute_digest([{**VOLL, "id": "r1", "rolling": True, "frist": "2020-01-01"}], TODAY)
        assert d["counts"]["rolling"] == 1
        assert d["counts"]["urgent"] == 0
        assert d["counts"]["expired"] == 0

    def test_keine_frist(self):
        d = dd.compute_digest([{**VOLL, "id": "n1", "frist": None}], TODAY)
        assert d["counts"] == {"urgent": 0, "upcoming": 0, "expired": 0, "rolling": 0}

    def test_kaputte_frist_kein_crash(self):
        d = dd.compute_digest([{**VOLL, "id": "k1", "frist": "bald"}], TODAY)
        assert d["counts"]["urgent"] == 0
        assert d["counts"]["upcoming"] == 0
        assert d["counts"]["expired"] == 0

    def test_sortierung_urgent_aufsteigend(self):
        d = dd.compute_digest(
            [
                {**VOLL, "id": "b", "frist": _iso(20)},
                {**VOLL, "id": "a", "frist": _iso(5)},
            ],
            TODAY,
        )
        assert [e["id"] for e in d["urgent"]] == ["a", "b"]

    def test_frist_genau_heute_ist_urgent(self):
        d = dd.compute_digest([{**VOLL, "id": "t", "frist": TODAY.isoformat()}], TODAY)
        assert d["counts"]["urgent"] == 1
        assert d["urgent"][0]["tage_bis_frist"] == 0

    def test_frist_genau_urgent_grenze_inklusiv(self):
        d = dd.compute_digest([{**VOLL, "id": "g", "frist": _iso(30)}], TODAY, urgent_days=30)
        assert d["counts"]["urgent"] == 1

    def test_frist_ein_tag_ueber_urgent(self):
        d = dd.compute_digest([{**VOLL, "id": "o", "frist": _iso(31)}], TODAY, urgent_days=30, upcoming_days=90)
        assert d["counts"]["urgent"] == 0
        assert d["counts"]["upcoming"] == 1

    def test_eintrag_felder(self):
        d = dd.compute_digest([{**VOLL, "id": "x", "frist": _iso(10)}], TODAY)
        e = d["urgent"][0]
        assert e["id"] == "x"
        assert e["name"] == "Testprogramm"
        assert e["kategorie"] == "DFG"
        assert e["frist"] == _iso(10)
        assert e["status"] == "zu-pruefen"
        assert e["quelle"] == "https://example.org"
        assert e["rolling"] is False


class TestDiffUrgent:
    def test_erster_lauf_alle_neu(self):
        new = {"urgent": [{"id": "a"}, {"id": "b"}]}
        assert [e["id"] for e in dd.diff_urgent(new, None)] == ["a", "b"]

    def test_keine_neuen(self):
        old = {"urgent": [{"id": "a"}, {"id": "b"}]}
        new = {"urgent": [{"id": "a"}, {"id": "b"}]}
        assert dd.diff_urgent(new, old) == []

    def test_neu_dazu(self):
        old = {"urgent": [{"id": "a"}]}
        new = {"urgent": [{"id": "a"}, {"id": "c"}]}
        assert [e["id"] for e in dd.diff_urgent(new, old)] == ["c"]

    def test_abgelaufen_nicht_mehr_neu(self):
        # Wenn ein zuvor dringendes Programm abgelaufen ist (nicht mehr in
        # urgent), ist es KEINE neue dringende Frist.
        old = {"urgent": [{"id": "a"}]}
        new = {"urgent": []}
        assert dd.diff_urgent(new, old) == []


class TestSaveLoad:
    def test_save_load_roundtrip(self, tmp_path):
        d = dd.compute_digest([{**VOLL, "id": "x", "frist": _iso(10)}], TODAY)
        p = tmp_path / "digest.json"
        dd.save_digest(d, p)
        loaded = dd.load_digest(p)
        assert loaded is not None
        assert loaded["counts"]["urgent"] == 1
        assert loaded["stand"] == TODAY.isoformat()

    def test_load_fehlend(self, tmp_path):
        assert dd.load_digest(tmp_path / "gibt-es-nicht.json") is None

    def test_load_kaputt(self, tmp_path):
        p = tmp_path / "bad.json"
        p.write_text("{not json", encoding="utf-8")
        assert dd.load_digest(p) is None

    def test_load_kein_dict(self, tmp_path):
        p = tmp_path / "arr.json"
        p.write_text("[1,2,3]", encoding="utf-8")
        assert dd.load_digest(p) is None


class _FixedDate:
    """Fixe date.today() für CLI-Tests."""

    @classmethod
    def today(cls) -> date:
        return TODAY


class TestMain:
    def _write_catalog(self, tmp_path, programmes) -> None:
        cat = tmp_path / "catalog.json"
        cat.write_text(json.dumps({"programme": programmes}), encoding="utf-8")

    def test_main_schreibt_digest(self, tmp_path, monkeypatch, capsys):
        self._write_catalog(tmp_path, [{**VOLL, "id": "u1", "frist": _iso(10)}])
        out = tmp_path / "digest.json"
        monkeypatch.setattr(dd, "date", _FixedDate)
        monkeypatch.setattr(
            sys, "argv", ["deadline_digest", "--catalog", str(tmp_path / "catalog.json"),
                          "--out", str(out)]
        )
        dd.main()
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["counts"]["urgent"] == 1
        assert data["neu_urgent"] == 1  # erster Lauf: alle dringenden sind neu
        captured = capsys.readouterr()
        assert "NEUE dringende" in captured.out

    def test_main_dedup_zweiter_lauf(self, tmp_path, monkeypatch, capsys):
        self._write_catalog(tmp_path, [{**VOLL, "id": "u1", "frist": _iso(10)}])
        out = tmp_path / "digest.json"
        monkeypatch.setattr(dd, "date", _FixedDate)
        argv = lambda: ["deadline_digest", "--catalog", str(tmp_path / "catalog.json"),
                        "--out", str(out)]
        monkeypatch.setattr(sys, "argv", argv())
        dd.main()
        monkeypatch.setattr(sys, "argv", argv())
        dd.main()  # zweiter Lauf: gleiche dringende Frist → keine neuen
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["neu_urgent"] == 0
        captured = capsys.readouterr()
        assert "Keine neuen dringenden Fristen" in captured.out

    def test_main_check_schreibt_nicht(self, tmp_path, monkeypatch):
        self._write_catalog(tmp_path, [{**VOLL, "id": "u1", "frist": _iso(10)}])
        out = tmp_path / "digest.json"
        monkeypatch.setattr(dd, "date", _FixedDate)
        monkeypatch.setattr(
            sys, "argv", ["deadline_digest", "--catalog", str(tmp_path / "catalog.json"),
                          "--out", str(out), "--check"]
        )
        dd.main()
        assert not out.exists()

    def test_main_nationale_zahl(self, tmp_path, monkeypatch):
        d = dd.compute_digest([{**VOLL, "id": "n", "frist": _iso(10)}], TODAY)
        assert d["stand"] == "2026-09-01"


class TestIssueBody:
    def test_render_body_zeilen(self, tmp_path):
        digest = {
            "stand": "2026-08-29",
            "neu_urgent": 2,
            "urgent": [
                {"id": "a", "name": "Alpha", "kategorie": "DFG",
                 "frist": "2026-09-01", "tage_bis_frist": 3, "status": "zu-pruefen"},
                {"id": "b", "name": "Beta", "kategorie": "EU",
                 "frist": "2026-09-10", "tage_bis_frist": 12, "status": "verifiziert"},
            ],
        }
        body = dd.render_body(digest)
        assert "## 🔴 Neue dringende Fristen" in body
        assert "| a | Alpha | DFG | 2026-09-01 | 3 | zu-pruefen |" in body
        assert "| b | Beta | EU | 2026-09-10 | 12 | verifiziert |" in body
        assert "_Stand: 2026-08-29" in body

    def test_render_body_leer(self):
        body = dd.render_body({"urgent": [], "stand": "x"})
        # Tabelle bleibt (Header), aber keine Datenzeilen
        assert "|---|---|" in body


# --- Import des Issue-Body-Skripts (nutzt dd.render) ---
from pathlib import Path as _P

_SCRIPT = _P(__file__).resolve().parents[1] / ".github/scripts/deadline_issue_body.py"
if _SCRIPT.exists():
    import importlib.util as _ilu

    _spec = _ilu.spec_from_file_location("deadline_issue_body", _SCRIPT)
    _mod = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)  # type: ignore[union-attr]

    class TestBodyScript:
        def test_render_body_datei(self, tmp_path, monkeypatch):
            d = {"stand": "2026-08-29", "neu_urgent": 1,
                 "urgent": [{"id": "a", "name": "A", "kategorie": "DFG",
                             "frist": "2026-09-01", "tage_bis_frist": 3,
                             "status": "zu-pruefen"}]}
            out = tmp_path / "body.md"
            monkeypatch.setattr(_mod, "DIGEST", tmp_path / "no-digest.json")
            # render() direkt testen (Datei-Schreibpfad ist in CI relevant,
            # hier offline ohne Digest-Datei)
            out.write_text(dd.render_body(d), encoding="utf-8")
            assert "| a | A | DFG | 2026-09-01 | 3 | zu-pruefen |" in out.read_text(encoding="utf-8")
