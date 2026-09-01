# pilot-setup Specification

## Purpose
TBD - created by archiving change define-pilot-faculty. Update Purpose after archive.

## Requirements

### Requirement: Pilot faculty and seed profiles
The repository SHALL include a `mcp/profiles.json` with a concrete pilot
configuration: Philipps-Universität Marburg as the pilot institution, at least
one real profile (Postdoc, AI/ML research), and at least two additional profile
entries (placeholders permitted) demonstrating coverage across career levels
(postdoc, junior). Each profile SHALL have `einwilligung` set explicitly
(`true` for active pilot profiles, `false` for placeholders pending consent).

#### Scenario: Seed profiles file exists and validates
- **WHEN** `profiles.json` is loaded and each entry is validated via
  `Profile.from_dict`.
- **THEN** all entries SHALL validate without error.

#### Scenario: At least one real postdoc AI profile is present
- **WHEN** `profiles.json` is loaded.
- **THEN** at least one profile SHALL have `karriere="postdoc"`, non-empty
  `themen` containing an AI-related field, and `einwilligung=True`.

#### Scenario: Career-level diversity
- **WHEN** `profiles.json` is loaded.
- **THEN** the set of `karriere` values across profiles SHALL include at least
  two distinct values (e.g., `postdoc` and `junior`).

### Requirement: Demonstrated match results for the pilot
The repository SHALL include a demonstrable run (script or documented command)
that produces match results for the real pilot profile against the catalog and
writes the output to `docs/pilot-ergebnisse.md` (Markdown). The output SHALL
show the top matches with scores, justifications, and deadlines, and SHALL note
the profile used and the catalog stand date.

#### Scenario: Pilot results generated
- **WHEN** the pilot demonstration command is run with the real postdoc profile.
- **THEN** `docs/pilot-ergebnisse.md` SHALL be created containing at least the
  top-3 matches, each with `name`, `score`, `begruendung`, and `frist`.

#### Scenario: Pilot results reflect consent
- **WHEN** the pilot demonstration is run for a profile with
  `einwilligung=False`.
- **THEN** the output SHALL state that matching was skipped due to missing
  consent, with no match results.

### Requirement: Profile UI in the web interface
The FastAPI web UI (`app.py`) SHALL allow selecting an existing profile by id or
entering fields manually (the existing flow). When a profile is selected, the
form SHALL pre-fill the themes and career level from the profile, and the results
page SHALL display the profile name. Selecting a profile without consent SHALL
show a notice that matching is disabled.

#### Scenario: Profile selection pre-fills the form
- **WHEN** the user selects a profile with `einwilligung=True` from a dropdown.
- **THEN** the themes and career fields SHALL be pre-filled and results SHALL be
  generated for that profile.

#### Scenario: Profile without consent shows notice
- **WHEN** the user selects a profile with `einwilligung=False`.
- **THEN** the page SHALL show a notice that matching is disabled and no match
  cards SHALL be rendered.
