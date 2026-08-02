# Architektur-Skizze

## 1. Prinzip
Kleine, offene Bausteine statt Monolith. Ein Beispiel-Profil erzeugt eine
Bewertungsansicht „nächste Chance + Begründung + Frist". Erste Daten: 2–3
Programmfamilien, keine Voll-Recherche.

## 2. Bausteine
1. **Datenquellen / Förderkatalog**
   - DFG (GePrIS/Antragsdaten), ERC (Nachwuchs-/Weiterlinien), BMBF-/Landeslinien,
     eine regionale Stiftung.
   - Format je Abbildung: Ausschreibungstext, Themen-Keywords, Karrierestufe,
     Rolle, Budget, Frist, Rolling-Struktur, Quelle, Stand-Datum.
2. **Profil-Adapter**
   - Eingabe ORCID / Publikationen / Stichworte (mit Einwilligung).
   - Themen-Vektor + Karrierestufe („Postdoc", „Junior-Prof").
3. **Matching-Engine**
   - Gewichtete Punkte (Thema, Karriere, Rolle, Geo), Ausgabe Score +
     kurze Begründung je Treffer.
   - Verhindert mehrfache Einreichungen desselben Vorhabens.
4. **Frist-Pipeline / Benachrichtigung**
   - Nächste Frist je Programm, Rolling-Fenster, Alarm (E-Mail/Kalender).
5. **Oberfläche**
   - Eine Seite: „Meine 2–3 Chancen + Begründung + Frist-Zähler".
   - Zusätzlich aggregierte Dekanats-Ansicht (datenschutzfreundlich).

## 3. Datenmodell (Kernentitäten)
```
Programm {
  id, name, themen[], kategorie(DFG|ERC|BMBF|Land|Stiftung),
  frist: Date, rolling: boolean,
  budgetMin, budgetMax, rolle[lead|partner],
  karriere[postdoc|junior|prof], quelle, standDatum
}
Profil {
  id, themen[], karriere, orcid, publikationen, einwilligung, status
}
Match { profilId, programmId, score, begruendung }
FristAlert { profilId, programmId, frist, alarm }
```

## 4. Technologie (Vorschlag)
- Backend: Python (FastAPI) oder Node; Frontend: einfache HTML/JS; Daten: SQLite.
- Katalog als kuratierte JSON für den Prototyp, gepflegt über Update-Skript.
- Keine teuren Dienste; KI optional nur für die Begründung.

## 5. Offene Fragen
- Zugriff auf ORCID/Uni-Daten (ORCID Public API ja; der Rest je Plattform).
- Aktualisierungswege je Quelle (Datei / RSS / API).
- Sprach- und Datumsnormalisierung.