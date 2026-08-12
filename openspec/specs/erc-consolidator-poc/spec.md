# Spec: erc-consolidator-poc

## Purpose

Requirements derived from grant catalog expansion changes.

---

# Spec: ERC Consolidator Grant + Proof of Concept

## ADDED Requirements

### Requirement: R1: ERC Consolidator Grant (CoG) entry
The catalog.json MUST include an `erc-cog-2027` programme entry.
- `id`: `erc-cog-2027`
- `kategorie`: `ERC`
- `themen`: `["frei"]`
- `karriere`: `["postdoc", "junior"]`
- `rolle`: `["lead"]`
- `budget_max`: 2,000,000
- `dauerJahre`: 5
- `status`: `zu-pruefen`
- `quelle`: `https://erc.europa.eu/apply-grant/consolidator-grant`
- `rolling`: `false`
- `standDatum`: date of entry creation

#### Scenario: Postdoc searches for ERC funding
Given a researcher profile with `karriere="postdoc"` and `themen=["KI"]`
When `match_profile()` is called
Then `erc-cog-2027` appears in results with score ≥ 2

### Requirement: R2: ERC Proof of Concept (PoC) entry
The catalog.json MUST include an `erc-poc` programme entry.
- `id`: `erc-poc`
- `kategorie`: `ERC`
- `themen`: `["Innovation", "Transfer"]`
- `karriere`: `["postdoc", "junior", "prof"]`
- `rolle`: `["lead"]`
- `budget_max`: 150,000
- `dauerJahre`: 1
- `status`: `zu-pruefen`
- `quelle`: `https://erc.europa.eu/apply-grant/proof-concept`
- `rolling`: `true`
- `standDatum`: date of entry creation

#### Scenario: Professor searches for innovation transfer
Given a researcher profile with `karriere="prof"` and `themen=["Innovation", "KI"]`
When `match_profile()` is called
Then `erc-poc` appears in results with score ≥ 2

### Requirement: R3: Source groups in sources.yaml
The sources.yaml MUST include `erc-cog` and `erc-poc` source groups.
- `erc-cog`: URL `https://erc.europa.eu/apply-grant/consolidator-grant`, `type: manual`, `update_frequency: quarterly`
- `erc-poc`: URL `https://erc.europa.eu/apply-grant/proof-concept`, `type: manual`, `update_frequency: quarterly`

#### Scenario: Source lookup for ERC CoG
Given `sources.yaml` is loaded
When `sources["erc-cog"]` is accessed
Then it contains `url` pointing to `erc.europa.eu/apply-grant/consolidator-grant`
