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
