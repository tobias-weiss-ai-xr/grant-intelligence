#!/usr/bin/env python3
"""Förder-Radar – Parser für externe Feed-/Portal-Formate.

Reine Parsing-Logik **ohne Netzwerkzugriff** und ohne Zeitbezug, damit sie
offline deterministisch testbar ist. Das Abrufen (HTTP) bleibt in
`fetchers.py`; hier wird nur interpretiert (eine Sache – Parsen).

Unix-Philosophie: kleine, zusammensetzbare Teile; Text in, Text out.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

# Distanz in Tagen bis zur Frist, ab der ein Programm als „urgent“ gilt,
# ist Sache der Digest-Pipeline – nicht hier.


def slug_id(source: str, title: str) -> str:
    """Deterministische Programm-id aus Quelle und Titel.

    Re-fetching desselben RSS-Items erzeugt dieselbe id (upsert-sicher),
    anders als zeitstempelbasierte ids, die Duplikate erzeugen würden.

    Args:
        source: Quell-Kennung (z. B. "bmbf").
        title: Item-Titel.

    Returns:
        Slugified id wie "bmbf-<slug>".
    """
    slug = "".join(c if c.isalnum() else "-" for c in title.lower()).strip("-")
    slug = "-".join(part for part in slug.split("--") if part)[:60].rstrip("-")
    return f"{source}-{slug}"


def parse_bmbf_rss(
    content: bytes | str,
    fallback_url: str,
    source: str = "bmbf",
) -> list[dict[str, Any]]:
    """Parse BMBF-RSS-Items zu Teil-Programmen.

    Args:
        content: XML-Inhalt (Bytes oder Text).
        fallback_url: Quelle, wenn ein Item kein <link>-Element hat.
        source: Quell-Kennung für die id-Bildung (Standard "bmbf").

    Returns:
        Liste von Teil-Programmen mit id, name, quelle, hinweis.
        standDatum ist bewusst NICHT hier (Zeitbezug = Abruf-Schicht).

    Raises:
        xml.etree.ElementTree.ParseError: bei unlesbarem XML.
    """
    root = ET.fromstring(content)
    programmes: list[dict[str, Any]] = []
    for item in root.findall(".//item"):
        title = item.find("title")
        link = item.find("link")
        if title is not None and title.text:
            programmes.append(
                {
                    "id": slug_id(source, title.text),
                    "name": title.text,
                    "quelle": link.text if link is not None else fallback_url,
                    "hinweis": "Automatically imported from RSS - manual verification required",
                }
            )
    return programmes
