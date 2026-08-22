# Tasks: gh-pages-dashboard

## 1. Data Sync Layer

- [ ] 1.1 Create `dashboard/` directory structure: `dashboard/`, `dashboard/data/`
- [ ] 1.2 Create `dashboard/sync-data.sh`: copies `mcp/catalog.json`,
      `mcp/sources.json`, `mcp/profiles.json` → `dashboard/data/`; DSGVO-filters
      profiles (`einwilligung: true` AND `status: "aktiv"` only) via `jq` or
      Python fallback; prints sync summary
- [ ] 1.3 Run `sync-data.sh` and verify `dashboard/data/*.json` are valid JSON
      with correct content (97 programmes, 26 sources, only active profiles)
- [ ] 1.4 Add `dashboard/data/` to `.gitignore` (generated, not committed) OR
      commit it (decide: commit for first deploy, then let Action regenerate)

## 2. Dashboard HTML (`dashboard/index.html`)

- [ ] 2.1 Create `dashboard/index.html` with CDN `<script>` tags for Alpine.js
      3.x (deferred) and Chart.js 4.x
- [ ] 2.2 Add `<body x-data="dashboard()">` root; `<noscript>` fallback linking
      to `data/catalog.json`
- [ ] 2.3 Overview cards section: total programmes, categories, sources,
      upcoming deadlines (next 90 days) — bound to Alpine state
- [ ] 2.4 Source browser section: table of all source groups (name, URL, type,
      update_frequency, last_check, calls count, programs count, fetcher badge)
- [ ] 2.5 Programme explorer section: filterable table (search input, category
      dropdown, status dropdown, career dropdown, sortable column headers)
- [ ] 2.6 Charts section: three `<canvas>` elements for doughnut (categories),
      bar (status), horizontal bar (deadline timeline)
- [ ] 2.7 Profile matcher section: profile dropdown + scored results table
- [ ] 2.8 Footer with data-as-of date (`stand` from catalog), link to repo,
      "Scores are orientation" disclaimer

## 3. Dashboard Logic (`dashboard/app.js`)

- [ ] 3.1 Create `dashboard/app.js` with `dashboard()` Alpine component function
- [ ] 3.2 `init()`: `Promise.all([fetch catalog, fetch sources, fetch profiles])`
      with try/catch error handling; set `loading=false` when done
- [ ] 3.3 State: `catalog`, `sources`, `profiles`, `loading`, `error`, `search`,
      `kategorie`, `status`, `karriere`, `profil_id`, chart instances
- [ ] 3.4 Computed getters: `filtered` (programmes after all filters),
      `categories` (unique), `upcomingDeadlines` (next 90 days sorted),
      `sourceStats` (fetcher coverage), `matchedProgrammes` (profile-scored)
- [ ] 3.5 `scoreProgramme(profile, programme)`: client-side scoring (themen
      overlap, karriere match, rolle match, rolling bonus, status bonus) → 0-5
- [ ] 3.6 `renderCharts()`: destroy existing chart instances, create new
      doughnut (categories), bar (status), horizontal bar (deadlines) on canvases
- [ ] 3.7 Sort functionality: `sortKey`, `sortDir`, `toggleSort(key)` method
- [ ] 3.8 Profile matcher: `selectProfile(id)` loads profile, calls
      `scoreProgramme` for each programme, sorts by score descending

## 4. Dashboard Styling (`dashboard/style.css`)

- [ ] 4.1 Create `dashboard/style.css`: system font stack, responsive grid
      (max-width 1200px), card/table/badge/chart styling
- [ ] 4.2 CSS custom properties for colors (green `#0b5`, blue `#36a2eb`,
      red `#d33`, gray `#777`)
- [ ] 4.3 Dark-mode-friendly via `prefers-color-scheme: dark` media query
- [ ] 4.4 Mobile responsive: 1-column on mobile, 2-column on tablet, 3-column
      on desktop for cards

## 5. GitHub Action (`.github/workflows/deploy-dashboard.yml`)

- [ ] 5.1 Create `.github/workflows/deploy-dashboard.yml` with triggers:
      push to `main` on `dashboard/**`, `mcp/catalog.json`, `mcp/sources.json`,
      `mcp/profiles.json`; `workflow_dispatch`
- [ ] 5.2 Job steps: checkout, run `sync-data.sh`, configure-pages,
      upload-pages-artifact (path: `./dashboard`), deploy-pages
- [ ] 5.3 Permissions: `pages: write`, `id-token: write`; environment:
      `github-pages`
- [ ] 5.4 Enable GitHub Pages via `gh api` (Source: GitHub Actions)

## 6. Documentation

- [ ] 6.1 Create `docs/Dashboard.md`: overview, data flow, local testing
      (`python3 -m http.server` in `dashboard/`), deployment instructions,
      DSGVO notes
- [ ] 6.2 Update `README.md`: add dashboard section with link to GitHub Pages URL,
      mention `dashboard/` directory
- [ ] 6.3 Update `CHANGELOG.md`: add "Dashboard" entry under "Added"

## 7. Local Testing

- [ ] 7.1 Run `python3 -m http.server 8080` in `dashboard/`, open
      `http://localhost:8080` in browser
- [ ] 7.2 Verify: overview cards show 97 programmes, 9 categories, 26 sources,
      correct upcoming deadlines count
- [ ] 7.3 Verify: source browser lists all 26 sources with correct metadata
- [ ] 7.4 Verify: programme table shows all 97 programmes; filters work (search,
      category, status, career); sorting works
- [ ] 7.5 Verify: charts render (doughnut for categories, bar for status,
      timeline for deadlines)
- [ ] 7.6 Verify: profile matcher loads active profiles, scores programmes,
      shows relevance badges
- [ ] 7.7 Verify: DSGVO filter — `dashboard/data/profiles.json` contains only
      `einwilligung: true` + `status: "aktiv"` profiles

## 8. Deployment & Verification

- [ ] 8.1 Commit all files, push to `main`
- [ ] 8.2 Verify GitHub Action runs successfully
- [ ] 8.3 Verify dashboard is live at
      `https://tobias-weiss-ai-xr.github.io/grant-intelligence/`
- [ ] 8.4 Run `openspec validate gh-pages-dashboard` and ensure green
