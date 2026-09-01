# Konzept: Förder-Radar

## 1. Problem
- Forschende verlieren Zeit, passende Förder-Calls zu finden. Abo-Datenbanken
  liefern „mehr Treffer" statt „die richtige nächste Frist".
- Fristen werden verpasst; Wiederholungs- und Rolling-Chancen bleiben ungenutzt.
- Viele bestehende Angebote sind international/US-zentriert, englischsprachig und
  binden ein Profil (ORCID, Publikationen) nicht an konkrete
  Fördervoraussetzungen.

## 2. Scharfe These
> „Es braucht keine weitere Welt-Datenbank. Es braucht für jede Person die
> realistischsten nächsten Förderchancen – mit Begründung und Fristen-Zähler."

Der Wert entsteht an der Schnittstelle **Profil + Frist**, nicht durch eine
größere Liste.

## 3. Persona / Zielgruppe
- **Pilot-Fakultät:** ein klar abgegrenzter Fachbereich (z. B. Naturwissenschaft
  und Technik, Medizin oder Geisteswissenschaft) – eine zuerst.
- Primär: Postdocs/Wissenschaftler\*innen, die Drittmittel (DFG/ERC/Land) suchen.
- Sekundär: Transfer-/Forschungsreferat und Dekanat (Portfolio-Übersicht).

## 4. Scope

### 4.1 Enthalten (MVP)
1. **Profil:** ORCID/Publikationen/Stichworte, DSGVO-geklärt, mit Einwilligung;
   Karrierestufe (Postdoc/Junior/Prof). Öffentliche oder private Pflege.
2. **Kuratierter Katalog:** DFG, ERC, BMBF, EU, Bund, Land, Stiftungen,
   Industrie, International – 108 Programme aus offiziellen Quellen.
3. **Matching:** Themen-Überlappung, Karrierestufe, Rolle (Lead/Partner),
   Geografie.
4. **Begründung:** „Warum passt diese Ausschreibung zu dir?" – kein Keyword-Dump.
5. **Frist-Pipeline:** nächste Einreichung, Rolling-Fenster, Frist-Zähler.
6. **Dashboard je Persona:** nächste 5 Chancen, Pipeline-Status.

### 4.2 Bewusst nicht
- **Keine** Voll-Welt-Datenbank aller Stiftungen und Förderer.
- **Kein** Antrags-Schreib-Assistent (das bleibt Sache der Person; wir planen
  und bereiten nur vor).
- **Keine** Verwaltung bereits bewilligter Projekte (eigenes Feld).

## 5. Nutzen / „Warum jetzt"
- Unis stehen unter Drittmittel-Druck: früher erkannte, passende Calls erhöhen
  die Qualität der Einreichungen.
- Förder-Matching bleibt weitgehend ungelöst und ohne deutschsprachigen Standard;
  die Lücke zwischen großer Datenbank und dem einzelnen Standort ist offen.
- Der persönliche Fokus (meine nächste Frist) ist klarer als eine generische Suche.

## 6. Abgrenzung (Wettbewerb)
PIVOT, GrantForward und Research Professional existieren (kommerziell) – siehe
`docs/Wettbewerb.md`. Die Differenz hier: **dein Profil + deine Frist + Deutsch +
Begründung**, nicht eine größere Datenbank. Das wird nicht als „noch eine
Datenbank" gepitcht.

## 7. Risiken & Gegenmaßnahmen
- **Datenqualität:** nur offizielle Quellen, jedes Datum mit Stand, Update-Prozess.
- **DSGVO:** Profil nur mit Einwilligung, minimale Daten; Institution verantwortlich.
- **Demo-Illusion:** Der Prototyp zeigt reale Programme an echten Profilen, nicht „alles".
- **Erwartungsmanagement:** Matching gibt Orientierung, keine Zusage und keinen
  Rechtsanspruch.

## 8. Messbare Wirkung
- Anzahl früh erkannter passender Calls, weniger verpasste Fristen, weniger
  Stunden für den manuellen Abgleich.

## 9. Umsetzungsstand

| Schritt | Status |
|---------|--------|
| Pilot-Fakultät festlegen | offen (deferred) |
| 2–3 reale Profile | ⚠ 1 aktiv (pilot-01-tobias), weitere offen |
| Förderprogramme sammeln | ✅ 108 Programme, 9 Kategorien |
| Prototyp umsetzen | ✅ Agent-Schleife + UI + MCP-Server + Brief |
| Einreichungstext finalisieren | ✅ V2, ≤300 Wörter |
| Update-Pipeline | ✅ Fetchers + Cron + Audit-Log |
| Open Source | ✅ MIT-Lizenz, GitHub |
| Tests + Qualität | ✅ 566 Tests, 99 % Coverage, mypy clean |
