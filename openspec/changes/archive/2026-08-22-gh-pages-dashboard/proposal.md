## Why

The Förder-Radar catalog (97 programmes, 26 source groups) is currently only
accessible via the Python CLI, MCP server, or FastAPI web UI — all of which
require a local Python environment. Stakeholders (researchers, FLASH jury,
collaborators) cannot browse the catalog, investigate sources, or check deadline
status without running the project locally. A static dashboard on GitHub Pages
makes the catalog publicly explorable with zero setup: no Python, no server, no
build step.

## What Changes

- **Static dashboard** (`dashboard/` directory): Single-page app using Alpine.js
  (15KB CDN) and Chart.js (70KB CDN). No npm, no build step, no server.
- **Data sync**: `dashboard/sync-data.sh` copies `catalog.json`, `sources.json`,
  and `profiles.json` from `mcp/` to `dashboard/data/` (public profiles only,
  DSGVO-filtered).
- **GitHub Pages deployment**: `.github/workflows/deploy-dashboard.yml` deploys
  `dashboard/` on every push to `main` (and on manual dispatch).
- **Dashboard features**:
  - Overview cards (total programmes, categories, sources, upcoming deadlines)
  - Source browser (26 source groups: fetcher coverage, update frequency, last
    check, linked programmes)
  - Programme explorer (filterable/sortable table: search, category, status,
    career, deadline)
  - Visualizations (category doughnut chart, status bar chart, deadline timeline)
  - Profile matcher (load public profiles, show matching programmes client-side)
- **Documentation**: `docs/Dashboard.md` explaining the dashboard, data flow, and
  deployment.

## Capabilities

### New Capabilities
- `dashboard`: Static GitHub Pages dashboard for catalog/source exploration with
  client-side filtering, charts, and profile matching. No build step, no server,
  CDN-loaded Alpine.js + Chart.js.

### Modified Capabilities
<!-- None — the dashboard is additive, no existing specs change. -->

## Impact

- **New files**: `dashboard/index.html`, `dashboard/app.js`, `dashboard/style.css`,
  `dashboard/data/` (synced JSON), `dashboard/sync-data.sh`,
  `.github/workflows/deploy-dashboard.yml`, `docs/Dashboard.md`
- **No changes to existing code**: `mcp/` Python modules are untouched. The
  dashboard reads JSON at runtime via `fetch()`.
- **Dependencies**: Alpine.js 3.x and Chart.js 4.x via CDN (no npm, no bundler).
  No new Python dependencies.
- **GitHub Pages**: Must be enabled in repo settings (Source: GitHub Actions).
  The workflow handles build and deployment.
- **DSGVO**: Only public profiles (`einwilligung: true` or `status: aktiv`) are
  shipped to the dashboard. `sync-data.sh` filters out non-consented profiles.
