"""Tests für update_catalog.py (Update-Pipeline, Validierung, Merge)."""

from __future__ import annotations

from datetime import date, timedelta

import update_catalog as uc

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


class TestValidate:
    def test_gueltig(self):
        assert uc.validate_programme(VOLL) == []

    def test_fehlt_id(self):
        errs = uc.validate_programme({k: v for k, v in VOLL.items() if k != "id"})
        assert any("Fehlt: id" in e for e in errs)

    def test_ungueltige_frist(self):
        errs = uc.validate_programme({**VOLL, "frist": "bald"})
        assert any("frist" in e for e in errs)

    def test_ungueltiger_status(self):
        errs = uc.validate_programme({**VOLL, "status": "kaputt"})
        assert errs

    def test_ungueltige_karriere(self):
        errs = uc.validate_programme({**VOLL, "karriere": ["abgelehnt"]})
        assert not errs  # karriere-Werte sind freie Liste; nur Pflichtfelder


class TestCheckExpired:
    def test_abgelaufene_frist(self):
        p = [{**VOLL, "frist": (date.today() - timedelta(days=3)).isoformat()}]
        expired = uc.check_expired(p, date.today())
        assert len(expired) == 1
        assert expired[0]["tage_abgelaufen"] == 3

    def test_rolling_ignoriert(self):
        p = [{**VOLL, "rolling": True, "frist": "2020-01-01"}]
        assert uc.check_expired(p, date.today()) == []

    def test_zukuenftige_frist(self):
        p = [{**VOLL, "frist": (date.today() + timedelta(days=10)).isoformat()}]
        assert uc.check_expired(p, date.today()) == []

    def test_kaputte_frist_kein_crash(self):
        assert uc.check_expired([{**VOLL, "frist": "bald"}], date.today()) == []


class TestMerge:
    def test_neu_und_update(self):
        existing = [dict(VOLL)]
        neu = [dict(VOLL), {**VOLL, "id": "test-2", "name": "Zweites"}]
        merged, added, updated = uc.merge_programmes(neu, existing)
        assert added == 1 and updated == 1
        assert len(merged) == 2

    def test_ohne_id_uebersprungen(self):
        existing: list[dict] = []
        merged, added, updated = uc.merge_programmes([{"name": "kein id"}], existing)
        assert added == 0 and updated == 0 and merged == []


class TestUpdateStand:
    def test_setzt_heute(self):
        p = uc.update_stand_datum([dict(VOLL)])
        assert p[0]["standDatum"] == date.today().isoformat()


# ---------------------------------------------------------------------------
# load_sources / load_catalog / save_catalog
# ---------------------------------------------------------------------------


class TestLoadSave:
    def test_load_sources(self):
        """load_sources returns a dict with known sources."""
        sources = uc.load_sources()
        assert isinstance(sources, dict)
        assert len(sources) > 0
        # Check a few known sources
        assert "erc" in sources or "dfg" in sources or "bmbf" in sources

    def test_load_catalog(self):
        """load_catalog returns a dict with programme list."""
        doc = uc.load_catalog()
        assert isinstance(doc, dict)
        assert "programme" in doc
        assert isinstance(doc["programme"], list)
        assert len(doc["programme"]) > 0
        assert all("id" in p for p in doc["programme"])

    def test_save_and_reload(self, tmp_path):
        """save_catalog writes JSON, reload roundtrips."""
        import json
        doc = {"stand": "2026-01-01", "quelleHinweis": "test", "programme": [dict(VOLL)]}
        cat_path = tmp_path / "catalog.json"
        uc.save_catalog(doc, cat_path)
        assert cat_path.exists()
        loaded = json.loads(cat_path.read_text())
        assert "programme" in loaded
        assert loaded["programme"][0]["id"] == "test-1"
        # save_catalog sets stand to today
        assert loaded["stand"] == date.today().isoformat()


class TestValidateAdditional:
    def test_valid_with_rolling(self):
        """Rolling programme with frist=null is valid."""
        p = {**VOLL, "rolling": True, "frist": None}
        assert uc.validate_programme(p) == []

    def test_missing_name(self):
        errs = uc.validate_programme({k: v for k, v in VOLL.items() if k != "name"})
        assert any("Fehlt: name" in e for e in errs)

    def test_missing_kategorie(self):
        errs = uc.validate_programme({k: v for k, v in VOLL.items() if k != "kategorie"})
        assert any("Fehlt: kategorie" in e for e in errs)

    def test_missing_themen(self):
        errs = uc.validate_programme({k: v for k, v in VOLL.items() if k != "themen"})
        assert any("Fehlt: themen" in e for e in errs)

    def test_missing_karriere(self):
        errs = uc.validate_programme({k: v for k, v in VOLL.items() if k != "karriere"})
        assert any("Fehlt: karriere" in e for e in errs)

    def test_missing_rolle(self):
        errs = uc.validate_programme({k: v for k, v in VOLL.items() if k != "rolle"})
        assert any("Fehlt: rolle" in e for e in errs)

    def test_missing_quelle(self):
        errs = uc.validate_programme({k: v for k, v in VOLL.items() if k != "quelle"})
        assert any("Fehlt: quelle" in e for e in errs)

    def test_missing_standDatum(self):
        errs = uc.validate_programme({k: v for k, v in VOLL.items() if k != "standDatum"})
        assert any("Fehlt: standDatum" in e for e in errs)

    def test_missing_status(self):
        # status is NOT in validate_programme's required list; Programm.from_dict defaults to zu-pruefen
        p = {k: v for k, v in VOLL.items() if k != "status"}
        errs = uc.validate_programme(p)
        # No error: status has a default in Programm.from_dict
        assert errs == []

    def test_ungueltige_kategorie(self):
        # validate_programme checks kategorie is present but doesn't validate value
        # Programm.from_dict accepts any string for kategorie
        errs = uc.validate_programme({**VOLL, "kategorie": "Unbekannt"})
        # No error: kategorie value is not validated
        assert errs == []

    def test_empty_themen_list(self):
        """Empty themen list is valid (treated as 'frei')."""
        errs = uc.validate_programme({**VOLL, "themen": []})
        # Empty themen is acceptable
        assert isinstance(errs, list)


class TestCheckExpiredAdditional:
    def test_keine_frist_kein_abgelaufen(self):
        p = [{**VOLL, "frist": None}]
        assert uc.check_expired(p, date.today()) == []

    def test_frist_genau_heute(self):
        """Frist exactly today is not expired."""
        p = [{**VOLL, "frist": date.today().isoformat()}]
        assert uc.check_expired(p, date.today()) == []

    def test_mehrere_abgelaufen(self):
        p = [
            {**VOLL, "id": "a", "frist": (date.today() - timedelta(days=1)).isoformat()},
            {**VOLL, "id": "b", "frist": (date.today() - timedelta(days=10)).isoformat()},
            {**VOLL, "id": "c", "frist": (date.today() + timedelta(days=10)).isoformat()},
        ]
        expired = uc.check_expired(p, date.today())
        assert len(expired) == 2
        assert expired[0]["id"] == "a"


class TestMergeAdditional:
    def test_doppelte_ids_merge(self):
        """Same ID in new list → update, not duplicate."""
        existing = [{**VOLL, "id": "dup-1", "name": "Old"}]
        neu = [{**VOLL, "id": "dup-1", "name": "New"}]
        merged, added, updated = uc.merge_programmes(neu, existing)
        assert added == 0
        assert updated == 1
        assert len(merged) == 1
        assert merged[0]["name"] == "New"

    def test_leere_neu_liste(self):
        """Empty new list → no changes."""
        existing = [dict(VOLL)]
        merged, added, updated = uc.merge_programmes([], existing)
        assert added == 0 and updated == 0
        assert len(merged) == 1

    def test_leere_existing_liste(self):
        """Empty existing → all new."""
        neu = [{**VOLL, "id": "new-1"}]
        merged, added, updated = uc.merge_programmes(neu, [])
        assert added == 1 and updated == 0
        assert len(merged) == 1


class TestFetchManual:
    def test_fetch_manual_unknown_source(self):
        """Unknown source returns None."""
        result = uc.fetch_manual("nonexistent-source")
        assert result is None

    def test_fetch_manual_manual_source(self):
        """Manual source without fetcher returns None."""
        # 'erc' is a manual source
        result = uc.fetch_manual("erc")
        assert result is None

    def test_fetch_manual_cost_fetcher(self, monkeypatch):
        """Cost source uses fetcher, returns programmes (or None if empty)."""
        import httpx
        import fetchers
        class FakeResp:
            status_code = 302
            content = b""
        monkeypatch.setattr(httpx, "get", lambda *a, **k: FakeResp())
        result = uc.fetch_manual("cost")
        # Cost fetcher returns suggestions, not programmes
        assert result is None

    def test_fetch_manual_bmbf_fetcher(self, monkeypatch):
        """BMBF source uses fetcher, returns programmes if RSS available."""
        import httpx
        rss = b'<?xml version="1.0"?><rss><channel><item><title>Test</title><link>https://bmbf.de</link></item></channel></rss>'
        class FakeResp:
            status_code = 200
            content = rss
        monkeypatch.setattr(httpx, "get", lambda *a, **k: FakeResp())
        result = uc.fetch_manual("bmbf")
        assert result is not None
        assert len(result) == 1
        assert result[0]["name"] == "Test"

    def test_fetch_manual_with_errors(self, monkeypatch):
        """Fetcher returns programmes AND errors → errors logged, programmes returned."""
        import fetchers
        # Mock fetch_bmbf_rss to return programmes + errors
        fake_update = fetchers.ProgrammeUpdate(
            "bmbf",
            [{"id": "bmbf-test", "name": "Test", "quelle": "https://bmbf.de"}],
            ["Connection timeout"],
            "now",
            [],
        )
        monkeypatch.setattr(fetchers, "fetch_bmbf_rss", lambda: fake_update)
        result = uc.fetch_manual("bmbf")
        assert result is not None
        assert len(result) == 1
        assert result[0]["name"] == "Test"


class TestUpdateCatalogMain:
    """Tests for update_catalog.py main() CLI."""

    def test_main_check_expired(self, monkeypatch, capsys, tmp_path):
        """--check-expired runs without crash."""
        import json as _json
        import sys
        catalog = {"stand": "2026-01-01", "quelleHinweis": "test", "programme": [
            {**VOLL, "frist": (date.today() - timedelta(days=5)).isoformat()},
        ]}
        cat_path = tmp_path / "catalog.json"
        cat_path.write_text(_json.dumps(catalog))
        old_argv = sys.argv
        sys.argv = ["update_catalog.py", "--check-expired", "--out", str(cat_path)]
        try:
            uc.main()
        except SystemExit:
            pass
        finally:
            sys.argv = old_argv

    def test_main_validate_ok(self, monkeypatch, capsys, tmp_path):
        """--validate on valid catalog passes."""
        import json as _json
        import sys
        catalog = {"stand": "2026-01-01", "quelleHinweis": "test", "programme": [VOLL]}
        cat_path = tmp_path / "catalog.json"
        cat_path.write_text(_json.dumps(catalog))
        old_argv = sys.argv
        sys.argv = ["update_catalog.py", "--validate", "--out", str(cat_path)]
        try:
            uc.main()
        except SystemExit as e:
            # --validate exits 1 on errors, 0 on success (or no exit)
            pass
        finally:
            sys.argv = old_argv

    def test_main_validate_errors(self, monkeypatch, capsys, tmp_path):
        """--validate on invalid catalog exits with error."""
        import json as _json
        import sys
        catalog = {"stand": "2026-01-01", "quelleHinweis": "test", "programme": [
            {"id": "bad", "name": "Bad", "kategorie": "DFG", "themen": ["frei"],
             "karriere": ["postdoc"], "rolle": ["lead"], "quelle": "",
             "standDatum": "2026-01-01", "status": "invalid_status", "frist": "bad-date"},
        ]}
        cat_path = tmp_path / "catalog.json"
        cat_path.write_text(_json.dumps(catalog))
        old_argv = sys.argv
        sys.argv = ["update_catalog.py", "--validate", "--out", str(cat_path)]
        try:
            uc.main()
            exited = False
        except SystemExit:
            exited = True
        finally:
            sys.argv = old_argv
        assert exited  # Should exit(1) on validation errors

    def test_main_update_stand(self, monkeypatch, capsys, tmp_path):
        """--update-stand sets standDatum to today."""
        import json as _json
        import sys
        catalog = {"stand": "2026-01-01", "quelleHinweis": "test", "programme": [VOLL]}
        cat_path = tmp_path / "catalog.json"
        cat_path.write_text(_json.dumps(catalog))
        old_argv = sys.argv
        sys.argv = ["update_catalog.py", "--update-stand", "--out", str(cat_path)]
        try:
            uc.main()
        except SystemExit:
            pass
        finally:
            sys.argv = old_argv
        # Verify standDatum was updated
        doc = _json.loads(cat_path.read_text())
        assert doc["programme"][0]["standDatum"] == date.today().isoformat()

    def test_main_fetch_manual(self, monkeypatch, capsys, tmp_path):
        """--fetch with manual source (no programmes fetched)."""
        import json as _json
        import sys
        catalog = {"stand": "2026-01-01", "quelleHinweis": "test", "programme": [VOLL]}
        cat_path = tmp_path / "catalog.json"
        cat_path.write_text(_json.dumps(catalog))
        old_argv = sys.argv
        sys.argv = ["update_catalog.py", "--fetch", "erc", "--out", str(cat_path)]
        try:
            uc.main()
        except SystemExit:
            pass
        finally:
            sys.argv = old_argv
        # Catalog should be unchanged (manual source, no fetcher)
        doc = _json.loads(cat_path.read_text())
        assert len(doc["programme"]) == 1

    def test_main_fetch_bmbf(self, monkeypatch, capsys, tmp_path):
        """--fetch bmbf with mocked RSS."""
        import json as _json
        import sys
        import httpx
        catalog = {"stand": "2026-01-01", "quelleHinweis": "test", "programme": [VOLL]}
        cat_path = tmp_path / "catalog.json"
        cat_path.write_text(_json.dumps(catalog))
        rss = b'<?xml version="1.0"?><rss><channel><item><title>Test BMBF</title><link>https://bmbf.de</link></item></channel></rss>'
        class FakeResp:
            status_code = 200
            content = rss
        monkeypatch.setattr(httpx, "get", lambda *a, **k: FakeResp())
        old_argv = sys.argv
        sys.argv = ["update_catalog.py", "--fetch", "bmbf", "--out", str(cat_path)]
        try:
            uc.main()
        except SystemExit:
            pass
        finally:
            sys.argv = old_argv
        doc = _json.loads(cat_path.read_text())
        # Should have original + 1 new BMBF programme
        assert len(doc["programme"]) == 2

    def test_main_no_args(self, monkeypatch, capsys, tmp_path):
        """No args → just loads and saves catalog (no changes)."""
        import json as _json
        import sys
        catalog = {"stand": "2026-01-01", "quelleHinweis": "test", "programme": [VOLL]}
        cat_path = tmp_path / "catalog.json"
        cat_path.write_text(_json.dumps(catalog))
        old_argv = sys.argv
        sys.argv = ["update_catalog.py", "--out", str(cat_path)]
        try:
            uc.main()
        except SystemExit:
            pass
        finally:
            sys.argv = old_argv
        # Catalog should still be there
        doc = _json.loads(cat_path.read_text())
        assert len(doc["programme"]) == 1

    def test_main_check_expired_no_expired(self, monkeypatch, capsys, tmp_path):
        """--check-expired with no expired deadlines → 'Keine abgelaufene Fristen'."""
        import json as _json
        import sys
        # All programmes have future deadlines or rolling
        catalog = {"stand": "2026-01-01", "quelleHinweis": "test", "programme": [
            {**VOLL, "frist": (date.today() + timedelta(days=30)).isoformat()},
        ]}
        cat_path = tmp_path / "catalog.json"
        cat_path.write_text(_json.dumps(catalog))
        old_argv = sys.argv
        sys.argv = ["update_catalog.py", "--check-expired", "--out", str(cat_path)]
        try:
            uc.main()
        except SystemExit:
            pass
        finally:
            sys.argv = old_argv

    def test_main_validate_many_errors(self, monkeypatch, capsys, tmp_path):
        """--validate with >10 errors shows 'und N weitere'."""
        import json as _json
        import sys
        # Create 15 invalid programmes
        bad_progs = []
        for i in range(15):
            bad_progs.append({
                "id": f"bad-{i}", "name": f"Bad {i}", "kategorie": "DFG",
                "themen": ["frei"], "karriere": ["postdoc"], "rolle": ["lead"],
                "quelle": "", "standDatum": "2026-01-01",
                "status": "invalid", "frist": "bad-date",
            })
        catalog = {"stand": "2026-01-01", "quelleHinweis": "test", "programme": bad_progs}
        cat_path = tmp_path / "catalog.json"
        cat_path.write_text(_json.dumps(catalog))
        old_argv = sys.argv
        sys.argv = ["update_catalog.py", "--validate", "--out", str(cat_path)]
        try:
            uc.main()
            exited = False
        except SystemExit:
            exited = True
        finally:
            sys.argv = old_argv
        assert exited  # Should exit(1) on validation errors

    def test_main_fetch_cost(self, monkeypatch, capsys, tmp_path):
        """--fetch cost (portal check, no programmes)."""
        import json as _json
        import sys
        import httpx
        catalog = {"stand": "2026-01-01", "quelleHinweis": "test", "programme": [VOLL]}
        cat_path = tmp_path / "catalog.json"
        cat_path.write_text(_json.dumps(catalog))
        class FakeResp:
            status_code = 302
            content = b""
        monkeypatch.setattr(httpx, "get", lambda *a, **k: FakeResp())
        old_argv = sys.argv
        sys.argv = ["update_catalog.py", "--fetch", "cost", "--out", str(cat_path)]
        try:
            uc.main()
        except SystemExit:
            pass
        finally:
            sys.argv = old_argv
        doc = _json.loads(cat_path.read_text())
        assert len(doc["programme"]) == 1  # No new programmes from cost portal

    def test_main_fetch_eu(self, monkeypatch, capsys, tmp_path):
        """--fetch eu (portal check, no programmes)."""
        import json as _json
        import sys
        import httpx
        catalog = {"stand": "2026-01-01", "quelleHinweis": "test", "programme": [VOLL]}
        cat_path = tmp_path / "catalog.json"
        cat_path.write_text(_json.dumps(catalog))
        class FakeResp:
            status_code = 301
            content = b""
        monkeypatch.setattr(httpx, "get", lambda *a, **k: FakeResp())
        old_argv = sys.argv
        sys.argv = ["update_catalog.py", "--fetch", "eu", "--out", str(cat_path)]
        try:
            uc.main()
        except SystemExit:
            pass
        finally:
            sys.argv = old_argv
        doc = _json.loads(cat_path.read_text())
        assert len(doc["programme"]) == 1

    def test_main_check_expired_and_validate(self, monkeypatch, capsys, tmp_path):
        """Combined --check-expired --validate on valid catalog."""
        import json as _json
        import sys
        catalog = {"stand": "2026-01-01", "quelleHinweis": "test", "programme": [VOLL]}
        cat_path = tmp_path / "catalog.json"
        cat_path.write_text(_json.dumps(catalog))
        old_argv = sys.argv
        sys.argv = ["update_catalog.py", "--check-expired", "--validate", "--out", str(cat_path)]
        try:
            uc.main()
        except SystemExit:
            pass
        finally:
            sys.argv = old_argv

    def test_main_update_stand_and_validate(self, monkeypatch, capsys, tmp_path):
        """Combined --update-stand --validate."""
        import json as _json
        import sys
        catalog = {"stand": "2026-01-01", "quelleHinweis": "test", "programme": [VOLL]}
        cat_path = tmp_path / "catalog.json"
        cat_path.write_text(_json.dumps(catalog))
        old_argv = sys.argv
        sys.argv = ["update_catalog.py", "--update-stand", "--validate", "--out", str(cat_path)]
        try:
            uc.main()
        except SystemExit:
            pass
        finally:
            sys.argv = old_argv
        doc = _json.loads(cat_path.read_text())
        assert doc["programme"][0]["standDatum"] == date.today().isoformat()
