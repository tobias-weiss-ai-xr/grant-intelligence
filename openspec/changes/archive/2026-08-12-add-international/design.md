## Design

### Approach

Pure additive data entries. Introduces new `kategorie="International"` alongside existing categories. All 5 are bilateral/collaborative — German researchers typically participate as co-PIs or partners, not as lead on foreign national grants.

### Data

#### 1. NSF (US)

| Field | Value |
|---|---|
| `id` | `nsf-international` |
| `kategorie` | `International` |
| `themen` | `["frei"]` |
| `karriere` | `["postdoc", "junior", "prof"]` |
| `rolle` | `["partner"]` |
| `dauerJahre` | 3 |
| `frist` | `null` |
| `rolling` | `false` |
| `status` | `laufend` |

**Note**: US National Science Foundation. German researchers as international collaborators. All disciplines. Multiple calls/year.

#### 2. NIH (US)

| Field | Value |
|---|---|
| `id` | `nih-international` |
| `kategorie` | `International` |
| `themen` | `["Medizin", "Biotechnologie", "Gesundheit", "Life Sciences"]` |
| `karriere` | `["postdoc", "prof"]` |
| `rolle` | `["partner"]` |
| `dauerJahre` | 5 |
| `frist` | `null` |
| `rolling` | `false` |
| `status` | `laufend` |

**Note**: US National Institutes of Health. World's largest biomedical funder. German collaborators common on R01 grants.

#### 3. UKRI (UK)

| Field | Value |
|---|---|
| `id` | `ukri-international` |
| `kategorie` | `International` |
| `themen` | `["frei"]` |
| `karriere` | `["postdoc", "junior", "prof"]` |
| `rolle` | `["lead", "partner"]` |
| `dauerJahre` | 3 |
| `frist` | `null` |
| `rolling` | `false` |
| `status` | `laufend` |

**Note**: UK Research and Innovation. Post-Brexit bilateral agreements with Germany. German researchers can lead or partner.

#### 4. SNSF/FWF (DACH)

| Field | Value |
|---|---|
| `id` | `dach-snsf-fwf` |
| `kategorie` | `International` |
| `themen` | `["frei"]` |
| `karriere` | `["postdoc", "junior", "prof"]` |
| `rolle` | `["lead", "partner"]` |
| `dauerJahre` | 3 |
| `frist` | `null` |
| `rolling` | `false` |
| `status` | `laufend` |

**Note**: DACH cooperation (Switzerland SNSF + Austria FWF). Close structural alignment with DFG. German researchers can lead bilateral projects.

#### 5. Wellcome Trust (UK)

| Field | Value |
|---|---|
| `id` | `wellcome-international` |
| `kategorie` | `International` |
| `themen` | `["Gesundheit", "Global Health", "Medizin", "Life Sciences"]` |
| `karriere` | `["postdoc", "junior", "prof"]` |
| `rolle` | `["lead", "partner"]` |
| `dauerJahre` | 5 |
| `frist` | `null` |
| `rolling` | `false` |
| `status` | `laufend` |

**Note**: Global health research foundation. International programmes. German researchers can lead collaborative grants.

### Online Verification

| Programme | URL | HTTP |
|---|---|---|
| NSF | `nsf.gov/funding` | 200 ✅ |
| NIH | `grants.nih.gov` | 403 (blocks curl, verified domain) ✅ |
| UKRI | `ukri.org/apply-for-funding/` | 200 ✅ |
| SNSF | `snf.ch/de/foerderung` | 200 ✅ (SPA) |
| FWF | `fwf.ac.at` | 200 ✅ |
| Wellcome | `wellcome.org/research-funding` | 200 ✅ |

### Note on `rolle`

Most international entries have `rolle: ["partner"]` since German researchers typically collaborate, not lead foreign national grants. Exceptions: UKRI, DACH, Wellcome where German researchers can lead bilateral/international grants.
