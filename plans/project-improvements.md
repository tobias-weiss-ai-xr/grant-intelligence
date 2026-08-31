# Grant-Intelligence: 8-Point Improvement Plan

## Current State (verified on Python 3.12)

**Tests:** 525 passed, 0 failed, **1 warning**. Coverage: **97%** overall.
- Core modules (grant_types, match, profile, brief, server, app, catalog_lint,
  deadline_digest, export, ingest, fetchers, parsers, update_catalog, saia): **100%**
- `verify_sources.py`: **77%** (54 missing lines — browser/Playwright path, YAML loading, CLI flags)
- `pilot_demo.py`: **88%** (7 missing lines — error/unhappy paths)
- Deprecation warning: `TestAppHttp::test_get_index` — class-scoped fixture as instance method

**Lint (ruff):** 81 errors across 13 files.
- Auto-fixable: 36× I001 (import sort), ~13× F401 (unused imports), 2× F541 (f-string no placeholders), 3× E401 (multi-imports)
- Manual: 3× E402 (import not at top), 1× E731 (lambda assignment)

**Type-check (mypy):** 4 errors
- yaml stubs missing, playwright stubs missing, 2 test annotation issues

**CI:** 4 workflows (catalog-lint, deadline-check, verify-sources, deploy-dashboard) — all on
`self-hosted, ci-host` runners. **No general test/lint/type-check CI.**

**Config gaps:** No `[tool.coverage]` in pyproject.toml, no `fail-under` threshold, no Makefile,
`mcp>=1.0.0` unpinned (v2.x breaks `from mcp.server.fastmcp import FastMCP`).

## Plan

### Phase 1 — Hygiene & CI Gate (single PR, ~2h)

1. **Fix all ruff errors** — `ruff check --fix` (auto) + manual E402/E731 fixes
2. **Fix all mypy errors** — add `types-PyYAML` to dev deps, mypy override for playwright,
   fix 2 test annotations in `test_deadline_digest.py`
3. **Pin `mcp>=1.0,<2`** in `requirements.txt` (prevents v2 breakage)
4. **Add `[tool.coverage]` config** with `fail_under=95` to `pyproject.toml`
5. **Fix deprecation warning** — convert class-scoped fixture to `@classmethod` in `test_mvp.py`
6. **Add `ci-test.yml` workflow** — ruff + mypy + pytest+coverage on push/PR (uses `ubuntu-latest`)
7. **Add `Makefile`** at repo root (test, lint, check, brief, dashboard targets)

### Phase 2 — Coverage Completion (single PR, ~2h)

8. **Add verify_sources.py tests** — mock Playwright, test YAML loading, CLI `--browser`/`--report`
   → 77% → ≥95%
9. **Add pilot_demo.py tests** → 88% → 100%

## Acceptance Criteria
- [ ] `ruff check` → 0 errors
- [ ] `mypy` → 0 errors
- [ ] `pytest` → 525+ passed, 0 warnings
- [ ] Coverage ≥ 95% overall, 100% on all core modules
- [ ] CI test workflow exists
- [ ] `mcp>=1.0,<2` pinned
- [ ] Makefile with test/lint/check/brief targets
