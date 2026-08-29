#!/usr/bin/env python3
"""Förder-Radar – Issue-Body für neue dringende Fristen rendern.

Wird von der GitHub Action `deadline-check.yml` aufgerufen: liest den
Frist-Digest und schreibt den Issue-Body nach `.github/deadline-issue-body.md`
(oder entfernt die Datei, wenn neu_urgent == 0).

Reine I/O-Schicht; die Logik (`render_body`) lebt in `mcp/deadline_digest.py`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "mcp"))

from deadline_digest import render_body  # noqa: E402

DIGEST = REPO_ROOT / "mcp" / "deadline-digest.json"
OUT = REPO_ROOT / ".github" / "deadline-issue-body.md"


def main() -> int:
    if not DIGEST.exists():
        print(f"Kein Digest gefunden: {DIGEST}", file=sys.stderr)
        OUT.unlink(missing_ok=True)
        return 0
    data = json.loads(DIGEST.read_text(encoding="utf-8"))
    if data.get("neu_urgent", 0) <= 0:
        print("Keine neuen dringenden Fristen – kein Issue-Body nötig.")
        OUT.unlink(missing_ok=True)
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render_body(data), encoding="utf-8")
    print(f"Issue-Body geschrieben: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
