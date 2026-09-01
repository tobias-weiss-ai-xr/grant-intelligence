# Tasks: match-scoring-transparency

## 1. Datenschicht

- [x] 1.1 `MatchResult.punkte` (optional, Default `None`) in
      `grant_types.py`.
- [x] 1.2 `match._punkte_teile()`: Aufschlüsselung aus `_score`-Teilen.
- [x] 1.3 `match_profile` und `next_deadline` setzen `punkte`.

## 2. Exponierung

- [x] 2.1 `server._serialize`: `punkte` in MCP-Antwort.
- [x] 2.2 `brief._zeile`: echte Maxima + Komponenten statt `/5`; Fallback `/4`.

## 3. Tests

- [x] 3.1 Konsistenz: Summe(punkte)==score, Summe(max)==4, Namen.
- [x] 3.2 Details: Felder-Liste bzw. `None`; Karriere-Detail.
- [x] 3.3 `next_deadline` übernimmt `punkte`.
- [x] 3.4 `_serialize` enthält `punkte`.
- [x] 3.5 Brief-Zeile: `3/4 (Thema 2/3 · Karriere 1/1)`, kein `/5`;
      Fallback `/4`.
- [x] 3.6 Determinsmus: identische punkte bei gleicher Eingabe.
- [x] 3.7 `pytest` gesamt grün, `mypy` grün.

## 4. Qualitätssicherung

- [x] 4.1 `openspec validate match-scoring-transparency` grün.
- [x] 4.2 commit + push, CI nicht rot.
