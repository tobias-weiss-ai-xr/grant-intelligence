"""Förder-Radar – Tests (pytest). Lauf:  python -m pytest test_mvp.py -q

Abdeckung: Katalog-Integrität, Matching (inkl. harter Karriere-Filter),
Fristen, Persistenz, MCP-Tools, UI-Rendering, Wochen-Brief.
"""
from __future__ import annotations

from datetime import date, datetime

import pytest

from match import (CATALOG, load_catalog, save_catalog, match_profile,
                   next_deadline, _frist_text, _begruendung)
import server
import app as appmod
import brief as briefmod

PROGS = load_catalog()
POSTDOC = ["Biologie", "Nachhaltigkeit"]

# Schutz: echte catalog.json darf durch Tests nie veraendert werden
_KATALOG_SNAPSHOT = CATALOG.read_bytes()
_REAL_CATALOG = CATALOG  # Original-Pfad vor jedem Monkeypatch


@pytest.fixture(autouse=True, scope="session")
def _katalog_schutz():
    """Prueft nach der ganzen Session: catalog.json unveraendert?"""
    yield
    assert CATALOG.read_bytes() == _KATALOG_SNAPSHOT, \
        "FEHLER: catalog.json wurde durch Tests veraendert!"


# --------------------------------------------------------------- Katalog-Integrität
class TestKatalog:
    def test_alle_pflichtfelder(self):
        for p in PROGS:
            for k in ("id", "name", "kategorie", "themen", "karriere", "rolle",
                      "quelle", "standDatum", "status"):
                assert k in p, f"{p.get('id')} fehlt: {k}"

    def test_ids_eindeutig(self):
        ids = [p["id"] for p in PROGS]
        assert len(ids) == len(set(ids))

    def test_status_werte(self):
        for p in PROGS:
            assert p["status"] in ("verifiziert", "laufend", "zu-pruefen"), p["id"]

    def test_daten_formate(self):
        for p in PROGS:
            if p.get("frist"):
                datetime.strptime(p["frist"], "%Y-%m-%d")
            datetime.strptime(p["standDatum"], "%Y-%m-%d")
            assert isinstance(p["themen"], list) and p["themen"]
            assert isinstance(p["karriere"], list) and p["karriere"]

    def test_laufend_ist_rolling(self):
        for p in PROGS:
            if p["status"] == "laufend":
                assert p.get("rolling") is True, p["id"]

    def test_verifiziert_hat_frist(self):
        for p in PROGS:
            if p["status"] == "verifiziert":
                assert p.get("frist"), f"verifiziert ohne Frist: {p['id']}"


# ----------------------------------------------------------------------- Matching
class TestMatch:
    def test_karriere_harter_filter(self):
        # Emmy Noether nur postdoc -> darf bei prof nicht erscheinen
        r = match_profile(PROGS, ["Biologie"], "prof", top=10)
        assert all(x.id != "dfg-emmy-noether" for x in r)

    def test_karriere_filter_laesst_passende_durch(self):
        r = match_profile(PROGS, ["Biologie"], "postdoc", top=10)
        assert any(x.id == "dfg-emmy-noether" for x in r)

    def test_frei_passt_immer(self):
        r = match_profile(PROGS, ["Gartenbau", "Quantenphysik"], "postdoc", top=10)
        assert any(x.id == "erc-stg-2027" for x in r)  # themen frei

    def test_leere_felder_keine_treffer(self):
        assert match_profile(PROGS, [], "postdoc") == []

    def test_unbekannte_karriere_kein_crash(self):
        # Völlig unbekannte Karrierestufe -> harter Filter, kein Match, kein Crash
        assert match_profile(PROGS, ["Biologie"], "abgelehnt") == []

    def test_top_limit(self):
        assert len(match_profile(PROGS, ["Biologie"], "postdoc", top=2)) == 2

    def test_rolle_filter(self):
        # StG erlaubt nur lead -> bei rolle=partner ausgeschlossen
        r = match_profile(PROGS, POSTDOC, "postdoc", rolle="partner", top=10)
        assert all(x.id != "erc-stg-2027" for x in r)
        # Sachbeihilfe (lead+partner) bleibt
        assert any(x.id == "dfg-sachbeihilfe" for x in r)

    def test_score_range(self):
        for r in match_profile(PROGS, POSTDOC, "postdoc", top=10):
            assert 1 <= r.score <= 5
            assert r.begruendung

    def test_sortierung_score_dann_frist(self):
        r = match_profile(PROGS, POSTDOC, "postdoc", top=10)
        scores = [x.score for x in r]
        assert scores == sorted(scores, reverse=True)

    def test_unbekanntes_feld_trifft_freie_programme(self):
        # ERC ist themenfrei -> auch exotische Felder matchen (ehrlich, kein Bug)
        r = match_profile(PROGS, ["Astroteilchenphysik"], "postdoc", top=10)
        assert any(x.id == "erc-stg-2027" for x in r)

    def test_kein_fehler_bei_kein_match(self):
        # Völlig unbekannte Karrierestufe -> harter Filter, kein Match, kein Crash
        assert match_profile(PROGS, ["Biologie"], "abgelehnt") == []
        assert next_deadline(PROGS, ["Biologie"], "abgelehnt") == []


# ----------------------------------------------------------------------- Fristen
class TestFristen:
    def test_tage_bis_frist(self):
        r = next_deadline(PROGS, POSTDOC, "postdoc", top=10)
        for x in r:
            if x.frist:
                d = datetime.strptime(x.frist, "%Y-%m-%d").date()
                assert x.tage_bis_frist == (d - date.today()).days

    def test_rolling_frist_none(self):
        r = next_deadline(PROGS, POSTDOC, "postdoc", top=10)
        rolling = [x for x in r if x.rolling]
        assert rolling and all(x.tage_bis_frist is None for x in rolling)

    def test_frist_text_abgelaufen(self):
        t = _frist_text("2020-01-01", False)
        assert "abgelaufen" in t

    def test_frist_text_rolling(self):
        assert "Rolling" in _frist_text(None, True)

    def test_frist_text_kaputt(self):
        t = _frist_text("bald", False)
        assert "prüfen" in t

    def test_begruendung_felder_und_karriere(self):
        p = next(p for p in PROGS if p["id"] == "erc-stg-2027")
        b = _begruendung(p, {"felder": ["Biologie"], "karriere": 1}, 4)
        assert "Biologie" in b and "Karrierestufe passt" in b


# -------------------------------------------------------------------- Persistenz
class TestPersistenz:
    def test_save_roundtrip(self, tmp_path):
        path = tmp_path / "catalog.json"
        save_catalog(PROGS, path)
        back = load_catalog(path)
        assert len(back) == len(PROGS)
        assert back[0]["id"] == PROGS[0]["id"]

    def test_save_setzt_stand_neu(self, tmp_path):
        import json
        path = tmp_path / "catalog.json"
        save_catalog(PROGS, path)
        doc = json.loads(path.read_text(encoding="utf-8"))
        assert doc["stand"] == date.today().isoformat()

    def test_hauptkatalog_unveraendert_nach_tests(self):
        # Tests dürfen catalog.json nicht mutiert haben
        assert len(load_catalog()) == len(PROGS)
        assert CATALOG.read_bytes() == _KATALOG_SNAPSHOT


# ---------------------------------------------------------------------- MCP-Tools
class TestServer:
    def test_programs_filter(self):
        assert all(p["kategorie"] == "ERC" for p in server.programs("ERC"))
        assert len(server.programs()) == len(PROGS)

    def test_search_stichwort(self):
        r = server.search(stichwort="Starting")
        assert r and r[0]["id"] == "erc-stg-2027"

    def _tmp_umgebung(self, tmp_path, monkeypatch):
        """Katalog nach tmp verlegen UND server-PROGRAMME daraus neu laden."""
        import match as matchmod
        kat = tmp_path / "catalog.json"
        save_catalog(PROGS, kat)
        monkeypatch.setattr(matchmod, "CATALOG", kat)
        server.PROGRAMME[:] = load_catalog()
        return kat

    def test_ingest_persistiert(self, tmp_path, monkeypatch):
        kat = self._tmp_umgebung(tmp_path, monkeypatch)
        neu = {"id": "test-prog", "name": "Test", "kategorie": "DFG",
               "themen": ["frei"], "karriere": ["prof"], "rolle": ["lead"],
               "frist": None, "rolling": True, "status": "zu-pruefen",
               "quelle": "test", "standDatum": "2026-08-03"}
        res = server.ingest([neu])
        assert res["neu"] == 1
        assert any(x["id"] == "test-prog" for x in load_catalog(kat))
        # echte Datei unberuehrt (Original-Pfad, nicht der gemockte)
        assert not any(x["id"] == "test-prog" for x in load_catalog(_REAL_CATALOG))

    def test_ingest_ohne_id_wird_ignoriert(self):
        res = server.ingest([{"name": "kaputt"}])
        assert res["neu"] == 0

    def test_loeschen(self, monkeypatch, tmp_path):
        kat = self._tmp_umgebung(tmp_path, monkeypatch)
        res = server.loeschen("dfg-emmy-noether")
        assert res["entfernt"] == 1
        assert not any(x["id"] == "dfg-emmy-noether" for x in load_catalog(kat))
        assert any(x["id"] == "dfg-emmy-noether" for x in load_catalog(_REAL_CATALOG))  # echte Datei unberuehrt

    def test_notify_warnfenster(self):
        warn = server.notify(POSTDOC, "postdoc", tage=60)
        for w in warn:
            if w.get("tageBisFrist") is not None:
                assert w["tageBisFrist"] <= 60

    def test_notify_rolling_immer(self):
        warn = server.notify(POSTDOC, "postdoc", tage=0)
        assert any(w.get("rolling") for w in warn)

    def test_brief_ohne_match_kein_crash(self):
        # Völlig unbekannte Karrierestufe -> harter Filter, keine Treffer
        b = server.brief(["Biologie"], "abgelehnt")
        assert b["top_matches"] == []
        assert b["naechste_frist"] is None
        assert b["warnungen"] == []

    def test_brief_mit_match(self):
        b = server.brief(POSTDOC, "postdoc")
        assert b["top_matches"] and b["naechste_frist"]
        assert set(b) == {"top_matches", "naechste_frist", "warnungen"}


# --------------------------------------------------------------------------- UI
class TestApp:
    def test_index_enthaelt_formular(self):
        html = appmod.index()
        assert "form" in html and "felder" in html

    def test_brief_postdoc_vs_prof(self):
        html_pd = appmod.brief(felder="Biologie, Nachhaltigkeit", karriere="postdoc")
        html_pr = appmod.brief(felder="Medizin", karriere="prof")
        assert "Emmy Noether" in html_pd
        assert "Emmy Noether" not in html_pr

    def test_leere_felder_hinweis(self):
        html = appmod.brief(felder="", karriere="postdoc")
        assert "Keine Treffer" in html or "Felder" in html

    def test_html_escaping(self):
        # XSS-Schutz: Eingabe darf nicht roh in HTML landen
        html = appmod.brief(felder='<script>alert(1)</script>', karriere="postdoc")
        assert "<script>alert(1)</script>" not in html

    def test_karriere_optionen(self):
        html = appmod.index()
        for k in ("postdoc", "junior", "prof"):
            assert f'value="{k}"' in html

    def test_keine_doppelt_frist(self):
        html = appmod.brief(felder="Biologie", karriere="postdoc")
        assert "Frist: Frist" not in html


class TestAppHttp:
    """HTTP-Ebene: Browser-Formular-Verhalten inkl. leerer Eingaben."""

    @pytest.fixture(scope="class")
    def client(self):
        from fastapi.testclient import TestClient
        return TestClient(appmod.app)

    def test_get_index(self, client):
        r = client.get("/")
        assert r.status_code == 200
        assert "Förder-Radar" in r.text

    def test_post_normal(self, client):
        r = client.post("/brief", data={"felder": "Biologie, Nachhaltigkeit", "karriere": "postdoc"})
        assert r.status_code == 200
        assert "Emmy Noether" in r.text

    def test_post_leeres_feld_kein_422(self, client):
        # Browser sendet leere Inputs als felder= -> freundliche Meldung, kein Fehler
        r = client.post("/brief", data={"felder": "", "karriere": "postdoc"})
        assert r.status_code == 200
        assert "Keine Treffer" in r.text

    def test_post_fehlt_feld_kein_422(self, client):
        r = client.post("/brief", data={"karriere": "postdoc"})
        assert r.status_code == 200

    def test_post_xss_escaped(self, client):
        r = client.post("/brief", data={"felder": "<script>x</script>", "karriere": "postdoc"})
        assert r.status_code == 200
        assert "<script>x</script>" not in r.text

    def test_post_unbekannte_karriere_whitelist(self, client):
        # 'abgelehnt' ist keine gueltige Karrierestufe -> Whitelist greift
        r = client.post("/brief", data={"felder": "Biologie", "karriere": "abgelehnt"})
        assert r.status_code == 200
        assert 'value="abgelehnt"' not in r.text
        assert 'value="postdoc"' in r.text  # Default fallback


# ------------------------------------------------------------------ Wochen-Brief
class TestBrief:
    def test_generate_markdown_struktur(self):
        md = briefmod.generate(POSTDOC, "postdoc")
        assert md.startswith("# Förder-Radar")
        assert "Top-Matches" in md and "Frist-Warnungen" in md
        assert "Stand:" in md

    def test_generate_leere_felder(self):
        md = briefmod.generate([], "postdoc")
        assert "Top-Matches" in md  # kein Crash

    def test_generate_kein_match(self):
        md = briefmod.generate(["Biologie"], "abgelehnt")
        assert "Top-Matches" in md and "Frist-Warnungen" in md

    def test_komma_argument_wird_getrennt(self):
        md = briefmod.generate(["Biologie, Nachhaltigkeit"], "postdoc")
        assert "Biologie" in md  # kein Crash; Feld-Kommas werden im CLI getrennt

    def test_cli_komma_split(self, monkeypatch, capsys):
        import sys
        monkeypatch.setattr(sys, "argv", ["brief", "--felder", "Biologie, Nachhaltigkeit", "--karriere", "postdoc"])
        briefmod.main()
        out = capsys.readouterr().out
        assert "Top-Matches" in out and "| DFG – Emmy Noether" in out
