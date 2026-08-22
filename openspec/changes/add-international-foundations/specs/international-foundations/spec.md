## Purpose

International foundation and funder entries in the Förder-Radar catalog, enabling
researchers to discover funding from non-German foundations, bilateral councils,
and UN/international organizations beyond the existing 5 entries (NSF, NIH, UKRI,
DACH, Wellcome).

## ADDED Requirements

### Requirement: R1 — EMBO entry
The catalog.json MUST include an `embo-fellowships` programme entry for EMBO
fellowships (postdoc, junior, prof; lead+partner; Life Sciences, Medizin).

#### Scenario: Postdoc searches for life sciences funding
- **WHEN** a researcher profile with `karriere="postdoc"` and `themen=["Life Sciences"]` calls `match_profile()`
- **THEN** `embo-fellowships` appears in results with score ≥ 2

### Requirement: R2 — HFSP entry
The catalog.json MUST include an `hfsp-research-grants` programme entry for the
Human Frontier Science Program (postdoc, prof; lead; Life Sciences, Biotechnologie).

#### Scenario: Professor searches for international life sciences grants
- **WHEN** a researcher profile with `karriere="prof"` and `themen=["Life Sciences"]` calls `match_profile()`
- **THEN** `hfsp-research-grants` appears in results with score ≥ 2

### Requirement: R3 — Gates Foundation entry
The catalog.json MUST include a `gates-foundation` programme entry for the Bill &
Melinda Gates Foundation (postdoc, prof, senior; partner; Gesundheit, Global Health).

#### Scenario: Senior researcher searches for global health funding
- **WHEN** a researcher profile with `karriere="prof"` and `themen=["Global Health"]` calls `match_profile()`
- **THEN** `gates-foundation` appears in results with score ≥ 2

### Requirement: R4 — Rockefeller Foundation entry
The catalog.json MUST include a `rockefeller-foundation` programme entry for the
Rockefeller Foundation (postdoc, prof, senior; partner; Gesundheit, Klimawandel,
Nachhaltigkeit).

#### Scenario: Researcher searches for climate/health funding
- **WHEN** a researcher profile with `karriere="prof"` and `themen=["Gesundheit"]` calls `match_profile()`
- **THEN** `rockefeller-foundation` appears in results with score ≥ 2

### Requirement: R5 — Sloan Foundation entry
The catalog.json MUST include a `sloan-foundation` programme entry for the Alfred
P. Sloan Foundation (postdoc, prof; lead, partner; Digital, KI, Informatik).

#### Scenario: Researcher searches for computational/STEM funding
- **WHEN** a researcher profile with `karriere="prof"` and `themen=["Digital"]` calls `match_profile()`
- **THEN** `sloan-foundation` appears in results with score ≥ 2

### Requirement: R6 — Kavli Foundation entry
The catalog.json MUST include a `kavli-foundation` programme entry for the Kavli
Foundation (postdoc, prof; partner; frei — astrophysics, nanoscience, neuroscience).

#### Scenario: Researcher searches for open-theme international funding
- **WHEN** a researcher profile with `karriere="prof"` and `themen=["frei"]` calls `match_profile()`
- **THEN** `kavli-foundation` appears in results with score ≥ 2

### Requirement: R7 — Templeton Foundation entry
The catalog.json MUST include a `templeton-foundation` programme entry for the
John Templeton Foundation (postdoc, prof; lead, partner; frei — science, philosophy,
big questions).

#### Scenario: Researcher searches for interdisciplinary funding
- **WHEN** a researcher profile with `karriere="prof"` and `themen=["frei"]` calls `match_profile()`
- **THEN** `templeton-foundation` appears in results with score ≥ 2

### Requirement: R8 — HHMI entry
The catalog.json MUST include an `hhmi-international` programme entry for Howard
Hughes Medical Institute international scholars (postdoc, prof; partner; Medizin,
Life Sciences, Biotechnologie).

#### Scenario: Postdoc searches for biomedical international funding
- **WHEN** a researcher profile with `karriere="postdoc"` and `themen=["Medizin"]` calls `match_profile()`
- **THEN** `hhmi-international` appears in results with score ≥ 2

### Requirement: R9 — Moore Foundation entry
The catalog.json MUST include a `moore-foundation` programme entry for the Gordon
and Betty Moore Foundation (postdoc, prof; partner; Nachhaltigkeit, Umwelt, Life
Sciences).

#### Scenario: Researcher searches for environmental/conservation funding
- **WHEN** a researcher profile with `karriere="prof"` and `themen=["Umwelt"]` calls `match_profile()`
- **THEN** `moore-foundation` appears in results with score ≥ 2

### Requirement: R10 — Leverhulme Trust entry
The catalog.json MUST include a `leverhulme-trust` programme entry for the
Leverhulme Trust (postdoc, junior, prof; lead, partner; frei — all disciplines).

#### Scenario: Junior researcher searches for UK funding
- **WHEN** a researcher profile with `karriere="junior"` and `themen=["frei"]` calls `match_profile()`
- **THEN** `leverhulme-trust` appears in results with score ≥ 2

### Requirement: R11 — Royal Society entry
The catalog.json MUST include a `royal-society` programme entry for the Royal
Society (postdoc, prof; lead, partner; frei — STEM).

#### Scenario: Postdoc searches for UK science fellowship
- **WHEN** a researcher profile with `karriere="postdoc"` and `themen=["frei"]` calls `match_profile()`
- **THEN** `royal-society` appears in results with score ≥ 2

### Requirement: R12 — JSPS entry
The catalog.json MUST include a `jsps-international` programme entry for the Japan
Society for the Promotion of Science (postdoc, junior, prof; partner; frei).

#### Scenario: Postdoc searches for Japan collaboration
- **WHEN** a researcher profile with `karriere="postdoc"` and `themen=["frei"]` calls `match_profile()`
- **THEN** `jsps-international` appears in results with score ≥ 2

### Requirement: R13 — ARC entry
The catalog.json MUST include an `arc-international` programme entry for the
Australian Research Council (postdoc, prof; partner; frei).

#### Scenario: Professor searches for Australia collaboration
- **WHEN** a researcher profile with `karriere="prof"` and `themen=["frei"]` calls `match_profile()`
- **THEN** `arc-international` appears in results with score ≥ 2

### Requirement: R14 — CIHR entry
The catalog.json MUST include a `cihr-international` programme entry for the
Canadian Institutes of Health Research (postdoc, prof; partner; Medizin, Gesundheit,
Life Sciences).

#### Scenario: Postdoc searches for Canadian health funding
- **WHEN** a researcher profile with `karriere="postdoc"` and `themen=["Medizin"]` calls `match_profile()`
- **THEN** `cihr-international` appears in results with score ≥ 2

### Requirement: R15 — NSERC entry
The catalog.json MUST include an `nserc-international` programme entry for the
Natural Sciences and Engineering Research Council of Canada (postdoc, prof; partner;
frei — STEM, Informatik, Technik).

#### Scenario: Professor searches for Canadian science funding
- **WHEN** a researcher profile with `karriere="prof"` and `themen=["frei"]` calls `match_profile()`
- **THEN** `nserc-international` appears in results with score ≥ 2

### Requirement: R16 — WHO/TDR entry
The catalog.json MUST include a `who-tdr` programme entry for WHO/TDR tropical
disease research (postdoc, prof; partner; Medizin, Gesundheit, Global Health).

#### Scenario: Researcher searches for tropical disease funding
- **WHEN** a researcher profile with `karriere="prof"` and `themen=["Global Health"]` calls `match_profile()`
- **THEN** `who-tdr` appears in results with score ≥ 2

### Requirement: R17 — UNESCO entry
The catalog.json MUST include a `unesco-research` programme entry for UNESCO
research and heritage programmes (postdoc, junior, prof; partner; Bildung, Kultur,
Gesellschaft, frei).

#### Scenario: Researcher searches for education/heritage funding
- **WHEN** a researcher profile with `karriere="prof"` and `themen=["Bildung"]` calls `match_profile()`
- **THEN** `unesco-research` appears in results with score ≥ 2
