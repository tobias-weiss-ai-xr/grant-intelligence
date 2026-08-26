"""End-to-End User-Story-Tests für den Förder-Radar.

Anders als die Unit-Tests laufen diese Tests komplette Nutzer-Workflows über
die echten Einstiegspunkte:

  - Web-UI    : FastAPI TestClient (GET /, POST /brief) – wie im Browser
  - CLI       : Subprozesse (brief.py, export.py, update_catalog.py, ingest.py)
  - Assistent : verkettete MCP-Tools (profile → match_best → naechste_fristen
                → notify → brief)

Jede Story ist deterministisch, lokal und ohne Netzwerkzugriffe. Die Stories
können 1:1 als User Stories in der FLASH-Einreichung verwendet werden.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

MCP_DIR = Path(__file__).parent


# ---------------------------------------------------------------------------
# Helfer
# ---------------------------------------------------------------------------


def _cli(*args: str, timeout: int = 60) -> subprocess.CompletedProcess:
    """CLI-Tool als echten Subprozess ausführen (wie ein Terminal-Nutzer)."""
    return subprocess.run(
        [sys.executable, *args],
        cwd=str(MCP_DIR),
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def _karten(html: str) -> list[str]:
    """Programm-Namen aus den gerenderten Ergebnis-Karten extrahieren."""
    return re.findall(r"<h3>([^<]+) <span", html)


def _cli_brief_zeilen(md: str) -> list[str]:
    """Datenzeilen (ohne Header) der Top-Matches-Tabelle extrahieren."""
    section = md.split("## Top-Matches", 1)[1] if "## Top-Matches" in md else ""
    section = section.split("## ", 1)[0] if "## " in section else section
    return [
        r for r in section.strip().splitlines()
        if r.startswith("| ") and "--" not in r and "Begründung" not in r
    ]


@pytest.fixture(scope="module")
def client():
    """FastAPI TestClient – simuliert den Browser gegen die echte App."""
    from fastapi.testclient import TestClient

    import app as appmod

    return TestClient(appmod.app)


# ===========================================================================
# FR-01 · "Neu an der Uni – ich probiere das Tool zum ersten Mal aus."
# ===========================================================================


class TestStoryNeulingWeb:
    """Ohne Profil: freie Sucheingabe über die Web-Oberfläche."""

    def test_startseite_oeffnet(self, client):
        r = client.get("/")
        assert r.status_code == 200
        assert "Förder-Radar" in r.text
        # Eingabeformular + Karriere-Auswahl vorhanden
        assert 'name="felder"' in r.text
        assert 'name="karriere"' in r.text
        # Fusszeile zeigt den echten Katalog
        m = re.search(r"Katalog: (\d+) Programme", r.text)
        assert m is not None and int(m.group(1)) >= 80

    def test_erste_suche_liefert_karten(self, client):
        r = client.post(
            "/brief", data={"felder": "Biologie, Nachhaltigkeit", "karriere": "postdoc"}
        )
        assert r.status_code == 200
        karten = _karten(r.text)
        assert karten, "Es werden Ergebnis-Karten gerendert"
        assert "Score" in r.text
        # Jede Karte nennt Quelle oder Frist (Orientierung statt Zusage)
        assert "Quelle:" in r.text

    def test_freitext_ist_xss_sicher(self, client):
        r = client.post(
            "/brief",
            data={"felder": "<script>alert(1)</script>", "karriere": "postdoc"},
        )
        assert r.status_code == 200
        assert "<script>alert(1)</script>" not in r.text


class TestStoryNeulingKonsistenz:
    """Gleiche freie Eingabe über Web, CLI und Assistent → gleiche Rangfolge."""

    def test_top_match_web_gleich_cli_gleich_mcp(self, client):
        fe1, fe2 = "Biologie", "Nachhaltigkeit"
        # Web
        html = client.post(
            "/brief", data={"felder": f"{fe1}, {fe2}", "karriere": "postdoc"}
        ).text
        web_top = _karten(html)[0]
        # Assistent (MCP)
        import server

        mcp_top = server.match_best(felder=[fe1, fe2], karriere="postdoc", top=1)[0]
        assert mcp_top["id"]
        # CLI (Subprozess)
        proc = _cli("brief.py", "--felder", fe1, fe2, "--karriere", "postdoc", "--top", "1")
        assert proc.returncode == 0
        cli_row = _cli_brief_zeilen(proc.stdout)[0]

        # Web-Karte und MCP nennen dasselbe Programm (Name == catalog name)
        from match import load_catalog

        katalog = load_catalog()
        mcp_name = next(p["name"] for p in katalog if p["id"] == mcp_top["id"])
        assert web_top == mcp_name, f"Web weicht ab: {web_top} != {mcp_name}"
        # CLI nennt das gleiche Programm im Markdown
        assert mcp_name in cli_row


# ===========================================================================
# FR-02 · "Ich habe ein Profil – mein wöchentlicher Brief, auf drei Wegen."
# ===========================================================================


class TestStoryProfilBrief:
    """Profil-gesteuertes Matching ist über alle Interfaces konsistent."""

    PROFIL = "pilot-01-tobias"

    def test_web_brief_mit_profil(self, client):
        r = client.post(
            "/brief", data={"felder": "", "karriere": "postdoc", "profil_id": self.PROFIL}
        )
        assert r.status_code == 200
        karten = _karten(r.text)
        assert karten
        assert "Profil: Tobias Weiss" in r.text

    def test_cli_brief_mit_profil(self):
        proc = _cli("brief.py", "--profil-id", self.PROFIL, "--top", "3")
        assert proc.returncode == 0
        assert "## Top-Matches" in proc.stdout
        rows = _cli_brief_zeilen(proc.stdout)
        assert rows, "Top-Matches-Tabelle hat Datenzeilen"

    def test_mcp_brief_mit_profil(self):
        import server

        b = server.brief(profil_id=self.PROFIL, top=3)
        assert "fehler" not in b
        assert len(b["top_matches"]) >= 1
        assert b["naechste_frist"] is not None
        assert b["warnungen"]

    def test_die_drei_wege_nennen_dasselbe_top_programm(self, client):
        import server
        from match import load_catalog

        katalog = load_catalog()
        # MCP: oberstes Programm
        mcp_top = server.brief(profil_id=self.PROFIL, top=1)["top_matches"][0]
        mcp_name = next(p["name"] for p in katalog if p["id"] == mcp_top["id"])
        # CLI: erste Zeile der Top-Matches
        proc = _cli("brief.py", "--profil-id", self.PROFIL, "--top", "1")
        cli_name = _cli_brief_zeilen(proc.stdout)[0].split("|")[1].strip()
        # Web: oberste Karte
        html = client.post(
            "/brief",
            data={"felder": "", "karriere": "postdoc", "profil_id": self.PROFIL},
        ).text
        web_name = _karten(html)[0]

        assert cli_name == mcp_name
        assert web_name == mcp_name


# ===========================================================================
# FR-03 · DSGVO: "Ohne Einwilligung gibt es kein Matching."
# ===========================================================================


class TestStoryDsgvo:
    """Profil ohne Einwilligung wird überall abgelehnt – transparent & lokal."""

    def test_web_zeigt_hinweis_statt_ergebnissen(self, client):
        r = client.post(
            "/brief",
            data={"felder": "Mathematik", "karriere": "postdoc",
                  "profil_id": "pilot-02-math-postdoc"},
        )
        assert r.status_code == 200
        assert "consent-notice" in r.text
        assert "Einwilligung" in r.text
        assert _karten(r.text) == []  # keine Treffer

    def test_mcp_leert_bei_ohne_einwilligung(self):
        import server

        assert server.match_best(profil_id="pilot-02-math-postdoc", top=5) == []
        assert server.naechste_fristen(profil_id="pilot-02-math-postdoc") == []
        assert server.notify(profil_id="pilot-02-math-postdoc") == []

    def test_cli_meldet_fehler(self):
        proc = _cli("brief.py", "--profil-id", "pilot-02-math-postdoc")
        assert proc.returncode == 0
        assert "Fehler" in proc.stdout
        assert "Einwilligung" in proc.stdout

    def test_unbekanntes_profil_ueberall_abgelehnt(self, client):
        import server

        assert server.match_best(profil_id="gibt-es-nicht") == []
        # CLI
        proc = _cli("brief.py", "--profil-id", "gibt-es-nicht")
        assert "nicht gefunden" in proc.stdout
        # Web fällt auf freie Eingabe zurück (kein 500)
        r = client.post(
            "/brief",
            data={"felder": "Physik", "karriere": "postdoc", "profil_id": "gibt-es-nicht"},
        )
        assert r.status_code == 200
        assert _karten(r.text)  # Ergebnisse trotzdem da


# ===========================================================================
# FR-04 · "Ich frage den Assistenten: Was passt, was drängt?"
# ===========================================================================


class TestStoryAssistent:
    """Verkettete Assistenten-Nutzung: Profil → Matches → Fristen → Warnungen."""

    def test_profil_liste_und_einzel_abruf(self):
        import server

        alle = server.profile()
        ids = [p["id"] for p in alle]
        assert "pilot-01-tobias" in ids
        einzeln = server.profile(profil_id="pilot-01-tobias")
        assert einzeln["einwilligung"] is True
        assert einzeln["karriere"] == "postdoc"

    def test_match_best_ids_stammen_aus_katalog_und_sortiert(self):
        import server
        from match import load_catalog

        katalog = load_catalog()
        katalog_ids = {p["id"] for p in katalog}
        res = server.match_best(felder=["Künstliche Intelligenz"], karriere="postdoc", top=10)
        assert res
        for r in res:
            assert r["id"] in katalog_ids
        scores = [r["score"] for r in res]
        assert scores == sorted(scores, reverse=True)

    def test_fristen_haben_tage_oder_rolling(self):
        import server
        from match import load_catalog

        katalog = load_catalog()
        katalog_ids = {p["id"] for p in katalog}
        res = server.naechste_fristen(felder=["Biologie"], karriere="postdoc", top=20)
        assert res
        for r in res:
            assert r["id"] in katalog_ids
            # entweder berechnete Frist-Tage, Rolling, oder "Frist offen" (frist=None)
            assert r["tageBisFrist"] is not None or r["rolling"] or r["frist"] is None

    def test_notify_schliesst_rolling_immer_ein(self):
        import server

        warn = server.notify(felder=["Biologie"], karriere="postdoc", tage=0)
        assert warn
        assert all(w["rolling"] or (w["tageBisFrist"] is not None and w["tageBisFrist"] <= 0)
                   for w in warn)

    def test_suche_findet_und_filtert(self):
        import server

        treffer = server.search(stichwort="Sachbeihilfe")
        assert treffer
        dfg = server.search(kategorie="DFG", stichwort="Sachbeihilfe")
        assert dfg
        assert all(p["kategorie"] == "DFG" for p in dfg)


# ===========================================================================
# FR-05 · Kurator: "Ich pflege und veröffentliche den Katalog."
# ===========================================================================


class TestStoryKurator:
    """Update-Pipeline + Export als echte CLI-Aufrufe (lokal, ohne Netz)."""

    def test_validate_updatestand_checkexpired(self, tmp_path):
        kat = tmp_path / "catalog.json"
        shutil.copy(MCP_DIR / "catalog.json", kat)
        proc = _cli(
            "update_catalog.py", "--validate", "--update-stand", "--check-expired",
            "--out", str(kat),
        )
        assert proc.returncode == 0
        import json
        doc = json.loads(kat.read_text(encoding="utf-8"))
        from datetime import date
        assert len(doc["programme"]) == 100
        assert all(p["standDatum"] == date.today().isoformat() for p in doc["programme"])
        assert doc["programme"]  # Trailing-Newline & Stand-Datum gesetzt

    def test_validate_weist_kaputtes_programm_zurueck(self, tmp_path):
        import json
        kat = tmp_path / "catalog.json"
        doc = {"stand": "2026-01-01", "quelleHinweis": "test", "programme": [
            {"id": "kaputt", "name": "Kaputt", "kategorie": "DFG",
             "themen": ["frei"], "karriere": ["postdoc"], "rolle": ["lead"],
             "quelle": "", "standDatum": "2026-01-01", "status": "invalid",
             "frist": "kein-datum"},
        ]}
        kat.write_text(json.dumps(doc), encoding="utf-8")
        proc = _cli("update_catalog.py", "--validate", "--out", str(kat))
        assert proc.returncode == 1  # Validierungsfehler → Exit 1
        assert "Validierungsfehler" in proc.stderr or "Validierungsfehler" in proc.stdout

    def test_ingest_list_zeigt_alle_quellen(self):
        proc = _cli("ingest.py", "--list")
        assert proc.returncode == 0
        for key in ("openaire", "nih", "nsf", "crossref", "cost", "eu", "bmbf"):
            assert key in proc.stdout

    def test_export_csv(self):
        proc = _cli("export.py", "--format", "csv", "--out", "-")
        assert proc.returncode == 0
        lines = proc.stdout.strip().splitlines()
        header = lines[0].split(",")
        assert header[0] == "id"
        assert len(lines) == 101  # 100 Programme + Kopfzeile

    def test_export_json(self, tmp_path):
        import json
        out = tmp_path / "export.json"
        proc = _cli("export.py", "--format", "json", "--out", str(out))
        assert proc.returncode == 0
        doc = json.loads(out.read_text(encoding="utf-8"))
        assert len(doc["programme"]) == 100

    def test_export_markdown(self):
        proc = _cli("export.py", "--format", "markdown", "--out", "-")
        assert proc.returncode == 0
        assert "# Förder-Radar" in proc.stdout
        assert "## Nach Kategorie" in proc.stdout


# ===========================================================================
# FR-06 · "Alle Oberflächen zeigen denselben Katalog."
# ===========================================================================


class TestStoryKonsistenz:
    """Web-Fusszeile, Assistent und Export zählen identische Programme."""

    def test_anzahl_web_gleich_assistent_gleich_export(self, client):
        # Web
        html = client.get("/").text
        m = re.search(r"Katalog: (\d+) Programme", html)
        assert m is not None
        web_n = int(m.group(1))
        # Assistent
        import server

        mcp_n = len(server.programs())
        # Export CLI
        proc = _cli("export.py", "--format", "csv", "--out", "-")
        cli_n = len(proc.stdout.strip().splitlines()) - 1
        # Katalog-Datei
        import json

        file_n = len(json.loads((MCP_DIR / "catalog.json").read_text(encoding="utf-8"))["programme"])

        assert web_n == mcp_n == cli_n == file_n == 100
