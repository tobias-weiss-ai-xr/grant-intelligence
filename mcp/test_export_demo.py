"""Tests für export.py (CSV/JSON/Markdown-Roundtrips) und demo.py (Smoke)."""

from __future__ import annotations

import csv
import json

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


class TestDemo:
    def test_demo_main_laeuft(self, capsys):
        import demo

        demo.main()
        out = capsys.readouterr().out
        assert "Grant-Agent" in out
        assert "Top 2:" in out

    def test_demo_notify_dataclass(self):
        import demo

        warn = demo.notify(["Biologie", "Nachhaltigkeit"], "postdoc", tage=60)
        assert all(hasattr(r, "tage_bis_frist") for r in warn)
