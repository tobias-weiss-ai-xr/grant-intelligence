# Spec: phd-grad-colleges

## Purpose

Requirements derived from initial grant catalog expansion for PhD and graduate college funding programmes.

---

## Requirements

### Requirement: DFG IRTG programme entry
The system SHALL include a `dfg-irtg` (International Research Training Group)
programme entry with `kategorie="DFG"`, `karriere=["student", "junior"]`,
`themen=["thematisch-offen"]`, `rolling=False`, and `status="zu-pruefen"`.
The `hinweis` field SHALL note that IRTGs are bilateral and location-specific.

#### Scenario: DFG IRTG visible for PhD students
- **WHEN** `match_profile()` is called with `karriere="junior"` and any field.
- **THEN** `dfg-irtg` SHALL appear in results.

### Requirement: Marie Skłodowska-Curie ITN entry
The system SHALL include an `msc-itn` (Marie Skłodowska-Curie Innovative
Training Networks) programme entry with `kategorie="EU"`,
`karriere=["junior"]`, `themen=["thematisch-offen"]`, `rolling=False`,
`status="zu-pruefen"`. The `quelle` SHALL link to the EU MSCA page.

#### Scenario: MSCA ITN visible for PhD/early postdocs
- **WHEN** `match_profile()` is called with `karriere="junior"`.
- **THEN** `msc-itn` SHALL appear in results.

### Requirement: Marie Skłodowska-Curie COFUND entry
The system SHALL include an `msc-cofund` programme entry with `kategorie="EU"`,
`karriere=["junior", "postdoc"]`, `themen=["thematisch-offen"]`, `rolling=False`,
`status="zu-pruefen"`.

#### Scenario: MSCA COFUND visible for junior and postdoc
- **WHEN** `match_profile()` is called with `karriere="postdoc"` or `"junior"`.
- **THEN** `msc-cofund` SHALL appear in results.

### Requirement: Max Weber Programm Bayern entry
The system SHALL include a `max-weber-bayern` programme entry with
`kategorie="Land"`, `karriere=["student", "junior"]`, `themen=["thematisch-offen"]`,
`rolling=True`, `status="laufend"`.

#### Scenario: Max Weber visible for students and PhD in Bavaria
- **WHEN** `match_profile()` is called with `karriere="student"` or `"junior"`.
- **THEN** `max-weber-bayern` SHALL appear in results.

### Requirement: Gerda Henkel Stiftung entry
The system SHALL include a `gerda-henkel` programme entry with
`kategorie="Stiftung"`, `karriere=["junior", "postdoc"]`,
`themen=["Geschichte", "Archäologie", "Kunstgeschichte", "Islamische Studien"]`,
`rolling=False`, `status="zu-pruefen"`.

#### Scenario: Gerda Henkel visible for humanities PhD/postdoc
- **WHEN** `match_profile()` is called with `karriere="junior"` and
  `felder=["Geschichte"]`.
- **THEN** `gerda-henkel` SHALL appear in results with a positive theme score.

### Requirement: Fritz Thyssen Stiftung entry
The system SHALL include a `fritz-thyssen` programme entry with
`kategorie="Stiftung"`, `karriere=["postdoc", "junior", "prof"]`,
`themen=["thematisch-offen"]`, `rolling=False`, `status="zu-pruefen"`.

#### Scenario: Fritz Thyssen visible for postdocs
- **WHEN** `match_profile()` is called with `karriere="postdoc"`.
- **THEN** `fritz-thyssen` SHALL appear in results.

### Requirement: DFG Graduate School programme entry
The system SHALL include a `dfg-graduate-school` programme entry with
`kategorie="DFG"`, `karriere=["student", "junior"]`, `themen=["thematisch-offen"]`,
`rolling=False`, and `status="zu-pruefen"`.

#### Scenario: DFG Graduate School visible for PhD students
- **WHEN** `match_profile()` is called with `karriere="junior"`.
- **THEN** `dfg-graduate-school` SHALL appear in results.
