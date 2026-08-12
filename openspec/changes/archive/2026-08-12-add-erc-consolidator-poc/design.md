## Design

### Approach

Pure additive — no code changes, only data additions following the established `Programm` dataclass pattern.

### Data

All 3 programmes follow the existing catalogue schema (camelCase JSON, required fields: `id`, `name`, `kategorie`, `status`, `standDatum`). The existing `expand-grant-sources` change established the pattern for programme entries, which we follow exactly.

#### ERC Consolidator Grant (CoG)

| Field | Value |
|---|---|
| `id` | `erc-cog-2027` |
| `kategorie` | `ERC` |
| `themen` | `["frei"]` |
| `karriere` | `["postdoc", "junior"]` |
| `rolle` | `["lead"]` |
| `budget_max` | 2,000,000 |
| `dauerJahre` | 5 |
| `status` | `zu-pruefen` |

**Note**: ERC CoG has rolling calls but with cut-off dates. Next call deadline: ~2026-04-17 (to verify). We use `rolling: false` with estimated deadline. The CoG scheme targets researchers 7–12 years after PhD — overlaps with `postdoc` and `junior` (W2/W3-equivalent).

#### ERC Proof of Concept (PoC)

| Field | Value |
|---|---|
| `id` | `erc-poc` |
| `kategorie` | `ERC` |
| `themen` | `["Innovation", "Transfer"]` |
| `karriere` | `["postdoc", "junior", "prof"]` |
| `rolle` | `["lead"]` |
| `budget_max` | 150,000 |
| `dauerJahre` | 1–1.5 |
| `status` | `zu-pruefen` |

**Note**: PoC is only for active ERC grantees. We mark with `themen: ["Innovation", "Transfer"]` so matching finds it for innovation searches. Rolling calls throughout the year. Budget is €150K max.

#### DFG Walter Benjamin Programme

| Field | Value |
|---|---|
| `id` | `dfg-walter-benjamin` |
| `kategorie` | `DFG` |
| `themen` | `["frei"]` |
| `karriere` | `["postdoc"]` |
| `rolle` | `["lead"]` |
| `dauerJahre` | 2–3 |
| `frist` | `null` (rolling) |
| `rolling` | `true` |
| `status` | `laufend` |

**Note**: This is the DFG's primary postdoctoral fellowship for researchers returning to Germany or re-entering research. Budget is a fellowship stipend (no project budget). `rolling: true` — applications accepted anytime via elan portal.

### Sources

- `sources.yaml`: Add `erc-cog` and `erc-poc` groups (same pattern as existing `erc` entry, different URLs). Add `walter-benjamin` as sub-source under `dfg`.
- All sources `type: manual`, `update_frequency: quarterly` (ERC) / `monthly` (DFG).

### Validation

- All 3 entries validated via `Programm.from_dict()` in tests
- `match_profile()` tested for each with relevant themes

### No Breaking Changes

All additions are purely additive. Existing 112 tests remain untouched.
