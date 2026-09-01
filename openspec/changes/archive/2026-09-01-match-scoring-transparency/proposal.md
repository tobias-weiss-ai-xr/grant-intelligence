# Change: match-scoring-transparency

## Problem

Der Matching-Score wurde zwar bereits aus Komponenten berechnet
(`_score`: Thema 0–3, Karriere 0–1), aber nur der **Gesamt-Score** und ein
Freitext (`begruendung`) wurden exponiert. Die strukturierte Begründung
(„Warum diese Punktzahl?") fehlte in `MatchResult`, der MCP-API und dem
Wochen-Brief. Zusätzlich zeigte der Brief „score/5", obwohl das Maximum
real 4 ist (3+1) – irreführend.

## Proposal

Rein additive Transparenz **ohne Score-Änderung**:

1. **`MatchResult.punkte`** (neues, optionales Feld): strukturierte
   Aufschlüsselung `[{"name", "punkte", "max", "detail"}, ...]` (Thema,
   Karriere). Summe der `punkte` == `score`; Summe der `max` == 4.
2. **`match._punkte_teile()`**: baut die Aufschlüsselung aus `_score`-Teilen;
   `match_profile` und `next_deadline` setzen `punkte`.
3. **`server._serialize`**: exponiert `punkte` in der MCP-Antwort.
4. **`brief._zeile`**: Score-Zelle zeigt echte Maxima + Komponenten
   (z. B. `3/4 (Thema 2/3 · Karriere 1/1)`) statt `/5`; Fallback `/4`.

## Keine Breaking Changes

- Score-Berechnung unverändert; `punkte` ist optional (Default `None`).
- `_begruendung`-Text unverändert (bestehende Tests unangetastet).
