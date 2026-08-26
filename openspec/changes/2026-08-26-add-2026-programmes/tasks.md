# Tasks: Add 2026 Programmes + Source-Link Repair

## Catalog data (mcp/catalog.json)

- [ ] T1 — Add `msc-staff-exchanges` (EU, MSCA Staff Exchanges; karriere postdoc/junior/prof; themen thematisch-offen; rolling; status zu-pruefen; quelle `https://marie-sklodowska-curie-actions.ec.europa.eu/actions/staff-exchanges`; non-empty hinweis).
- [ ] T2 — Add `humboldt-feodor-lynen` (Stiftung, Feodor Lynen Fellowship; karriere postdoc; rolling; status laufend; quelle `https://www.humboldt-foundation.de/bewerben/foerderprogramme/feodor-lynen-forschungsstipendium`; non-empty hinweis).
- [ ] T3 — Add `dfg-int-kooperationen` (DFG, Aufbau internationaler Kooperationen; karriere junior/postdoc/prof; rolle lead+partner; rolling; status zu-pruefen; quelle `.../programme/inter-foerdermassnahmen/aufbau-internationaler-kooperationen`; hinweis notes Stichtage via DFG-Portal).
- [ ] T4 — Add `dfg-int-veranstaltungen` (DFG, Internationale wiss. Veranstaltungen; karriere junior/postdoc/prof; rolle lead; rolling; status zu-pruefen; quelle `.../programme/inter-foerdermassnahmen/int-wiss-veranstaltungen`; non-empty hinweis).
- [ ] T5 — Remove `dfg-graduate-school` (stale duplicate; structured-doctoral coverage remains `dfg-graduiertenkolleg`).
- [ ] T6 — Repair DFG URLs (10): sachbeihilfe→`einzelfoerderung/sachbeihilfe`; emmy-noether→`einzelfoerderung/emmy-noether`; heisenberg→`einzelfoerderung/heisenberg`; graduiertenkolleg→`koordinierte-programme/graduiertenkollegs`; sfb→`koordinierte-programme/sfb`; fdm→`infrastruktur/lis/lis-foerderangebote/forschungsdaten`; ub-digiserv→`infrastruktur/lis/lis-foerderangebote/digitalisierung-erschliessung`; hrz-it-infra→`infrastruktur/wgi/foerderangebote/forschungsgrossgeraete`; irtg→`koordinierte-programme/graduiertenkollegs` (IRTG sind ein GRK-Typ, hinweis ergänzen); alle unter `https://www.dfg.de/de/foerderung/foerdermoeglichkeiten/programme/…` (200-verified).
- [ ] T7 — Repair MSCA hostname (2): msc-itn→`https://marie-sklodowska-curie-actions.ec.europa.eu/actions/doctoral-networks`; msc-cofund→`.../actions/cofund`.
- [ ] T8 — Repair ERC Plus (1): erc-plus-2026→`https://erc.europa.eu/apply-grant/erc-plus-grant`.
- [ ] T9 — Repair Hessen LOEWE (2) + refresh entry: loewe-hessen & loewe-verwaltung→`https://wissenschaft.hessen.de/forschen/landesprogramm-loewe`; update loewe-hessen name/hinweis to Förderlinien (Zentren/Schwerpunkte/Spitzen-/Start-Professuren); standDatum today.
- [ ] T10 — Repair BMBF (5): bmbf-*→`https://www.foerderinfo.bund.de/foerderinfo/de/home/home_node.html` (bundesweites Portal, BMBF→BMFTR-unabhängig).
- [ ] T11 — Repair VW Stiftung (1): volkswagen-stiftung→`https://www.volkswagenstiftung.de/en/funding/our-funding-portfolio`.
- [ ] T12 — Repair weitere (3): max-weber-bayern→`https://www.studienstiftung.de/max-weber-programm`; nrw-mwk-wissenschaft→`https://www.mkw.nrw/`; krebshilfe-onkologie→`https://www.krebshilfe.de/forschen`.
- [ ] T13 — Set `standDatum` to today (2026-08-26) for all touched entries; every entry keeps non-empty hinweis; budgets stay null where unknown.

## Tests & validation

- [ ] T14 — Update `mcp/test_e2e.py` programme-count assertions 100 → 103 (lines ~324/354/362/397) and add/keep determinism (top ids unchanged for pilot-01-tobias).
- [ ] T15 — Add coverage for the new entries: matching scenarios (postdoc/junior/prof) mirrored from specs; assert new ids appear for suitable profiles, `dfg-graduate-school` absent.
- [ ] T16 — Add regression test for URL hygiene (polish R5): the 23 repaired entries use the verified URLs (fixed list, no network).
- [ ] T17 — Run full suite: pytest (mypy clean, 100% core coverage) + `openspec validate`.

## Dashboard & docs

- [ ] T18 — Regenerate dashboard data: `dashboard/sync-data.sh` (or manual copy of catalog.json) so deployed counts show 103.
- [ ] T19 — Update honest counts in README.md + docs (Promo.md, Konzept.md, MVP-Demo.md, brief.md, export.md, SPEC-Update-Pipeline.md): 100 → 103 Programme, tests 435 → new total.
- [ ] T20 — Regenerate `docs/pilot-ergebnisse.md` via `python3 mcp/pilot_demo.py`.
- [ ] T21 — Commit + push; GH Actions deploy dashboard; verify live page.

## Out of scope (backlog, documented in proposal/design)

- SNSF, UNESCO, political-foundation stipend pages (bfw-rls/hss/sdw), ARC timeout, CIHR network errors — couldn't verify new URLs within scope.
- Anti-bot 403 URLs (NIH, HHMI, HFSP, Leverhulme, ec.europa.eu, DAAD, KAS/FNS) — browser-valid, deliberately untouched.
