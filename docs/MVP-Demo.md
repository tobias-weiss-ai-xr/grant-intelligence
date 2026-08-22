# MVP / Demo

> **Status:** ✅ umgesetzt als lokale Ein-Bildschirm-UI
> `mcp/app.py` (uvicorn, http://127.0.0.1:8000) + MCP-Server `mcp/server.py`.
> Katalog: 97 Programme aus 9 Kategorien, alle aus offiziellen Quellen.

## Zweck
Ein greifbarer, ehrlicher Prototyp: ein Beispiel-Profil eingeben → die
realistischsten aktuellen Förder-Calls, mit Begründung und Frist-Zähler,
aus offizieller Quelle (Stand sichtbar).

## Sicht (ein Bildschirm)
```
[ Profil: ▼ Dropdown ]  [ Stichworte / Karrierestufe ]
        [ Wer sucht: ..... ]

Deine nächsten 5 Chancen (Stand: 2026-08-20):
1. DFG Sachbeihilfe        – passt: Thema X, Einzelantrag, PostDoc
                              Rolling → jederzeit einreichbar (Rolle: Lead)
2. ERC Starting (StG)      – passt gut: Thema Y; Hinweis Track A/B
                              Frist in ca. X Wochen (nicht Rolling)
3. Regionale Stiftung F    – Teil-Überlapp: Biologie/Methodik
                              Antragsfrist am DD.MM.

[ je Karte: Score, Begründung, Quelle + Stand ]
```

## Profil-Auswahl
- **Dropdown** mit allen Profilen aus `profiles.json` (Pilot: Mathematik FB).
- Bei Auswahl: Themen und Karrierestufe werden automatisch ausgefüllt.
- Profile ohne Einwilligung zeigen einen Hinweis und deaktivieren Matching.
- Manuelles Eingeben bleibt möglich (kein Breaking Change).```

## Was es demonstriert
- Profil-Übertragung statt leerer Trefferliste.
- 9 Kategorien (DFG, ERC, BMBF, EU, Bund, Land, Stiftungen, Industrie,
  International) sind verknüpft, nicht Phantasie.
- Frist ist sichtbar und zählt herunter.

## Ehrlichkeit
- Kuratierter Katalog, keine Volldurchsuchung aller existierenden Fördertöpfe.
- Scores sind Orientierung, keine Zusage.
- Nur offizielle Quellen, alle mit Stand-Datum.
