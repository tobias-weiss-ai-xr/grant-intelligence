## Purpose

A static, publicly accessible dashboard for exploring the Förder-Radar catalog
and source registry. Runs on GitHub Pages with zero build step, zero server, and
zero runtime dependencies beyond two CDN-loaded scripts (Alpine.js, Chart.js).
Enables researchers, FLASH jury members, and collaborators to browse 97
programmes, 26 source groups, and deadline status without installing Python.

## Requirements

### Requirement: Static Dashboard Without Build Step

The dashboard must be deployable as static files (HTML, CSS, JS) with no
compilation, bundling, or server-side rendering. All interactivity comes from
CDN-loaded Alpine.js and Chart.js.

#### Scenario: User opens dashboard URL
- **WHEN** a user navigates to the GitHub Pages URL in any modern browser
- **THEN** the dashboard loads `index.html`, fetches `data/catalog.json` and
  `data/sources.json` via `fetch()`, and renders the overview within 2 seconds
  on a broadband connection
- **AND** no npm install, build step, or Python runtime is required

#### Scenario: CDN unavailable
- **WHEN** the CDN (jsdelivr) is unreachable
- **THEN** the dashboard shows a static fallback message ("Daten werden geladen…
  Bitte später erneut versuchen.") and does not crash with a blank page

### Requirement: Data Sync From Catalog

The dashboard data must be synced from `mcp/catalog.json` and
`mcp/sources.json` before deployment. The sync step is automated via
`dashboard/sync-data.sh` and runs in the GitHub Action before deployment.

#### Scenario: Sync copies catalog data
- **WHEN** `sync-data.sh` runs
- **THEN** `dashboard/data/catalog.json` and `dashboard/data/sources.json` are
  created from their `mcp/` counterparts
- **AND** the JSON is valid and parseable by `fetch()` in the browser

### Requirement: Overview Cards

The dashboard must display summary statistics as cards at the top of the page.

#### Scenario: Overview cards render
- **WHEN** the dashboard loads
- **THEN** four cards are visible: total programmes, total categories, total
  source groups, and upcoming deadlines (next 90 days)
- **AND** each card shows a numeric count and a descriptive label

### Requirement: Source Browser

The dashboard must list all source groups from `sources.json` with metadata.

#### Scenario: Source browser renders
- **WHEN** the user navigates to the "Quellen" (Sources) section
- **THEN** all source groups are listed with: name, URL (as link), type,
  update_frequency, last_check, number of calls, and number of programs
- **AND** each source links to its portal URL

#### Scenario: Fetcher coverage indicator
- **WHEN** the source browser renders
- **THEN** sources with automated fetchers (cost, eu, bmbf) are marked with a
  badge ("Automatisiert") vs. manual sources ("Manuell")

### Requirement: Programme Explorer With Filters

The dashboard must provide a filterable, sortable table of all programmes.

#### Scenario: Full programme table
- **WHEN** the dashboard loads
- **THEN** all programmes from `catalog.json` are displayed in a table with
  columns: name, category, status, career levels, deadline, rolling, budget,
  source

#### Scenario: Filter by search text
- **WHEN** the user types in the search box
- **THEN** the table filters to programmes whose name or themen contain the
  search text (case-insensitive)
- **AND** the filter applies within 100ms for 97 programmes

#### Scenario: Filter by category
- **WHEN** the user selects a category from the dropdown
- **THEN** only programmes in that category are shown
- **AND** selecting "Alle" (All) clears the filter

#### Scenario: Filter by status
- **WHEN** the user selects a status (verifiziert, laufend, zu-pruefen)
- **THEN** only programmes with that status are shown

#### Scenario: Filter by career level
- **WHEN** the user selects a career level (postdoc, junior, prof, senior,
  student, verwaltung, service, IT, bibliothek)
- **THEN** only programmes whose `karriere` array includes that level are shown

#### Scenario: Sort by column
- **WHEN** the user clicks a column header (name, category, deadline, budget)
- **THEN** the table sorts by that column (ascending first, descending on second
  click)

### Requirement: Visualizations

The dashboard must render charts using Chart.js to visualize catalog data.

#### Scenario: Category distribution chart
- **WHEN** the dashboard loads
- **THEN** a doughnut chart shows the distribution of programmes across the 9
  categories (DFG, ERC, BMBF, EU, LAND, STIFTUNG, INDUSTRIE, BUND, INTERNATIONAL)

#### Scenario: Status distribution chart
- **WHEN** the dashboard loads
- **THEN** a bar chart shows the count of programmes by status (verifiziert,
  laufend, zu-pruefen)

#### Scenario: Deadline timeline chart
- **WHEN** the dashboard loads
- **THEN** a horizontal bar chart shows upcoming deadlines (next 90 days),
  sorted by date ascending, with programme name and days-until-deadline

### Requirement: Accessibility (WCAG 2.1 AA)

The dashboard must meet WCAG 2.1 AA contrast ratios and include ARIA labels
for screen readers.

#### Scenario: Text contrast meets WCAG AA
- **WHEN** the dashboard renders in light or dark mode
- **THEN** all text colors meet 4.5:1 contrast ratio against their background
- **AND** all UI components (borders, chart elements) meet 3:1 contrast ratio

#### Scenario: ARIA labels on interactive elements
- **WHEN** a screen reader user navigates the dashboard
- **THEN** all filter inputs have `aria-label`
- **AND** all table headers have `scope="col"`
- **AND** chart canvases have `role="img"` and `aria-label`
- **AND** loading and error regions have `role="status"` / `role="alert"` with
  `aria-live`

#### Scenario: Keyboard navigation
- **WHEN** a keyboard user tabs through the dashboard
- **THEN** a skip-to-content link is visible on focus
- **AND** all sortable column headers are focusable (`tabindex="0"`)
- **AND** focus indicators (2px outline) are visible on all interactive elements

#### Scenario: Reduced motion
- **WHEN** the user has `prefers-reduced-motion: reduce` set
- **THEN** all CSS transitions and animations are disabled

### Requirement: GitHub Pages Deployment

The dashboard must be deployed to GitHub Pages via a GitHub Action on every push
to `main` that touches `dashboard/`, `mcp/catalog.json`, or `mcp/sources.json`.

#### Scenario: Push to main triggers deployment
- **WHEN** a commit is pushed to `main` that changes files in `dashboard/` or
  the JSON data files
- **THEN** the GitHub Action runs `sync-data.sh`, uploads the `dashboard/`
  directory as a Pages artifact, and deploys it
- **AND** the dashboard is live at `https://<owner>.github.io/grant-intelligence/`
  within 2 minutes

#### Scenario: Manual deployment
- **WHEN** the workflow is triggered manually via `workflow_dispatch`
- **THEN** the same deployment process runs regardless of changed files

### Requirement: Honest Data Display

The dashboard must display the same data as the Python catalog — no caching,
no stale data, no hardcoded numbers.

#### Scenario: Data freshness
- **WHEN** the dashboard loads
- **THEN** the `stand` (as-of date) from `catalog.json` is displayed prominently
- **AND** the number of programmes matches `len(programme)` in `catalog.json`

#### Scenario: Source links are real
- **WHEN** the user clicks a source URL
- **THEN** the link opens the real portal (e.g., `https://erc.europa.eu/funding`)
  in a new tab
