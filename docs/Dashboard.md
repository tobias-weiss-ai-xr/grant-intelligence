# Dashboard

Static GitHub Pages dashboard for exploring the Förder-Radar catalog and source
registry. No build step, no server — pure HTML/CSS/JS with CDN-loaded Alpine.js
and Chart.js.

## URL

**Live:** <https://tobias-weiss-ai-xr.github.io/grant-intelligence/>

## Architecture

```
mcp/catalog.json ─┐
mcp/sources.json ─┤── sync-data.sh ──→ dashboard/data/*.json
                   │                         │
                   └── (no profiles)         ▼
                                    browser fetch() at runtime
                                              │
                                              ▼
                                    Alpine.js dashboard()
                                    ├── Overview cards
                                    ├── Frist-Radar (upcoming deadlines)
                                    ├── Source browser
                                    ├── Programme explorer
                                    └── Charts (Chart.js)
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
- Total programmes (103)
- Categories (9)
- Source groups (26)
- Upcoming deadlines (next 90 days)
- **Urgent deadlines (next 30 days)** – turns red when > 0
- Rolling / no-deadline counts

### Frist-Radar
Table of all upcoming deadlines (next 90 days), sorted by date:
- Programm, Kategorie, Frist, Tage, Status
- Color-coded rows by urgency (WCAG-compliant):
  - red ≤ 14 days (`dl-critical`)
  - orange ≤ 30 days (`dl-soon`)
  - green > 30 days (`dl-normal`)
- Shows an empty hint when no deadlines are within 90 days

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
- **Status bar**: Verifiziert / Laufend / Zu prüfen
- **Deadline timeline**: Upcoming deadlines (next 90 days), color-coded by urgency

## Data Flow

| Source | Dashboard | Filter |
|---|---|---|
| `mcp/catalog.json` | `dashboard/data/catalog.json` | None (full copy) |
| `mcp/sources.json` | `dashboard/data/sources.json` | None (full copy) |
| `mcp/deadline-digest.json` (optional, if present) | `dashboard/data/deadline-digest.json` | None (full copy) |

No profile data is shipped to the dashboard. Profile matching remains a
client-side Python feature (`mcp/profile.py`, `mcp/brief.py --profil-id`).

## Deployment

The GitHub Action (`.github/workflows/deploy-dashboard.yml`) deploys on every
push to `main` that touches `dashboard/`, `mcp/catalog.json`, or
`mcp/sources.json`.

**Steps:**
1. Checkout repository
2. Run `bash dashboard/sync-data.sh` (sync catalog + sources + optional digest)
3. Configure GitHub Pages
4. Upload `dashboard/` as Pages artifact
5. Deploy to GitHub Pages

**Manual deploy:** GitHub → Actions → "Deploy Dashboard" → Run workflow

## Accessibility (WCAG 2.1 AA)

- All text colors meet 4.5:1 contrast ratio (light and dark mode)
- UI components (borders, chart elements) meet 3:1 contrast ratio
- ARIA labels on filters, tables, charts, loading/error regions
- `aria-live="polite"` for dynamic content (filter count, loading)
- `scope="col"` on all table headers
- Skip-to-content link for keyboard users
- Focus indicators (2px blue outline on all interactive elements)
- `prefers-reduced-motion` respected
- `prefers-color-scheme: dark` with WCAG-compliant dark palette
- Colorblind-friendly chart palette (9 distinguishable colors)

## Dependencies

| Dependency | Version | Size | License | Source |
|---|---|---|---|---|
| Alpine.js | 3.x | 15KB | MIT | cdn.jsdelivr.net |
| Chart.js | 4.x | 70KB | MIT | cdn.jsdelivr.net |

No npm, no bundler, no build step. Two `<script>` tags in `index.html`.

## Tech Stack

- **Alpine.js**: Declarative reactivity (`x-data`, `x-for`, `x-show`, `x-model`)
  for filterable tables and dropdowns
- **Chart.js**: Doughnut, bar, and horizontal bar charts for visualizations
- **fetch()**: Runtime JSON loading (same-origin, no CORS issues)
- **CSS custom properties**: WCAG-compliant palette with dark mode via
  `prefers-color-scheme: dark`
