"""Offline tests for verify_sources.py (link-liveness verifier).

Network is mocked: http_check is exercised via a fake requests.get; the
browser stage is disabled (browser=False) so no Playwright is needed.
"""
import json
from unittest import mock

import pytest
import requests

import verify_sources as vs


# ── entry extraction ──────────────────────────────────────────────────────
def test_iter_entries_json_list_skips_empty(tmp_path):
    cat = {"programme": [
        {"id": "a", "quelle": "https://x.example/a"},
        {"id": "b", "quelle": ""},          # empty -> skipped
    ]}
    (tmp_path / "catalog.json").write_text(json.dumps(cat))
    cfg = {"file": "catalog.json", "format": "json", "list_key": "programme",
           "id_field": "id", "url_fields": ["quelle"]}
    items = list(vs.iter_entries(cfg, str(tmp_path)))
    assert [i[0] for i in items] == ["a"]
    assert items[0][2] == "quelle"


def test_iter_entries_json_object_map(tmp_path):
    src = {"ev": {"name": "EV", "url": "https://ev.example"},
           "kas": {"name": "KAS", "url": ""}}   # empty -> skipped
    (tmp_path / "sources.json").write_text(json.dumps(src))
    cfg = {"file": "sources.json", "object_map": True, "id_field": "key",
           "url_fields": ["url"]}
    items = list(vs.iter_entries(cfg, str(tmp_path)))
    assert {i[0] for i in items} == {"ev"}


def test_iter_entries_yaml_list_multi_field(tmp_path):
    txt = ("papers:\n"
           "- title: P1\n  url: https://p.example/1\n"
           "- title: P2\n  url: ''\n  code_url: https://c.example/2\n")
    (tmp_path / "papers.yaml").write_text(txt)
    cfg = {"file": "papers.yaml", "format": "yaml", "list_key": "papers",
           "id_field": "title", "url_fields": ["url", "code_url"]}
    items = list(vs.iter_entries(cfg, str(tmp_path)))
    assert {i[0] for i in items} == {"P1", "P2"}
    assert len(items) == 2  # P2: empty url but code_url counted


# ── http classification (mock requests.get) ──────────────────────────────
class _FakeResp:
    def __init__(self, status):
        self.status_code = status


def _fake_get(url, **kw):
    if "dead.example" in url:
        return _FakeResp(404)
    if "block.example" in url:
        return _FakeResp(403)
    if "rate.example" in url:
        return _FakeResp(429)
    if "down.example" in url:
        raise requests.exceptions.ConnectionError("x")
    if "slow.example" in url:
        raise requests.exceptions.Timeout("x")
    return _FakeResp(200)


def test_http_check_classification():
    with mock.patch("requests.get", side_effect=_fake_get):
        assert vs.http_check("https://ok.example", 5, vs.DEFAULT_UA)["kind"] == "ok"
        assert vs.http_check("https://dead.example", 5, vs.DEFAULT_UA)["kind"] == "broken"
        assert vs.http_check("https://block.example", 5, vs.DEFAULT_UA)["kind"] == "uncertain"
        assert vs.http_check("https://rate.example", 5, vs.DEFAULT_UA)["kind"] == "uncertain"
        assert vs.http_check("https://down.example", 5, vs.DEFAULT_UA)["kind"] == "broken"


def test_run_rate_limit_is_botblock_not_broken(tmp_path):
    cat = {"programme": [{"id": "r", "quelle": "https://rate.example/r"}]}
    cfg = _write_cfg(tmp_path, cat)
    with mock.patch("requests.get", side_effect=_fake_get):
        totals, results, status = vs.run(cfg, str(tmp_path / "x.json"))
    assert totals["broken"] == 0 and totals["botblock"] == 1 and status == 0
        assert vs.http_check("https://slow.example", 5, vs.DEFAULT_UA)["kind"] == "uncertain"


def test_resolve_verdict():
    assert vs.resolve_verdict("ok", None) == "ok"
    assert vs.resolve_verdict("broken", None) == "broken"
    assert vs.resolve_verdict("uncertain", None) == "botblock"   # no browser -> warn
    assert vs.resolve_verdict("uncertain", "ok") == "ok"
    assert vs.resolve_verdict("uncertain", "broken") == "broken"
    assert vs.resolve_verdict("uncertain", "botblock") == "botblock"


# ── end-to-end run ───────────────────────────────────────────────────────
def _write_cfg(tmp_path, catalogue):
    (tmp_path / "catalog.json").write_text(json.dumps(catalogue))
    cfg = {
        "inputs": [{"file": "catalog.json", "format": "json", "list_key": "programme",
                    "id_field": "id", "url_fields": ["quelle"]}],
        "settings": {"browser": False, "fail_on_broken": True,
                     "report": str(tmp_path / "r.json")},
    }
    return cfg


def test_run_end_to_end_counts_and_fails(tmp_path):
    cat = {"programme": [
        {"id": "a", "quelle": "https://ok.example/a"},
        {"id": "b", "quelle": "https://dead.example/b"},
        {"id": "c", "quelle": "https://block.example/c"},
    ]}
    cfg = _write_cfg(tmp_path, cat)
    with mock.patch("requests.get", side_effect=_fake_get):
        totals, results, status = vs.run(cfg, str(tmp_path / "x.json"))
    assert totals["ok"] == 1 and totals["broken"] == 1 and totals["botblock"] == 1
    assert status == 1  # broken -> fail


def test_run_botblock_does_not_fail(tmp_path):
    cat = {"programme": [{"id": "c", "quelle": "https://block.example/c"}]}
    cfg = _write_cfg(tmp_path, cat)
    with mock.patch("requests.get", side_effect=_fake_get):
        totals, results, status = vs.run(cfg, str(tmp_path / "x.json"))
    assert totals["broken"] == 0
    assert status == 0  # only bot-block -> ok


def test_main_no_fail_override(tmp_path, capsys):
    cat = {"programme": [{"id": "b", "quelle": "https://dead.example/b"}]}
    (tmp_path / "catalog.json").write_text(json.dumps(cat))
    cfgf = tmp_path / "cfg.json"
    cfgf.write_text(json.dumps({
        "inputs": [{"file": "catalog.json", "format": "json", "list_key": "programme",
                    "id_field": "id", "url_fields": ["quelle"]}],
        "settings": {"report": str(tmp_path / "r.json")},
    }))
    with mock.patch("requests.get", side_effect=_fake_get):
        rc = vs.main([str(cfgf), "--no-fail"])
    assert rc == 0  # --no-fail overrides fail_on_broken
    # main() also writes the JSON report
    assert (tmp_path / "r.json").exists()
    rep = json.load(open(tmp_path / "r.json"))
    assert rep["totals"]["broken"] == 1
