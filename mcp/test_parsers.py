"""Tests für parsers.py (reine Parsing-Logik, offline, deterministisch)."""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

from parsers import parse_bmbf_rss, slug_id

FEED = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>BMBF Bekanntmachungen</title>
    <item>
      <title>BMBF Bekanntmachung KI</title>
      <link>https://www.bmbf.de/bekanntmachung-ki</link>
    </item>
    <item>
      <title>BMBF Bekanntmachung Klima</title>
      <link>https://www.bmbf.de/bekanntmachung-klima</link>
    </item>
  </channel>
</rss>
"""


class TestSlugId:
    def test_deterministisch(self):
        a = slug_id("bmbf", "Test Bekanntmachung: KI!")
        b = slug_id("bmbf", "Test Bekanntmachung: KI!")
        assert a == b
        assert a.startswith("bmbf-")
        assert a != slug_id("bmbf", "Ganz anderes Thema")

    def test_not_collides_across_sources(self):
        assert slug_id("bmbf", "X") != slug_id("dfg", "X")

    def test_special_chars(self):
        s = slug_id("src", "Test: KI & ML!")
        assert ":" not in s
        assert "&" not in s
        assert "!" not in s

    def test_collapses_hyphens(self):
        s = slug_id("src", "A B C")
        assert "--" not in s

    def test_truncates(self):
        long = "x" * 200
        s = slug_id("src", long)
        assert len(s) <= 64  # "src-" (4) + Slug max. 60

    def test_empty_title(self):
        assert slug_id("src", "") == "src-"


class TestParseBmbfRss:
    def test_parst_items(self):
        items = parse_bmbf_rss(FEED, "https://fallback.example")
        assert len(items) == 2
        assert items[0]["name"] == "BMBF Bekanntmachung KI"
        assert items[0]["id"].startswith("bmbf-")
        assert items[0]["quelle"] == "https://www.bmbf.de/bekanntmachung-ki"
        assert "hinweis" in items[0] and items[0]["hinweis"]
        # Zeitbezug gehört zur Abruf-Schicht, nicht in den Parser
        assert "standDatum" not in items[0]

    def test_bytes_input(self):
        items = parse_bmbf_rss(FEED.encode("utf-8"), "https://fallback.example")
        assert len(items) == 2

    def test_item_ohne_link_nutzt_fallback(self):
        feed = """<rss><channel><item><title>Nur Titel</title></item></channel></rss>"""
        items = parse_bmbf_rss(feed, "https://fallback.example")
        assert items[0]["quelle"] == "https://fallback.example"

    def test_item_ohne_titel_uebersprungen(self):
        feed = """<rss><channel><item><link>https://x</link></item></channel></rss>"""
        assert parse_bmbf_rss(feed, "https://fallback.example") == []

    def test_leerer_feed(self):
        feed = """<rss><channel></channel></rss>"""
        assert parse_bmbf_rss(feed, "https://fallback.example") == []

    def test_kaputtes_xml_wirft_parseerror(self):
        with pytest.raises(ET.ParseError):
            parse_bmbf_rss("<rss><channel><item>", "https://fallback.example")
