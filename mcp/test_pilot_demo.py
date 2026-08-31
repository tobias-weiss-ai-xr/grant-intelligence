"""Tests for pilot_demo.py (Fachbereich Mathematik demonstration).

Covers:
  - generate_pilot_results() with profiles that have/don't have consent
  - Profiles with no matches (empty results)
  - main() writes to the expected file path
  - Profiles with no fristen (next_deadline returns empty)
"""
from __future__ import annotations

from pathlib import Path
from profile import Profile

import pytest

import pilot_demo as pd
from match import load_catalog

PROGS = load_catalog()


def test_generate_pilot_results_basic():
    """Full run with real profiles: produces valid markdown."""
    md = pd.generate_pilot_results()
    assert md.startswith("# Pilot-Ergebnisse")
    assert "**Stand:**" in md
    assert "**Profile:**" in md
    assert "**Pilot-Fakultät:**" in md


def test_generate_pilot_results_no_einwilligung():
    """Profile without consent: matching skipped, warning shown."""
    p = Profile(id="test-noconsent", name="No Consent", karriere="postdoc",
                themen=["Biologie"], einwilligung=False)
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr(pd, "load_profiles", lambda path=None: [p])
        md = pd.generate_pilot_results()
    assert "Keine Einwilligung erteilt" in md
    assert "Top-Matches" not in md


def test_generate_pilot_results_empty_themen():
    """Profile with consent but no themes: no matches found."""
    p = Profile(id="test-nothemen", name="No Themes", karriere="postdoc",
                themen=[], einwilligung=True)
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr(pd, "load_profiles", lambda path=None: [p])
        md = pd.generate_pilot_results()
    assert "_Keine Treffer._" in md
    assert "Top-Matches" in md  # section heading still present


def test_generate_pilot_results_no_fristen():
    """Profile with matches but no upcoming deadlines: 'Nächste Fristen' omitted."""
    p = Profile(id="test-nodeadline", name="No Deadline", karriere="postdoc",
                themen=["Quantenkryptographie"],
                einwilligung=True)
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr(pd, "load_profiles", lambda path=None: [p])
        mp.setattr(pd, "next_deadline", lambda *a, **kw: [])
        md = pd.generate_pilot_results()
    assert "## Profil: No Deadline" in md
    assert "Einwilligung:** ja" in md
    assert "### Nächste Fristen" not in md


def test_generate_pilot_results_with_fristen():
    """Profile with deadlines: 'Nächste Fristen' section appears."""
    p = Profile(id="test-deadline", name="Has Deadline", karriere="postdoc",
                themen=["Biologie"], einwilligung=True)
    with pytest.MonkeyPatch().context() as mp:
        mp.setattr(pd, "load_profiles", lambda path=None: [p])
        md = pd.generate_pilot_results()
    assert "### Nächste Fristen" in md


def test_main_writes_file(tmp_path, monkeypatch):
    """main() writes pilot-ergebnisse.md to docs/ via write_text."""
    written = []
    orig_write = Path.write_text

    def fake_write(self, data, *args, **kwargs):
        written.append((str(self), data))
        return orig_write(self, data, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", fake_write)
    pd.main()
    assert len(written) == 1
    assert written[0][1].startswith("# Pilot-Ergebnisse")
