# Spec: DFG Einzelförderung Extra

Delta for `dfg-einzelfoerderung-extra`.

## ADDED Requirements

### Requirement: R3 — DFG Aufbau internationaler Kooperationen entry
The catalog.json MUST include a `dfg-int-kooperationen` programme entry for the DFG measure "Aufbau internationaler Kooperationen" (`kategorie="DFG"`, `karriere` covering junior/postdoc/prof with partner role, bottom-up themes). Its `quelle` MUST point to `https://www.dfg.de/de/foerderung/foerdermoeglichkeiten/programme/inter-foerdermassnahmen/aufbau-internationaler-kooperationen` (200-verified). Non-empty `hinweis` required; deadline/application facts MUST be phrased conservatively ("Stichtage via DFG-Portal") because the page is JS-rendered.

#### Scenario: Postdoc searches for international cooperation setup
Given a researcher profile with `karriere="postdoc"` and `themen=["thematisch-offen"]`
When `match_profile()` is called with sufficient `top`
Then `dfg-int-kooperationen` appears in results with score ≥ 2

### Requirement: R4 — DFG Internationale wissenschaftliche Veranstaltungen entry
The catalog.json MUST include a `dfg-int-veranstaltungen` programme entry for the DFG funding of international conferences/workshops (`kategorie="DFG"`, `karriere` covering junior/postdoc/prof, lead role). Its `quelle` MUST point to `https://www.dfg.de/de/foerderung/foerdermoeglichkeiten/programme/inter-foerdermassnahmen/int-wiss-veranstaltungen` (200-verified). Non-empty `hinweis` required.

#### Scenario: Professor searches for workshop/conference funding
Given a researcher profile with `karriere="prof"` and `themen=["thematisch-offen"]`
When `match_profile()` is called with sufficient `top`
Then `dfg-int-veranstaltungen` appears in results with score ≥ 2
