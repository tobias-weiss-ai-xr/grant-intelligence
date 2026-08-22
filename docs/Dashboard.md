# Dashboard

Static GitHub Pages dashboard for exploring the Förder-Radar catalog and source
registry. No build step, no server — pure HTML/CSS/JS with CDN-loaded Alpine.js
and Chart.js.

## URL

**Live:** <https://tobias-weiss-ai-xr.github.io/grant-intelligence/>

## Architecture

```
mcp/catalog.json ─────┐
mcp/sources.json ─────┤── sync-data.sh ──→ dashboard/data/*.json
mcp/profiles.json ────┘                      (DSGVO-filtered)
                                                    │
                                                    ▼
                                         browser fetch() at runtime
                                                    │
                                                    ▼
                                         Alpine.js dashboard()
                                         ├── Overview cards
                                         ├── Source browser
                                         ├── Programme explorer
                                         ├── Charts (Chart.js)
                                         └── Profile matcher
```

## Local Testing

```bash
# 1. Sync data from mcp/ to dashboard/data/
bash dashboard/sync-data.sh

# 2. Start a local web server
cd dashboard
python3 -m http.server 8080

# 3. Open in browser
open http://localhost:8080
```

## Features

### Overview Cards
- Total programmes (97)
- Categories (9)
- Source groups (26)
- Upcoming deadlines (next 90 days)

### Source Browser
All 26 source groups with:
- Name and portal URL (clickable)
- Type (manual / automated)
- Update frequency
- Last check date
- Number of calls and programs

### Programme Explorer
Filterable, sortable table of all programmes:
- **Search**: Full-text search in name and themen
- **Category filter**: DFG, ERC, BMBF, EU, Land, Stiftung, Industrie, Bund, International
- **Status filter**: Verifiziert, Laufend, Zu prüfen
- **Career filter**: Postdoc, Junior, Prof, Senior, Student, Verwaltung, Service, IT, Bibliothek
- **Sortable columns**: Name, Category, Status, Deadline, Budget

### Charts (Chart.js)
- **Category doughnut**: Distribution across 9 categories
- **Status bar**: Verifiziert / Laufend / Zu prüfen
- **Deadline timeline**: Upcoming deadlines (next 90 days), color-coded by urgency

### Profile Matcher
- Load public profiles (DSGVO-filtered: `einwilligung: true` + `status: "aktiv"`)
- Client-side scoring: themen overlap + karriere match + rolle + rolling + status → 0-5
- Results sorted by score, with relevance reason

## Data Flow

| Source | Dashboard | Filter |
|---|---|---|
| `mcp/catalog.json` | `dashboard/data/catalog.json` | None (full copy) |
| `mcp/sources.json` | `dashboard/data/sources.json` | None (full copy) |
| `mcp/profiles.json` | `dashboard/data/profiles.json` | DSGVO: only `einwilligung: true` + `status: "aktiv"` |

`sync-data.sh` uses `jq` (or Python fallback) to filter profiles before
deployment. No private data reaches GitHub Pages.

## Deployment

The GitHub Action (`.github/workflows/deploy-dashboard.yml`) deploys on every
push to `main` that touches `dashboard/`, `mcp/catalog.json`, `mcp/sources.json`,
or `mcp/profiles.json`.

**Steps:**
1. Checkout repository
2. Run `bash dashboard/sync-data.sh` (sync + DSGVO filter)
3. Configure GitHub Pages
4. Upload `dashboard/` as Pages artifact
5. Deploy to GitHub Pages

**Manual deploy:** GitHub → Actions → "Deploy Dashboard" → Run workflow

## DSGVO Compliance

- Only public profiles (`einwilligung: true`, `status: "aktiv"`) are shipped
- No ORCID API calls from dashboard (client-side only)
- No cookies, no tracking, no analytics
- `sync-data.sh` filters profiles via `jq` before deployment

## Dependencies

| Dependency | Version | Size | License | Source |
|---|---|---|---|---|
| Alpine.js | 3.x | 15KB | MIT | cdn.jsdelivr.net |
| Chart.js | 4.x | 70KB | MIT | cdn.jsdelivr.net |

No npm, no bundler, no build step. Two `<script>` tags in `index.html`.

## Tech Stack

- **Alpine.js**: Declarative reactivity (`x-data`, `x-for`, `x-show`, `x-model`)
  for filterable tables, dropdowns, and profile matcher
- **Chart.js**: Doughnut, bar, and horizontal bar charts for visualizations
- **fetch()**: Runtime JSON loading (same-origin, no CORS issues)
- **CSS custom properties**: Dark mode via `prefers-color-scheme: dark`
