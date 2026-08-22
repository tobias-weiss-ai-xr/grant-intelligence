# Design: Add International Foundations

## Context

The catalog currently has 5 `International` entries (NSF, NIH, UKRI, DACH,
Wellcome). This change adds 15–17 international foundation/funder entries to
cover the major non-German funders that German university researchers can apply
to or collaborate with.

## Approach

### Catalog entries

Each entry follows the existing `International` schema:

```json
{
  "id": "embo-fellowships",
  "name": "EMBO – Fellowships & Young Investigators",
  "kategorie": "International",
  "themen": ["Life Sciences", "Medizin", "Biotechnologie"],
  "karriere": ["postdoc", "junior", "prof"],
  "rolle": ["lead", "partner"],
  "budget_min": null,
  "budget_max": null,
  "dauerJahre": 3,
  "frist": null,
  "rolling": true,
  "status": "laufend",
  "quelle": "https://www.embo.org/funding",
  "standDatum": "2026-08-20",
  "hinweis": "..."
}
```

### Design decisions

1. **Status `"laufend"`** for foundations with rolling/continuous calls.
   **Status `"zu-pruefen"`** for foundations with specific deadlines that
   need periodic verification.

2. **`rolle`**: `"partner"` for foundations that require a local PI (NSF,
   NIH, Gates, Rockefeller, HHMI, CIHR, NSERC, JSPS, ARC, WHO, UNESCO).
   `"lead"` or `"lead+partner"` for foundations where German researchers can
   be PI (EMBO, HFSP, Sloan, Kavli, Templeton, Moore, Leverhulme, Royal
   Society).

3. **`themen`**: Use existing thema values where possible (`Medizin`,
   `Gesundheit`, `Life Sciences`, `Digital`, `KI`, `frei`). Add new thema
   values only if truly needed (`Global Health` already exists for
   Wellcome).

4. **`budget_max`**: `null` (unknown/variable) for most entries. Foundations
   with known grant sizes get specific values (e.g., HFSP postdoc ~$200k).

5. **`dauerJahre`**: Typical grant duration (2–5 years).

6. **`frist`/`rolling`**: `rolling=true` for continuous submission;
   `frist="YYYY-MM-DD"` for specific deadlines; `frist=null` for
   ausschreibungsgebunden (call-based, no fixed deadline).

7. **`hinweis`**: Each entry gets a non-empty `hinweis` describing the
   funder, scope, eligibility for German researchers, and submission mode.

### Source group

Add one source group `international-foundations` to `sources.json` with
per-funder entries (similar to the existing `international` group).

### No code changes

This is a data-only change. No `match.py`, `grant_types.py`, `app.py`, or
`server.py` changes needed. The `Kategorie.INTERNATIONAL` enum value already
exists. New thema values (if any) are free-form strings in the catalog —
no enum validation needed for `themen` (only `kategorie` is enum-validated).

## Entries to add

| # | ID | Name | Themen | Karriere | Rolle | Rolling |
|---|----|------|-------|----------|-------|---------|
| 1 | embo-fellowships | EMBO – Fellowships & Young Investigators | Life Sciences, Medizin, Biotechnologie | postdoc, junior, prof | lead, partner | yes |
| 2 | hfsp-research-grants | HFSP – Human Frontier Science Program | Life Sciences, Biotechnologie | postdoc, prof | lead | yes |
| 3 | gates-foundation | Bill & Melinda Gates Foundation | Gesundheit, Global Health | postdoc, prof, senior | partner | no |
| 4 | rockefeller-foundation | Rockefeller Foundation | Gesundheit, Klimawandel, Nachhaltigkeit | postdoc, prof, senior | partner | no |
| 5 | sloan-foundation | Alfred P. Sloan Foundation | Digital, KI, Informatik | postdoc, prof | lead, partner | no |
| 6 | kavli-foundation | Kavli Foundation | frei | postdoc, prof | partner | no |
| 7 | templeton-foundation | John Templeton Foundation | frei | postdoc, prof | lead, partner | no |
| 8 | hhmi-international | Howard Hughes Medical Institute (International) | Medizin, Life Sciences, Biotechnologie | postdoc, prof | partner | no |
| 9 | moore-foundation | Gordon and Betty Moore Foundation | Nachhaltigkeit, Umwelt, Life Sciences | postdoc, prof | partner | no |
| 10 | leverhulme-trust | Leverhulme Trust | frei | postdoc, junior, prof | lead, partner | yes |
| 11 | royal-society | Royal Society | frei | postdoc, prof | lead, partner | yes |
| 12 | jsps-international | JSPS – Japan Society for Promotion of Science | frei | postdoc, junior, prof | partner | yes |
| 13 | arc-international | ARC – Australian Research Council | frei | postdoc, prof | partner | no |
| 14 | cihr-international | CIHR – Canadian Institutes of Health Research | Medizin, Gesundheit, Life Sciences | postdoc, prof | partner | no |
| 15 | nserc-international | NSERC – Natural Sciences & Engineering Research Council | frei | postdoc, prof | partner | no |
| 16 | who-tdr | WHO/TDR – Tropical Disease Research | Medizin, Gesundheit, Global Health | postdoc, prof | partner | no |
| 17 | unesco-research | UNESCO – Research & Heritage | Bildung, Kultur, Gesellschaft, frei | postdoc, junior, prof | partner | no |

## Risks & mitigations

- **Funder specificity**: Some funders (Gates, Rockefeller) are invitation-based
  or have narrow calls. `hinweis` clarifies eligibility for German researchers.
  `status="zu-pruefen"` for call-based funders.
- **Themen values**: New values like `Global Health` already exist (Wellcome).
  No new enum values needed — `themen` is free-form in the catalog.
- **No breaking changes**: All entries are additive. No existing programme is
  modified. Tests are additive.
