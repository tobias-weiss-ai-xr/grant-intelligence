#!/usr/bin/env python3
"""Förder-Radar – Frist-Digest.

Erzeugt einen strukturierten Frist-Überblick (dringende Fristen, anstehende
Fristen, abgelaufene Fristen) aus dem Katalog und persistiert ihn als
`deadline-digest.json`. Beim wiederholten Aufruf werden nur *neue* dringende
Fristen gemeldet (Deduplizierung gegen den vorherigen Digest).

Unix-Philosophie: macht *eine* Sache (Frist-Übersicht erzeugen), textbasiert,
nur Stdlib + `grant_types`/`match` (keine neuen Abhängigkeiten). Läuft lokal
(Cron/systemd), in CI (GitHub Action) und als MCP-Baustein gleichermaßen.

Beispiel:
    python mcp/deadline_digest.py                        # schreibt mcp/deadline-digest.json
    python mcp/deadline_digest.py --days 90 --urgent 30
    python mcp/deadline_digest.py --check                # nur ausgeben, nicht speichern
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import date
from pathlib import Path
from typing import Any

from grant_types import parse_frist
from match import load_catalog

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
log = logging.getLogger(__name__)

CATALOG = Path(__file__).with_name("catalog.json")
DIGEST = Path(__file__).with_name("deadline-digest.json")


def _entry(p: dict[str, Any], today: date) -> dict[str, Any]:
    """Baue einen Digest-Eintrag aus einem Programm-Dict.

    Args:
        p: Programm-Dict im Katalogformat.
        today: Referenzdatum für die Tageszählung.

    Returns:
        Digest-Eintrag mit id, name, kategorie, frist, tage_bis_frist, rolling,
        status und quelle.
    """
    frist = p.get("frist")
    tage = None
    if frist:
        d = parse_frist(frist)
        if d is not None:
            tage = (d - today).days
    return {
        "id": p.get("id", ""),
        "name": p.get("name", ""),
        "kategorie": p.get("kategorie", ""),
        "frist": frist,
        "tage_bis_frist": tage,
        "rolling": bool(p.get("rolling", False)),
        "status": p.get("status", ""),
        "quelle": p.get("quelle", ""),
    }


def compute_digest(
    programme: list[dict[str, Any]],
    today: date | None = None,
    urgent_days: int = 30,
    upcoming_days: int = 90,
) -> dict[str, Any]:
    """Berechne einen strukturierten Frist-Digest.

    Args:
        programme: Liste der Programm-Dicts.
        today: Referenzdatum (Standard: heute).
        urgent_days: Tage, innerhalb derer eine Frist als dringend gilt
            (inklusiv, 0..urgent_days).
        upcoming_days: Tage, innerhalb derer eine Frist als anstehend gilt
            (0..upcoming_days).

    Returns:
        Digest-Dict mit Schlüsseln: stand, urgent_days, upcoming_days, urgent,
        upcoming, expired, counts.
        - urgent: Fristen 0..urgent_days Tage, sortiert aufsteigend.
        - upcoming: Fristen 0..upcoming_days Tage, sortiert aufsteigend.
        - expired: abgelaufene Fristen (nicht rolling), am längsten
          abgelaufene zuerst.
        - counts: {urgent, upcoming, expired, rolling}.
    """
    today = today or date.today()
    urgent: list[dict[str, Any]] = []
    upcoming: list[dict[str, Any]] = []
    expired: list[dict[str, Any]] = []
    rolling = 0

    for p in programme:
        if p.get("rolling"):
            rolling += 1
            continue
        frist = p.get("frist")
        if not frist:
            continue
        d = parse_frist(frist)
        if d is None:
            continue
        tage = (d - today).days
        entry = _entry(p, today)
        if tage < 0:
            expired.append(entry)
        elif tage <= upcoming_days:
            upcoming.append(entry)
            if tage <= urgent_days:
                urgent.append(entry)

    # Sortierung: urgent/upcoming nach tage_bis_frist aufsteigend,
    # expired nach am längsten abgelaufen zuerst.
    urgent.sort(key=lambda e: e["tage_bis_frist"] if e["tage_bis_frist"] is not None else 10**9)
    upcoming.sort(key=lambda e: e["tage_bis_frist"] if e["tage_bis_frist"] is not None else 10**9)
    expired.sort(key=lambda e: e["tage_bis_frist"] if e["tage_bis_frist"] is not None else -(10**9), reverse=True)

    return {
        "stand": today.isoformat(),
        "urgent_days": urgent_days,
        "upcoming_days": upcoming_days,
        "urgent": urgent,
        "upcoming": upcoming,
        "expired": expired,
        "counts": {
            "urgent": len(urgent),
            "upcoming": len(upcoming),
            "expired": len(expired),
            "rolling": rolling,
        },
    }


def diff_urgent(
    new_digest: dict[str, Any], old_digest: dict[str, Any] | None
) -> list[dict[str, Any]]:
    """Liefere dringende Einträge von `new_digest`, die im alten fehlen (by id).

    Deduplizierung: Beim ersten Lauf (kein alter Digest) gelten alle
    dringenden Fristen als neu. Abgelaufene (nicht mehr in `urgent`) gelten
    nie als neu.

    Args:
        new_digest: Der aktuelle Digest.
        old_digest: Der vorherige Digest oder None.

    Returns:
        Liste der neuen dringenden Einträge.
    """
    if old_digest is None:
        return list(new_digest.get("urgent", []))
    old_ids = {e["id"] for e in old_digest.get("urgent", [])}
    return [e for e in new_digest.get("urgent", []) if e["id"] not in old_ids]


def save_digest(digest: dict[str, Any], path: Path = DIGEST) -> None:
    """Persistiere den Digest als JSON (UTF-8, indent 2, Trailing-Newline).

    Args:
        digest: Digest-Dict.
        path: Zieldatei.
    """
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(digest, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
    c = digest.get("counts", {})
    log.info(
        f"Digest gespeichert: {path} "
        f"(urgent={c.get('urgent', 0)}, upcoming={c.get('upcoming', 0)}, "
        f"expired={c.get('expired', 0)}, rolling={c.get('rolling', 0)})"
    )


def load_digest(path: Path = DIGEST) -> dict[str, Any] | None:
    """Lade einen vorherigen Digest oder None.

    Fehlende oder unlesbare Dateien liefern None (kein Crash).

    Args:
        path: Digest-Datei.

    Returns:
        Digest-Dict oder None.
    """
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        log.warning(f"Konnte vorherigen Digest nicht laden: {path} – {e}")
        return None
    if not isinstance(data, dict):
        return None
    return data


def main() -> None:
    """CLI: Digest berechnen, ausgeben und (außer bei --check) speichern."""
    ap = argparse.ArgumentParser(description="Förder-Radar Frist-Digest")
    ap.add_argument("--catalog", type=Path, default=CATALOG, help="Katalog-Datei")
    ap.add_argument("--out", type=Path, default=DIGEST, help="Ausgabe-Datei (Digest)")
    ap.add_argument("--urgent", type=int, default=30, help="Dringlichkeitsfenster (Tage)")
    ap.add_argument("--days", type=int, default=90, help="Anstehend-Fenster (Tage)")
    ap.add_argument("--check", action="store_true", help="Nur ausgeben, nicht speichern")
    args = ap.parse_args()

    programme = load_catalog(args.catalog)
    today = date.today()
    digest = compute_digest(
        programme, today, urgent_days=args.urgent, upcoming_days=args.days
    )

    old = load_digest(args.out) if not args.check else None
    neu = diff_urgent(digest, old)

    # Zusammenfassung auf stdout (maschinenlesbar + menschenlesbar)
    c = digest["counts"]
    print(f"Stand: {digest['stand']}")
    print(f"Dringende Fristen (<= {args.urgent}d): {c['urgent']}")
    print(f"Anstehende Fristen (<= {args.days}d): {c['upcoming']}")
    print(f"Abgelaufene Fristen: {c['expired']}")
    print(f"Rolling: {c['rolling']}")
    if neu:
        print(f"\nWARN: {len(neu)} NEUE dringende Frist(en) seit letztem Lauf:")
        for e in neu:
            print(f"  {e['id']}: {e['name']} (Frist {e['frist']}, {e['tage_bis_frist']}d)")
    else:
        print("\nKeine neuen dringenden Fristen seit letztem Lauf.")

    if not args.check:
        digest["neu_urgent"] = len(neu)
        save_digest(digest, args.out)


if __name__ == "__main__":
    main()
