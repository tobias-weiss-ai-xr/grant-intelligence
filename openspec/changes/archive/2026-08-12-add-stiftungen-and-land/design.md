## Design

### Approach

Pure additive data entries following the `Programm` dataclass pattern.

### Data

#### 1. Humboldt Forschungsstipendium

| Field | Value |
|---|---|
| `id` | `humboldt-forschungsstipendium` |
| `kategorie` | `Stiftung` |
| `themen` | `["frei"]` |
| `karriere` | `["postdoc", "junior", "prof"]` |
| `rolle` | `["lead"]` |
| `dauerJahre` | 2 |
| `frist` | `null` |
| `rolling` | `true` |
| `status` | `laufend` |

**Note**: For excellent researchers worldwide. Inbound (to Germany) and outbound. All disciplines. 6–24 months. Rolling applications.

#### 2. Robert Bosch Stiftung

| Field | Value |
|---|---|
| `id` | `robert-bosch-stiftung` |
| `kategorie` | `Stiftung` |
| `themen` | `["Gesundheit", "Bildung", "Gesellschaft", "Globale Fragen"]` |
| `karriere` | `["postdoc", "junior", "prof"]` |
| `rolle` | `["lead"]` |
| `dauerJahre` | 3 |
| `frist` | `null` |
| `rolling` | `false` |
| `status` | `laufend` |

**Note**: Health, education, global issues. Ausschreibungsgebunden. Multiple programme lines.

#### 3. NRW MWK Wissenschaft

| Field | Value |
|---|---|
| `id` | `nrw-mwk-wissenschaft` |
| `kategorie` | `Land` |
| `themen` | `["frei"]` |
| `karriere` | `["postdoc", "junior", "prof"]` |
| `rolle` | `["lead"]` |
| `dauerJahre` | 5 |
| `frist` | `null` |
| `rolling` | `false` |
| `status` | `laufend` |

**Note**: Landesfoerderung NRW. Forschungsinfrastruktur, Nachwuchs, Transfer. Ausschreibungsgebunden.

#### 4. Hightech Agenda Bayern

| Field | Value |
|---|---|
| `id` | `hightech-agenda-bayern` |
| `kategorie` | `Land` |
| `themen` | `["KI", "Digital", "Life Sciences", "Cleantech", "Luft- und Raumfahrt"]` |
| `karriere` | `["postdoc", "junior", "prof"]` |
| `rolle` | `["lead", "partner"]` |
| `dauerJahre` | 5 |
| `frist` | `null` |
| `rolling` | `false` |
| `status` | `laufend` |

**Note**: €5.5B state investment in AI, digital, aerospace, life sciences. Professuren, Forschungszentren, Nachwuchsgruppen.

### Online Verification

| Programme | URL | HTTP |
|---|---|---|
| Humboldt | `humboldt-foundation.de/.../humboldt-forschungsstipendium` | 200 ✅ |
| Bosch | `bosch-stiftung.de/foerderung` | 200 ✅ |
| NRW MWK | `mkw.nrw/wissenschaft` | 200 ✅ |
| HTA Bayern | `stmwk.bayern.de/.../hightech-agenda-bayern.html` | 200 ✅ |
