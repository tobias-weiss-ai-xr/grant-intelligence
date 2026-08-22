# Design: gh-pages-dashboard

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  GitHub Repo (main branch)                                  │
│                                                             │
│  mcp/catalog.json   mcp/sources.json   mcp/profiles.json    │
│         │                  │                   │            │
│         └──────────┬───────┴───────────────────┘            │
│                    │                                        │
│            dashboard/sync-data.sh                           │
│            (copies + DSGVO-filters JSON)                    │
│                    │                                        │
│            dashboard/data/*.json                            │
│                    │                                        │
│  ┌─────────────────┴──────────────────┐                     │
│  │  dashboard/index.html              │                     │
│  │  dashboard/app.js (Alpine + Chart)  │                     │
│  │  dashboard/style.css               │                     │
│  └────────────────────────────────────┘                     │
│                                                             │
│  .github/workflows/deploy-dashboard.yml                     │
│  (on push to main → sync → upload → deploy to gh-pages)    │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
              GitHub Pages (HTTPS)
   https://tobias-weiss-ai-xr.github.io/grant-intelligence/
```

## Framework Selection

**Alpine.js 3.x (15KB) + Chart.js 4.x (70KB)** — both via CDN, no build step.

| Criterion | Alpine.js + Chart.js | Vue 3 | React | Vanilla JS |
|---|---|---|---|---|
| Build step | None | None (CDN) | None (CDN) | None |
| Size | 85KB total | 90KB | 45KB+ | 0KB |
| Reactivity | Declarative (`x-data`, `x-for`, `x-show`) | Full SPA | Full SPA | Manual DOM |
| Learning curve | Low (HTML attributes) | Medium | Medium | N/A |
| Fit for dashboard | ★★★★★ | ★★★ | ★★★ | ★★ (verbose) |

**Why Alpine.js:** Declarative reactivity in HTML attributes (`x-data`, `x-for`,
`x-show`, `x-model`) — perfect for a filterable table + charts without a full
SPA framework. No virtual DOM, no build step, no npm.

**Why Chart.js:** Mature, CDN-loadable, supports doughnut/bar/horizontal-bar
charts out of the box. 70KB is acceptable for a dashboard.

## Components

### 1. `dashboard/index.html`

Single HTML file with:
- CDN `<script>` tags for Alpine.js (deferred) and Chart.js
- `<body x-data="dashboard()">` root component
- Overview cards section (4 cards)
- Source browser section (table of 26 source groups)
- Programme explorer section (filterable table)
- Charts section (3 Chart.js canvases)
- Profile matcher section (dropdown + filtered results)

### 2. `dashboard/app.js`

`dashboard()` Alpine component function with:
- **State**: `catalog`, `sources`, `profiles`, `loading`, `error`, filter state
  (`search`, `kategorie`, `status`, `karriere`, `profil_id`), chart instances
- **`init()`**: `Promise.all([fetch catalog, fetch sources, fetch profiles])`,
  then render charts
- **Computed getters**: `filtered` (programmes after filters), `categories`
  (unique categories), `upcomingDeadlines` (next 90 days), `sourceStats`
  (fetcher coverage), `matchedProgrammes` (profile-scored)
- **`renderCharts()`**: Destroy existing charts, create new ones on canvases
- **`scoreProgramme(profile, programme)`**: Client-side scoring (themen overlap,
  karriere match, rolle match, rolling bonus) → normalized 0-5

### 3. `dashboard/style.css`

Minimal CSS:
- System font stack (`system-ui, sans-serif`)
- Responsive grid (max-width 1200px, 2-col on tablet, 1-col on mobile)
- Card, table, badge, chart styling
- Dark-mode-friendly via CSS custom properties

### 4. `dashboard/sync-data.sh`

Bash script that:
1. Copies `mcp/catalog.json` → `dashboard/data/catalog.json`
2. Copies `mcp/sources.json` → `dashboard/data/sources.json`
3. Filters `mcp/profiles.json` → `dashboard/data/profiles.json` (only
   `einwilligung: true` AND `status: "aktiv"`)
4. Prints sync summary

**DSGVO filter** uses `jq` (available in GitHub Actions runners):
```bash
jq 'del(.profile[] | select(.einwilligung != true or .status != "aktiv"))' \
  mcp/profiles.json > dashboard/data/profiles.json
```

### 5. `.github/workflows/deploy-dashboard.yml`

GitHub Action:
- **Triggers**: push to `main` on `dashboard/**`, `mcp/catalog.json`,
  `mcp/sources.json`, `mcp/profiles.json`; `workflow_dispatch`
- **Steps**: checkout → run `sync-data.sh` → configure pages → upload artifact
  → deploy
- **Permissions**: `pages: write`, `id-token: write`
- **Environment**: `github-pages`

## Data Flow

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

## Client-Side Matching Algorithm

The profile matcher reimplements a simplified version of `match.py`'s scoring
in JavaScript (no Python dependency at runtime):

```
score = 0
+ themen overlap (count of profile.themen ∩ programme.themen, max 3)
+ karriere match (profile.karriere ∈ programme.karriere → +1)
+ rolle match (if programme.rolle includes "lead" or is empty → +0.5)
+ rolling bonus (programme.rolling → +0.5, no deadline pressure)
+ status bonus (verifiziert → +0.5, laufend → +0.25)
normalized = min(score / 5, 5)  // clamp to 0-5
```

This is intentionally simpler than the Python `match_profile()` (which uses
weighted scoring with `harte_filter` and detailed `begruendung`). The dashboard
matcher is for exploration, not final matching — users should use the CLI/MCP
for authoritative results.

## Error Handling

- **`fetch()` fails**: Display error message in dashboard, show last-known data
  if cached (Alpine stores in component state)
- **Invalid JSON**: Display "Daten konnten nicht geladen werden" error
- **CDN unavailable**: Alpine/Chart.js won't load — `<noscript>` fallback
  with static link to `data/catalog.json`
- **Empty profiles**: Profile matcher dropdown shows "Keine öffentlichen Profile
  verfügbar" if `dashboard/data/profiles.json` has no active profiles

## DSGVO Compliance

- **No private data on GitHub Pages**: `sync-data.sh` filters profiles to
  `einwilligung: true` AND `status: "aktiv"` only
- **No ORCID API calls from dashboard**: Profile matching uses only the
  `themen`/`karriere` fields from `profiles.json`, no external API calls
- **No cookies, no tracking, no analytics**: Pure static page
- **Profiles with `einwilligung: false`**: Excluded entirely from
  `dashboard/data/profiles.json`

## Testing Strategy

1. **Local testing**: Open `dashboard/index.html` via `python3 -m http.server`
   in `dashboard/` directory — verify all features work
2. **Data sync test**: Run `sync-data.sh`, verify JSON is valid and DSGVO filter
   works (no `einwilligung: false` profiles in output)
3. **GitHub Action test**: Push to `main`, verify Action runs and deploys
4. **Browser test**: Verify in Chrome and Firefox that:
   - Overview cards show correct counts
   - Source browser lists all 26 sources
   - Programme table has 97 rows
   - Filters work (search, category, status, career)
   - Charts render correctly
   - Profile matcher scores and filters
5. **DSGVO test**: Verify `dashboard/data/profiles.json` contains only
   `einwilligung: true` + `status: "aktiv"` profiles

## Dependencies

| Dependency | Version | Size | License | Source |
|---|---|---|---|---|
| Alpine.js | 3.x | 15KB | MIT | cdn.jsdelivr.net |
| Chart.js | 4.x | 70KB | MIT | cdn.jsdelivr.net |
| jq | any | — | MIT (GPL) | GitHub Actions runner (pre-installed) |

No npm, no bundler, no build step. Two `<script>` tags in `index.html`.
