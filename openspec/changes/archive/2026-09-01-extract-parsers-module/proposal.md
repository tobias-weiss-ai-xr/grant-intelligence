# Change: extract-parsers-module

## Problem

`fetchers.py` (524–548 LOC) mischte zwei Verantwortlichkeiten: **Abrufen**
(HTTP via `httpx`) und **Parsen** (XML/Text in Programm-Dicts). Das Parsen war
dadurch nur über Netzwerk-Mocks testbar und die Datei war die größte im
Modul – ein Verstoß gegen die Unix-Leitlinie „eine Sache gut“.

## Proposal

Reine, additive Aufspaltung ohne Verhaltensänderung:

1. **`parsers.py`** (neu, ~71 LOC): `slug_id(source, title)` und
   `parse_bmbf_rss(content, fallback_url, source)` – pur, ohne Netzwerk, ohne
   Zeitbezug, offline deterministisch testbar.
2. **`fetchers.py`**: HTTP bleibt hier; XML-Parsing entfällt. `_slug_id`
   bleibt als Alias erhalten (genutzt von `ingest.py` und Testcode); der
   `standDatum`-Zeitstempel wird jetzt in der Abruf-Schicht gesetzt (Zeitbezug
   = Abruf-Zeitpunkt).
3. **`ingest.py`**: importiert `slug_id` jetzt direkt aus `parsers`
   (single source of truth).
4. **`test_parsers.py`** (12 Tests) prüft die Parser offline.

## Keine Breaking Changes

- Öffentliche API von `fetchers`/`ingest` unverändert; `_slug_id`-Alias.
- Verhalten identisch (alle 504 bestehenden Tests bleiben grün).
