# researcher-profile Specification

## Purpose
TBD - created by archiving change define-pilot-faculty. Update Purpose after archive.

## Requirements

### Requirement: Profile data model
The system SHALL provide a type-safe `Profile` dataclass in `mcp/profile.py`
with the fields: `id`, `name`, `karriere`, `themen` (list), `orcid` (string,
optional), `publikationen` (list), `einwilligung` (bool), `status` (string),
`standDatum` (ISO date), `hinweis` (string). It SHALL support `from_dict` /
`to_dict` converting between the camelCase JSON storage format and the dataclass,
analogous to `Programm` in `grant_types.py`.

#### Scenario: Valid profile round-trips through JSON
- **WHEN** a `Profile` is constructed with all required fields and `to_dict()` is
  called, then `from_dict(result)` SHALL produce an equal `Profile`.
- **THEN** camelCase keys (`standDatum`) map correctly to snake_case fields
  (`standDatum` ↔ `stand_datum`).

#### Scenario: Missing required fields are rejected
- **WHEN** a `Profile` is constructed without `id`, `name`, or `karriere`.
- **THEN** construction SHALL raise `ValueError` listing the missing fields.

#### Scenario: Invalid career level is rejected
- **WHEN** a `Profile` is constructed with `karriere="astronaut"`.
- **THEN** construction SHALL raise `ValueError`, because the value is not in the
  `Karrierestufe` enum.

### Requirement: Profile persistence
The system SHALL persist profiles in `mcp/profiles.json` with the same envelope
structure as `catalog.json` (a `stand` date, a `quelleHinweis` string, and a
`profile` array). A `load_profiles()` function SHALL read and return the list;
a `save_profiles()` function SHALL write the list back with an updated `stand`
date.

#### Scenario: Load and save round-trip
- **WHEN** `save_profiles(list)` is called followed by `load_profiles()`.
- **THEN** the returned list SHALL equal the saved list.

#### Scenario: Missing profiles file
- **WHEN** `load_profiles()` is called and `profiles.json` does not exist.
- **THEN** it SHALL return an empty list (not raise), so a fresh pilot starts
  without error.

### Requirement: Consent gating for matching
The system SHALL refuse to match a profile whose `einwilligung` is `False`.
`match_profile()` and `next_deadline()`, when given a `Profile` with
`einwilligung=False`, SHALL return an empty list. The MCP `brief` and
`match_best` tools, when given a `profil_id` resolving to a profile without
consent, SHALL return a clear error message indicating missing consent rather
than silent empty results.

#### Scenario: Matching refused without consent
- **WHEN** `match_profile()` is called with a `Profile` where
  `einwilligung=False`.
- **THEN** it SHALL return an empty list, regardless of `themen` or `karriere`.

#### Scenario: Matching works with consent
- **WHEN** `match_profile()` is called with a `Profile` where
  `einwilligung=True` and matching `themen`.
- **THEN** it SHALL return scored results identical to calling with the same
  `themen`/`karriere` directly.

#### Scenario: MCP brief reports missing consent
- **WHEN** the `brief` MCP tool is called with a `profil_id` whose profile has
  `einwilligung=False`.
- **THEN** the response SHALL include a `fehler` field with the message
  „Einwilligung fehlt – Profil kann nicht gematcht werden" and empty match lists.

### Requirement: ORCID Public API adapter
The system SHALL provide a `fetch_orcid(orcid_id)` function that queries the
ORCID Public API (`https://pub.orcid.org/v3.0/{orcid}/works`, JSON) and returns
a list of publication titles plus derived theme keywords. It SHALL only be
invoked when the profile has `einwilligung=True` and a non-empty `orcid`. It
SHALL handle network errors, non-200 responses, and malformed JSON gracefully by
returning an empty result with a logged warning (no exception propagated to the
caller).

#### Scenario: Successful ORCID fetch enriches themes
- **WHEN** `fetch_orcid("0000-0001-2345-6789")` is called and the API returns
  200 with works.
- **THEN** it SHALL return a non-empty list of titles; derived themes are added
  to the profile's `themen` without removing manually-set themes.

#### Scenario: Network failure is graceful
- **WHEN** `fetch_orcid` is called and the HTTP request raises a connection
  error.
- **THEN** it SHALL return an empty list and log a warning; no exception is
  raised.

#### Scenario: ORCID fetch without consent is refused
- **WHEN** `fetch_orcid` is called for a profile with `einwilligung=False`.
- **THEN** it SHALL return an empty list and log that consent is missing.

### Requirement: Profile-based matching interface
The system SHALL extend `match_profile()` and `next_deadline()` with an optional
`profil: Profile | None = None` parameter. When provided, the profile's `themen`
and `karriere` are used as defaults; explicit `felder`/`karriere` arguments take
precedence over the profile values (so the existing UI keeps working). The MCP
tools `match_best`, `naechste_fristen`, `notify`, and `brief` SHALL accept an
optional `profil_id` that resolves to a `Profile` via `load_profiles()`.

#### Scenario: Profile provides defaults when no explicit fields given
- **WHEN** `match_profile(programme, profil=p)` is called with no `felder`
  argument and `p.themen = ["KI"]`.
- **THEN** the profile's `themen` SHALL be used for matching.

#### Scenario: Explicit fields override profile
- **WHEN** `match_profile(programme, felder=["Biologie"], profil=p)` is called
  and `p.themen = ["KI"]`.
- **THEN** `["Biologie"]` SHALL be used, not `["KI"]`.

#### Scenario: Unknown profil_id returns error
- **WHEN** an MCP tool is called with `profil_id="does-not-exist"`.
- **THEN** the response SHALL include a `fehler` field and empty match lists.

### Requirement: Profile MCP tool
The system SHALL provide an MCP tool `profile` that loads a profile by `id`
from `profiles.json` and returns it (without matching). It SHALL also support
listing all profiles when called without an `id`.

#### Scenario: Load profile by id
- **WHEN** `profile(id="pilot-01-tobias")` is called.
- **THEN** the response SHALL contain the profile's `themen`, `karriere`,
  `einwilligung`, and `name`.

#### Scenario: List all profiles
- **WHEN** `profile()` is called without an `id`.
- **THEN** the response SHALL be a list of all profiles in `profiles.json`.
