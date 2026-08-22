"""Tests für export.py (CSV/JSON/Markdown-Roundtrips)."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from export import export_csv, export_json, export_markdown
from match import load_catalog

PROGS = load_catalog()


class TestExport:
    def test_csv_roundtrip(self, tmp_path):
        out = tmp_path / "export.csv"
        export_csv(PROGS, out)
        with open(out, encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        assert len(rows) == len(PROGS)
        assert rows[0]["id"] == PROGS[0]["id"]
        assert "themen" in rows[0]

    def test_json_roundtrip(self, tmp_path):
        out = tmp_path / "export.json"
        export_json(PROGS, out)
        doc = json.loads(out.read_text(encoding="utf-8"))
        assert len(doc["programme"]) == len(PROGS)
        assert doc["programme"][0]["id"] == PROGS[0]["id"]

    def test_markdown_struktur(self, tmp_path):
        out = tmp_path / "export.md"
        export_markdown(PROGS, out)
        md = out.read_text(encoding="utf-8")
        assert md.startswith("# Förder-Radar")
        assert "| ID | Name |" in md
        assert "## Nach Kategorie" in md
        assert "### ERC" in md

    def test_csv_stdout(self):
        """export_csv supports '-' for stdout."""
        import io
        import sys
        old = sys.stdout
        sys.stdout = io.StringIO()
        try:
            export_csv(PROGS, "-")
        finally:
            captured = sys.stdout
            sys.stdout = old
        output = captured.getvalue()
        assert "id" in output
        assert PROGS[0]["id"] in output

    def test_json_stdout(self):
        """export_json supports '-' for stdout."""
        import io
        import sys
        old = sys.stdout
        sys.stdout = io.StringIO()
        try:
            export_json(PROGS, "-")
        finally:
            captured = sys.stdout
            sys.stdout = old
        doc = json.loads(captured.getvalue())
        assert len(doc["programme"]) == len(PROGS)

    def test_markdown_stdout(self):
        """export_markdown supports '-' for stdout."""
        import io
        import sys
        old = sys.stdout
        sys.stdout = io.StringIO()
        try:
            export_markdown(PROGS, "-")
        finally:
            captured = sys.stdout
            sys.stdout = old
        output = captured.getvalue()
        assert "# Förder-Radar" in output

    def test_csv_stdout_path(self):
        """export_csv supports Path('-') for stdout (CLI path)."""
        import io
        import sys
        old = sys.stdout
        sys.stdout = io.StringIO()
        try:
            export_csv(PROGS, Path("-"))
        finally:
            captured = sys.stdout
            sys.stdout = old
        output = captured.getvalue()
        assert "id" in output

    def test_cli_stdout(self):
        """CLI --out - writes to stdout."""
        import io
        import sys
        import subprocess
        result = subprocess.run(
            [sys.executable, "export.py", "--format", "csv", "--out", "-"],
            capture_output=True, text=True, cwd=str(Path(__file__).parent),
        )
        assert result.returncode == 0
        assert "id" in result.stdout
        assert PROGS[0]["id"] in result.stdout
