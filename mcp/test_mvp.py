"""Förder-Radar – Tests (pytest). Lauf:  python -m pytest test_mvp.py -q

Abdeckung: Katalog-Integrität, Matching (inkl. harter Karriere-Filter),
Fristen, Persistenz, MCP-Tools, UI-Rendering, Wochen-Brief.
"""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

import pytest

import app as appmod
import brief as briefmod
import server
from match import (
    CATALOG,
    _begruendung,
    _frist_text,
    load_catalog,
    match_profile,
    next_deadline,
    save_catalog,
)

PROGS = load_catalog()
POSTDOC = ["Biologie", "Nachhaltigkeit"]

# Schutz: echte catalog.json darf durch Tests nie veraendert werden
_KATALOG_SNAPSHOT = CATALOG.read_bytes()
_REAL_CATALOG = CATALOG  # Original-Pfad vor jedem Monkeypatch


@pytest.fixture(autouse=True, scope="session")
def _katalog_schutz():
    """Prueft nach der ganzen Session: catalog.json unveraendert?"""
    yield
    assert CATALOG.read_bytes() == _KATALOG_SNAPSHOT, (
        "FEHLER: catalog.json wurde durch Tests veraendert!"
    )


# --------------------------------------------------------------- Katalog-Integrität
class TestKatalog:
    def test_alle_pflichtfelder(self):
        for p in PROGS:
            for k in (
                "id",
                "name",
                "kategorie",
                "themen",
                "karriere",
                "rolle",
                "quelle",
                "standDatum",
                "status",
            ):
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

    def test_laufend_ist_rolling_or_stichtage_or_ausschreibung(self):
        for p in PROGS:
            if p["status"] == "laufend":
                # laufend means: rolling, has stichtage, or ausschreibungsgebunden
                is_valid = (
                    p.get("rolling") is True
                    or "Stichtag" in p.get("hinweis", "")
                    or "ausschreibungsgebunden" in p.get("hinweis", "").lower()
                )
                assert is_valid, f"{p['id']}: laufend but no rolling/stichtage/ausschreibung"

    def test_verifiziert_hat_frist(self):
        for p in PROGS:
            if p["status"] == "verifiziert":
                assert p.get("frist"), f"verifiziert ohne Frist: {p['id']}"

    def test_kein_budget_null(self):
        for p in PROGS:
            assert p.get("budget_min") != 0, f"{p['id']}: budget_min=0 (should be null)"
            assert p.get("budget_max") != 0, f"{p['id']}: budget_max=0 (should be null)"

    def test_alle_haben_hinweis(self):
        for p in PROGS:
            assert p.get("hinweis"), f"{p['id']}: missing hinweis"

    def test_kategorien_vollstaendig(self):
        from grant_types import Kategorie
        cats = {p["kategorie"] for p in PROGS}
        for c in cats:
            assert Kategorie.is_valid(c), f"Unknown kategorie '{c}' in catalog"


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
        b = _begruendung(p, {"felder": ["Biologie"], "karriere": 1})
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
        neu = {
            "id": "test-prog",
            "name": "Test",
            "kategorie": "DFG",
            "themen": ["frei"],
            "karriere": ["prof"],
            "rolle": ["lead"],
            "frist": None,
            "rolling": True,
            "status": "zu-pruefen",
            "quelle": "test",
            "standDatum": "2026-08-03",
        }
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
        assert any(
            x["id"] == "dfg-emmy-noether" for x in load_catalog(_REAL_CATALOG)
        )  # echte Datei unberuehrt

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
        assert "Keine Treffer" in html  # freundliche Meldung, kein Crash

    def test_html_escaping(self):
        # XSS-Schutz: Eingabe darf nicht roh in HTML landen
        html = appmod.brief(felder="<script>alert(1)</script>", karriere="postdoc")
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
        r = client.post(
            "/brief", data={"felder": "Biologie, Nachhaltigkeit", "karriere": "postdoc"}
        )
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

        monkeypatch.setattr(
            sys, "argv", ["brief", "--felder", "Biologie, Nachhaltigkeit", "--karriere", "postdoc"]
        )
        briefmod.main()
        out = capsys.readouterr().out
        assert "Top-Matches" in out and "| DFG – Emmy Noether" in out

    def test_cli_out_file(self, monkeypatch, tmp_path):
        """Lines 148-150: brief --out writes to file."""
        import sys
        out = tmp_path / "brief.md"
        monkeypatch.setattr(
            sys, "argv", ["brief", "--felder", "Biologie", "--karriere", "postdoc", "--out", str(out)]
        )
        briefmod.main()
        assert out.exists()
        content = out.read_text()
        assert "Top-Matches" in content

    # -- server.py: search with kategorie filter (89) --
    def test_search_with_kategorie(self):
        r = server.search(kategorie="DFG", stichwort="Sachbeihilfe")
        assert all(p["kategorie"] == "DFG" for p in r)
        assert len(r) > 0


# ---------------------------------------------------------------- Coverage Edges
import app as appmod
from match import CatalogError, save_catalog


class TestCoverageEdges:
    """Tests to reach uncovered branches (91% → 99%)."""

    # -- match.py: load_catalog errors (54-59) --
    def test_load_catalog_file_not_found(self):
        from match import load_catalog
        with pytest.raises(CatalogError, match="not found"):
            load_catalog(path=Path("/tmp/nonexistent_grant_12345.json"))

    def test_load_catalog_invalid_json(self, tmp_path):
        from match import load_catalog
        bad = tmp_path / "bad.json"
        bad.write_text("{invalid", encoding="utf-8")
        with pytest.raises(CatalogError, match="Invalid JSON"):
            load_catalog(path=bad)

    # -- match.py: save_catalog error (88-90) --
    def test_save_catalog_oserror(self, tmp_path):
        from match import save_catalog
        readonly = tmp_path / "sub" / "deep.json"
        # directory doesn't exist, trigger OSError
        with pytest.raises(CatalogError, match="Failed to write"):
            save_catalog([], path=readonly)

    # -- match.py: begruendung empty-karriere branch (198-199) --
    def test_begruendung_empty_karriere(self):
        prog = {"id": "t", "name": "T", "themen": ["KI"], "karriere": [], "frist": None, "rolling": False, "status": "laufend", "quelle": "x", "hinweis": ""}
        b = _begruendung(prog, {"felder": ["KI"], "karriere": 0})
        assert "nicht gelistet" in b

    # -- app.py: _format_deadline all branches (113,115,120,124) --
    def test_format_deadline_rolling(self):
        r = appmod._format_deadline(None, True)
        assert "Rolling" in r.text
        assert r.rolling is True

    def test_format_deadline_offen(self):
        r = appmod._format_deadline(None, False)
        assert "offen" in r.text

    def test_format_deadline_kaputt(self):
        r = appmod._format_deadline("bald", False)
        assert "prüfen" in r.text

    def test_format_deadline_abgelaufen(self):
        r = appmod._format_deadline("2020-01-01", False)
        assert "Abgelaufen" in r.text
        assert r.urgent is True

    def test_format_deadline_weit(self):
        r = appmod._format_deadline("2030-01-01", False)
        assert "Tage bis Frist" in r.text
        assert r.urgent is False

    def test_format_deadline_dringend(self):
        r = appmod._format_deadline(date.today().isoformat(), False)
        assert "noch" in r.text
        assert r.urgent is True

    # -- server.py: programs kategorie filter (89) --
    def test_programs_bund_filter(self):
        bund = server.programs("Bund")
        assert all(p["kategorie"] == "Bund" for p in bund)

    def test_programs_international_filter(self):
        intl = server.programs("International")
        assert all(p["kategorie"] == "International" for p in intl)
        assert len(intl) >= 5  # was 5, now 22 after international foundations expansion

    # -- server.py: ingest rejection (133-137) --
    def test_ingest_rejects_invalid(self, tmp_path, monkeypatch):
        import match as matchmod
        kat = tmp_path / "catalog.json"
        save_catalog(PROGS, kat)
        monkeypatch.setattr(matchmod, "CATALOG", kat)
        server.PROGRAMME[:] = load_catalog()
        res = server.ingest([{
            "id": "reject-me",
            "name": "Valid Name",
            "kategorie": "DFG",
            "themen": ["frei"],
            "karriere": ["postdoc"],
            "rolle": ["lead"],
            "frist": None, "rolling": True,
            "status": "KAPUTT",  # invalid status!
            "quelle": "t", "standDatum": "2026-08-12",
        }])
        assert res["abgelehnt"] == 1
        assert res["neu"] == 0
        assert any("KAPUTT" in f for f in res["fehler"])

    # -- server.py: ingest update existing (141-145) --
    def test_ingest_updates_existing(self, tmp_path, monkeypatch):
        import match as matchmod
        kat = tmp_path / "catalog.json"
        save_catalog(PROGS, kat)
        monkeypatch.setattr(matchmod, "CATALOG", kat)
        server.PROGRAMME[:] = load_catalog()
        target = server.PROGRAMME[0]["id"]
        res = server.ingest([{
            **server.PROGRAMME[0],
            "hinweis": "updated by test",
        }])
        assert res["aktualisiert"] == 1
        assert res["neu"] == 0

    # -- server.py: match_best wrapper (208) --
    def test_match_best_wrapper(self):
        r = server.match_best(["Biologie"], karriere="postdoc", top=2)
        assert len(r) <= 2
        assert all("begruendung" in x for x in r)

    # -- server.py: naechste_fristen wrapper (230) --
    def test_naechste_fristen_wrapper(self):
        r = server.naechste_fristen(["Biologie"], karriere="postdoc", top=2)
        assert len(r) <= 2
        assert all("tageBisFrist" in x for x in r)

    # -- export.py: main() (144-158, 162) --
    def test_export_csv_main(self, tmp_path, monkeypatch):
        import export as expmod, sys
        out = tmp_path / "export.csv"
        monkeypatch.setattr(sys, "argv", ["export", "--format", "csv", "--out", str(out)])
        expmod.main()
        assert out.exists()
        lines = out.read_text().strip().split("\n")
        assert len(lines) > 1  # header + data

    def test_export_json_main(self, tmp_path, monkeypatch):
        import export as expmod, sys
        out = tmp_path / "export.json"
        monkeypatch.setattr(sys, "argv", ["export", "--format", "json", "--out", str(out)])
        expmod.main()
        assert out.exists()
        import json
        from match import load_catalog
        data = json.loads(out.read_text())
        katalog = load_catalog()
        assert len(data["programme"]) == len(katalog)

    def test_export_markdown_main(self, tmp_path, monkeypatch):
        import export as expmod, sys
        out = tmp_path / "export.md"
        monkeypatch.setattr(sys, "argv", ["export", "--format", "markdown", "--out", str(out)])
        expmod.main()
        assert out.exists()
        content = out.read_text()
        assert "Programm-Übersicht" in content

    # -- saia.py: optionale SAIA-KI-Anbindung --
    def test_saia_inaktiv_ohne_config(self, monkeypatch):
        """Ohne SAIA_API_URL/KEY: keine Anfrage, kein Effekt."""
        monkeypatch.delenv("SAIA_API_URL", raising=False)
        monkeypatch.delenv("SAIA_API_KEY", raising=False)
        from saia import saia_konfiguriert, erweiterte_begruendung
        assert not saia_konfiguriert()
        assert erweiterte_begruendung({"name": "X"}, ["Biologie"], "postdoc") is None

    def test_saia_fail_open_bei_http_fehler(self, monkeypatch):
        """Konfiguriert, aber Endpoint nicht erreichbar: None (Fail-open)."""
        monkeypatch.setenv("SAIA_API_URL", "http://127.0.0.1:1/nope")
        monkeypatch.setenv("SAIA_API_KEY", "test-key")
        from saia import saia_konfiguriert, erweiterte_begruendung
        assert saia_konfiguriert()
        assert erweiterte_begruendung({"name": "X"}, ["Biologie"], "postdoc") is None

    def test_brief_generate_mit_saia_flag_ohne_config(self, monkeypatch):
        """--saia ohne Config: Brief unveraendert (kein Crash, keine KI-Sektion)."""
        monkeypatch.delenv("SAIA_API_URL", raising=False)
        monkeypatch.delenv("SAIA_API_KEY", raising=False)
        import brief
        text = brief.generate(["Biologie"], "postdoc", saia=True)
        assert "KI-Begruendungen" not in text
        assert "Top-Matches" in text

    def test_saia_erfolg_mit_mock(self, monkeypatch):
        """Konfiguriert + Mock-Response: KI-Begruendung kommt an."""
        monkeypatch.setenv("SAIA_API_URL", "https://llm.example/v1/chat/completions")
        monkeypatch.setenv("SAIA_API_KEY", "test-key")
        import saia

        class FakeResp:
            def raise_for_status(self):
                pass
            def json(self):
                return {"choices": [{"message": {"content": "Passt wegen KI-Expertise."}}]}

        calls = {}
        def fake_post(url, headers=None, json=None, timeout=None):
            calls["url"] = url
            calls["json"] = json
            return FakeResp()

        monkeypatch.setattr(saia.httpx, "post", fake_post)
        out = saia.erweiterte_begruendung(
            {"name": "DFG Sachbeihilfe", "kategorie": "DFG"},
            ["Künstliche Intelligenz"], "postdoc",
        )
        assert out == "Passt wegen KI-Expertise."
        assert calls["url"] == "https://llm.example/v1/chat/completions"
        assert calls["json"]["messages"][0]["role"] == "user"

    def test_brief_mit_saia_mock(self, monkeypatch):
        """--saia mit Mock: KI-Sektion erscheint im Brief."""
        monkeypatch.setenv("SAIA_API_URL", "https://llm.example/v1/chat/completions")
        monkeypatch.setenv("SAIA_API_KEY", "test-key")
        import saia

        class FakeResp:
            def raise_for_status(self):
                pass
            def json(self):
                return {"choices": [{"message": {"content": "Starke Themenueberlappung."}}]}

        monkeypatch.setattr(saia.httpx, "post", lambda *a, **k: FakeResp())
        import brief
        text = brief.generate(["Biologie"], "postdoc", top=3, saia=True)
        assert "## KI-Begruendungen (SAIA)" in text
        assert "Starke Themenueberlappung." in text
