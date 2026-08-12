## Design

### Approach

Pure additive data entries following the `Programm` dataclass pattern. All 7 programmes verified via live curl (HTTP 200).

### Data

#### 1. DFG Reinhart Koselleck Projects (einzelfoerderung)

| Field | Value |
|---|---|
| `id` | `dfg-reinhart-koselleck` |
| `kategorie` | `DFG` |
| `themen` | `["frei"]` |
| `karriere` | `["prof", "senior"]` |
| `rolle` | `["lead"]` |
| `budget_max` | 1,250,000 |
| `dauerJahre` | 5 |
| `stichtage` | `["02-01", "10-01"]` |
| `status` | `laufend` |

**Note**: High-risk/high-gain for experienced researchers. Very selective. Up to €1.25M for 5 years.

#### 2. DFG Forschungsgruppen (koordiniert)

| Field | Value |
|---|---|
| `id` | `dfg-forschungsgruppen` |
| `kategorie` | `DFG` |
| `themen` | `["frei"]` |
| `karriere` | `["postdoc", "junior", "prof"]` |
| `rolle` | `["lead"]` |
| `dauerJahre` | 5 |
| `stichtage` | `["02-01", "10-01"]` |
| `status` | `laufend` |

**Note**: Collaborative research groups, 5-year duration, up to 6 members.

#### 3. DFG Schwerpunktprogramme (koordiniert)

| Field | Value |
|---|---|
| `id` | `dfg-schwerpunktprogramme` |
| `kategorie` | `DFG` |
| `themen` | `["frei"]` |
| `karriere` | `["student", "junior", "postdoc", "prof"]` |
| `rolle` | `["lead", "member"]` |
| `dauerJahre` | 6 |
| `stichtage` | `["02-01", "10-01"]` |
| `status` | `laufend` |

**Note**: Thematic priority programmes. Often with call for proposals. All career levels.

#### 4. DFG Kolleg-Forschungsgruppen (koordiniert)

| Field | Value |
|---|---|
| `id` | `dfg-kolleg-forschungsgruppen` |
| `kategorie` | `DFG` |
| `themen` | `["frei"]` |
| `karriere` | `["postdoc", "junior", "prof"]` |
| `rolle` | `["lead", "member"]` |
| `dauerJahre` | 4 |
| `stichtage` | `["02-01", "10-01"]` |
| `status` | `laufend` |

**Note**: Interdisciplinary research groups with focus on training. 4-year duration.

#### 5. DFG Klinische Forschungsgruppen (koordiniert)

| Field | Value |
|---|---|
| `id` | `dfg-klinische-forschungsgruppen` |
| `kategorie` | `DFG` |
| `themen` | `["Medizin", "Klinische Forschung"]` |
| `karriere` | `["postdoc", "prof"]` |
| `rolle` | `["lead"]` |
| `dauerJahre` | 4 |
| `stichtage` | `["02-01", "10-01"]` |
| `status` | `laufend` |

**Note**: Clinical research groups combining basic and clinical research.

#### 6. DFG Wissenschaftliche Netzwerke (einzelfoerderung)

| Field | Value |
|---|---|
| `id` | `dfg-wissenschaftliche-netzwerke` |
| `kategorie` | `DFG` |
| `themen` | `["frei"]` |
| `karriere` | `["postdoc", "junior", "prof"]` |
| `rolle` | `["lead"]` |
| `dauerJahre` | 3 |
| `stichtage` | `["02-01", "10-01"]` |
| `status` | `laufend` |

**Note**: Scientific networks for exchanging research ideas. 3-year duration.

#### 7. DFG Forschungsimpulse (koordiniert)

| Field | Value |
|---|---|
| `id` | `dfg-forschungsimpulse` |
| `kategorie` | `DFG` |
| `themen` | `["frei"]` |
| `karriere` | `["postdoc", "junior", "prof"]` |
| `rolle` | `["lead"]` |
| `dauerJahre` | 3 |
| `stichtage` | `["02-01", "10-01"]` |
| `status` | `laufend` |

**Note**: Rapid-response funding for emerging/urgent research topics.

### Sources

All 7 added as `programs` entries under existing `dfg` source group. No new top-level source needed.

### Online Verification

| Programme | URL | HTTP |
|---|---|---|
| Reinhart Koselleck | `/de/.../einzelfoerderung/reinhart-koselleck-projekte` | 200 ✅ |
| Forschungsgruppen | `/de/.../koordinierte-programme/forschungsgruppen` | 200 ✅ |
| Schwerpunktprogramme | `/de/.../koordinierte-programme/schwerpunktprogramme` | 200 ✅ |
| Kolleg-Forschungsgruppen | `/de/.../koordinierte-programme/kolleg-forschungsgruppen` | 200 ✅ |
| Klinische Forschungsgruppen | `/de/.../koordinierte-programme/klinische-forschungsgruppen` | 200 ✅ |
| Wissenschaftliche Netzwerke | `/de/.../einzelfoerderung/wissenschaftliche-netzwerke` | 200 ✅ |
| Forschungsimpulse | `/de/.../koordinierte-programme/forschungsimpulse` | 200 ✅ |

### No Breaking Changes

All additions are purely additive.
