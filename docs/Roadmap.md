# Roadmap (skizziert, bewusst nicht verbindlich)

> Diese Seite ist eine **Vision in Stichpunkten** – keine Zusagen, kein Plan zum
> sofortigen Bauen. Sie dient der Einordnung: Wo kann Grant-Agent langfristig
> hin, wenn er sich bewährt?

## Nah (MVP, jetzt)
- Förder-Radar als Agent-Schleife: `ingest` -> `search` -> `match_best` ->
  `naechste_fristen` -> `notify` -> `brief` (Demo vorhanden).
- **Frist-Pipeline aktiv:** `deadline_digest.py` erzeugt wöchentlich einen
  deduplizierten Frist-Digest (dringend/anstehend/abgelaufen); GitHub Action
  committet ihn und öffnet ein Issue bei neuen dringenden Fristen; das
  Dashboard zeigt ein „Frist-Radar“-Panel. Lokaler Lauf via
  `cron_check_expired.sh` (systemd-Timer dokumentiert).
- Erster Anwender: eigener Fachbereich; Katalog aus offiziellen, frei
  lizenzierten Quellen (DFG/ERC/Bund/Land/Stiftungen) pflegen.
- Betrieb: lokal, datenschutzfreundlich, optional über SAIA-KI-API (GWDG).

## Mitte (Ausbau zu Uni-Diensten)
- Weitere Domänen als **eigene MCP-Server** mit gleicher Bauweise:
  - Forschungsdaten (ORCID, OpenAlex, Repositorium der Uni),
  - Bibliotheks- und Lehrdienste (Katalog, LV-Verzeichnis),
  - Verwaltungs-/HR-Selbstauskünfte (bewusst nur aggregierte, freigegebene Daten).
- Gemeinsame Klammer: gleiche Transport-/Tool-Konvention, zentrale Governance
  (Wer stellt was bereit? Welche Daten sind freigegeben?).

## Fern (visionär: zentraler Uni-MCP-Server)
- Aus den Einzel-Servern entsteht **ein zentraler MCP-Einstiegspunkt** der
  Hochschule: ein Katalog, der die verfügbaren Uni-Dienste für Assistenzsysteme
  beschreibt – ein „One-Stop-Shop" für agents im Hochschulkontext.
- Vorteile, wenn er bewährt: einheitliche Schnittstelle, Daten bleiben in
  Haushand, Audits auf einen Blick (wer nutzt was?), weniger Parallelsysteme.
- **Keine Festlegung hier**: ob, wann und in welcher Form – entscheidet sich erst
  an Erfahrungen aus Nah/Mitte. Diese Seite beschreibt eine Möglichkeit, kein
  Programm.

## Grundsatz
Alles bleibt ehrlich, minimal und nachnutzbar: keine Übertreibungen, keine
Lizenzfallen, Daten in Haushand.
