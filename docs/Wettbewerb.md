# Wettbewerbs-Landschaft (Open Source & kommerziell)

> Hinweis: Diese Notiz trennt **verifiziert** (per gezieltem Web-Check) von
> **allgemeiner Domänenkenntnis** (vor einer Entscheidung nochmals prüfen).

## Kommerziell – Entdeckung/Matching (große Förder-Datenbanken)
- **PIVOT** (Ex Libris/ProQuest): große Förder-Datenbank + Profil-Matching,
  USA-zentriert, Abo. *(verifiziert, Eintrag existiert)*
- **GrantForward**: US-Fördersuche/-Matching. *(verifiziert)*
- **Research Professional** (UK/EU-Markt, Abo): Ausschreibungsdatenbank
  *(Domänenkenntnis)*.
- **SPIN (InfoEd), GrantStation** u. a.: weiterer US-Markt *(Domänenkenntnis)*.

## Kommerziell – KI-Antrags-Assistenz
- Verschiedene generative KI-Tools für Texte und Budget-Hilfe.
- Diese lösen **Schreiben/Texte**, nicht Entdeckung/Matching/Fristen.

## Open Source / offene Bausteine
- Keine reife, breit genutzte Open-Source-Plattform für *end-to-end*
  Grant Intelligence (Matching + Fristen) bekannt *(Domänenkenntnis)*.
- **Offene Daten als Quellen:**
  - EU: Funding-&-Tenders-Portal (Metadaten zu EU-Calls).
  - DFG: GEPRIS/Förderdaten.
  - US: Grants.gov (offene XML-Exporte).
- Open-Source-Förderverwaltung (sofern er bewilligte Mittel verwaltet) ersetzt
  Discovery/Matching nicht.

## Wo die Lücke/Stärke liegt
1. Sprache & Region: deutsch + EU, nicht nur US.
2. Integration eines konkreten Uni-/Fakultätsprofils (ORCID/Publikationen).
3. Begründung („Warum-Match") statt Keyword-Dump.
4. Frist-Pipeline als eigentlicher Mehrwert.
5. Transparenz, Mensch-in-der-Entscheidung statt reiner Automation.

## Preisperspektive der Aggregatoren
- **GrantStation**: Basis-Membership ~199 $/Jahr (verifiziert, öffentlich); höhere
  Stufen/Enterprise nicht öffentlich.
- **PIVOT / Research-Professional (Clarivate), SPIN, GrantForward**: **keine öffentlichen Preise**; typische institutionelle
  Enterprise-Subscriptions (meist € 10.000–50.000/Jahr je Uni), vom Budget der
  Unibibliothek oder des Forschungsreferats getragen.
- Folglich: an vielen Unis sind diese DB-Dienste **für Forschende bereits über
  die Uni-Lizenz verfügbar** („frei am Schreibtisch des einzelnen“, bezahlt von
  der Uni).

### Konsequenz für Förder-Radar
Wir brauchen **keine neue Abo-Datenbank**; wir setzen auf **freie offizielle
Quellen** (DFG/ERC/Bundes-Förderdatenbank/ORCID/OpenAlex) und legen darüber
eine **schmale, kuratierte Matching-/Frist-Schicht**. Der tatsächliche Wert (und Aufwand) liegt in der
kurativen Pflege + Integration, nicht die Datenlizenz.

## Fazit für die Richtung
Wir bauen **keine weitere Welt-Datenbank**, sondern nutzen offizielle Daten
(DFG/ERC/Land) und addieren Profil, Matching, Begründung und Frist-Pipeline für
eine Fakultät. „Bekannte Idee, neu auf einen konkreten Kontext angewendet" – das
ist für FLASH zulässig und für einen kleinen Prototyp gut geeignet.