# MVP / Demo (1 Seite)

> **Status (2026-08-03):** umgesetzt als lokale Ein-Bildschirm-UI
> `mcp/app.py` (uvicorn, http://127.0.0.1:8000) + MCP-Server `mcp/server.py`.
> Katalog enthält echte Programme; ERC-Fristen live verifiziert (StG 14.10.2026,
> AdG 27.08.2026, SyG 11.05.2027).

## Zweck
Ein greifbarer, ehrlicher Prototyp: ein Beispiel-Profil eingeben → die 2–3
realistischsten aktuellen Förder-Calls der passenden Familie, mit Begründung
und Frist-Zähler, aus offizieller Quelle (Stand sichtbar).

## Sicht (ein Bildschirm)
```
[ Profil: Stichworte / Publikations-Beispiel / Karrierestufe ]
        [ wer sucht: ..... ]

Deine nächsten 3 Chancen (Stand: 2026-08-02):
1. DFG Sachbeihilfe        – passt: Thema X, Einzelantrag, PostDoc
                              Frist: Rolling -> in 43 Tagen (Rolle: Lead)
2. ERC Starting (StG)      – passt gut: Thema Y; Hinweis Track A/B
                              Frist in ca. 8 Wochen (nicht Rolling)
3. Regionale Stiftung F    – Teil-Überlapp: Biologie/Methodik
                              Antragsfrist am 30.11.

[ je Karte: Score, Begründung, Quelle + Stand ]
```

## Was es demonstriert
- Profil-Übertragung statt leerer Trefferliste.
- Zwei reale Quellen (DFG, ERC) sind verknüpft, nicht Phantasie.
- Frist ist sichtbar und zählt herunter.

## Ehrlichkeit
- Nur diese Programm-Familien; Volldurchsuchung wird abgegrenzt.
- Hinweis: Scores sind Orientierung, keine Zusage.
- Nur offizielle Quellen, alle mit Stand-Datum.

## 5-Tage-Plan
1. Tag 1: JSON-Katalog (10–15 Programme: DFG + ERC + Land).
2. Tag 2: Profil-Eingabe + einfache Bewertung (Python).
3. Tag 3: Begründungs-Generator (Regeln, optional kleines Modell).
4. Tag 4: Seite (3 Karten + Frist-Zähler) zusammenfügen.
5. Tag 5: Screenshot, Stand-Doku, vorziehen von 1–2 echten Beispiel-Profilen.