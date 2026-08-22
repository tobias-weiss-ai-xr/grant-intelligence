## Why

The catalog has only 5 `International` entries (NSF, NIH, UKRI, DACH, Wellcome).
German university researchers regularly interact with a much broader set of
international foundations and funders — EMBO, HFSP, Gates Foundation, Rockefeller,
Sloan, Kavli, Templeton, Leverhulme Trust, Royal Society, JSPS, and others.
These funders offer postdoc fellowships, research grants, and international
collaboration opportunities that are missing from the radar.

## What Changes

Add ~15 international foundation/funder entries to `catalog.json`:

**European (life sciences):**
- EMBO – European Molecular Biology Organization (fellowships, young investigators)
- HFSP – Human Frontier Science Program (postdoc fellowships, research grants)

**US Foundations (international programs):**
- Gates Foundation – Grand Challenges, global health
- Rockefeller Foundation – health, climate, resilience
- Sloan Foundation – STEM research, computational
- Kavli Foundation – astrophysics, nanoscience, neuroscience
- Templeton Foundation – science, philosophy, big questions
- Howard Hughes Medical Institute (HHMI) – biomedical, international scholars
- Gordon and Betty Moore Foundation – science, environmental conservation

**UK Foundations (beyond Wellcome/UKRI):**
- Leverhulme Trust – all disciplines, research grants
- Royal Society – science fellowships and grants

**Asia/Pacific:**
- JSPS – Japan Society for the Promotion of Science (international fellowships)
- ARC – Australian Research Council (international collaboration)

**Canada:**
- CIHR – Canadian Institutes of Health Research
- NSERC – Natural Sciences and Engineering Research Council of Canada

**UN/International Organizations:**
- WHO/TDR – UN health research (tropical diseases)
- UNESCO – heritage, education, science

All entries are additive — no changes to existing programmes. Each entry
follows the existing `International` schema with `karriere`, `rolle`, `themen`,
`budget`, `frist`/`rolling`, `quelle`, and `hinweis`.

## Capabilities

### New Capabilities
- `international-foundations`: 15–17 international foundation/funder entries
  (EMBO, HFSP, Gates, Rockefeller, Sloan, Kavli, Templeton, HHMI, Moore,
  Leverhulme, Royal Society, JSPS, ARC, CIHR, NSERC, WHO/TDR, UNESCO) covering
  life sciences, global health, STEM, humanities, and bilateral collaboration.

### Modified Capabilities
_(none — all changes are additive)_

## Impact

- **catalog.json**: +15–17 programmes (80 → ~95–97)
- **sources.json**: +1 source group (`international-foundations`) with per-funder entries
- **Category**: `International` (5 → ~20–22)
- **Tests**: new test cases for each entry (additive, no breaking changes)
- **Docs**: `docs/Datenquellen.md` updated with new sources
- **No breaking changes**: existing 181 tests remain green
