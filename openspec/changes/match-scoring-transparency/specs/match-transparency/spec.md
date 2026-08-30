# Spec: Match Scoring Transparency

Delta for `match-transparency`.

## ADDED Requirements

### Requirement: M1 — Structured score breakdown on every match

Every `MatchResult` produced by `match_profile` or `next_deadline` MUST carry
a `punkte` field: a list of components `{"name", "punkte", "max", "detail"}`
covering exactly `Thema` (0–3) and `Karriere` (0–1). For every result the sum
of component `punkte` MUST equal `score`, the sum of `max` MUST equal 4, and
`thema` component `detail` MUST list the matched fields (or be `None`).
`MatchResult.punkte` defaults to `None` for results constructed without a
breakdown (backward compatible).

#### Scenario: Breakdown matches the total
- **GIVEN** a profile with fields and a career level
- **WHEN** `match_profile` runs with `top=10`
- **THEN** every result has `punkte` with names `["Thema", "Karriere"]`,
  `sum(punkte) == score`, and `sum(max) == 4`

#### Scenario: Career detail reflects the point
- **GIVEN** a result whose career component has 1 point
- **WHEN** inspecting its `punkte`
- **THEN** the Karriere `detail` is non-empty; for 0-point components it is
  `None`

### Requirement: M2 — Breakdown surfaces through the MCP API

`server._serialize` MUST include the `punkte` breakdown verbatim in the
serialized match result, so `match_best`/`naechste_fristen` clients can
explain scores. The field is additive; clients ignoring it keep working.

#### Scenario: Serialized result carries punkte
- **GIVEN** a `MatchResult` with a `punkte` breakdown
- **WHEN** `_serialize` runs
- **THEN** the output dict contains `punkte` equal to the result's breakdown

### Requirement: M3 — Brief shows true maxima and components

The weekly brief table row MUST render the score with its true maximum and
component breakdown (e.g. `3/4 (Thema 2/3 · Karriere 1/1)`) instead of a
fixed `/5`. Without a breakdown it falls back to `/4`. The string `/5` MUST
no longer appear in brief rows.

#### Scenario: Brief row renders breakdown
- **GIVEN** a `MatchResult` with `punkte`
- **WHEN** the brief row is rendered
- **THEN** the cell contains `3/4`, `Thema 2/3`, `Karriere 1/1` and not `/5`

#### Scenario: Fallback without breakdown
- **GIVEN** a `MatchResult` with `punkte=None`
- **WHEN** the brief row is rendered
- **THEN** the cell shows `/4` and not `/5`
