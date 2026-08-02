# Datenquellen

Übersicht der Primär-Quellen für Förder/Grants, mit **Verifikations-Stand**
(`✓` = Web-Check erreichbar; `(bot)` = Portal reagierte nicht auf Automations-Client,
Vermutbedürftig). Alle niederer Einträge sind **offizielle, frei zugängliche** Quellen –
die Paywall liegt in kommoden Aggregator-DBs (PIVOT/Research-Professional), nicht hier.

## 1. Bundesrepublik Deutschland
| Quelle | Portal | Verif. | Inhalt |
|---|---|---|---|
| DFG /> Förderung | `dfg.de/foerderung` | ✓ | Sachbeihilfe, Verbund-, Emmy Deverse, Fristen |
| DFG GEPRIS | `gepris.dfg.de` | ✓ | bewilligte Förderprojekte (Metadaten/Referenz) |
| BMBF | `bmbf.de` | ✓ | Bundes-/Programm-Calls |
| Bundes-Förderportal (easy-Online) | `foerderdigital.bund.de` | ✓ | Zentrales Elektroflix, Fristen |
| Förderdatenbank des Bundes | `foerderdatenbank.de` | ✓ | kostenlose Gesamt-DB der Bundesprogramme + Fristen |

## 2. Land (Beispiel Hessen) & Region
| Quelle | Verifiz. | Inhalt |
|---|---|---|
| Wissenschaftliche Hessen (Förderung, LOEWE) | Teilweise | Landesprogramme inkl. LOEWE |
| Fachhochschulen-/Regionalfonds Hessen | zu prüfen | je Pilot abzustimmen |

## 3. Angewandte Forschung / Industrie
| Quelle | Verifiz. | Inhalt |
|---|---|---|
| AiF (industrielle Gemeinschaftsforschung) | ✓ | Branchenübergreifende angewandte Vorhaben |
| ZIM (Mittelstand) | ✓ | KMU/VHQ: Innovation mit Hochschulen |

## 4. EU / Europa
| Inhalt | Portal | Verifiz. |
|---|---|---|
| EU Funding & Tenders | `ec.europa.eu/info/funding-tenders` | ✓ |
| ERC | `erc.europa.eu` | ✓ |
| EIT (Innovations-Communities) | `eit.europa.eu` | ✓ |
| COST (Netzwerke/Mobilität) | `cost.eu` | ✓ |
| Eurostars/EUREKA | `eurostars-eureka.eu` | (bot) |

## 5. Stiftungen (Deutschland)
| Inhalt | Verifiz. |
|---|---|
| VolkswagenStiftung | ✓ |
| Fritz-Thyssen-Stiftung | ✓ |
| Carl-Zeiss-Stiftung | ✓ |
| Alexander-von-Humboldt-Str. | ✓ (`humboldt-foundation.de`) |
| DBU (Umwelt) | ✓ |
| Deutsche Krebshilfe (Med/Onko) | ✓ |
| DAAD (Stipendium/Austausch) | ✓ |
| Studienstiftung d. dts. Volkes | ✓ |

## 6. International (nur wenn Scope-Ausland)
| Inhalt | Verifiz. |
|---|---|
| Grants.gov (US-Bund) | ✓ |
| NIH | (bot/403) |
| NSF | ✓ |
| UKRI | ✓ |
| SNSF (CH), FWF (AT) | ✓ main.tools |
| Wellcome | 202 ✓ |

## 7. Unterstützende Identementschicht (keine Förderung)
| Zweck | Quelle | Verifiz. |
|---|---|---|
| Profil-/Publikationen | ORCID (Public API, frei) | ✓ |
| Metadaten (open, CC-BY) | OpenAlex | ✓ |
| Zitations-Metriken (Abo, nur optional) | Web of Science / Scopus | Uni-Abo |

---

## Verarbeitung & Aktualisierungs-Runde
- **Kurativ:** Nur die **2–4 passenden** Quellen je Pilot-Fakultät aktiv pflegen
  (z. B. DFG + EU-Portal + DBU/Krebshilfe), nicht alle Port effective zykl.
- **Schema-Normalisierung** → `mcp/catalog.json`-Feldskema schon abgelegt:
  `id / name / kategorie / themen / rolle / budget / frist / rolling / quelle / standDatum`.
- **Aktualisierungs-Governance:** Quellen regelmäßig abziehen (Datei/RSS/API);
  Rolling- vs. Einmal-Flag prüfen; **Stand-Datum** immer sichtbar; tote Fristen
  herausführen.
- **Nutzen in MCP-Server:** `list_programs`/`match_profile` suchen direkt aus
  `catalog.json` (siehe `docs/MCP-Design.md`).