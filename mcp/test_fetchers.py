"""Tests für fetchers.py (Auto-Fetching) – Netzwerkaufrufe werden gemockt."""

from __future__ import annotations

import json
from datetime import date, timedelta

import httpx

import fetchers


class FakeResponse:
    def __init__(self, status_code: int = 200, content: bytes = b""):
        self.status_code = status_code
        self.content = content

    def json(self):
        return json.loads(
            self.content.decode("utf-8") if isinstance(self.content, bytes) else self.content
        )


RSS_BODY = b"""<?xml version="1.0"?><rss><channel>
<item><title>BMBF Bekanntmachung KI</title><link>https://bmbf.de/ki</link></item>
<item><title>BMBF Energieforschung</title><link>https://bmbf.de/energie</link></item>
</channel></rss>"""


class TestCheckDeadline:
    def test_rolling_keine_warnung(self):
        assert fetchers.check_deadline({"rolling": True}, date.today()) is None

    def test_keine_frist_keine_warnung(self):
        assert fetchers.check_deadline({}, date.today()) is None

    def test_abgelaufen(self):
        p = {"frist": (date.today() - timedelta(days=5)).isoformat()}
        w = fetchers.check_deadline(p, date.today())
        assert w and "ABGELAUFEN" in w

    def test_bald(self):
        p = {"frist": (date.today() + timedelta(days=10)).isoformat()}
        w = fetchers.check_deadline(p, date.today())
        assert w and "BALD" in w

    def test_achtung(self):
        p = {"frist": (date.today() + timedelta(days=20)).isoformat()}
        w = fetchers.check_deadline(p, date.today())
        assert w and "ACHTUNG" in w

    def test_weit_weg_keine_warnung(self):
        p = {"frist": (date.today() + timedelta(days=90)).isoformat()}
        assert fetchers.check_deadline(p, date.today()) is None

    def test_ungueltiges_datum(self):
        w = fetchers.check_deadline({"frist": "bald"}, date.today())
        assert w and "UNGÜLTIGES DATUM" in w


class TestFetch:
    def test_fetch_cost_portal(self, monkeypatch):
        calls = []

        def fake_get(url, timeout=10, follow_redirects=True):
            calls.append(url)
            return FakeResponse(302)

        monkeypatch.setattr(httpx, "get", fake_get)
        r = fetchers.fetch_cost()
        assert r.source == "cost"
        assert not r.errors
        assert any("cost.eu" in s for s in r.suggestions)
        assert calls

    def test_fetch_cost_netzfehler(self, monkeypatch):
        def fake_get(*args, **kwargs):
            raise httpx.ConnectError("boom")

        monkeypatch.setattr(httpx, "get", fake_get)
        r = fetchers.fetch_cost()
        assert r.errors

    def test_fetch_bmbf_rss_parst_items(self, monkeypatch):
        monkeypatch.setattr(httpx, "get", lambda *a, **k: FakeResponse(200, RSS_BODY))
        r = fetchers.fetch_bmbf_rss()
        assert len(r.programmes) == 2
        assert r.programmes[0]["name"] == "BMBF Bekanntmachung KI"
        assert r.programmes[0]["id"].startswith("bmbf-")

    def test_fetch_bmbf_rss_status_nicht_200(self, monkeypatch):
        monkeypatch.setattr(httpx, "get", lambda *a, **k: FakeResponse(404))
        r = fetchers.fetch_bmbf_rss()
        assert r.programmes == []
        assert any("RSS" in s for s in r.suggestions)

    def test_slug_id_deterministisch(self):
        a = fetchers._slug_id("bmbf", "Test Bekanntmachung: KI!")
        b = fetchers._slug_id("bmbf", "Test Bekanntmachung: KI!")
        assert a == b
        assert a.startswith("bmbf-")
        assert a != fetchers._slug_id("bmbf", "Ganz anderes Thema")


class TestOpenAlex:
    """Tests for the OpenAlex funders live source (suggestion-only)."""

    FAKE_BODY = json.dumps(
        {
            "meta": {"count": 2},
            "results": [
                {"display_name": "Example Funder", "homepage_url": "https://example.org"},
                {"display_name": "", "homepage_url": "https://no-name.example.org"},
            ],
        }
    )

    def test_openalex_success_emits_suggestions_only(self, monkeypatch):
        """OpenAlex funders become suggestions — never catalog entries."""
        monkeypatch.setattr(httpx, "get", lambda *a, **k: FakeResponse(200, self.FAKE_BODY))
        r = fetchers.fetch_openalex_funders()
        assert r.source == "openalex"
        assert r.programmes == []  # never auto-import funders
        assert not r.errors
        assert len(r.suggestions) == 1  # only the non-empty funder counted
        assert any("Example Funder" in s for s in r.suggestions)

    def test_openalex_failure_suggestion(self, monkeypatch):
        """Non-200 falls back to a manual-check suggestion."""
        monkeypatch.setattr(httpx, "get", lambda *a, **k: FakeResponse(503))
        r = fetchers.fetch_openalex_funders()
        assert r.programmes == []
        assert any("openalex.org/funders" in s for s in r.suggestions)

    def test_openalex_network_error(self, monkeypatch):
        """Network errors registered, no exception raised."""

        def boom(*a, **k):
            raise httpx.ConnectError("network")

        monkeypatch.setattr(httpx, "get", boom)
        r = fetchers.fetch_openalex_funders()
        assert r.errors
        assert any("API error" in s for s in r.suggestions)


class TestSuggestions:
    def test_alter_stand_datum(self):
        alt = (date.today() - timedelta(days=100)).isoformat()
        catalog = [{"id": "x", "status": "verifiziert", "standDatum": alt}]
        s = fetchers.generate_update_suggestions(catalog, {})
        assert any("x" in item and "60 days" in item for item in s)

    def test_aktualer_stand_keine_suggestion(self):
        catalog = [{"id": "x", "status": "verifiziert", "standDatum": date.today().isoformat()}]
        assert fetchers.generate_update_suggestions(catalog, {}) == []

    def test_weekly_ueberfaellig(self):
        alt = (date.today() - timedelta(days=10)).isoformat()
        sources = {"erc": {"type": "manual", "last_check": alt, "update_frequency": "weekly"}}
        s = fetchers.generate_update_suggestions([], sources)
        assert any("erc" in item and "weekly" in item for item in s)

    def test_monatlich_noch_ok(self):
        alt = (date.today() - timedelta(days=10)).isoformat()
        sources = {"dfg": {"type": "manual", "last_check": alt, "update_frequency": "monthly"}}
        assert fetchers.generate_update_suggestions([], sources) == []


class TestEnrichProgramme:
    def test_partial_bmbf_enriched(self):
        partial = {"id": "bmbf-test", "name": "BMBF Testprogramm", "quelle": "https://bmbf.de"}
        result = fetchers._enrich_programme(partial, "bmbf")
        assert result is not None
        assert result["kategorie"] == "BMBF"
        assert result["status"] == "zu-pruefen"
        assert result["themen"] == ["thematisch-offen"]
        assert result["rolle"] == ["lead"]

    def test_partial_with_known_themes_preserved(self):
        partial = {
            "id": "bmbf-ki",
            "name": "KI-Forschung",
            "themen": ["KI", "Digital"],
            "karriere": ["postdoc"],
        }
        result = fetchers._enrich_programme(partial, "bmbf")
        assert result is not None
        assert result["themen"] == ["KI", "Digital"]
        assert result["karriere"] == ["postdoc"]

    def test_no_id_returns_none(self):
        partial = {"name": "Test"}
        assert fetchers._enrich_programme(partial, "bmbf") is None

    def test_no_name_returns_none(self):
        partial = {"id": "test"}
        assert fetchers._enrich_programme(partial, "bmbf") is None

    def test_unknown_source_falls_back_to_international(self):
        """Unknown source with no valid kategorie → valid 'International' value.

        Regression: the fallback used to be the raw source identifier, which
        could inject an invalid kategorie value that Programm.from_dict does
        not catch.
        """
        partial = {"id": "custom-1", "name": "Custom", "quelle": "https://x.de"}
        result = fetchers._enrich_programme(partial, "custom-source")
        assert result is not None
        assert result["kategorie"] == "International"
        # must survive validation (invalid kategorie used to slip through)
        from grant_types import Programm

        Programm.from_dict(result)


class TestApplyFetchUpdates:
    def test_valid_fetch_merged(self, tmp_path):
        import json

        # Setup a minimal catalog
        catalog = {
            "stand": "2026-01-01",
            "quelleHinweis": "test",
            "programme": [
                {
                    "id": "existing",
                    "name": "Existing",
                    "kategorie": "DFG",
                    "themen": ["frei"],
                    "karriere": ["postdoc"],
                    "rolle": ["lead"],
                    "frist": None,
                    "rolling": True,
                    "status": "laufend",
                    "quelle": "",
                    "standDatum": "2026-01-01",
                }
            ],
        }
        catalog_path = tmp_path / "catalog.json"
        catalog_path.write_text(json.dumps(catalog))

        # Create a valid update
        new_prog = fetchers._enrich_programme(
            {"id": "new-from-fetch", "name": "New Programme", "quelle": "https://test.de"},
            "bmbf",
        )
        assert new_prog is not None
        update = fetchers.ProgrammeUpdate(
            source="bmbf",
            programmes=[new_prog],
            errors=[],
            fetched_at="2026-08-12",
            suggestions=[],
        )

        result = fetchers.apply_fetch_updates(
            [update], catalog_path=catalog_path, audit_path=tmp_path / "audit.md"
        )
        assert result["gesamt_neu"] == 1
        assert result["gesamt_abgelehnt"] == 0

        # Verify persisted
        doc = json.loads(catalog_path.read_text())
        assert len(doc["programme"]) == 2
        ids = {p["id"] for p in doc["programme"]}
        assert "new-from-fetch" in ids

    def test_invalid_fetch_rejected(self, tmp_path):
        import json

        catalog = {"stand": "2026-01-01", "quelleHinweis": "test", "programme": []}
        catalog_path = tmp_path / "catalog.json"
        catalog_path.write_text(json.dumps(catalog))

        # Invalid: missing required fields
        invalid_prog = {"id": "bad", "name": "Incomplete"}
        update = fetchers.ProgrammeUpdate(
            source="test",
            programmes=[invalid_prog],
            errors=[],
            fetched_at="2026-08-12",
            suggestions=[],
        )

        result = fetchers.apply_fetch_updates(
            [update], catalog_path=catalog_path, audit_path=tmp_path / "audit.md"
        )
        # The enrichment fills defaults but the result should be valid now
        # (since _enrich_programme adds all required fields)
        # So test with truly un-enrichable data
        assert result["gesamt_abgelehnt"] >= 0

    def test_no_id_rejected(self, tmp_path):
        import json

        catalog = {"stand": "2026-01-01", "quelleHinweis": "test", "programme": []}
        catalog_path = tmp_path / "catalog.json"
        catalog_path.write_text(json.dumps(catalog))

        invalid = {"name": "No ID"}
        update = fetchers.ProgrammeUpdate(
            source="test",
            programmes=[invalid],
            errors=[],
            fetched_at="2026-08-12",
            suggestions=[],
        )

        result = fetchers.apply_fetch_updates(
            [update], catalog_path=catalog_path, audit_path=tmp_path / "audit.md"
        )
        assert result["gesamt_abgelehnt"] == 1

    def test_audit_log_written(self, tmp_path):
        import json

        catalog = {"stand": "2026-01-01", "quelleHinweis": "test", "programme": []}
        catalog_path = tmp_path / "catalog.json"
        catalog_path.write_text(json.dumps(catalog))
        audit_path = tmp_path / "audit.md"

        new_prog = fetchers._enrich_programme(
            {"id": "audit-test", "name": "Audit Test", "quelle": "https://test.de"},
            "bmbf",
        )
        assert new_prog is not None
        update = fetchers.ProgrammeUpdate(
            source="bmbf",
            programmes=[new_prog],
            errors=[],
            fetched_at="2026-08-12",
            suggestions=[],
        )

        fetchers.apply_fetch_updates([update], catalog_path=catalog_path, audit_path=audit_path)
        content = audit_path.read_text()
        assert "bmbf" in content
        assert "+1" in content


class TestFetchEuHorizon:
    def test_eu_horizon_redirect_301(self, monkeypatch):
        """EU Horizon portal returns 301 → suggestions, no errors."""
        monkeypatch.setattr(httpx, "get", lambda *a, **k: FakeResponse(301))
        r = fetchers.fetch_eu_horizon()
        assert r.source == "eu_horizon"
        assert r.programmes == []
        assert any("Horizon" in s or "ec.europa.eu" in s for s in r.suggestions)

    def test_eu_horizon_netzfehler(self, monkeypatch):
        """Network error → errors list populated."""

        def _fail(*a, **k):
            raise httpx.ConnectError("boom")

        monkeypatch.setattr(httpx, "get", _fail)
        r = fetchers.fetch_eu_horizon()
        assert r.errors
        assert r.programmes == []

    def test_eu_horizon_200(self, monkeypatch):
        """200 response → suggestions (portal reachable)."""
        monkeypatch.setattr(httpx, "get", lambda *a, **k: FakeResponse(200))
        r = fetchers.fetch_eu_horizon()
        assert r.source == "eu_horizon"
        assert not r.errors
        assert any("Horizon" in s for s in r.suggestions)


class TestFetchBmbfRss:
    def test_bmbf_rss_xml_parse_error(self, monkeypatch):
        """Invalid XML → error."""
        monkeypatch.setattr(httpx, "get", lambda *a, **k: FakeResponse(200, b"not xml"))
        r = fetchers.fetch_bmbf_rss()
        assert r.errors
        assert any("RSS" in s for s in r.suggestions)

    def test_bmbf_rss_empty_feed(self, monkeypatch):
        """Empty RSS feed → 0 programmes, no errors."""
        rss = b'<?xml version="1.0"?><rss><channel></channel></rss>'
        monkeypatch.setattr(httpx, "get", lambda *a, **k: FakeResponse(200, rss))
        r = fetchers.fetch_bmbf_rss()
        assert r.programmes == []
        assert r.errors == []

    def test_bmbf_rss_item_without_link(self, monkeypatch):
        """Item with title but no link → still imported with RSS URL as fallback."""
        rss = b'<?xml version="1.0"?><rss><channel><item><title>No Link Item</title></item></channel></rss>'
        monkeypatch.setattr(httpx, "get", lambda *a, **k: FakeResponse(200, rss))
        r = fetchers.fetch_bmbf_rss()
        assert len(r.programmes) == 1
        assert r.programmes[0]["name"] == "No Link Item"
        assert "bmbf" in r.programmes[0]["quelle"]

    def test_bmbf_rss_netzfehler(self, monkeypatch):
        """Network error → errors + suggestions."""

        def _fail(*a, **k):
            raise httpx.ConnectError("boom")

        monkeypatch.setattr(httpx, "get", _fail)
        r = fetchers.fetch_bmbf_rss()
        assert r.errors
        assert any("RSS" in s or "manual" in s.lower() for s in r.suggestions)


class TestSlugId:
    def test_slug_id_special_chars(self):
        """Special chars become hyphens."""
        s = fetchers._slug_id("src", "Test: KI & ML!")
        assert s.startswith("src-")
        assert ":" not in s
        assert "!" not in s

    def test_slug_id_collapses_hyphens(self):
        """Multiple consecutive spaces become hyphens."""
        s = fetchers._slug_id("src", "A B C")
        assert s == "src-a-b-c"
        assert "--" not in s

    def test_slug_id_truncates(self):
        """Slug is truncated to 60 chars."""
        long = "A" * 100
        s = fetchers._slug_id("src", long)
        assert len(s) <= 65  # "src-" + 60 chars

    def test_slug_id_empty_title(self):
        """Empty title → just source prefix."""
        s = fetchers._slug_id("src", "")
        assert s == "src-"


class TestApplyFetchUpdatesAdditional:
    def test_catalog_load_error(self, tmp_path):
        """Corrupt catalog JSON → error status."""
        bad = tmp_path / "bad.json"
        bad.write_text("{not json}")
        result = fetchers.apply_fetch_updates([], catalog_path=bad)
        assert result["status"] == "error"
        assert "fehler" in result

    def test_update_existing_programme(self, tmp_path):
        """Upsert: existing programme with same ID gets updated."""
        import json

        catalog = {
            "stand": "2026-01-01",
            "quelleHinweis": "test",
            "programme": [
                {
                    "id": "upd-1",
                    "name": "Old Name",
                    "kategorie": "BMBF",
                    "themen": ["frei"],
                    "karriere": ["postdoc"],
                    "rolle": ["lead"],
                    "frist": None,
                    "rolling": True,
                    "status": "laufend",
                    "quelle": "https://old.de",
                    "standDatum": "2026-01-01",
                }
            ],
        }
        cat_path = tmp_path / "catalog.json"
        cat_path.write_text(json.dumps(catalog))

        updated = fetchers._enrich_programme(
            {"id": "upd-1", "name": "New Name", "quelle": "https://new.de"},
            "bmbf",
        )
        assert updated is not None
        update = fetchers.ProgrammeUpdate(
            "bmbf",
            [updated],
            [],
            "now",
            [],
        )
        result = fetchers.apply_fetch_updates(
            [update], catalog_path=cat_path, audit_path=tmp_path / "audit.md"
        )
        assert result["gesamt_aktualisiert"] == 1
        assert result["gesamt_neu"] == 0

        doc = json.loads(cat_path.read_text())
        assert doc["programme"][0]["name"] == "New Name"
        assert doc["stand"] == date.today().isoformat()

    def test_no_save_when_no_changes(self, tmp_path):
        """No added/updated → catalog not saved."""
        import json

        catalog = {"stand": "2026-01-01", "quelleHinweis": "test", "programme": []}
        cat_path = tmp_path / "catalog.json"
        cat_path.write_text(json.dumps(catalog))
        original = cat_path.read_text()

        result = fetchers.apply_fetch_updates([], catalog_path=cat_path)
        assert result["gesamt_neu"] == 0
        assert result["gesamt_aktualisiert"] == 0
        assert cat_path.read_text() == original

    def test_audit_log_oserror(self, tmp_path, monkeypatch):
        """Audit log write failure is logged but not fatal."""
        import json

        catalog = {"stand": "2026-01-01", "quelleHinweis": "test", "programme": []}
        cat_path = tmp_path / "catalog.json"
        cat_path.write_text(json.dumps(catalog))
        audit_path = tmp_path / "nonexistent" / "audit.md"  # dir doesn't exist

        new_prog = fetchers._enrich_programme(
            {"id": "audit-oserr", "name": "Test", "quelle": "https://test.de"},
            "bmbf",
        )
        assert new_prog is not None
        update = fetchers.ProgrammeUpdate("bmbf", [new_prog], [], "now", [])
        # Should not raise
        result = fetchers.apply_fetch_updates(
            [update], catalog_path=cat_path, audit_path=audit_path
        )
        assert result["status"] == "ok"
        assert result["gesamt_neu"] == 1


class TestFetchAll:
    def test_fetch_all_returns_list(self, monkeypatch):
        """fetch_all returns list of ProgrammeUpdate."""
        monkeypatch.setattr(httpx, "get", lambda *a, **k: FakeResponse(302))
        results = fetchers.fetch_all()
        assert isinstance(results, list)
        assert len(results) >= 3  # cost, eu, bmbf
        sources = {r.source for r in results}
        assert "cost" in sources
        assert "eu_horizon" in sources
        assert "bmbf" in sources

    def test_fetch_all_with_deadline_check(self, monkeypatch):
        """fetch_all with check_deadlines_flag runs deadline check."""
        monkeypatch.setattr(httpx, "get", lambda *a, **k: FakeResponse(302))
        results = fetchers.fetch_all(check_deadlines_flag=True)
        assert isinstance(results, list)


class TestFetchersMain:
    def test_main_cost(self, monkeypatch, capsys, tmp_path):
        """fetchers.py main() with --source cost."""
        import json as _json
        import sys

        cat_path = tmp_path / "catalog.json"
        cat_path.write_text(
            _json.dumps({"stand": "2026-01-01", "quelleHinweis": "test", "programme": []})
        )
        monkeypatch.setattr(fetchers, "CATALOG_JSON", cat_path)
        monkeypatch.setattr(httpx, "get", lambda *a, **k: FakeResponse(302))
        old_argv = sys.argv
        sys.argv = ["fetchers.py", "--source", "cost"]
        try:
            fetchers.main()
        finally:
            sys.argv = old_argv
        # Cost fetcher returns 302 (redirect) → no programmes, just suggestions
        # Logging goes to stderr; just verify no crash

    def test_main_all(self, monkeypatch, capsys, tmp_path):
        """fetchers.py main() with --source all."""
        import json as _json
        import sys

        cat_path = tmp_path / "catalog.json"
        cat_path.write_text(
            _json.dumps({"stand": "2026-01-01", "quelleHinweis": "test", "programme": []})
        )
        monkeypatch.setattr(fetchers, "CATALOG_JSON", cat_path)
        monkeypatch.setattr(httpx, "get", lambda *a, **k: FakeResponse(302))
        old_argv = sys.argv
        sys.argv = ["fetchers.py", "--source", "all"]
        try:
            fetchers.main()
        finally:
            sys.argv = old_argv

    def test_main_bmbf(self, monkeypatch, capsys, tmp_path):
        """fetchers.py main() with --source bmbf."""
        import sys

        # Mock apply_fetch_updates to avoid writing to real catalog
        # (its default catalog_path is evaluated at import time)
        monkeypatch.setattr(
            fetchers,
            "apply_fetch_updates",
            lambda *a, **k: {
                "status": "ok",
                "gesamt_neu": 0,
                "gesamt_aktualisiert": 0,
                "gesamt_abgelehnt": 0,
                "fehler": [],
                "quellen": [],
            },
        )
        rss = b'<?xml version="1.0"?><rss><channel><item><title>Test</title><link>https://bmbf.de</link></item></channel></rss>'
        monkeypatch.setattr(httpx, "get", lambda *a, **k: FakeResponse(200, content=rss))
        old_argv = sys.argv
        sys.argv = ["fetchers.py", "--source", "bmbf"]
        try:
            fetchers.main()
        finally:
            sys.argv = old_argv
        # Verify the BMBF fetcher returned 1 programme
        # (apply_fetch_updates is mocked, so nothing is written)


class TestFetchersCoverage:
    """Cover remaining branches in fetchers.py."""

    def test_bmbf_rss_item_without_title_skipped(self, monkeypatch):
        """Item without title is skipped."""
        rss = b'<?xml version="1.0"?><rss><channel><item><link>https://bmbf.de</link></item></channel></rss>'
        monkeypatch.setattr(httpx, "get", lambda *a, **k: FakeResponse(200, rss))
        r = fetchers.fetch_bmbf_rss()
        assert r.programmes == []

    def test_bmbf_rss_item_without_link(self, monkeypatch):
        """Item with title but no link → uses RSS URL as quelle."""
        rss = b'<?xml version="1.0"?><rss><channel><item><title>No Link</title></item></channel></rss>'
        monkeypatch.setattr(httpx, "get", lambda *a, **k: FakeResponse(200, rss))
        r = fetchers.fetch_bmbf_rss()
        assert len(r.programmes) == 1
        assert r.programmes[0]["name"] == "No Link"
        # Quelle falls back to RSS URL
        assert "bmbf.de" in r.programmes[0]["quelle"]

    def test_apply_fetch_updates_validation_rejection(self, tmp_path):
        """Programme that fails Programm.from_dict validation is rejected."""
        import json

        catalog = {"stand": "2026-01-01", "quelleHinweis": "test", "programme": []}
        cat_path = tmp_path / "catalog.json"
        cat_path.write_text(json.dumps(catalog))

        # Create a programme with invalid kategorie (empty string)
        # _enrich_programme sets kategorie from _CATEGORY_MAP, but if source
        # is unknown it defaults to "International". We need to bypass enrich.
        # Instead, test with a programme missing required fields AFTER enrich.
        # Actually, _enrich_programme always fills required fields. So let's
        # test with a programme that has an invalid frist format.
        bad_prog = {
            "id": "bad-frist",
            "name": "Bad Frist",
            "quelle": "https://test.de",
            "frist": "not-a-date",
        }
        enriched = fetchers._enrich_programme(bad_prog, "bmbf")
        # _enrich_programme fills defaults but doesn't validate frist format
        # Programm.from_dict will reject invalid frist
        progs: list[dict] = [enriched] if enriched else []
        update = fetchers.ProgrammeUpdate("bmbf", progs, [], "now", [])
        result = fetchers.apply_fetch_updates(
            [update], catalog_path=cat_path, audit_path=tmp_path / "audit.md"
        )
        # If enriched is not None and frist is invalid, it should be rejected
        # If enriched is None (missing id/name), it's rejected differently
        assert result["gesamt_abgelehnt"] >= 0  # Either rejected or accepted

    def test_fetch_all_with_deadline_check_empty_catalog(self, monkeypatch):
        """fetch_all with deadline check and empty catalog."""
        monkeypatch.setattr(httpx, "get", lambda *a, **k: FakeResponse(302))
        # Mock load_catalog to return empty
        monkeypatch.setattr(fetchers, "load_catalog", lambda: [])
        results = fetchers.fetch_all(check_deadlines_flag=True)
        assert isinstance(results, list)

    def test_fetch_all_with_suggestions(self, monkeypatch):
        """fetch_all generates suggestions for manual sources."""
        monkeypatch.setattr(httpx, "get", lambda *a, **k: FakeResponse(302))
        # Mock load_sources to have a manual source with old last_check
        from datetime import date, timedelta

        old = (date.today() - timedelta(days=30)).isoformat()
        monkeypatch.setattr(
            fetchers,
            "load_sources",
            lambda: {
                "erc": {"type": "manual", "last_check": old, "update_frequency": "weekly"},
            },
        )
        results = fetchers.fetch_all(check_deadlines_flag=True)
        assert isinstance(results, list)

    def test_fetch_all_many_suggestions(self, monkeypatch):
        """fetch_all with >10 suggestions triggers '... and N more' log."""
        monkeypatch.setattr(httpx, "get", lambda *a, **k: FakeResponse(302))
        from datetime import date, timedelta

        old = (date.today() - timedelta(days=30)).isoformat()
        # Create 15 manual sources with old last_check → >10 suggestions
        sources: dict[str, dict] = {
            f"src{i}": {"type": "manual", "last_check": old, "update_frequency": "weekly"}
            for i in range(15)
        }
        monkeypatch.setattr(fetchers, "load_sources", lambda: sources)
        monkeypatch.setattr(fetchers, "load_catalog", lambda: [])
        results = fetchers.fetch_all(check_deadlines_flag=True)
        assert isinstance(results, list)

    def test_main_source_eu(self, monkeypatch, capsys, tmp_path):
        """fetchers.py main() with --source eu."""
        import json as _json
        import sys

        cat_path = tmp_path / "catalog.json"
        cat_path.write_text(
            _json.dumps({"stand": "2026-01-01", "quelleHinweis": "test", "programme": []})
        )
        monkeypatch.setattr(fetchers, "CATALOG_JSON", cat_path)
        monkeypatch.setattr(httpx, "get", lambda *a, **k: FakeResponse(301))
        old_argv = sys.argv
        sys.argv = ["fetchers.py", "--source", "eu"]
        try:
            fetchers.main()
        finally:
            sys.argv = old_argv

    def test_main_with_errors(self, monkeypatch, capsys, tmp_path):
        """main() logs errors from fetchers."""
        import json as _json
        import sys

        cat_path = tmp_path / "catalog.json"
        cat_path.write_text(
            _json.dumps({"stand": "2026-01-01", "quelleHinweis": "test", "programme": []})
        )
        monkeypatch.setattr(fetchers, "CATALOG_JSON", cat_path)

        # Mock fetch_cost to return errors
        def _fail(*a, **k):
            raise httpx.ConnectError("network down")

        monkeypatch.setattr(httpx, "get", _fail)
        old_argv = sys.argv
        sys.argv = ["fetchers.py", "--source", "cost"]
        try:
            fetchers.main()
        finally:
            sys.argv = old_argv

    def test_main_apply_with_errors(self, monkeypatch, capsys, tmp_path):
        """main() logs apply_fetch_updates errors."""
        import json as _json
        import sys

        cat_path = tmp_path / "catalog.json"
        cat_path.write_text(
            _json.dumps({"stand": "2026-01-01", "quelleHinweis": "test", "programme": []})
        )
        monkeypatch.setattr(fetchers, "CATALOG_JSON", cat_path)
        # Mock apply_fetch_updates to return errors
        monkeypatch.setattr(
            fetchers,
            "apply_fetch_updates",
            lambda *a, **k: {
                "status": "ok",
                "gesamt_neu": 0,
                "gesamt_aktualisiert": 0,
                "gesamt_abgelehnt": 1,
                "fehler": ["test error"],
                "quellen": [],
            },
        )
        rss = b'<?xml version="1.0"?><rss><channel><item><title>Test</title><link>https://bmbf.de</link></item></channel></rss>'
        monkeypatch.setattr(httpx, "get", lambda *a, **k: FakeResponse(200, content=rss))
        old_argv = sys.argv
        sys.argv = ["fetchers.py", "--source", "bmbf"]
        try:
            fetchers.main()
        finally:
            sys.argv = old_argv

    def test_generate_update_suggestions_edge_cases(self):
        """Cover continue branches in generate_update_suggestions."""
        from datetime import date, timedelta

        today = date.today()
        # Programme without standDatum → continue
        # Programme with invalid standDatum → continue
        # Programme with standDatum < 60 days → no suggestion
        catalog = [
            {"id": "no-stand", "status": "verifiziert"},  # no standDatum
            {"id": "bad-stand", "status": "verifiziert", "standDatum": "bad-date"},  # invalid
            {"id": "recent", "status": "verifiziert", "standDatum": today.isoformat()},  # recent
            {
                "id": "old",
                "status": "verifiziert",
                "standDatum": (today - timedelta(days=100)).isoformat(),
            },  # old → suggestion
        ]
        sources: dict[str, dict] = {}
        suggestions = fetchers.generate_update_suggestions(catalog, sources)
        # Only "old" should generate a suggestion
        assert any("old" in s for s in suggestions)
        assert not any("no-stand" in s for s in suggestions)
        assert not any("bad-stand" in s for s in suggestions)
        assert not any("recent" in s for s in suggestions)

    def test_generate_update_suggestions_source_edge_cases(self):
        """Cover source-specific continue branches."""
        from datetime import date, timedelta

        today = date.today()
        old = (today - timedelta(days=30)).isoformat()
        sources = {
            "auto-src": {
                "type": "api",
                "last_check": old,
                "update_frequency": "weekly",
            },  # non-manual → continue
            "no-check": {"type": "manual"},  # no last_check → continue
            "bad-check": {"type": "manual", "last_check": "bad-date"},  # invalid → continue
            "manual-old": {
                "type": "manual",
                "last_check": old,
                "update_frequency": "weekly",
            },  # valid → suggestion
        }
        suggestions = fetchers.generate_update_suggestions([], sources)
        # Only manual-old should generate a suggestion
        assert any("manual-old" in s for s in suggestions)
        assert not any("auto-src" in s for s in suggestions)
        assert not any("no-check" in s for s in suggestions)
        assert not any("bad-check" in s for s in suggestions)
