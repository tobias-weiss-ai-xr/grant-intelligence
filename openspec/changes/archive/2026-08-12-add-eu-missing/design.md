## Design

### Approach

Pure additive data entries following the `Programm` dataclass pattern.

### Data

#### 1. MSCA Postdoctoral Fellowships (PF)

| Field | Value |
|---|---|
| `id` | `msca-pf` |
| `kategorie` | `EU` |
| `themen` | `["frei"]` |
| `karriere` | `["postdoc"]` |
| `rolle` | `["lead"]` |
| `dauerJahre` | 2 |
| `frist` | `2026-09-09` |
| `rolling` | `false` |
| `status` | `zu-pruefen` |

**Note**: €399M call, deadline 9 Sept 2026. European PF (within/outside Europe) and Global PF (outside EU + return). Max 8 years post-PhD. All disciplines. Mobility rule: not resided in host country >12 months in last 36 months.

#### 2. Horizon Europe Cluster 1 — Health

| Field | Value |
|---|---|
| `id` | `eu-horizon-health` |
| `kategorie` | `EU` |
| `themen` | `["Medizin", "Gesundheit", "Life Sciences", "Biotechnologie"]` |
| `karriere` | `["postdoc", "junior", "prof"]` |
| `rolle` | `["lead", "partner"]` |
| `budget_max` | 15000000 |
| `dauerJahre` | 4 |
| `frist` | `2026-10-20` |
| `rolling` | `false` |
| `status` | `zu-pruefen` |

**Note**: International consortia. €8.5B budget. Topics: disease understanding, prevention, therapy, health systems.

#### 3. Horizon Europe Cluster 2 — Culture, Creativity, Inclusive Society

| Field | Value |
|---|---|
| `id` | `eu-horizon-culture` |
| `kategorie` | `EU` |
| `themen` | `["Kultur", "Kreativwirtschaft", "Sozialwissenschaften", "Demokratie", "Medien"]` |
| `karriere` | `["postdoc", "junior", "prof"]` |
| `rolle` | `["lead", "partner"]` |
| `budget_max` | 10000000 |
| `dauerJahre` | 4 |
| `frist` | `2026-10-20` |
| `rolling` | `false` |
| `status` | `zu-pruefen` |

**Note**: Culture, heritage, social inclusion, democracy, media literacy.

#### 4. Horizon Europe Cluster 3 — Civil Security for Society

| Field | Value |
|---|---|
| `id` | `eu-horizon-security` |
| `kategorie` | `EU` |
| `themen` | `["Cybersicherheit", "Krisenmanagement", "Katastrophenschutz", "Sicherheit"]` |
| `karriere` | `["postdoc", "junior", "prof"]` |
| `rolle` | `["lead", "partner"]` |
| `budget_max` | 10000000 |
| `dauerJahre` | 4 |
| `frist` | `2026-10-20` |
| `rolling` | `false` |
| `status` | `zu-pruefen` |

**Note**: Disaster resilience, cybersecurity, CBRN, border management.

### Online Verification

| Programme | URL | Status |
|---|---|---|
| MSCA PF | `marie-sklodowska-curie-actions.ec.europa.eu/actions/postdoctoral-fellowships` | ✅ HTTP 200, deadline 9 Sep 2026 confirmed |
| Clusters 1-3 | `ec.europa.eu/info/funding-tenders` | Same pattern as existing Cluster 4/5 entries |
