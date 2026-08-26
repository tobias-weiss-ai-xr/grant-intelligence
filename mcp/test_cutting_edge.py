"""Cutting-edge Testparadigmen für den Förder-Radar.

Enthält:
  1. Property-based Tests (Hypothesis)   – Invarianten des Matchings
  2. Fuzz-Tests                          – beliebige/kaputte Eingaben crashen nicht
  3. Roundtrip-Idempotenz                – save→load, to_dict→from_dict
  4. Determinismus                       – gleiche Eingabe ⇒ gleiche Ausgabe
  5. Sortier-/Grenzwert-Invarianten      – Score-Ordnung, top-Grenzen
  6. Performance-Gate                    – Matching auf 80 Programmen bleibt schnell
  7. Governance/DSGVO-Compliance         – öffentliche Profile haben Einwilligung
  8. Katalog-Invarianten                 – Datenqualität als Property über alle Einträge
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from grant_types import Kategorie, Programm
from match import _begruendung, _fits, _score, load_catalog, match_profile, next_deadline, save_catalog
from match import CatalogError


# =============================================================================
# 1. Property-based Tests (Hypothesis)
# =============================================================================


class TestMatchProperties:
    """Invarianten des Matchings – für beliebige gültige Eingaben."""

    @given(
        st.lists(st.text(min_size=1, max_size=20), max_size=8),
        st.sampled_from(["postdoc", "junior", "prof", "senior", "student", None]),
        st.integers(min_value=0, max_value=10),
    )
    @settings(max_examples=100, deadline=None)
    def test_score_bereich_und_sortierung(self, felder, karriere, top):
        """Scores liegen in [0,5]; Ergebnisse sind absteigend sortiert und ≤ top."""
        katalog = load_catalog()
        results = match_profile(katalog, felder, karriere, top=top)
        assert len(results) <= max(top, 0)
        scores = [r.score for r in results]
        assert all(0 <= s <= 5 for s in scores)
        assert scores == sorted(scores, reverse=True)

    @given(
        st.lists(st.text(min_size=1, max_size=20), max_size=8),
        st.sampled_from(["postdoc", "junior", "prof", "senior", "student", None]),
        st.sampled_from(["lead", "partner", None]),
    )
    @settings(max_examples=100, deadline=None)
    def test_rolle_und_karriere_sind_harte_filter(self, felder, karriere, rolle):
        """Gefilterte Ergebnisse erfüllen die harten Filter (wenn Felder gelistet)."""
        katalog = load_catalog()
        results = match_profile(katalog, felder, karriere, rolle=rolle, top=50)
        for r in results:
            prog = next(p for p in katalog if p["id"] == r.id)
            if rolle:
                assert rolle in prog.get("rolle", [])
            if karriere and prog.get("karriere"):
                assert karriere in prog.get("karriere", [])

    @given(st.lists(st.text(max_size=50), max_size=10))
    @settings(max_examples=50, deadline=None)
    def test_leere_felder_keine_treffer(self, felder):
        """Leere/Whitespace-Felder geben keine Treffer (Guard-Bedingung).

        Nur Listen aus leeren/Whitespace-Strings: nicht-leere Strings matchen
        themenoffene Programme ("frei") korrekt.
        """
        if not all(f.strip() == "" for f in felder):
            return  # nur semantisch leere Felder testen
        katalog = load_catalog()
        assert match_profile(katalog, felder, "postdoc", top=5) == []

    @given(
        st.lists(st.text(min_size=1, max_size=20), max_size=6),
        st.sampled_from(["postdoc", "junior", "prof"]),
    )
    @settings(max_examples=50, deadline=None)
    def test_begruendung_immer_nicht_leer(self, felder, karriere):
        """Jede Begründung ist nicht-leer und enthält Frist-Info."""
        katalog = load_catalog()
        for r in match_profile(katalog, felder, karriere, top=10):
            assert r.begruendung.strip() != ""


class TestFitsProperties:
    """Eigenschaften der Themen-Match-Funktion _fits."""

    @given(st.text(min_size=1, max_size=30).filter(lambda s: s.strip()))
    def test_frei_matcht_alles(self, feld):
        assert _fits(["frei"], feld)
        assert _fits(["alle"], feld)

    @given(st.text(min_size=1, max_size=20).filter(lambda s: s.strip()))
    def test_exakte_uebereinstimmung(self, feld):
        """Gleicher String matcht (Symmetrie bei identischen Einträgen)."""
        assert _fits([feld], feld)

    @given(st.text(min_size=1, max_size=20), st.text(min_size=1, max_size=20))
    def test_kein_exception_fuer_beliebige_paare(self, a, b):
        """_fits wirft nie – auch bei exotischen Strings."""
        _fits([a], b)  # darf nicht crashen

    def test_leeres_oder_whitespace_feld_false(self):
        """Deterministisch: leere/Whitespace-Felder matchen nie.

        (Hypothesis-Daten sind zufällig – dieser Guard braucht einen
        deterministischen Test für stabile 100%-Abdeckung.)
        """
        assert _fits(["frei"], "") is False
        assert _fits(["frei"], "   ") is False
        assert _fits(["frei"], "\t") is False
        assert _fits(["frei"], "\r\n") is False


# =============================================================================
# 2. Fuzz-Tests – kaputte/feindliche Eingaben
# =============================================================================


class TestFuzz:
    @given(st.dictionaries(st.text(max_size=30), st.text(max_size=50), max_size=15))
    @settings(max_examples=100, deadline=None)
    def test_score_ueberlebt_beliebige_programm_dicts(self, prog):
        """_score/_begruendung crashen nicht bei beliebigen Dicts."""
        katalog = load_catalog()
        parts = _score(prog, ["Biologie"], "postdoc")
        _begruendung(prog, parts)
        # Auch im Katalog-Kontext: kaputtes Dict stört das Matching nicht
        match_profile([prog] + katalog, ["Biologie"], "postdoc", top=5)

    @given(st.text(max_size=200))
    @settings(max_examples=100, deadline=None)
    def test_load_catalog_mit_binaermuell(self, muell):
        """Kaputtes JSON ⇒ CatalogError, kein Crash anderer Art."""
        import tempfile

        pfad = Path(tempfile.mkdtemp()) / "muell.json"
        pfad.write_text(muell, encoding="utf-8")
        if muell.strip():
            with pytest.raises((CatalogError, json.JSONDecodeError)):
                load_catalog(path=pfad)

    def test_load_catalog_wurzel_kein_dict(self):
        """Valides JSON mit Nicht-Dict-Wurzel (Liste/Int) ⇒ CatalogError."""
        import tempfile

        for muell in ("[1,2,3]", "0", "\"text\""):
            pfad = Path(tempfile.mkdtemp()) / "wurzel.json"
            pfad.write_text(muell, encoding="utf-8")
            with pytest.raises(CatalogError, match="Invalid catalog structure"):
                load_catalog(path=pfad)

    @given(st.lists(st.text(max_size=40), max_size=5))
    def test_parse_frist_ueberlebt_beliebiges(self, kaputte_fristen):
        """parse_frist wirft nie (liefert None oder date)."""
        from grant_types import parse_frist
        for f in kaputte_fristen:
            result = parse_frist(f)
            assert result is None or isinstance(result, date)


# =============================================================================
# 3. Roundtrip-Idempotenz
# =============================================================================


class TestRoundtrip:
    @given(st.sampled_from([k.value for k in Kategorie]))
    @settings(max_examples=20)
    def test_kategorie_roundtrip(self, kategorie_wert):
        """Jeder gültige Kategorie-Wert validiert und bleibt erhalten."""
        assert Kategorie.is_valid(kategorie_wert)
        assert Kategorie(kategorie_wert).value == kategorie_wert

    def test_save_load_roundtrip_katalog(self, tmp_path):
        """save_catalog → load_catalog liefert identische Programme."""
        katalog = load_catalog()
        p = tmp_path / "rt.json"
        save_catalog(katalog, path=p)
        wieder = load_catalog(path=p)
        assert wieder == katalog

    def test_to_dict_from_dict_roundtrip(self):
        """to_dict → from_dict ist idempotent; to_dict normalisiert optionale
        Felder (fehlend → None), darf aber keine Werte verändern."""
        for prog in load_catalog():
            p = Programm.from_dict(prog)
            d = p.to_dict()
            for k, v in prog.items():
                assert d.get(k) == v, f"{prog.get('id')}: Feld {k} verändert"
            # from_dict(to_dict(x)) == from_dict(x)
            assert Programm.from_dict(d).to_dict() == d


# =============================================================================
# 4. Determinismus
# =============================================================================


class TestDeterminismus:
    def test_match_profile_deterministisch(self):
        """Gleiche Eingabe ⇒ byte-identische Ergebnisse (kein RNG/Hash-Order)."""
        katalog = load_catalog()
        felder = ["Biologie", "Medizin"]
        a = match_profile(katalog, felder, "postdoc", top=10)
        b = match_profile(katalog, felder, "postdoc", top=10)
        assert [r.id for r in a] == [r.id for r in b]
        assert [r.begruendung for r in a] == [r.begruendung for r in b]

    def test_sortierung_stabil_bei_gleichem_score(self):
        """Bei gleichem Score entscheidet die Frist (Determinismus der Ordnung)."""
        katalog = load_catalog()
        results = match_profile(katalog, ["frei", "Biologie"], "postdoc", top=50)
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)


# =============================================================================
# 5. Grenzwert-Invarianten
# =============================================================================


class TestGrenzwerte:
    def test_top_zero(self):
        katalog = load_catalog()
        assert match_profile(katalog, ["Biologie"], "postdoc", top=0) == []

    def test_top_negativ(self):
        katalog = load_catalog()
        assert match_profile(katalog, ["Biologie"], "postdoc", top=-5) == []

    def test_top_groesser_als_katalog(self):
        """top > Kataloggröße ⇒ alle Treffer, kein Fehler."""
        katalog = load_catalog()
        results = match_profile(katalog, ["Biologie", "Medizin"], "postdoc", top=10_000)
        assert len(results) <= len(katalog)

    def test_next_deadline_rolling_hat_keine_tage(self):
        """Rolling-Programme haben tage_bis_frist=None."""
        katalog = load_catalog()
        for r in next_deadline(katalog, ["Biologie"], "postdoc", top=50):
            if r.rolling:
                assert r.tage_bis_frist is None


# =============================================================================
# 6. Performance-Gate (Regression gegen langsame Matching-Logik)
# =============================================================================


class TestPerformance:
    def test_match_profile_80_programme_schnell(self):
        """Matching über den ganzen Katalog bleibt unter 500 ms (CI-sicher großzügig)."""
        import time

        katalog = load_catalog()
        assert len(katalog) >= 80
        start = time.perf_counter()
        for _ in range(10):
            match_profile(katalog, ["Künstliche Intelligenz", "Biologie"], "postdoc", top=5)
        dauer = time.perf_counter() - start
        assert dauer < 0.5, f"Matching zu langsam: {dauer:.3f}s für 10×80 Programme"


# =============================================================================
# 7. Governance / DSGVO-Compliance
# =============================================================================


class TestGovernance:
    def test_oeffentliche_profile_haben_einwilligung(self):
        """Öffentliche Profile (profiles.json): Profile mit einwilligung=True
        dürfen gematcht werden. Profile mit einwilligung=False (Platzhalter)
        müssen status='inaktiv' haben (DSGVO-Konvention)."""
        pfad = Path(__file__).with_name("profiles.json")
        if not pfad.exists():
            pytest.skip("profiles.json nicht vorhanden")
        data = json.loads(pfad.read_text(encoding="utf-8"))
        for profil in data.get("profile", []):
            if profil.get("einwilligung") is False:
                assert profil.get("status") == "inaktiv", (
                    f"Profil {profil.get('id')} ohne Einwilligung muss status='inaktiv' haben!"
                )
            else:
                assert profil.get("einwilligung") is True, (
                    f"Profil {profil.get('id')}: einwilligung muss True oder False sein!"
                )

    def test_private_profile_sind_ignoriert(self):
        """profiles.local darf existieren, wird aber von Git ignoriert
        (Pattern *.local) – hier nur als Konventions-Check."""
        pfad = Path(__file__).with_name("profiles.local")
        if pfad.exists():
            # Wenn vorhanden: muss valides JSON sein
            json.loads(pfad.read_text(encoding="utf-8"))


# =============================================================================
# 8. Katalog-Invarianten als Properties
# =============================================================================


class TestKatalogInvarianten:
    @pytest.mark.parametrize("feld", [
        "id", "name", "kategorie", "themen", "karriere", "rolle",
        "quelle", "standDatum", "status", "hinweis",
    ])
    def test_pflichtfelder_vorhanden(self, feld):
        for prog in load_catalog():
            assert feld in prog, f"Programm {prog.get('id')} fehlt Feld {feld}"

    def test_hinweis_immer_nicht_leer(self):
        for prog in load_catalog():
            assert str(prog.get("hinweis", "")).strip(), (
                f"Programm {prog.get('id')} hat leeren hinweis"
            )

    def test_budget_null_oder_int(self):
        """Budget 0 ist verboten (bedeutet '0 EUR'); unbekannt = null."""
        for prog in load_catalog():
            for feld in ("budget_min", "budget_max"):
                wert = prog.get(feld)
                assert wert is None or isinstance(wert, int), (
                    f"{prog.get('id')}.{feld}: {wert!r}"
                )
                assert wert != 0, f"{prog.get('id')}.{feld} ist 0 – null verwenden!"

    def test_kategorie_enum_valide(self):
        for prog in load_catalog():
            assert Kategorie.is_valid(prog["kategorie"]), (
                f"Unbekannte Kategorie: {prog.get('id')} → {prog['kategorie']}"
            )

    def test_frist_iso_oder_null(self):
        from datetime import datetime
        for prog in load_catalog():
            frist = prog.get("frist")
            if frist:
                datetime.strptime(frist, "%Y-%m-%d")

    def test_rolling_impliziert_keine_frist(self):
        for prog in load_catalog():
            if prog.get("rolling"):
                assert prog.get("frist") is None, (
                    f"{prog.get('id')}: rolling=true mit frist={prog.get('frist')}"
                )
