## Why

The Förder-Radar is Germany-focused, but German researchers frequently collaborate internationally. Bilateral funding opportunities exist but are completely absent from the catalog (0 `International` programmes). The most important international funders for German researchers are:

1. **NSF (US)** — National Science Foundation, the world's largest basic research funder. German researchers can be co-PIs on NSF grants through international collaboration agreements. Confirmed live at `nsf.gov/funding`.

2. **NIH (US)** — National Institutes of Health. German medical/health researchers collaborate on NIH-funded projects. The largest biomedical funder globally. Domain `grants.nih.gov` is real but blocks curl (403).

3. **UKRI (UK)** — UK Research and Innovation. UK-German research collaboration is a major bilateral relationship, especially post-Brexit with dedicated bilateral agreements. Confirmed live at `ukri.org/apply-for-funding/`.

4. **SNSF (CH) / FWF (AT)** — Swiss and Austrian national funders. DACH cooperation (Germany-Austria-Switzerland) is structurally important for German researchers, especially in border regions. SNSF confirmed at `snf.ch`, FWF at `fwf.ac.at`. Added as a single DACH-generic entry since the programmes are structurally similar.

5. **Wellcome Trust (UK)** — Global health funder with an international programme. German health researchers can lead or collaborate on Wellcome-funded projects. Confirmed live at `wellcome.org/research-funding`.

These entries carry the `karriere` `international` flag to signal bilateral/collaborative nature.

## What Changes

- Add 5 programme entries to `catalog.json` with new `kategorie="International"`
- Add 5 source groups to `sources.yaml`
- Add tests for all 5 entries
- Update docs

## Capabilities

### New Capabilities
- `international-funders`: NSF, NIH, UKRI, SNSF/FWF (DACH), Wellcome Trust — all with `kategorie="International"`

### Modified Capabilities
_(none — all changes are additive)_

## Impact

- **catalog.json**: +5 programmes (70 → 75)
- **sources.yaml**: +5 source groups
- **New category**: `International` (0 → 5)
- **Tests**: 112 green (additive)
- **Affected docs**: Datenquellen.md, README.md, CHANGELOG.md
