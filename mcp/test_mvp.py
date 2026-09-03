"""Förder-Radar – Tests (pytest). Lauf:  python -m pytest test_mvp.py -q

Abdeckung: Katalog-Integrität, Matching (inkl. harter Karriere-Filter),
Fristen, Persistenz, MCP-Tools, UI-Rendering, Wochen-Brief.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import ClassVar

import pytest

import app as appmod
import brief as briefmod
import server
from match import (
    CATALOG,
    CatalogError,
    _begruendung,
    _fits,
    _frist_text,
    _score,
    _theme_score,
    load_catalog,
    match_profile,
    next_deadline,
    save_catalog,
)

PROGS = load_catalog()
POSTDOC = ["Biologie", "Nachhaltigkeit"]

with open(Path(__file__).parent / "sources.json", encoding="utf-8") as _f:
    SOURCES = json.load(_f)

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
                # verifiziert must have a frist OR be rolling (no deadline)
                assert p.get("frist") or p.get("rolling"), \
                    f"verifiziert ohne Frist und nicht rolling: {p['id']}"

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


# ------------------------------------------------- Katalog 2026 (add-2026-programmes)
class TestKatalog2026:
    """Neue 2026-Eintraege, entferntes Duplikat, reparierte Quelle-URLs."""

    NEU: ClassVar[set[str]] = {"msca-staff-exchanges", "humboldt-feodor-lynen",
           "dfg-int-kooperationen", "dfg-int-veranstaltungen"}

    def test_neue_eintraege_vorhanden(self):
        ids = {p["id"] for p in PROGS}
        assert ids >= self.NEU, f"fehlende 2026-Eintraege: {self.NEU - ids}"

    def test_graduate_school_entfernt(self):
        ids = {p["id"] for p in PROGS}
        assert "dfg-graduate-school" not in ids
        # strukturierte Promotion bleibt durch Graduiertenkolleg abgedeckt
        assert "dfg-graduiertenkolleg" in ids

    def test_neue_kategorien(self):
        by = {p["id"]: p for p in PROGS}
        assert by["msca-staff-exchanges"]["kategorie"] == "EU"
        assert by["humboldt-feodor-lynen"]["kategorie"] == "Stiftung"
        assert by["dfg-int-kooperationen"]["kategorie"] == "DFG"
        assert by["dfg-int-veranstaltungen"]["kategorie"] == "DFG"

    def test_alle_neuen_haben_hinweis_und_budget_null(self):
        for p in PROGS:
            if p["id"] in self.NEU:
                assert p.get("hinweis"), p["id"]
                assert p.get("budget_min") is None, p["id"]

    def test_quelle_urls_repariert(self):
        """Polski-R5: reparierte Eintraege nutzen die verifizierten URLs (deterministisch)."""
        by = {p["id"]: p["quelle"] for p in PROGS}
        dfg = "https://www.dfg.de/de/foerderung/foerdermoeglichkeiten/programme/"
        msca = "https://marie-sklodowska-curie-actions.ec.europa.eu/"
        erwartet = {
            "dfg-sachbeihilfe": dfg + "einzelfoerderung/sachbeihilfe",
            "dfg-emmy-noether": dfg + "einzelfoerderung/emmy-noether",
            "dfg-heisenberg": dfg + "einzelfoerderung/heisenberg",
            "dfg-graduiertenkolleg": dfg + "koordinierte-programme/graduiertenkollegs",
            "dfg-sfb": dfg + "koordinierte-programme/sfb",
            "dfg-fdm": dfg + "infrastruktur/lis/lis-foerderangebote/forschungsdaten",
            "dfg-ub-digiserv": dfg + "infrastruktur/lis/lis-foerderangebote/digitalisierung-erschliessung",
            "hrz-it-infra": dfg + "infrastruktur/wgi/foerderangebote/forschungsgrossgeraete",
            "dfg-irtg": dfg + "koordinierte-programme/graduiertenkollegs",
            "dfg-int-kooperationen": dfg + "inter-foerdermassnahmen/aufbau-internationaler-kooperationen",
            "dfg-int-veranstaltungen": dfg + "inter-foerdermassnahmen/int-wiss-veranstaltungen",
            "msc-itn": msca + "actions/doctoral-networks",
            "msc-cofund": msca + "actions/cofund",
            "msca-staff-exchanges": msca + "actions/staff-exchanges",
            "erc-plus-2026": "https://erc.europa.eu/apply-grant/erc-plus-grant",
            "loewe-hessen": "https://wissenschaft.hessen.de/forschen/landesprogramm-loewe",
            "loewe-verwaltung": "https://wissenschaft.hessen.de/forschen/landesprogramm-loewe",
            "volkswagen-stiftung": "https://www.volkswagenstiftung.de/en/funding/our-funding-portfolio",
            "max-weber-bayern": "https://www.studienstiftung.de/max-weber-programm",
            "nrw-mwk-wissenschaft": "https://www.mkw.nrw/",
            "krebshilfe-onkologie": "https://www.krebshilfe.de/forschen",
            "humboldt-feodor-lynen": "https://www.humboldt-foundation.de/bewerben/foerderprogramme/feodor-lynen-forschungsstipendium",
        }
        for pid, url in erwartet.items():
            assert pid in by, f"fehlender Eintrag {pid}"
            assert by[pid] == url, f"{pid}: falsche Quelle\n  {by[pid]}\n  != {url}"
        # keine reparierten URLs mehr auf toten Pfaeden
        tote = [by["dfg-sachbeihilfe"], by["dfg-emmy-noether"], by["dfg-heisenberg"],
                by["dfg-graduiertenkolleg"], by["dfg-sfb"], by["dfg-fdm"],
                by["dfg-ub-digiserv"], by["hrz-it-infra"], by["dfg-irtg"]]
        assert all("/de/foerderung/foerdermoeglichkeiten/programme/" in u for u in tote)
        for bf in ("bmbf-digital-ai", "bmbf-energie-nachhaltigkeit",
                   "bmbf-gesundheit-medizin", "bmbf-forschungsdaten", "bmbf-digiserv"):
            assert "foerderinfo.bund.de" in by[bf], f"{bf}: BMBF->BMFTR-Portal erwartet"

    def test_quellen_verify_run_repariert(self):
        """Source-verify run (2026-08-26): kaputte Quell-Links repariert.

        Browser/requests-check fand 9 tote Links (Begabtenfoerderwerke, SNSF,
        ARC, UNESCO, KAS) + 2 nur-per-Browser-erreichbare (CIHR, Sloan).
        Hier wird nur die reparierte URL deterministisch geprueft (kein Netz).
        """
        by = {p["id"]: p["quelle"] for p in PROGS}
        erwartet = {
            "bfw-ev-studienwerk": "https://www.evstudienwerk.de",
            "bfw-rls": "https://www.rosalux.de/stiftung/studienwerk/stipendien",
            "bfw-hss": "https://www.hss.de/stipendium/",
            "bfw-sdw": "https://www.sdw.org/bewerbung",
            "bfw-avicenna": "https://www.avicenna-studienwerk.de/",
            "dach-snsf-fwf": "https://www.snf.ch/en/ORgUpoSFePiH6QCp/page/get-a-grant",
            "arc-international": "https://www.arc.gov.au/funding-research",
            "unesco-research": "https://www.unesco.org/en/fellowships",
            "bfw-kas": "https://www.kas.de/web/begabtenfoerderung-und-kultur/home",
        }
        for pid, url in erwartet.items():
            assert pid in by, f"fehlender Eintrag {pid}"
            assert by[pid] == url, f"{pid}: falsche Quelle\n  {by[pid]}\n  != {url}"
        # alte tote Pfaede duerfen nicht mehr referenziert werden
        assert "rosalux.de/stipendien" not in by["bfw-rls"], by["bfw-rls"]
        assert "snf.ch/de/foerderung" not in by["dach-snsf-fwf"], by["dach-snsf-fwf"]
        assert "arc.gov.au/grants" not in by["arc-international"], by["arc-international"]
        assert "unesco.org/en/funding" not in by["unesco-research"], by["unesco-research"]
        assert "kas.de/de/studienfoerderung" not in by["bfw-kas"], by["bfw-kas"]

    def test_sources_verify_run_repariert(self):
        """Verify-Sources run (2026-08-27): kaputte sources.json-URLs repariert.

        Der verallgemeinerte Link-Verifier (verify_sources.py) fand 5 tote
        Quell-Links in sources.json, die der Katalog-Audit (67c1f7c) uebersah:
        BMBF-Domain nach BMFTR-Migration, LOEWE-Hessen, NRW-MWK-Pfad,
        MSCA-Hostname (Bindestrich), SNSF-Pfad. Deterministic (kein Netz).
        """
        by = {k: v["url"] for k, v in SOURCES.items()
              if isinstance(v, dict) and v.get("url")}
        erwartet = {
            "bmbf": "https://www.bmftr.bund.de/SiteGlobals/Forms/Suche/Bekanntmachungsuche/Bekanntmachungsuche_Formular.html?nn=907934",
            "loewe": "https://www.wissenschaft-hessen.de/foerderprogramme/loewe",
            "nrw-mwk": "https://www.mkw.nrw/themen/wissenschaft",
            "msc": "https://marie-sklodowska-curie-actions.ec.europa.eu",
            "dach-snsf-fwf": "https://www.snf.ch/de",
        }
        for sid, url in erwartet.items():
            assert sid in by, f"fehlende Quelle {sid}"
            assert by[sid] == url, f"{sid}: falsche URL\n  {by[sid]}\n  != {url}"
        # alte tote Pfaede duerfen nicht mehr referenziert werden
        assert "bmbf.de/bmbf/de/forschung/foerderung/bekanntmachungen" not in by["bmbf"]
        assert "wissenschaft.hessen.de/forschung/loewe" not in by["loewe"]
        assert "mkw.nrw/wissenschaft" not in by["nrw-mwk"]
        assert "marie-sklodowska-curieactions.ec.europa.eu" not in by["msc"]  # ohne Bindestrich
        assert "snf.ch/de/foerderung" not in by["dach-snsf-fwf"]

    def test_loewe_hinweis_nennt_foerderlinien(self):
        loewe = next(p for p in PROGS if p["id"] == "loewe-hessen")
        assert "Förderlinien" in loewe["hinweis"] or "Foerderlinien" in loewe["hinweis"]

    def test_neue_eintraege_matchen(self):
        """Spec-Szenarien: Postdoc/junior/prof finden die 2026-Eintraege."""
        ids = {p["id"] for p in PROGS}
        assert ids >= self.NEU

        def _found(karriere: str, feld: str, top: int = 40) -> set[str]:
            r = match_profile(PROGS, fields=[feld], karriere=karriere, top=top)
            assert r, f"keine Treffer fuer {karriere}/{feld}"
            return {m.id for m in r}

        # Postdoc mit offenem Themenfeld findet MSCA SE, Feodor Lynen, DFG int.
        post = _found("postdoc", "Mathematik")
        assert "msca-staff-exchanges" in post
        assert "humboldt-feodor-lynen" in post
        assert "dfg-int-kooperationen" in post
        assert "dfg-int-veranstaltungen" in post
        # Junior (MSCA SE) und Prof (Konferenzen) ebenfalls
        assert "msca-staff-exchanges" in _found("junior", "frei")
        assert "dfg-int-veranstaltungen" in _found("prof", "frei")
        # ausgefallenes Programm erscheint nicht mehr
        assert "dfg-graduate-school" not in _found("junior", "frei")


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

    def test_thematisch_offen_gilt_als_wildcard(self):
        # thematisch-offen = offen fuer alle Felder (wie "frei") -> Programme
        # mit thematisch-offen muessen in normalen Suchen auffindbar sein.
        offen = next(p for p in PROGS if p["id"] == "fritz-thyssen")  # thematisch-offen + postdoc
        assert offen["themen"] == ["thematisch-offen"]
        r = match_profile(PROGS, ["Astroteilchenphysik"], "postdoc", top=1000)
        assert any(x.id == offen["id"] for x in r), (
            f"thematisch-offen-Eintrag {offen['id']} unsichtbar in normaler Suche"
        )

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
        # Use top=30 to ensure rolling programmes are included (they sort after
        # programmes with deadlines in next_deadline)
        r = next_deadline(PROGS, POSTDOC, "postdoc", top=30)
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

    def test_filter_warnungen_included_in_brief(self):
        """brief uses _filter_warnungen: rolling + within window survive, others don't."""
        from grant_types import MatchResult
        from server import _filter_warnungen

        def make(id_: str, rolling: bool = False, tage_bis_frist: int | None = None):
            return MatchResult(
                id=id_, name="X", kategorie="DFG", score=1, frist=None,
                rolling=rolling, status="laufend", quelle="", stand_datum="",
                begruendung="", tage_bis_frist=tage_bis_frist,
            )

        rolling = make("r1", rolling=True)
        within = make("r2", tage_bis_frist=5)
        outside = make("r3", tage_bis_frist=200)
        ohne = make("r4")

        out = _filter_warnungen([rolling, within, outside, ohne], tage=60)
        assert {r.id for r in out} == {"r1", "r2"}

        # Edge: negative (bereits abgelaufen) taucht ebenfalls auf → stale data
        expired = make("r5", tage_bis_frist=-3)
        out2 = _filter_warnungen([expired], tage=60)
        assert out2[0].id == "r5"

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
    @classmethod
    def client(cls):
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

    def test_load_catalog_doc_full(self):
        """load_catalog_doc returns the full document (dict with 'programme')."""
        from match import load_catalog, load_catalog_doc
        doc = load_catalog_doc()
        assert isinstance(doc, dict)
        assert "programme" in doc
        assert "stand" in doc
        assert len(doc["programme"]) == len(load_catalog())

    def test_load_catalog_doc_roundtrip(self, tmp_path):
        """load_catalog_doc on a written file matches the programme list."""
        from match import load_catalog, load_catalog_doc, save_catalog
        katalog = load_catalog()
        p = tmp_path / "rt_doc.json"
        save_catalog(katalog, path=p)
        doc = load_catalog_doc(path=p)
        assert doc["programme"] == katalog
        assert doc["stand"] == date.today().isoformat()

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
        _target = server.PROGRAMME[0]["id"]
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
        import sys

        import export as expmod
        out = tmp_path / "export.csv"
        monkeypatch.setattr(sys, "argv", ["export", "--format", "csv", "--out", str(out)])
        expmod.main()
        assert out.exists()
        lines = out.read_text().strip().split("\n")
        assert len(lines) > 1  # header + data

    def test_export_json_main(self, tmp_path, monkeypatch):
        import sys

        import export as expmod
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
        import sys

        import export as expmod
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
        from saia import erweiterte_begruendung, saia_konfiguriert
        assert not saia_konfiguriert()
        assert erweiterte_begruendung({"name": "X"}, ["Biologie"], "postdoc") is None

    def test_saia_fail_open_bei_http_fehler(self, monkeypatch):
        """Konfiguriert, aber Endpoint nicht erreichbar: None (Fail-open)."""
        monkeypatch.setenv("SAIA_API_URL", "http://127.0.0.1:1/nope")
        monkeypatch.setenv("SAIA_API_KEY", "test-key")
        from saia import erweiterte_begruendung, saia_konfiguriert
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


# --------------------------------------------------------------- _fits unit tests
class TestFits:
    """Unit-Tests für _fits(): Wildcards, Substring (bidirektional), leere Inputs.

    Erwartetes Verhalten laut match.py:
      - _fits(theme_defs, field) -> bool
      - 'alle' / 'frei' / 'thematisch-offen' als Theme-Definition = Wildcard,
        matcht jedes nicht-leere Feld
      - sonst case-insensitiver Substring-Match in BEIDE Richtungen
        (t in f ODER f in t)
      - leeres/Whitespace-Feld -> False, leere Theme-Liste -> False
    """

    # -- Exakter Match --------------------------------------------------------
    def test_fits_exact_match(self):
        assert _fits(["Biologie"], "Biologie") is True

    def test_fits_exact_match_multiple_themes(self):
        """Trifft, sobald EINE Theme-Definition passt (any-Semantik)."""
        assert _fits(["Chemie", "Physik", "Biologie"], "Biologie") is True
        assert _fits(["Chemie", "Physik", "Biologie"], "Chemie") is True

    # -- Bidirektionaler Substring ---------------------------------------------
    def test_fits_substring_theme_in_field(self):
        """Kurze Theme-Definition steckt im Feld (t in f)."""
        assert _fits(["Bio"], "Biologie") is True

    def test_fits_substring_field_in_theme(self):
        """Kurzes Feld steckt in der Theme-Definition (f in t)."""
        assert _fits(["Biologie"], "Bio") is True

    def test_fits_substring_bidirectional(self):
        """Teilstring-Überlappung zählt in beide Richtungen."""
        assert _fits(["Bio"], "Biologie") is True      # t in f
        assert _fits(["Biologie"], "Bio") is True      # f in t
        assert _fits(["nach"], "Nachhaltigkeit") is True
        assert _fits(["Nachhaltigkeit"], "nach") is True

    def test_fits_substring_inside_word(self):
        """Substring mittig im Wort (nicht nur Präfix) zählt."""
        assert _fits(["halti"], "Nachhaltigkeit") is True
        assert _fits(["chhalt"], "Nachhaltigkeit") is True

    def test_fits_no_match_returns_false(self):
        assert _fits(["Biologie"], "Literatur") is False

    def test_fits_no_match_any_theme(self):
        """Keine der Definitionen passt -> False."""
        assert _fits(["Chemie", "Physik"], "Biologie") is False

    # -- Groß-/Kleinschreibung ------------------------------------------------
    def test_fits_case_insensitive(self):
        assert _fits(["biologie"], "BIOLOGIE") is True
        assert _fits(["BIOLOGIE"], "biologie") is True

    def test_fits_mixed_case_themes(self):
        assert _fits(["NaChHaLtIgKeIt"], "nachhaltigkeit") is True

    # -- Wildcards: frei / alle / thematisch-offen ----------------------------
    def test_fits_wildcard_frei(self):
        assert _fits(["frei"], "Archäologie") is True

    def test_fits_wildcard_alle(self):
        assert _fits(["alle"], "Beliebiges Querschnittsfeld") is True

    def test_fits_wildcard_thematisch_offen(self):
        assert _fits(["thematisch-offen"], "Astroteilchenphysik") is True

    def test_fits_wildcard_any_field(self):
        """Wildcard matcht jedes nicht-leere Feld."""
        for field in ("Biologie", "Kunst", "Mathematik", "Soziologie"):
            assert _fits(["frei"], field) is True
            assert _fits(["alle"], field) is True
            assert _fits(["thematisch-offen"], field) is True

    def test_fits_wildcard_case_insensitive(self):
        """Wildcards werden case-insensitiv erkannt (t.lower())."""
        assert _fits(["FREI"], "Biologie") is True
        assert _fits(["Alle"], "Biologie") is True
        assert _fits(["Thematisch-Offen"], "Biologie") is True

    def test_fits_wildcard_among_other_themes(self):
        """Wildcard neben konkreten Themen matcht trotzdem alles."""
        assert _fits(["Biologie", "frei"], "Kunst") is True

    def test_fits_wildcard_not_triggered_by_plain_substring(self):
        """Kein Wildcard: 'offen' allein ist kein Wildcard, nur 'thematisch-offen'."""
        assert _fits(["offen"], "Physik") is False
        assert _fits(["frei"], "freiwillig") is True  # frei ist Wildcard, egal

    # -- Leere Inputs -> False -------------------------------------------------
    def test_fits_empty_field_false(self):
        assert _fits(["Biologie"], "") is False

    def test_fits_whitespace_field_false(self):
        assert _fits(["Biologie"], "   ") is False

    def test_fits_empty_themes_false(self):
        assert _fits([], "Biologie") is False

    def test_fits_whitespace_theme_does_not_match(self):
        """Nur-Whitespace-Definitionen erzeugen keinen Treffer."""
        assert _fits(["   "], "Biologie") is False
        assert _fits(["\t\n"], "Biologie") is False

    def test_fits_no_themen_key_semantics(self):
        """Leere Liste == kein einziges Theme -> nichts matcht."""
        assert _fits([], "") is False
        assert _fits([], "Biologie") is False

    # -- Integration mit realem Katalog ----------------------------------------
    def test_fits_integration_real_catalog(self):
        """Echter Katalog: _fits verhält sich konsistent zum Inline-Modell."""
        fields = ["Biologie", "Chemie", "Physik", "Mathematik", "Kunst"]
        for prog in PROGS:
            themes = prog.get("themen", [])
            for f in fields:
                assert _fits(themes, f) == _fits_probe(themes, f), (
                    f"Abweichung für {prog.get('id')} / Feld {f!r}"
                )

    def test_fits_integration_consistent_with_theme_score(self):
        """Konsistenz: _fits-Treffer == hits von _theme_score."""
        fields = ["Biologie", "Chemie", "Physik", "Kunst"]
        for prog in PROGS[:30]:
            themes = prog.get("themen", [])
            expected = [f for f in fields if _fits(themes, f)]
            _, hits = _theme_score(prog, fields)
            assert hits == expected


# --------------------------------------------------------------- _theme_score capping
class TestThemeScoreCapping:
    """Unit-Tests für _theme_score(): Score wird bei 3 gekappt, leere Inputs -> 0.

    Erwartetes Verhalten laut match.py:
      - _theme_score(prog, fields) -> (score, hits)
      - Score = min(Anzahl gematchter Felder, 3)
      - leere fields / fehlende "themen" -> (0, [])
    """

    def _prog(self, themes):
        """Minimales Programm-Dict nur mit Themenliste."""
        return {"themen": themes}

    # -- Capping bei 3 --------------------------------------------------------
    def test_themeScore_capped_at_3(self):
        """Vier passende Felder -> Score ist weiterhin 3 (Cap)."""
        score, hits = _theme_score(self._prog(["Biologie"]),
                                   ["Biologie"] * 4)
        assert score == 3
        assert len(hits) == 4  # alle Treffer bleiben sichtbar

    def test_themeScore_many_distinct_fields_capped_at_3(self):
        """Viele verschiedene Treffer: Score bleibt 3, hits listet alle."""
        fields = ["Biologie", "Chemie", "Physik", "Mathematik"]
        score, hits = _theme_score(self._prog(fields[:]), fields)
        assert score == 3
        assert set(hits) == set(fields)

    def test_themeScore_cap_never_exceeds_3(self):
        """Beliebig viele Felder: Score kann 3 nicht überschreiten."""
        fields = ["A", "B", "C", "D", "E", "F", "G", "H"]
        score, _ = _theme_score(self._prog(fields[:]), fields)
        assert score == 3

    # -- Unterhalb des Caps ---------------------------------------------------
    def test_themeScore_single_match(self):
        score, hits = _theme_score(self._prog(["Biologie"]), ["Biologie"])
        assert score == 1
        assert hits == ["Biologie"]

    def test_themeScore_two_matches(self):
        score, hits = _theme_score(self._prog(["Biologie", "Chemie"]),
                                   ["Biologie", "Chemie"])
        assert score == 2
        assert hits == ["Biologie", "Chemie"]

    def test_themeScore_exactly_three_matches(self):
        """Genau 3 Treffer: Cap noch nicht greifend, Score == 3."""
        score, hits = _theme_score(self._prog(["Biologie", "Chemie", "Physik"]),
                                   ["Biologie", "Chemie", "Physik"])
        assert score == 3
        assert len(hits) == 3

    # -- Kein Treffer / leere Inputs -> 0 -------------------------------------
    def test_themeScore_no_match_zero(self):
        score, hits = _theme_score(self._prog(["Biologie"]), ["Literatur"])
        assert score == 0
        assert hits == []

    def test_themeScore_mixed_match_and_nonmatch(self):
        """Nur passende Felder zählen; Nicht-Treffer bleiben außen vor."""
        score, hits = _theme_score(self._prog(["Biologie"]),
                                   ["Biologie", "Literatur", "Musik"])
        assert score == 1
        assert hits == ["Biologie"]

    def test_themeScore_empty_fields_zero(self):
        score, hits = _theme_score(self._prog(["Biologie"]), [])
        assert score == 0
        assert hits == []

    def test_themeScore_empty_themes_zero(self):
        """Programm ohne 'themen'-Schlüssel -> keine Treffer."""
        score, hits = _theme_score({"name": "No Themes"}, ["Biologie"])
        assert score == 0
        assert hits == []

    def test_themeScore_no_themen_key_zero(self):
        """Prog ohne 'themen'-Eintrag: minimale Punkte pro Feld, Cap egal."""
        score, hits = _theme_score({"id": "x"}, ["A", "B", "C", "D"])
        assert score == 0
        assert hits == []

    def test_themeScore_blank_fields_ignored(self):
        """Leere/Whitespace-Felder matchen nichts."""
        score, hits = _theme_score(self._prog(["Biologie"]),
                                   ["", "   ", "Biologie"])
        assert score == 1
        assert hits == ["Biologie"]

    # -- Wildcards -------------------------------------------------------------
    def test_themeScore_wildcard_alle(self):
        score, hits = _theme_score(self._prog(["alle"]), ["Archäologie", "Kunst"])
        assert score == 2
        assert set(hits) == {"Archäologie", "Kunst"}

    def test_themeScore_wildcard_frei(self):
        score, _ = _theme_score(self._prog(["frei"]), ["Beliebiges Fach"])
        assert score == 1

    def test_themeScore_wildcard_thematisch_offen(self):
        score, _ = _theme_score(self._prog(["thematisch-offen"]),
                                ["Querschnittsfeld"])
        assert score == 1

    # -- Substring & Groß-/Kleinschreibung ------------------------------------
    def test_themeScore_case_insensitive(self):
        score, hits = _theme_score(self._prog(["biologie"]), ["BIOLOGIE"])
        assert score == 1
        assert hits == ["BIOLOGIE"]

    def test_themeScore_substring_both_directions(self):
        """Teilstring-Überlappung in beide Richtungen zählt."""
        assert _theme_score(self._prog(["Bio"]), ["Biologie"])[0] == 1
        assert _theme_score(self._prog(["Biologie"]), ["Bio"])[0] == 1

    # -- Integration mit realem Katalog ----------------------------------------
    def test_themeScore_integration_real_catalog(self):
        """Echter Katalog: Thema-Score bleibt immer im Bereich 0..3."""
        fields = ["Biologie", "Chemie", "Physik", "Mathematik", "Informatik"]
        for prog in PROGS:
            score, hits = _theme_score(prog, fields)
            assert 0 <= score <= 3
            assert all(h in fields for h in hits)
            assert len(hits) == sum(
                _fits_probe(prog.get("themen", []), f) for f in fields
            )

    def test_themeScore_integration_consistent_with_score(self):
        """Konsistenz: _theme_score == 'thema'-Komponente von _score."""
        fields = ["Biologie", "Nachhaltigkeit", "Physik"]
        for prog in PROGS[:20]:
            t_score, _ = _theme_score(prog, fields)
            parts = _score(prog, fields, None)
            assert parts["thema"] == t_score
            assert 0 <= parts["thema"] <= 3


def _fits_probe(theme_defs, field):
    """Kleines Inline-Modell der _fits-Logik für Konsistenzprobe."""
    f = field.lower().strip()
    if not f:
        return False
    wildcards = ("alle", "frei", "thematisch-offen")
    return any(
        t.lower() in wildcards or t.lower() in f or f in t.lower()
        for t in theme_defs or []
    )
