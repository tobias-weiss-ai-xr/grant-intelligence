"""Tests für ingest.py (Extensible Ingestion Pipeline).

Tests cover:
  - Registry: register, list_fetchers, ingest_source, ingest_all
  - Helpers: _oa_get, _make_prog, _category_for_source
  - API fetchers: OpenAIRE, NIH, NSF, Crossref (mocked HTTP)
  - CLI: --list, --source, --all, --apply, dry-run
  - Upsert: idempotent merge, validation, dry-run safety
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import httpx
import pytest

import ingest


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------


class TestRegistry:
    def test_registry_has_fetchers(self):
        fetchers = ingest.list_fetchers()
        assert len(fetchers) >= 7  # 3 existing + 4 new

    def test_registry_keys(self):
        keys = {e.key for e in ingest.list_fetchers()}
        for k in ("bmbf", "cost", "eu", "openaire", "nih", "nsf", "crossref"):
            assert k in keys, f"Missing fetcher: {k}"

    def test_register_adds_to_registry(self):
        @ingest.register("test-fixture", "Test", "Test fixture", "api")
        def _test_fetcher():
            return ingest.ProgrammeUpdate("test-fixture", [], [], "now", [])

        assert "test-fixture" in ingest._REGISTRY
        entry = ingest._REGISTRY["test-fixture"]
        assert entry.name == "Test"
        assert entry.category == "api"
        # Cleanup
        del ingest._REGISTRY["test-fixture"]

    def test_ingest_source_unknown_raises(self):
        with pytest.raises(KeyError, match="Unknown fetcher"):
            ingest.ingest_source("nonexistent")

    def test_ingest_source_returns_update(self):
        @ingest.register("test-fixture2", "Test2", "", "api")
        def _test_fetcher():
            return ingest.ProgrammeUpdate("test-fixture2", [{"id": "t1", "name": "T"}], [], "now", [])

        result = ingest.ingest_source("test-fixture2")
        assert result.source == "test-fixture2"
        assert len(result.programmes) == 1
        del ingest._REGISTRY["test-fixture2"]

    def test_ingest_all_runs_all(self):
        # ingest_all should not crash even if some fetchers fail
        results = ingest.ingest_all()
        assert len(results) == len(ingest.list_fetchers())

    def test_ingest_all_collects_errors(self):
        @ingest.register("test-fail", "Fail", "", "api")
        def _fail():
            raise RuntimeError("boom")

        results = ingest.ingest_all()
        fail_result = next(r for r in results if r.source == "test-fail")
        assert fail_result.errors
        assert "boom" in fail_result.errors[0]
        del ingest._REGISTRY["test-fail"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class TestOaGet:
    def test_simple_key(self):
        obj = {"name": {"$": "European Commission"}}
        assert ingest._oa_get(obj, "name") == "European Commission"

    def test_nested_path(self):
        obj = {"fundingtree": {"funder": {"name": {"$": "DFG"}}}}
        assert ingest._oa_get(obj, "fundingtree", "funder", "name") == "DFG"

    def test_missing_key(self):
        assert ingest._oa_get({}, "nonexistent") is None

    def test_non_dict(self):
        assert ingest._oa_get("string", "key") is None

    def test_plain_string_value(self):
        obj = {"code": "12345"}
        assert ingest._oa_get(obj, "code") == "12345"

    def test_none_input(self):
        assert ingest._oa_get(None, "key") is None


class TestMakeProg:
    def test_basic_prog(self):
        p = ingest._make_prog("openaire", "oa-1", "Test", "https://example.org", "hint")
        assert p["id"] == "oa-1"
        assert p["name"] == "Test"
        assert p["kategorie"] == "EU"
        assert p["status"] == "zu-pruefen"
        assert p["themen"] == ["thematisch-offen"]
        assert p["rolle"] == ["lead"]
        assert p["quelle"] == "https://example.org"
        assert p["hinweis"] == "hint"
        assert p["frist"] is None
        assert p["rolling"] is True  # No frist → rolling

    def test_with_frist(self):
        p = ingest._make_prog("nsf", "nsf-1", "Test", "https://nsf.gov", "hint", frist="2027-01-15")
        assert p["frist"] == "2027-01-15"
        assert p["rolling"] is False

    def test_explicit_rolling(self):
        p = ingest._make_prog("nsf", "nsf-1", "Test", "https://nsf.gov", "hint",
                              frist="2027-01-15", rolling=True)
        assert p["rolling"] is True

    def test_international_default(self):
        p = ingest._make_prog("unknown", "u-1", "Test", "https://x", "h")
        assert p["kategorie"] == "International"

    def test_name_truncated(self):
        long_name = "A" * 300
        p = ingest._make_prog("x", "x-1", long_name, "https://x", "h")
        assert len(p["name"]) <= 200


# ---------------------------------------------------------------------------
# API Fetchers (mocked)
# ---------------------------------------------------------------------------


class FakeResponse:
    def __init__(self, status_code=200, json_data=None, content=b""):
        self.status_code = status_code
        self._json = json_data or {}
        self.content = content

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"HTTP {self.status_code}", request=MagicMock(), response=self  # type: ignore[arg-type]
            )


class TestOpenAIRE:
    def test_fetch_parses_projects(self, monkeypatch):
        data = {
            "response": {
                "header": {"total": {"$": "100"}},
                "results": {"result": [
                    {
                        "metadata": {
                            "oaf:entity": {
                                "oaf:project": {
                                    "code": {"$": "123456"},
                                    "title": {"$": "AI for Science"},
                                    "acronym": {"$": "AIS"},
                                    "fundingtree": {
                                        "funder": {"name": {"$": "EC"}},
                                        "funding_level_0": {"name": {"$": "HORIZON"}},
                                    },
                                }
                            }
                        }
                    },
                    {
                        "metadata": {
                            "oaf:entity": {
                                "oaf:project": {
                                    "code": {"$": "789012"},
                                    "title": {"$": "Quantum Computing"},
                                    "fundingtree": {
                                        "funder": {"name": {"$": "DFG"}},
                                    },
                                }
                            }
                        }
                    },
                ]},
            }
        }
        monkeypatch.setattr(httpx, "get", lambda *a, **k: FakeResponse(200, data))
        result = ingest.fetch_openaire()
        assert result.source == "openaire"
        assert len(result.programmes) == 2
        assert result.errors == []
        # First programme
        p0 = result.programmes[0]
        assert "123456" in p0["id"]
        assert p0["name"] == "HORIZON"
        assert p0["kategorie"] == "EU"
        assert p0["quelle"] == "https://cordis.europa.eu/project/id/123456"
        assert p0["status"] == "zu-pruefen"
        # Second: no funding_level, falls back to funder + title
        p1 = result.programmes[1]
        assert "789012" in p1["id"]
        assert "DFG" in p1["name"]
        assert "Quantum Computing" in p1["name"]

    def test_fetch_deduplicates(self, monkeypatch):
        data = {
            "response": {
                "header": {"total": {"$": "2"}},
                "results": {"result": [
                    {
                        "metadata": {
                            "oaf:entity": {
                                "oaf:project": {
                                    "code": {"$": "001"},
                                    "title": {"$": "Same Project"},
                                }
                            }
                        }
                    },
                    {
                        "metadata": {
                            "oaf:entity": {
                                "oaf:project": {
                                    "code": {"$": "001"},
                                    "title": {"$": "Same Project"},
                                }
                            }
                        }
                    },
                ]},
            }
        }
        monkeypatch.setattr(httpx, "get", lambda *a, **k: FakeResponse(200, data))
        result = ingest.fetch_openaire()
        assert len(result.programmes) == 1  # Deduped

    def test_fetch_skips_missing_code(self, monkeypatch):
        data = {
            "response": {
                "header": {"total": {"$": "0"}},
                "results": {"result": [
                    {"metadata": {"oaf:entity": {"oaf:project": {"title": {"$": "No Code"}}}}},
                ]},
            }
        }
        monkeypatch.setattr(httpx, "get", lambda *a, **k: FakeResponse(200, data))
        result = ingest.fetch_openaire()
        assert len(result.programmes) == 0

    def test_fetch_handles_http_error(self, monkeypatch):
        def _fail(*a, **k):
            raise httpx.ConnectError("network down")
        monkeypatch.setattr(httpx, "get", _fail)
        result = ingest.fetch_openaire()
        assert result.errors
        assert "Network error" in result.errors[0]
        assert result.programmes == []

    def test_fetch_handles_empty_response(self, monkeypatch):
        data: dict = {"response": {"results": {"result": []}}}
        monkeypatch.setattr(httpx, "get", lambda *a, **k: FakeResponse(200, data))
        result = ingest.fetch_openaire()
        assert result.programmes == []
        assert result.errors == []


class TestNIH:
    def test_fetch_parses_projects(self, monkeypatch):
        data = {
            "meta": {"total": 76000},
            "results": [
                {
                    "project_num": "R01AG012345",
                    "project_title": "Alzheimer Research",
                    "agency": "NIA",
                    "fundProgramName": "AG Aging Research",
                },
                {
                    "project_num": "R01CA067890",
                    "project_title": "Cancer Genomics",
                    "agency": "NCI",
                },
            ],
        }
        monkeypatch.setattr(httpx, "post", lambda *a, **k: FakeResponse(200, data))
        result = ingest.fetch_nih_reporter()
        assert result.source == "nih"
        assert len(result.programmes) == 2
        p0 = result.programmes[0]
        assert "r01ag012345" in p0["id"]
        assert p0["name"] == "AG Aging Research"
        assert p0["kategorie"] == "International"
        assert p0["quelle"] == "https://reporter.nih.gov/project/R01AG012345"
        # Second: no fundProgramName, falls back to title
        p1 = result.programmes[1]
        assert "Cancer Genomics" in p1["name"]

    def test_fetch_skips_missing_project_num(self, monkeypatch):
        data = {"meta": {"total": 0}, "results": [{"project_title": "No Num"}]}
        monkeypatch.setattr(httpx, "post", lambda *a, **k: FakeResponse(200, data))
        result = ingest.fetch_nih_reporter()
        assert result.programmes == []

    def test_fetch_handles_http_error(self, monkeypatch):
        def _fail(*a, **k):
            raise httpx.ConnectError("boom")
        monkeypatch.setattr(httpx, "post", _fail)
        result = ingest.fetch_nih_reporter()
        assert result.errors


class TestNSF:
    def test_fetch_parses_awards(self, monkeypatch):
        data = {
            "response": {
                "award": [
                    {
                        "id": "1234567",
                        "title": "Quantum Information",
                        "agency": "NSF",
                        "fundProgramName": "ECCS",
                        "expDate": "06/30/2027",
                    },
                    {
                        "id": "8901234",
                        "title": "AI Research",
                        "agency": "NSF",
                        "expDate": "12/15/2026",
                    },
                ]
            }
        }
        monkeypatch.setattr(httpx, "get", lambda *a, **k: FakeResponse(200, data))
        result = ingest.fetch_nsf_awards()
        assert result.source == "nsf"
        assert len(result.programmes) == 2
        p0 = result.programmes[0]
        assert "1234567" in p0["id"]
        assert p0["name"] == "ECCS"
        assert p0["kategorie"] == "International"
        assert p0["frist"] == "2027-06-30"
        assert p0["rolling"] is False
        p1 = result.programmes[1]
        assert "AI Research" in p1["name"]
        assert p1["frist"] == "2026-12-15"

    def test_fetch_invalid_date(self, monkeypatch):
        data = {
            "response": {
                "award": [
                    {"id": "1", "title": "Bad Date", "expDate": "not-a-date"},
                ]
            }
        }
        monkeypatch.setattr(httpx, "get", lambda *a, **k: FakeResponse(200, data))
        result = ingest.fetch_nsf_awards()
        assert len(result.programmes) == 1
        assert result.programmes[0]["frist"] is None
        assert result.programmes[0]["rolling"] is True

    def test_fetch_skips_missing_id(self, monkeypatch):
        data = {"response": {"award": [{"title": "No ID"}]}}
        monkeypatch.setattr(httpx, "get", lambda *a, **k: FakeResponse(200, data))
        result = ingest.fetch_nsf_awards()
        assert result.programmes == []


class TestCrossref:
    def test_fetch_parses_funders(self, monkeypatch):
        data = {
            "message": {
                "total-results": 1134,
                "items": [
                    {"id": "100000001", "name": "Deutsche Forschungsgemeinschaft",
                     "location": "Germany", "count": 50000},
                    {"id": "100000002", "name": "Max Planck Society",
                     "location": "Germany", "count": 30000},
                ],
            }
        }
        monkeypatch.setattr(httpx, "get", lambda *a, **k: FakeResponse(200, data))
        result = ingest.fetch_crossref_funders()
        assert result.source == "crossref"
        assert len(result.programmes) == 2
        p0 = result.programmes[0]
        assert "100000001" in p0["id"]
        assert "Deutsche Forschungsgemeinschaft" in p0["name"]
        assert p0["kategorie"] == "International"
        assert p0["quelle"] == "https://api.crossref.org/funders/100000001"
        assert "50000 works" in p0["hinweis"]

    def test_fetch_deduplicates(self, monkeypatch):
        data = {
            "message": {
                "total-results": 1,
                "items": [
                    {"id": "dup1", "name": "Funder A", "location": "Germany", "count": 1},
                    {"id": "dup1", "name": "Funder A", "location": "Germany", "count": 1},
                ],
            }
        }
        monkeypatch.setattr(httpx, "get", lambda *a, **k: FakeResponse(200, data))
        result = ingest.fetch_crossref_funders()
        assert len(result.programmes) == 1

    def test_fetch_skips_missing_id(self, monkeypatch):
        data = {"message": {"total-results": 0, "items": [{"name": "No ID"}]}}
        monkeypatch.setattr(httpx, "get", lambda *a, **k: FakeResponse(200, data))
        result = ingest.fetch_crossref_funders()
        assert result.programmes == []


# ---------------------------------------------------------------------------
# Existing fetchers (re-registered)
# ---------------------------------------------------------------------------


class TestExistingFetchers:
    def test_cost_portal(self, monkeypatch):
        from fetchers import ProgrammeUpdate
        monkeypatch.setattr(httpx, "get", lambda *a, **k: FakeResponse(302))
        result = ingest.fetch_cost_portal()
        assert result.source == "cost"
        assert isinstance(result, ProgrammeUpdate)

    def test_eu_horizon_portal(self, monkeypatch):
        monkeypatch.setattr(httpx, "get", lambda *a, **k: FakeResponse(301))
        result = ingest.fetch_eu_horizon_portal()
        assert result.source == "eu_horizon"

    def test_bmbf_rss(self, monkeypatch):
        rss = b'<?xml version="1.0"?><rss><channel><item><title>Test</title><link>https://bmbf.de</link></item></channel></rss>'
        monkeypatch.setattr(httpx, "get", lambda *a, **k: FakeResponse(200, content=rss))
        result = ingest.fetch_bmbf_feed()
        assert result.source == "bmbf"
        assert len(result.programmes) == 1
        assert result.programmes[0]["name"] == "Test"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


class TestCLI:
    def test_list_shows_all_fetchers(self, capsys):
        import sys
        old_argv = sys.argv
        sys.argv = ["ingest.py", "--list"]
        try:
            ingest.main()
        finally:
            sys.argv = old_argv
        out = capsys.readouterr().out
        assert "openaire" in out
        assert "Total:" in out
        assert "Category" in out

    def test_list_argparse(self, capsys):
        import sys
        old_argv = sys.argv
        sys.argv = ["ingest.py", "--list"]
        try:
            ingest.main()
        except SystemExit:
            pass
        finally:
            sys.argv = old_argv
        out = capsys.readouterr().out
        assert "Total:" in out

    def test_source_dry_run_no_write(self, tmp_path, monkeypatch, capsys):
        """Dry-run should NOT modify catalog."""
        import sys
        # Create a temp catalog
        catalog = {
            "stand": "2026-01-01",
            "quelleHinweis": "test",
            "programme": [{"id": "existing", "name": "Existing", "kategorie": "DFG",
                           "themen": ["frei"], "karriere": ["postdoc"], "rolle": ["lead"],
                           "frist": None, "rolling": True, "status": "laufend",
                           "quelle": "", "standDatum": "2026-01-01"}],
        }
        cat_path = tmp_path / "catalog.json"
        cat_path.write_text(json.dumps(catalog))

        # Mock a fetcher that returns one programme
        @ingest.register("test-dry", "Test Dry", "", "api")
        def _test():
            return ingest.ProgrammeUpdate(
                "test-dry",
                [{"id": "test-dry-new", "name": "New Test", "quelle": "https://test.de"}],
                [], "now", [],
            )

        # Point CATALOG_JSON to temp
        monkeypatch.setattr(ingest, "CATALOG_JSON", cat_path)
        old_argv = sys.argv
        sys.argv = ["ingest.py", "--source", "test-dry"]
        try:
            ingest.main()
        except SystemExit:
            pass
        finally:
            sys.argv = old_argv

        out = capsys.readouterr().out
        assert "DRY-RUN" in out
        assert "Would add: 1" in out

        # Verify catalog was NOT modified
        doc = json.loads(cat_path.read_text())
        assert len(doc["programme"]) == 1  # Only original
        assert doc["programme"][0]["id"] == "existing"

        del ingest._REGISTRY["test-dry"]

    def test_source_apply_writes(self, tmp_path, monkeypatch, capsys):
        """--apply should merge into catalog."""
        import sys
        catalog = {
            "stand": "2026-01-01",
            "quelleHinweis": "test",
            "programme": [{"id": "existing", "name": "Existing", "kategorie": "DFG",
                           "themen": ["frei"], "karriere": ["postdoc"], "rolle": ["lead"],
                           "frist": None, "rolling": True, "status": "laufend",
                           "quelle": "", "standDatum": "2026-01-01"}],
        }
        cat_path = tmp_path / "catalog.json"
        cat_path.write_text(json.dumps(catalog))
        audit_path = tmp_path / "audit.md"

        @ingest.register("test-apply", "Test Apply", "", "api")
        def _test():
            return ingest.ProgrammeUpdate(
                "test-apply",
                [{"id": "test-apply-new", "name": "New From Fetch", "quelle": "https://test.de"}],
                [], "now", [],
            )

        monkeypatch.setattr(ingest, "CATALOG_JSON", cat_path)
        monkeypatch.setattr(ingest, "AUDIT_LOG", audit_path)
        old_argv = sys.argv
        sys.argv = ["ingest.py", "--source", "test-apply", "--apply"]
        try:
            ingest.main()
        except SystemExit:
            pass
        finally:
            sys.argv = old_argv

        out = capsys.readouterr().out
        assert "New:       1" in out

        # Verify catalog WAS modified
        doc = json.loads(cat_path.read_text())
        ids = {p["id"] for p in doc["programme"]}
        assert "existing" in ids
        assert "test-apply-new" in ids

        # Verify audit log
        assert audit_path.exists()
        assert "test-apply" in audit_path.read_text()

        del ingest._REGISTRY["test-apply"]

    def test_source_unknown_exits(self, capsys):
        import sys
        old_argv = sys.argv
        sys.argv = ["ingest.py", "--source", "nonexistent"]
        try:
            with pytest.raises(SystemExit):
                ingest.main()
        finally:
            sys.argv = old_argv


# ---------------------------------------------------------------------------
# Integration: fetched programmes pass validation
# ---------------------------------------------------------------------------


class TestFetchedProgrammesValid:
    """All fetched programmes must pass Programm.from_dict() validation."""

    def test_openaire_prog_valid(self):
        p = ingest._make_prog("openaire", "oa-1", "Test", "https://x", "hint")
        from grant_types import Programm
        prog = Programm.from_dict(p)
        assert prog.kategorie == "EU"
        assert prog.status == "zu-pruefen"

    def test_nih_prog_valid(self):
        p = ingest._make_prog("nih", "nih-1", "Test", "https://x", "hint", frist="2027-01-15")
        from grant_types import Programm
        prog = Programm.from_dict(p)
        assert prog.kategorie == "International"
        assert prog.frist == "2027-01-15"
        assert prog.rolling is False

    def test_nsf_prog_valid(self):
        p = ingest._make_prog("nsf", "nsf-1", "Test", "https://x", "hint", frist="2027-06-30")
        from grant_types import Programm
        prog = Programm.from_dict(p)
        assert prog.kategorie == "International"

    def test_crossref_prog_valid(self):
        p = ingest._make_prog("crossref", "cr-1", "Test", "https://x", "hint")
        from grant_types import Programm
        prog = Programm.from_dict(p)
        assert prog.kategorie == "International"

    def test_bmbf_prog_valid(self):
        # Simulate what _enrich_programme does for BMBF
        p = ingest._make_prog("bmbf", "bmbf-1", "Test", "https://x", "hint")
        from fetchers import _enrich_programme
        enriched = _enrich_programme(p, "bmbf")
        assert enriched is not None
        from grant_types import Programm
        prog = Programm.from_dict(enriched)
        assert prog.kategorie == "BMBF"
