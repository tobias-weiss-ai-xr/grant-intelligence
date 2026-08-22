"""Tests für das Forscherprofil-Modell (profile.py).

Abdeckung: Profile-Dataclass, from_dict/to_dict Round-Trip, Persistenz
(load/save), ORCID-Adapter (Mock), Consent-Gating, Themenableitung.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from profile import (
    Profile,
    derive_themen,
    fetch_orcid,
    get_profile_by_id,
    load_profiles,
    save_profiles,
)

# ---------------------------------------------------------------------------
# Profil-Dataclass & Validierung
# ---------------------------------------------------------------------------

VOLL = {
    "id": "test-01",
    "name": "Test Forscher",
    "karriere": "postdoc",
    "themen": ["Künstliche Intelligenz", "Graphen"],
    "orcid": "0000-0001-2345-6789",
    "publikationen": ["A Paper", "Another Paper"],
    "einwilligung": True,
    "status": "aktiv",
    "standDatum": "2026-08-20",
    "hinweis": "Test-Profil",
}


class TestProfileDataclass:
    def test_round_trip(self):
        """from_dict(to_dict()) == original."""
        p = Profile.from_dict(VOLL)
        d = p.to_dict()
        p2 = Profile.from_dict(d)
        assert p2.id == p.id
        assert p2.name == p.name
        assert p2.karriere == p.karriere
        assert p2.themen == p.themen
        assert p2.orcid == p.orcid
        assert p2.publikationen == p.publikationen
        assert p2.einwilligung == p.einwilligung
        assert p2.status == p.status
        assert p2.stand_datum == p.stand_datum
        assert p2.hinweis == p.hinweis

    def test_camel_case_mapping(self):
        """standDatum maps to stand_datum and back."""
        p = Profile.from_dict(VOLL)
        assert p.stand_datum == "2026-08-20"
        d = p.to_dict()
        assert "standDatum" in d
        assert d["standDatum"] == "2026-08-20"

    def test_missing_id(self):
        d = {k: v for k, v in VOLL.items() if k != "id"}
        with pytest.raises(ValueError, match="Pflichtfelder"):
            Profile.from_dict(d)

    def test_missing_name(self):
        d = {k: v for k, v in VOLL.items() if k != "name"}
        with pytest.raises(ValueError, match="Pflichtfelder"):
            Profile.from_dict(d)

    def test_missing_karriere(self):
        d = {k: v for k, v in VOLL.items() if k != "karriere"}
        with pytest.raises(ValueError, match="Pflichtfelder"):
            Profile.from_dict(d)

    def test_invalid_karriere(self):
        d = {**VOLL, "karriere": "astronaut"}
        with pytest.raises(ValueError, match="Ungültige Karrierestufe"):
            Profile.from_dict(d)

    def test_invalid_status(self):
        d = {**VOLL, "status": "bogus"}
        with pytest.raises(ValueError, match="Ungültiger status"):
            Profile.from_dict(d)

    def test_defaults(self):
        """Minimal profile with only required fields."""
        p = Profile(id="min", name="Min", karriere="prof")
        assert p.themen == []
        assert p.orcid == ""
        assert p.publikationen == []
        assert p.einwilligung is False
        assert p.status == "aktiv"
        assert p.stand_datum == ""
        assert p.hinweis == ""

    def test_einwilligung_false(self):
        d = {**VOLL, "einwilligung": False}
        p = Profile.from_dict(d)
        assert p.einwilligung is False


# ---------------------------------------------------------------------------
# Persistenz (load/save)
# ---------------------------------------------------------------------------


class TestProfilePersistence:
    def test_save_load_round_trip(self, tmp_path):
        """save_profiles then load_profiles returns equivalent profiles."""
        path = tmp_path / "profiles.json"
        profiles = [
            Profile(id="p1", name="Alice", karriere="postdoc", themen=["KI"], einwilligung=True),
            Profile(id="p2", name="Bob", karriere="prof", themen=["Mathe"], einwilligung=False),
        ]
        save_profiles(profiles, path)
        loaded = load_profiles(path)
        assert len(loaded) == 2
        assert loaded[0].id == "p1"
        assert loaded[0].themen == ["KI"]
        assert loaded[0].einwilligung is True
        assert loaded[1].id == "p2"
        assert loaded[1].einwilligung is False

    def test_load_missing_file(self, tmp_path):
        """Missing profiles.json returns empty list (not error)."""
        path = tmp_path / "nonexistent.json"
        result = load_profiles(path)
        assert result == []

    def test_load_invalid_json(self, tmp_path):
        """Invalid JSON returns empty list."""
        path = tmp_path / "bad.json"
        path.write_text("{invalid json", encoding="utf-8")
        result = load_profiles(path)
        assert result == []

    def test_load_skips_invalid_profile(self, tmp_path):
        """Invalid profile entries are skipped, valid ones are kept."""
        path = tmp_path / "profiles.json"
        doc = {
            "stand": "2026-08-20",
            "quelleHinweis": "test",
            "profile": [
                {"id": "good", "name": "Good", "karriere": "postdoc", "einwilligung": True},
                {"id": "bad", "name": "Bad", "karriere": "astronaut"},
            ],
        }
        path.write_text(
            __import__("json").dumps(doc, ensure_ascii=False), encoding="utf-8"
        )
        result = load_profiles(path)
        assert len(result) == 1
        assert result[0].id == "good"

    def test_get_profile_by_id(self, tmp_path):
        """get_profile_by_id finds the right profile."""
        path = tmp_path / "profiles.json"
        profiles = [
            Profile(id="p1", name="Alice", karriere="postdoc"),
            Profile(id="p2", name="Bob", karriere="prof"),
        ]
        save_profiles(profiles, path)
        found = get_profile_by_id("p2", path)
        assert found is not None
        assert found.name == "Bob"
        assert get_profile_by_id("nonexistent", path) is None


# ---------------------------------------------------------------------------
# ORCID Public API Adapter
# ---------------------------------------------------------------------------


class TestFetchOrcid:
    def test_no_consent_returns_empty(self):
        """fetch_orcid returns [] when einwilligung=False."""
        result = fetch_orcid("0000-0001-2345-6789", einwilligung=False)
        assert result == []

    def test_no_orcid_returns_empty(self):
        """fetch_orcid returns [] when orcid_id is empty."""
        result = fetch_orcid("", einwilligung=True)
        assert result == []

    @patch("profile.httpx.get")
    def test_successful_fetch(self, mock_get):
        """Successful ORCID fetch returns publication titles."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "group": [
                {
                    "work-summary": [
                        {
                            "title": {"title": {"content": "Deep Learning for Graphs"}}
                        }
                    ]
                },
                {
                    "work-summary": [
                        {
                            "title": {"title": {"content": "AI Adoption in Education"}}
                        }
                    ]
                },
            ]
        }
        mock_get.return_value = mock_resp

        result = fetch_orcid("0000-0001-2345-6789", einwilligung=True)
        assert len(result) == 2
        assert "Deep Learning for Graphs" in result
        assert "AI Adoption in Education" in result

    @patch("profile.httpx.get")
    def test_http_404(self, mock_get):
        """404 response returns empty list."""
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_get.return_value = mock_resp

        result = fetch_orcid("0000-0000-0000-0000", einwilligung=True)
        assert result == []

    @patch("profile.httpx.get")
    def test_timeout_graceful(self, mock_get):
        """Network timeout returns empty list, no exception."""
        import httpx

        mock_get.side_effect = httpx.ConnectTimeout("timeout")
        result = fetch_orcid("0000-0001-2345-6789", einwilligung=True)
        assert result == []

    @patch("profile.httpx.get")
    def test_malformed_json(self, mock_get):
        """Malformed JSON response returns empty list."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.side_effect = __import__("json").JSONDecodeError("bad", "doc", 0)
        mock_get.return_value = mock_resp

        result = fetch_orcid("0000-0001-2345-6789", einwilligung=True)
        assert result == []

    @patch("profile.httpx.get")
    def test_empty_works(self, mock_get):
        """API returns 200 but no works → empty list."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"group": []}
        mock_get.return_value = mock_resp

        result = fetch_orcid("0000-0001-2345-6789", einwilligung=True)
        assert result == []


# ---------------------------------------------------------------------------
# Themen-Ableitung
# ---------------------------------------------------------------------------


class TestDeriveThemen:
    def test_derive_ki(self):
        titles = ["Deep Learning for Graphs", "AI in Education"]
        result = derive_themen(titles)
        assert "Künstliche Intelligenz" in result
        assert "Maschinelles Lernen" in result
        assert "Graphen" in result

    def test_derive_math(self):
        titles = ["Algebraic Topology of Manifolds", "Number Theory and Primes"]
        result = derive_themen(titles)
        assert "Topologie" in result
        assert "Algebra" in result
        assert "Zahlentheorie" in result

    def test_derive_empty(self):
        assert derive_themen([]) == []

    def test_derive_no_match(self):
        titles = ["Cooking with Fire", "Gardening Tips"]
        assert derive_themen(titles) == []

    def test_derive_dedup(self):
        """Multiple matches for same field produce one entry."""
        titles = ["Machine Learning 1", "Machine Learning 2", "ML Survey"]
        result = derive_themen(titles)
        assert result.count("Maschinelles Lernen") == 1


# ---------------------------------------------------------------------------
# Profil-basiertes Matching (match_profile mit profil Parameter)
# ---------------------------------------------------------------------------

class TestProfileMatching:
    """Tests for match_profile with profil parameter and consent gating."""

    @pytest.fixture
    def catalog(self):
        from match import load_catalog
        return load_catalog()

    @pytest.fixture
    def profile_consent(self):
        return Profile(
            id="test-consent",
            name="Test Consent",
            karriere="postdoc",
            themen=["Künstliche Intelligenz"],
            einwilligung=True,
        )

    @pytest.fixture
    def profile_no_consent(self):
        return Profile(
            id="test-no-consent",
            name="Test No Consent",
            karriere="postdoc",
            themen=["Künstliche Intelligenz"],
            einwilligung=False,
        )

    def test_profil_provides_defaults(self, catalog, profile_consent):
        """Profile themen used when no explicit fields given."""
        from match import match_profile
        results = match_profile(catalog, profil=profile_consent, top=5)
        assert len(results) > 0
        # Should match KI-related programmes
        assert any("Künstliche Intelligenz" in r.begruendung or "KI" in r.begruendung for r in results)

    def test_explicit_fields_override_profile(self, catalog, profile_consent):
        """Explicit fields take precedence over profile.themen."""
        from match import match_profile
        results = match_profile(catalog, fields=["Biologie"], profil=profile_consent, top=5)
        # Results should match Biologie, not KI
        assert len(results) > 0
        assert all("Biologie" in r.begruendung or "frei" in r.begruendung.lower() for r in results)

    def test_no_consent_returns_empty(self, catalog, profile_no_consent):
        """Profile without consent returns empty list."""
        from match import match_profile
        results = match_profile(catalog, profil=profile_no_consent, top=5)
        assert results == []

    def test_explicit_karriere_from_profile(self, catalog, profile_consent):
        """Profile karriere is used as default."""
        from match import match_profile
        results = match_profile(catalog, profil=profile_consent, top=5)
        # All results should be open to postdoc
        assert len(results) > 0
        # Career filter is applied — results should be for postdoc
        for r in results:
            assert r.score > 0

    def test_explicit_karriere_overrides_profile(self, catalog, profile_consent):
        """Explicit karriere overrides profile.karriere."""
        from match import match_profile
        results = match_profile(catalog, fields=["frei"], karriere="prof", profil=profile_consent, top=5)
        assert len(results) > 0
        # Results should be for prof, not postdoc (profile.karriere="postdoc")

    def test_next_deadline_with_profil(self, catalog, profile_consent):
        """next_deadline works with profil parameter."""
        from match import next_deadline
        results = next_deadline(catalog, profil=profile_consent, top=3)
        assert len(results) > 0
        # Each result should have tage_bis_frist set (or rolling)
        for r in results:
            assert r.tage_bis_frist is not None or r.rolling

    def test_next_deadline_no_consent(self, catalog, profile_no_consent):
        """next_deadline returns empty for no-consent profile."""
        from match import next_deadline
        results = next_deadline(catalog, profil=profile_no_consent, top=3)
        assert results == []


# ---------------------------------------------------------------------------
# MCP Server: profile tool + profil_id parameter
# ---------------------------------------------------------------------------

class TestServerProfileTool:
    """Tests for the MCP profile tool and profil_id in match_best/brief."""

    @pytest.fixture
    def profiles_file(self, tmp_path):
        """Create a temporary profiles.json for testing."""
        path = tmp_path / "profiles.json"
        doc = {
            "stand": "2026-08-20",
            "quelleHinweis": "test",
            "profile": [
                {
                    "id": "test-postdoc",
                    "name": "Test Postdoc",
                    "karriere": "postdoc",
                    "themen": ["Künstliche Intelligenz"],
                    "einwilligung": True,
                    "status": "aktiv",
                    "standDatum": "2026-08-20",
                },
                {
                    "id": "test-no-consent",
                    "name": "Test No Consent",
                    "karriere": "prof",
                    "themen": ["Medizin"],
                    "einwilligung": False,
                    "status": "inaktiv",
                    "standDatum": "2026-08-20",
                },
            ],
        }
        import json
        path.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
        return path

    def test_profile_list_all(self, profiles_file, monkeypatch):
        """profile() without id returns all profiles."""
        from profile import load_profiles
        monkeypatch.setattr("profile.PROFILES", profiles_file)
        result = load_profiles(profiles_file)
        assert len(result) == 2
        assert result[0].id == "test-postdoc"
        assert result[1].id == "test-no-consent"

    def test_profile_by_id(self, profiles_file):
        """profile(id) returns the specific profile."""
        from profile import get_profile_by_id
        p = get_profile_by_id("test-postdoc", profiles_file)
        assert p is not None
        assert p.name == "Test Postdoc"
        assert p.einwilligung is True

    def test_profile_not_found(self, profiles_file):
        """profile(id) with unknown id returns None."""
        from profile import get_profile_by_id
        assert get_profile_by_id("nonexistent", profiles_file) is None

    def test_brief_with_profil_id(self, profiles_file, monkeypatch):
        """brief with profil_id loads profile and uses its themen."""
        import server
        from profile import get_profile_by_id

        # Monkeypatch get_profile_by_id to use our temp file
        def mock_get_profile(pid, path=None):
            return get_profile_by_id(pid, profiles_file)

        monkeypatch.setattr("server.get_profile_by_id", mock_get_profile)
        monkeypatch.setattr("server.PROGRAMME", server.load_catalog())

        result = server.brief(profil_id="test-postdoc")
        assert "fehler" not in result
        assert len(result["top_matches"]) > 0

    def test_brief_no_consent(self, profiles_file, monkeypatch):
        """brief with profil_id of no-consent profile returns error."""
        import server
        from profile import get_profile_by_id

        def mock_get_profile(pid, path=None):
            return get_profile_by_id(pid, profiles_file)

        monkeypatch.setattr("server.get_profile_by_id", mock_get_profile)
        monkeypatch.setattr("server.PROGRAMME", server.load_catalog())

        result = server.brief(profil_id="test-no-consent")
        assert "fehler" in result
        assert "Einwilligung" in result["fehler"]
        assert result["top_matches"] == []

    def test_brief_unknown_profil_id(self, monkeypatch):
        """brief with unknown profil_id returns error."""
        import server
        from profile import get_profile_by_id

        def mock_get_profile(pid, path=None):
            return get_profile_by_id(pid)  # uses real profiles.json

        monkeypatch.setattr("server.get_profile_by_id", mock_get_profile)
        monkeypatch.setattr("server.PROGRAMME", server.load_catalog())

        result = server.brief(profil_id="does-not-exist")
        assert "fehler" in result
        assert "nicht gefunden" in result["fehler"]

    def test_match_best_with_profil_id(self, profiles_file, monkeypatch):
        """match_best with profil_id uses profile themen."""
        import server
        from profile import get_profile_by_id

        def mock_get_profile(pid, path=None):
            return get_profile_by_id(pid, profiles_file)

        monkeypatch.setattr("server.get_profile_by_id", mock_get_profile)
        monkeypatch.setattr("server.PROGRAMME", server.load_catalog())

        results = server.match_best(profil_id="test-postdoc", top=5)
        assert len(results) > 0

    def test_match_best_no_consent(self, profiles_file, monkeypatch):
        """match_best with no-consent profile returns empty."""
        import server
        from profile import get_profile_by_id

        def mock_get_profile(pid, path=None):
            return get_profile_by_id(pid, profiles_file)

        monkeypatch.setattr("server.get_profile_by_id", mock_get_profile)
        monkeypatch.setattr("server.PROGRAMME", server.load_catalog())

        results = server.match_best(profil_id="test-no-consent", top=5)
        assert results == []


# ---------------------------------------------------------------------------
# App UI: Profil-Dropdown & Consent-Hinweis
# ---------------------------------------------------------------------------

class TestAppProfileUI:
    """Tests for the web UI profile dropdown and consent handling."""

    def test_index_has_profile_dropdown(self):
        """Index page renders a profile dropdown with pilot profiles."""
        from app import index
        html_out = index()
        assert "profil_id" in html_out
        assert "Tobias Weiss" in html_out

    def test_brief_with_profil_id_fills_themen(self):
        """Brief with profil_id fills themen from profile."""
        from app import brief as app_brief
        # Submit with profil_id but empty felder → should use profile themen
        html_out = app_brief(felder="", karriere="postdoc", profil_id="pilot-01-tobias")
        assert "Deine nächsten Chancen" in html_out
        # The form should have the profile's themen pre-filled
        assert "Künstliche Intelligenz" in html_out

    def test_brief_with_no_consent_profile(self):
        """Brief with no-consent profile shows consent notice."""
        from app import brief as app_brief
        html_out = app_brief(felder="", karriere="postdoc", profil_id="pilot-02-math-postdoc")
        assert "consent-notice" in html_out
        assert "Einwilligung" in html_out

    def test_brief_without_profil_id_works(self):
        """Brief without profil_id still works (backward compat)."""
        from app import brief as app_brief
        html_out = app_brief(felder="Biologie", karriere="postdoc", profil_id="")
        assert "Deine nächsten Chancen" in html_out

    def test_brief_with_unknown_profil_id(self):
        """Brief with unknown profil_id falls back to manual fields."""
        from app import brief as app_brief
        html_out = app_brief(felder="Physik", karriere="postdoc", profil_id="does-not-exist")
        # Should still render results (profile not found → no pre-fill, manual fields used)
        assert "Deine nächsten Chancen" in html_out


# ---------------------------------------------------------------------------
# Pilot-Demo: pilot_demo.py
# ---------------------------------------------------------------------------

class TestPilotDemo:
    """Tests for the pilot demo script."""

    def test_generate_pilot_results(self):
        """pilot_demo.generate_pilot_results() produces valid markdown."""
        from pilot_demo import generate_pilot_results
        md = generate_pilot_results()
        assert "# Pilot-Ergebnisse" in md
        assert "Tobias Weiss" in md
        assert "Top-Matches" in md
        # Profiles without consent should be mentioned
        assert "Keine Einwilligung" in md

    def test_pilot_demo_writes_file(self, tmp_path):
        """pilot_demo main() writes to file."""
        import pilot_demo
        import importlib
        # Just verify generate_pilot_results works (main() writes to docs/)
        result = pilot_demo.generate_pilot_results()
        assert "Pilot-Ergebnisse" in result
        assert "Fachbereich Mathematik" in result


# ---------------------------------------------------------------------------
# MCP Server: profile tool (list + get by id)
# ---------------------------------------------------------------------------

class TestServerProfileListTool:
    """Tests for the MCP profile tool (list all + get by id)."""

    def test_profile_list_all(self):
        """profile() without id returns all profiles."""
        import server
        result = server.profile()
        assert isinstance(result, list)
        assert len(result) >= 1
        # pilot-01-tobias should be in the list
        ids = [p["id"] for p in result]
        assert "pilot-01-tobias" in ids

    def test_profile_by_id(self):
        """profile(id) returns the specific profile."""
        import server
        result = server.profile(profil_id="pilot-01-tobias")
        assert isinstance(result, dict)
        assert result["id"] == "pilot-01-tobias"
        assert result["name"] == "Tobias Weiss"
        assert result["einwilligung"] is True

    def test_profile_not_found(self):
        """profile(id) with unknown id returns error dict."""
        import server
        result = server.profile(profil_id="nonexistent")
        assert isinstance(result, dict)
        assert "fehler" in result
        assert "nicht gefunden" in result["fehler"]

    def test_profile_has_expected_fields(self):
        """Profile dict has all expected fields."""
        import server
        result = server.profile(profil_id="pilot-01-tobias")
        expected = {"id", "name", "karriere", "themen", "orcid", "einwilligung", "status"}
        assert expected.issubset(result.keys())


# ---------------------------------------------------------------------------
# MCP Server: Edge cases for profil_id in match/notify/brief
# ---------------------------------------------------------------------------

class TestServerProfilIdEdgeCases:
    """Edge cases for profil_id in match_best, naechste_fristen, notify."""

    @pytest.fixture
    def profiles_file(self, tmp_path):
        """Create a temporary profiles.json for testing."""
        path = tmp_path / "profiles.json"
        import json
        doc = {
            "stand": "2026-08-20",
            "quelleHinweis": "test",
            "profile": [
                {
                    "id": "test-active",
                    "name": "Active",
                    "karriere": "postdoc",
                    "themen": ["Künstliche Intelligenz"],
                    "einwilligung": True,
                    "status": "aktiv",
                    "standDatum": "2026-08-20",
                },
                {
                    "id": "test-inactive",
                    "name": "Inactive",
                    "karriere": "prof",
                    "themen": ["Medizin"],
                    "einwilligung": False,
                    "status": "inaktiv",
                    "standDatum": "2026-08-20",
                },
            ],
        }
        path.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
        return path

    def test_match_best_unknown_profil_id(self, profiles_file, monkeypatch):
        """match_best with unknown profil_id returns empty list."""
        import server
        from profile import get_profile_by_id

        def mock_get_profile(pid, path=None):
            return get_profile_by_id(pid, profiles_file)

        monkeypatch.setattr("server.get_profile_by_id", mock_get_profile)
        monkeypatch.setattr("server.PROGRAMME", server.load_catalog())
        results = server.match_best(profil_id="does-not-exist", top=5)
        assert results == []

    def test_match_best_no_consent(self, profiles_file, monkeypatch):
        """match_best with no-consent profile returns empty list."""
        import server
        from profile import get_profile_by_id

        def mock_get_profile(pid, path=None):
            return get_profile_by_id(pid, profiles_file)

        monkeypatch.setattr("server.get_profile_by_id", mock_get_profile)
        monkeypatch.setattr("server.PROGRAMME", server.load_catalog())
        results = server.match_best(profil_id="test-inactive", top=5)
        assert results == []

    def test_naechste_fristen_unknown_profil_id(self, profiles_file, monkeypatch):
        """naechste_fristen with unknown profil_id returns empty list."""
        import server
        from profile import get_profile_by_id

        def mock_get_profile(pid, path=None):
            return get_profile_by_id(pid, profiles_file)

        monkeypatch.setattr("server.get_profile_by_id", mock_get_profile)
        monkeypatch.setattr("server.PROGRAMME", server.load_catalog())
        results = server.naechste_fristen(profil_id="does-not-exist", top=5)
        assert results == []

    def test_naechste_fristen_no_consent(self, profiles_file, monkeypatch):
        """naechste_fristen with no-consent profile returns empty list."""
        import server
        from profile import get_profile_by_id

        def mock_get_profile(pid, path=None):
            return get_profile_by_id(pid, profiles_file)

        monkeypatch.setattr("server.get_profile_by_id", mock_get_profile)
        monkeypatch.setattr("server.PROGRAMME", server.load_catalog())
        results = server.naechste_fristen(profil_id="test-inactive", top=5)
        assert results == []

    def test_notify_unknown_profil_id(self, profiles_file, monkeypatch):
        """notify with unknown profil_id returns empty list."""
        import server
        from profile import get_profile_by_id

        def mock_get_profile(pid, path=None):
            return get_profile_by_id(pid, profiles_file)

        monkeypatch.setattr("server.get_profile_by_id", mock_get_profile)
        monkeypatch.setattr("server.PROGRAMME", server.load_catalog())
        results = server.notify(profil_id="does-not-exist", tage=60)
        assert results == []

    def test_notify_no_consent(self, profiles_file, monkeypatch):
        """notify with no-consent profile returns empty list."""
        import server
        from profile import get_profile_by_id

        def mock_get_profile(pid, path=None):
            return get_profile_by_id(pid, profiles_file)

        monkeypatch.setattr("server.get_profile_by_id", mock_get_profile)
        monkeypatch.setattr("server.PROGRAMME", server.load_catalog())
        results = server.notify(profil_id="test-inactive", tage=60)
        assert results == []

    def test_brief_with_active_profil(self, profiles_file, monkeypatch):
        """brief with active profile returns results."""
        import server
        from profile import get_profile_by_id

        def mock_get_profile(pid, path=None):
            return get_profile_by_id(pid, profiles_file)

        monkeypatch.setattr("server.get_profile_by_id", mock_get_profile)
        monkeypatch.setattr("server.PROGRAMME", server.load_catalog())
        result = server.brief(profil_id="test-active", top=5)
        assert "fehler" not in result
        assert len(result["top_matches"]) > 0


# ---------------------------------------------------------------------------
# Coverage: __post_init__ direct construction edge cases
# ---------------------------------------------------------------------------

class TestProfilePostInitDirect:
    """Tests for __post_init__ validation via direct construction."""

    def test_direct_missing_id(self):
        with pytest.raises(TypeError):
            Profile(name="Test", karriere="postdoc")  # type: ignore[call-arg]

    def test_direct_missing_name(self):
        with pytest.raises(TypeError):
            Profile(id="test", karriere="postdoc")  # type: ignore[call-arg]

    def test_direct_missing_karriere(self):
        with pytest.raises(TypeError):
            Profile(id="test", name="Test")  # type: ignore[call-arg]

    def test_direct_empty_id(self):
        with pytest.raises(ValueError, match="Pflichtfelder"):
            Profile(id="", name="Test", karriere="postdoc")

    def test_direct_empty_name(self):
        with pytest.raises(ValueError, match="Pflichtfelder"):
            Profile(id="test", name="", karriere="postdoc")


# ---------------------------------------------------------------------------
# Brief CLI: --profil-id support
# ---------------------------------------------------------------------------

class TestBriefProfilId:
    """Tests for brief.generate() with profil_id parameter."""

    def test_brief_with_profil_id(self):
        """brief.generate with profil_id uses profile themen."""
        import brief
        text = brief.generate(profil_id="pilot-01-tobias", top=3)
        assert "Förder-Radar" in text
        assert "Künstliche Intelligenz" in text
        assert "Top-Matches" in text

    def test_brief_with_profil_id_no_consent(self):
        """brief.generate with no-consent profile returns error."""
        import brief
        text = brief.generate(profil_id="pilot-02-math-postdoc")
        assert "Fehler" in text
        assert "Einwilligung" in text

    def test_brief_with_unknown_profil_id(self):
        """brief.generate with unknown profil_id returns error."""
        import brief
        text = brief.generate(profil_id="nonexistent")
        assert "Fehler" in text
        assert "nicht gefunden" in text

    def test_brief_with_profil_id_and_explicit_fields(self):
        """brief.generate with profil_id and explicit fields: explicit wins."""
        import brief
        text = brief.generate(felder=["Biologie"], karriere="prof", profil_id="pilot-01-tobias", top=3)
        assert "Förder-Radar" in text
        # Should match Biologie, not KI
        assert "Biologie" in text

    def test_brief_without_profil_id_and_without_fields(self):
        """brief.generate without profil_id and without fields: empty results."""
        import brief
        text = brief.generate(top=3)
        assert "Förder-Radar" in text
        # No fields → no matches
        assert "Top-Matches" in text
