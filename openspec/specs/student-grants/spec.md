# Spec: student-grants

## Purpose

Requirements derived from initial grant catalog expansion (expand-grant-sources change).

---

## Requirements

### Requirement: Deutschlandstipendium programme entry
The system SHALL include a `deutschlandstipendium` programme entry in the catalog
with `kategorie="Bund"`, `karriere=["student"]`, `themen=["thematisch-offen"]`,
`rolling=True`, `status="laufend"`, and `quelle` pointing to the official BMBF
Deutschlandstipendium page. The `hinweis` field SHALL note that applications are
submitted through the university, not directly.

#### Scenario: Deutschlandstipendium visible for students
- **WHEN** `match_profile()` is called with `karriere="student"` and any field.
- **THEN** the Deutschlandstipendium SHALL appear in results with score ≥ 1.

### Requirement: Begabtenförderungswerke programme entries
The system SHALL include programme entries for all 12 Begabtenförderungswerke in
the catalog, each with `kategorie="Stiftung"`, appropriate career levels (student,
junior for BA/MA/PhD as applicable), `themen=["thematisch-offen"]`, and
`quelle` linking to the foundation's official page. IDs SHALL follow the pattern
`bfw-{slug}`. Each entry SHALL include the political/confessional affiliation in
the `hinweis` field (e.g., „SPD-nah", „katholisch").

#### Scenario: All 12 Begabtenförderungswerke present in catalog
- **WHEN** the catalog is loaded and filtered by `kategorie="Stiftung"`.
- **THEN** at least 12 entries with IDs matching `bfw-*` SHALL be present.

#### Scenario: Student matching returns Begabtenförderungswerke
- **WHEN** `match_profile()` is called with `karriere="student"` and any field.
- **THEN** at least 8 Begabtenförderungswerke with `karriere=["student"]` SHALL
  appear in the top results.

#### Scenario: PhD matching returns Begabtenförderungswerke
- **WHEN** `match_profile()` is called with `karriere="junior"`.
- **THEN** Begabtenförderungswerke that support PhD (e.g., Studienstiftung,
  Cusanuswerk, Evangelisches Studienwerk) SHALL appear.

### Requirement: DAAD Auslandsstipendium entry
The system SHALL include a `daad-auslandsstipendium` programme entry with
`kategorie="Stiftung"`, `karriere=["student"]`, `themen=["thematisch-offen"]`,
`rolling=False`, and a deadline reference. The `quelle` SHALL link to DAAD's
scholarship database.

#### Scenario: DAAD outgoing visible for students
- **WHEN** `match_profile()` is called with `karriere="student"` and any field.
- **THEN** `daad-auslandsstipendium` SHALL appear in results.

### Requirement: Erasmus+ programme entry
The system SHALL include an `erasmus-plus` programme entry with
`kategorie="EU"`, `karriere=["student"]`, `themen=["thematisch-offen"]`,
`rolling=True`. The `hinweis` field SHALL note that deadlines are set by the
home university.

#### Scenario: Erasmus+ visible for students
- **WHEN** `match_profile()` is called with `karriere="student"` and any field.
- **THEN** `erasmus-plus` SHALL appear in results with `rolling=True`.
