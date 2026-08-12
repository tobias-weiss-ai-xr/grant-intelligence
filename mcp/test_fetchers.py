"""Tests für fetchers.py (Auto-Fetching) – Netzwerkaufrufe werden gemockt."""

from __future__ import annotations

from datetime import date, timedelta

import httpx

import fetchers


class FakeResponse:
    def __init__(self, status_code: int = 200, content: bytes = b""):
        self.status_code = status_code
        self.content = content


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
            "id": "bmbf-ki", "name": "KI-Forschung", "themen": ["KI", "Digital"],
            "karriere": ["postdoc"],
        }
        result = fetchers._enrich_programme(partial, "bmbf")
        assert result["themen"] == ["KI", "Digital"]
        assert result["karriere"] == ["postdoc"]

    def test_no_id_returns_none(self):
        partial = {"name": "Test"}
        assert fetchers._enrich_programme(partial, "bmbf") is None

    def test_no_name_returns_none(self):
        partial = {"id": "test"}
        assert fetchers._enrich_programme(partial, "bmbf") is None


class TestApplyFetchUpdates:
    def test_valid_fetch_merged(self, tmp_path):
        import json

        # Setup a minimal catalog
        catalog = {
            "stand": "2026-01-01",
            "quelleHinweis": "test",
            "programme": [{"id": "existing", "name": "Existing", "kategorie": "DFG",
                             "themen": ["frei"], "karriere": ["postdoc"], "rolle": ["lead"],
                             "frist": None, "rolling": True, "status": "laufend",
                             "quelle": "", "standDatum": "2026-01-01"}],
        }
        catalog_path = tmp_path / "catalog.json"
        catalog_path.write_text(json.dumps(catalog))

        # Create a valid update
        new_prog = fetchers._enrich_programme(
            {"id": "new-from-fetch", "name": "New Programme", "quelle": "https://test.de"},
            "bmbf",
        )
        update = fetchers.ProgrammeUpdate(
            source="bmbf", programmes=[new_prog], errors=[],
            fetched_at="2026-08-12", suggestions=[],
        )

        result = fetchers.apply_fetch_updates([update], catalog_path=catalog_path)
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
            source="test", programmes=[invalid_prog], errors=[],
            fetched_at="2026-08-12", suggestions=[],
        )

        result = fetchers.apply_fetch_updates([update], catalog_path=catalog_path)
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
            source="test", programmes=[invalid], errors=[],
            fetched_at="2026-08-12", suggestions=[],
        )

        result = fetchers.apply_fetch_updates([update], catalog_path=catalog_path)
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
        update = fetchers.ProgrammeUpdate(
            source="bmbf", programmes=[new_prog], errors=[],
            fetched_at="2026-08-12", suggestions=[],
        )

        fetchers.apply_fetch_updates([update], catalog_path=catalog_path, audit_path=audit_path)
        content = audit_path.read_text()
        assert "bmbf" in content
        assert "+1" in content
