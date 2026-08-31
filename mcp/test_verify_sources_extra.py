"""Extra tests for verify_sources.py — browser, YAML, CLI, retry paths.

Covers the previously-untested branches:
  - load_config / read_data YAML loading
  - iter_entries edge cases (object_map non-dict, no list_key)
  - render_summary with no broken/bot, and >25 botblocks
  - browser_check (mocked Playwright): not-installed, all status codes, exception
  - run() with browser recheck enabled
  - main() with --browser and --report, --no-fail-early
  - http_check: 429 retry (Retry-After + backoff), 500 retry, SSLError,
    Timeout, ConnectionError, unusual status, throttle path
"""
from __future__ import annotations

import json
from collections import Counter
from unittest import mock

import verify_sources as vs


# ── YAML config / data loading ─────────────────────────────────────────
def test_load_config_json(tmp_path):
    f = tmp_path / "cfg.json"
    f.write_text(json.dumps({"inputs": [], "settings": {}}))
    cfg = vs.load_config(str(f))
    assert isinstance(cfg, dict)


def test_load_config_yaml(tmp_path):
    f = tmp_path / "cfg.yaml"
    f.write_text(
        "inputs:\n"
        "- file: catalog.json\n"
        "  format: yaml\n"
        "  list_key: programme\n"
        "  id_field: id\n"
        "  url_fields: [quelle]\n"
        "settings:\n"
        "  browser: false\n"
    )
    cfg = vs.load_config(str(f))
    assert cfg["settings"]["browser"] is False
    assert cfg["inputs"][0]["file"] == "catalog.json"


def test_read_data_yaml(tmp_path):
    f = tmp_path / "data.yaml"
    f.write_text(
        "papers:\n"
        "- title: P1\n  url: https://p.example/1\n"
        "- title: P2\n  url: https://p.example/2\n"
    )
    data = vs.read_data(str(f), "yaml")
    assert data["papers"][0]["title"] == "P1"


def test_read_data_auto_yaml_fmt(tmp_path):
    """read_data infers yaml format from .yml extension when fmt is None."""
    f = tmp_path / "data.yml"
    f.write_text("items:\n  - a: 1\n  - b: 2\n")
    data = vs.read_data(str(f), None)
    assert len(data["items"]) == 2


# ── iter_entries edge cases ──────────────────────────────────────────────
def test_iter_entries_object_map_non_dict_skipped(tmp_path):
    """object_map entries that aren't dicts are silently skipped."""
    src = {"ev": "not-a-dict", "ok": {"url": "https://ok.example"}}
    (tmp_path / "sources.json").write_text(json.dumps(src))
    cfg = [{"file": "sources.json", "object_map": True, "url_fields": ["url"]}]
    items = list(vs.iter_entries(cfg[0], str(tmp_path)))
    assert [i[0] for i in items] == ["ok"]


def test_iter_entries_no_list_key_uses_data_directly(tmp_path):
    """When list_key is absent, the data itself is the item list."""
    data = [{"id": "x", "quelle": "https://x.example"}]
    (tmp_path / "data.json").write_text(json.dumps(data))
    cfg = {"file": "data.json", "format": "json", "url_fields": ["quelle"]}
    items = list(vs.iter_entries(cfg, str(tmp_path)))
    assert [i[0] for i in items] == ["x"]


# ── render_summary edge cases ────────────────────────────────────────────
def test_render_summary_no_broken_no_bot():
    totals = Counter({"ok": 2})
    results = [
        vs.Result("s", "a", "quelle", "https://a.example", 200, "ok", None, "ok", ""),
        vs.Result("s", "b", "quelle", "https://b.example", 200, "ok", None, "ok", ""),
    ]
    text = vs.render_summary(totals, results)
    assert "BROKEN: 0" in text
    assert "### Broken links" not in text


def test_render_summary_many_botblocks():
    """More than 25 bot-block entries get truncated with a truncation marker."""
    bot_items = [
        vs.Result("s", f"b{i}", "quelle", f"https://b{i}.example", 403,
                  "uncertain", "botblock", "botblock", "")
        for i in range(30)
    ]
    totals = Counter({"botblock": 30})
    text = vs.render_summary(totals, bot_items)
    assert "30" in text
    assert "and 5 more" in text


# ── browser_check (mocked playwright) ────────────────────────────────────
def _make_fake_pw(status):
    """Build a MagicMock hierarchy that mimics playwright.sync_api."""
    fake_resp = mock.MagicMock()
    fake_resp.status = status
    fake_page = mock.MagicMock()
    fake_page.goto.return_value = fake_resp
    fake_browser = mock.MagicMock()
    fake_browser.new_page.return_value = fake_page
    fake_pw = mock.MagicMock()
    fake_pw.chromium.launch.return_value = fake_browser
    return fake_pw


def test_browser_check_not_installed():
    """When playwright cannot be imported, returns uncertain."""
    import builtins
    orig_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "playwright.sync_api":
            raise ImportError("no module")
        return orig_import(name, *args, **kwargs)

    with mock.patch.object(builtins, "__import__", side_effect=fake_import):
        result = vs.browser_check("https://x.example", vs.DEFAULT_UA)
    assert result["kind"] == "uncertain"
    assert "not installed" in result["note"]


def test_browser_check_all_statuses():
    """Browser check classifies: 200/302->ok, 404/410/999->broken, 403->botblock, 500->broken."""
    cases = [(200, "ok"), (302, "ok"), (404, "broken"), (410, "broken"),
             (403, "botblock"), (500, "broken"), (999, "broken")]
    for status, expected in cases:
        fake_pw = _make_fake_pw(status)
        fake_sync = mock.MagicMock()
        fake_sync.sync_playwright.return_value.__enter__ = lambda self, _pw=fake_pw: _pw
        fake_sync.sync_playwright.return_value.__exit__ = lambda *a: False
        with mock.patch.dict("sys.modules",
                             {"playwright": mock.MagicMock(),
                              "playwright.sync_api": fake_sync}):
            result = vs.browser_check("https://x.example", vs.DEFAULT_UA)
        assert result["kind"] == expected, (
            f"status {status} -> {result['kind']}, expected {expected}"
        )


def test_browser_check_exception():
    """Any exception in browser_check -> uncertain (fail-open)."""
    fake_sync = mock.MagicMock()
    fake_sync.sync_playwright.side_effect = RuntimeError("boom")
    with mock.patch.dict("sys.modules",
                         {"playwright": mock.MagicMock(),
                          "playwright.sync_api": fake_sync}):
        result = vs.browser_check("https://x.example", vs.DEFAULT_UA)
    assert result["kind"] == "uncertain"
    assert "RuntimeError" in result["note"]


def test_browser_check_response_none():
    """When goto() returns None (navigation failure) -> broken."""
    fake_pw = _make_fake_pw(0)
    fake_pw.chromium.launch.return_value.new_page.return_value.goto.return_value = None
    fake_sync = mock.MagicMock()
    fake_sync.sync_playwright.return_value.__enter__ = lambda self: fake_pw
    fake_sync.sync_playwright.return_value.__exit__ = lambda *a: False
    with mock.patch.dict("sys.modules",
                         {"playwright": mock.MagicMock(),
                          "playwright.sync_api": fake_sync}):
        result = vs.browser_check("https://x.example", vs.DEFAULT_UA)
    assert result["kind"] == "broken"


# ── run() with browser enabled ───────────────────────────────────────────
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
    return _FakeResp(200)


def _write_cfg(tmp_path, catalogue):
    (tmp_path / "catalog.json").write_text(json.dumps(catalogue))
    return {
        "inputs": [{"file": "catalog.json", "format": "json",
                     "list_key": "programme", "id_field": "id",
                     "url_fields": ["quelle"]}],
        "settings": {"browser": False, "fail_on_broken": True,
                     "per_host_delay": 0, "workers": 4,
                     "fail_early": False, "report": str(tmp_path / "r.json")},
    }


def test_run_with_browser_recheck(tmp_path):
    """Uncertain HTTP results trigger browser_check when browser=True."""
    cat = {"programme": [{"id": "c", "quelle": "https://block.example/c"}]}
    cfg = _write_cfg(tmp_path, cat)
    cfg["settings"]["browser"] = True
    with mock.patch("requests.get", side_effect=_fake_get), \
         mock.patch.object(vs, "browser_check",
                           return_value={"kind": "ok", "note": "browser ok"}):
        totals, results, status = vs.run(cfg, str(tmp_path / "x.json"))
    assert totals["ok"] == 1
    assert results[0].verdict == "ok"
    assert results[0].browser_kind == "ok"
    assert status == 0


# ── main() with --browser and --report ───────────────────────────────────
def test_main_browser_and_report(tmp_path):
    """main() with --browser and --report writes report and returns status."""
    cat = {"programme": [{"id": "a", "quelle": "https://ok.example/a"}]}
    (tmp_path / "catalog.json").write_text(json.dumps(cat))
    cfgf = tmp_path / "cfg.json"
    reportf = tmp_path / "report.json"
    cfgf.write_text(json.dumps({
        "inputs": [{"file": "catalog.json", "format": "json",
                     "list_key": "programme", "id_field": "id",
                     "url_fields": ["quelle"]}],
        "settings": {},
    }))
    with mock.patch("requests.get", side_effect=_fake_get):
        rc = vs.main([str(cfgf), "--browser", "--report", str(reportf)])
    assert rc == 0
    assert reportf.exists()
    rep = json.loads(reportf.read_text())
    assert "results" in rep and "totals" in rep


def test_main_fail_early_flag(tmp_path):
    """main() with --no-fail-early covers the fail_early CLI override path."""
    cat = {"programme": [{"id": "b", "quelle": "https://dead.example/b"}]}
    (tmp_path / "catalog.json").write_text(json.dumps(cat))
    cfgf = tmp_path / "cfg.json"
    cfgf.write_text(json.dumps({
        "inputs": [{"file": "catalog.json", "format": "json",
                     "list_key": "programme", "id_field": "id",
                     "url_fields": ["quelle"]}],
        "settings": {"fail_on_broken": True, "fail_early": True, "workers": 1,
                     "per_host_delay": 0, "report": str(tmp_path / "r.json")},
    }))
    with mock.patch("requests.get", side_effect=_fake_get):
        rc = vs.main([str(cfgf), "--no-fail-early"])
    assert rc == 1  # still fails on broken, but checks all links


def test_main_fail_early_default(tmp_path):
    """Without --no-fail-early, first broken link causes early abort."""
    cat = {"programme": [
        {"id": "b", "quelle": "https://dead.example/b"},
        {"id": "a", "quelle": "https://ok.example/a"},
    ]}
    (tmp_path / "catalog.json").write_text(json.dumps(cat))
    cfgf = tmp_path / "cfg.json"
    cfgf.write_text(json.dumps({
        "inputs": [{"file": "catalog.json", "format": "json",
                     "list_key": "programme", "id_field": "id",
                     "url_fields": ["quelle"]}],
        "settings": {"fail_on_broken": True, "fail_early": True, "workers": 1,
                     "per_host_delay": 0, "report": str(tmp_path / "r.json")},
    }))
    with mock.patch("requests.get", side_effect=_fake_get):
        rc = vs.main([str(cfgf)])
    assert rc == 1


# ── http_check: 429 retry, 500 retry, throttle ──────────────────────────
class _FakeRespWithHeaders:
    """Fake response with headers (for Retry-After)."""
    def __init__(self, status, retry_after=None):
        self.status_code = status
        self.headers = {"Retry-After": retry_after} if retry_after else {}


def test_http_check_429_with_retry_after():
    """429 with valid Retry-After: sleeps and retries; resolves on 2nd attempt."""
    responses = iter([
        _FakeRespWithHeaders(429, retry_after="5"),
        _FakeRespWithHeaders(200),
    ])
    with mock.patch("requests.get", side_effect=lambda *a, **kw: next(responses)), \
         mock.patch("verify_sources.time.sleep"):
        result = vs.http_check("https://rate.example/r", 5, vs.DEFAULT_UA)
    assert result["kind"] == "ok"


def test_http_check_429_with_bad_retry_after():
    """429 with non-numeric Retry-After: ValueError caught, falls back to backoff."""
    responses = iter([
        _FakeRespWithHeaders(429, retry_after="not-a-number"),
        _FakeRespWithHeaders(200),
    ])
    with mock.patch("requests.get", side_effect=lambda *a, **kw: next(responses)), \
         mock.patch("verify_sources.time.sleep"):
        result = vs.http_check("https://rate.example/r", 5, vs.DEFAULT_UA)
    assert result["kind"] == "ok"


def test_http_check_429_exhausted_retries():
    """429 after 3 attempts: returns uncertain (rate-limited)."""
    responses = iter([
        _FakeRespWithHeaders(429),
        _FakeRespWithHeaders(429),
        _FakeRespWithHeaders(429),
    ])
    with mock.patch("requests.get", side_effect=lambda *a, **kw: next(responses)), \
         mock.patch("verify_sources.time.sleep"):
        result = vs.http_check("https://rate.example/r", 5, vs.DEFAULT_UA)
    assert result["kind"] == "uncertain"
    assert "rate-limited" in result["note"]


def test_http_check_500_retries_then_broken():
    """500 server error: retries; if still 500, returns broken."""
    responses = iter([
        _FakeRespWithHeaders(500),
        _FakeRespWithHeaders(500),
        _FakeRespWithHeaders(500),
    ])
    with mock.patch("requests.get", side_effect=lambda *a, **kw: next(responses)), \
         mock.patch("verify_sources.time.sleep"):
        result = vs.http_check("https://srv.example/r", 5, vs.DEFAULT_UA)
    assert result["kind"] == "broken"
    assert "server error" in result["note"]


def test_http_check_ssLError():
    """SSLError -> uncertain."""
    import requests
    with mock.patch("requests.get", side_effect=requests.exceptions.SSLError("bad cert")):
        result = vs.http_check("https://x.example", 5, vs.DEFAULT_UA)
    assert result["kind"] == "uncertain"
    assert "SSL" in result["note"]


def test_http_check_timeout():
    """Timeout -> uncertain."""
    import requests
    with mock.patch("requests.get", side_effect=requests.exceptions.Timeout("slow")):
        result = vs.http_check("https://x.example", 5, vs.DEFAULT_UA)
    assert result["kind"] == "uncertain"
    assert "timeout" in result["note"]


def test_http_check_connection_error():
    """ConnectionError -> broken."""
    import requests
    with mock.patch("requests.get", side_effect=requests.exceptions.ConnectionError("down")):
        result = vs.http_check("https://x.example", 5, vs.DEFAULT_UA)
    assert result["kind"] == "broken"
    assert "connection" in result["note"]


def test_http_check_generic_exception():
    """Non-requests exception -> uncertain (catch-all in http_check)."""
    with mock.patch("requests.get", side_effect=ValueError("unexpected")):
        result = vs.http_check("https://x.example", 5, vs.DEFAULT_UA)
    assert result["kind"] == "uncertain"
    assert "ValueError" in result["note"]


def test_http_check_unusual_status():
    """Status code not matching any known category -> broken (catch-all return)."""
    with mock.patch("requests.get", return_value=_FakeRespWithHeaders(418)):
        result = vs.http_check("https://x.example", 5, vs.DEFAULT_UA)
    assert result["kind"] == "broken"
    assert "418" in result["note"]


def test_throttle_with_delay():
    """_throttle with per_host_delay > 0: enters critical section."""
    vs._throttle("test-host.example", 0.01)
    # Second call should still work (throttle releases lock)
    vs._throttle("test-host.example", 0.01)
    # Different host: independent lock
    vs._throttle("other-host.example", 0.01)


def test_run_with_per_host_delay(tmp_path):
    """run() with non-zero per_host_delay exercises the throttle path."""
    cat = {"programme": [
        {"id": "a", "quelle": "https://ok.example/a"},
        {"id": "b", "quelle": "https://ok.example/b"},
    ]}
    cfg = _write_cfg(tmp_path, cat)
    cfg["settings"]["per_host_delay"] = 0.01
    with mock.patch("requests.get", side_effect=_fake_get):
        totals, _, status = vs.run(cfg, str(tmp_path / "x.json"))
    assert totals["ok"] == 2
    assert status == 0


def test_iter_entries_list_skips_non_dict_items(tmp_path):
    """Non-dict items in a list source are silently skipped (branch coverage)."""
    data = [{"id": "x", "quelle": "https://x.example"}, "not-a-dict", None]
    (tmp_path / "data.json").write_text(json.dumps(data))
    cfg = {"file": "data.json", "format": "json", "url_fields": ["quelle"]}
    items = list(vs.iter_entries(cfg, str(tmp_path)))
    assert [i[0] for i in items] == ["x"]
