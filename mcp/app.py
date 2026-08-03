"""Förder-Radar – Single-screen UI (MVP).

FastAPI-based web interface for grant discovery.

Usage:
    cd mcp && uvicorn app:app --port 8000

Features:
    - Single-page form for profile input
    - Top 3 matching programs with scores and explanations
    - Deadline warnings (≤60 days highlighted)
    - XSS protection via HTML escaping
    - Career level whitelist validation
"""
from __future__ import annotations

import html
import logging
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse

from match import load_catalog, match_profile

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

app = FastAPI(title="Förder-Radar (MVP)")

# Load catalog at startup
PROGRAMME = load_catalog()
KARRIEREN = [
    "postdoc", "junior", "prof", "senior",
    "student",
    "verwaltung", "service", "IT", "bibliothek",
]

# =============================================================================
# Templates
# =============================================================================

PAGE_TEMPLATE = """<!doctype html>
<html lang="de"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Förder-Radar</title>
<style>
  body{{font-family:system-ui,sans-serif;max-width:720px;margin:2rem auto;padding:0 1rem;color:#222}}
  h1{{font-size:1.4rem}} h1 small{{font-weight:normal;color:#777;display:block;font-size:.85rem}}
  form{{display:flex;gap:.5rem;flex-wrap:wrap;margin:1rem 0}}
  input,select,button{{padding:.5rem;font-size:1rem;border:1px solid #bbb;border-radius:6px}}
  input[type=text]{{flex:2;min-width:220px}}
  button{{background:#0b5;color:#fff;border-color:#0b5;cursor:pointer}}
  .karte{{border:1px solid #ddd;border-left:4px solid #0b5;border-radius:8px;padding:.8rem 1rem;margin:.6rem 0}}
  .karte.dringend{{border-left-color:#d33}}
  .karte h3{{margin:.1rem 0 .3rem;font-size:1.05rem}}
  .badge{{display:inline-block;font-size:.75rem;padding:.1rem .5rem;border-radius:99px;background:#eee;margin-left:.4rem}}
  .score{{font-weight:700;color:#0b5}}
  .frist{{color:#777;font-size:.9rem}} .warn{{color:#d33;font-weight:600}}
  .meta{{font-size:.8rem;color:#888;margin-top:.4rem}}
  .fuss{{font-size:.75rem;color:#999;margin-top:1.5rem}}
</style></head><body>
<h1>Förder-Radar <small>Ein Profil, deine nächsten Chancen – Stand {heute}</small></h1>
<form method="post" action="/brief">
  <input type="text" name="felder" value="{felder}" placeholder="Forschungsfelder, kommagetrennt (z.B. Biologie, Nachhaltigkeit)" required>
  <select name="karriere">
    {optionen}
  </select>
  <button type="submit">Brief erstellen</button>
</form>
{inhalt}
<div class="fuss">Scores sind Orientierung, keine Zusage. Quellen und Stand-Datum sind je Karte sichtbar.
Katalog: {katalog} Programme, Stand {stand}. Lokaler MVP – Daten bleiben lokal.</div>
</body></html>"""

CARD_TEMPLATE = """<div class="karte {kclass}">
  <h3>{name} <span class="badge">{kategorie}</span></h3>
  <div><span class="score">Score {score}/5</span> {status}</div>
  <div>{begruendung}</div>
  <div class="meta">Quelle: {quelle} · Stand: {stand}</div>
</div>"""


@dataclass
class CardStatus:
    """Status information for a match card."""
    text: str
    urgent: bool = False
    rolling: bool = False


def _format_deadline(frist: str | None, rolling: bool) -> CardStatus:
    """Format deadline for display with urgency indicator.

    Args:
        frist: Deadline date in ISO format or None.
        rolling: Whether program has rolling admissions.

    Returns:
        CardStatus with formatted text and urgency flag.
    """
    if rolling:
        return CardStatus("<span class='frist'>Rolling</span>", rolling=True)
    if not frist:
        return CardStatus("<span class='frist'>Frist offen – Portal prüfen</span>")

    try:
        deadline = datetime.strptime(frist, "%Y-%m-%d").date()
        delta = (deadline - date.today()).days
        if delta < 0:
            return CardStatus(f"<span class='warn'>Abgelaufen ({-delta} Tage)</span>", urgent=True)
        elif delta <= 60:
            return CardStatus(f"<span class='warn'>⚠ noch {delta} Tage</span>", urgent=True)
        else:
            return CardStatus(f"<span class='frist'>{delta} Tage bis Frist</span>")
    except ValueError:
        return CardStatus(f"<span class='warn'>Frist: {frist} (prüfen)</span>")


def _render(felder: str = "", karriere: str = "postdoc", inhalt: str = "") -> str:
    """Render the main page HTML.

    Args:
        felder: User's research fields (escaped for display).
        karriere: Selected career level (whitelist validated).
        inhalt: HTML content for results section.

    Returns:
        Complete HTML page.
    """
    # Whitelist career level
    if karriere not in KARRIEREN:
        karriere = "postdoc"
        log.warning(f"Invalid career level '{karriere}' - using default 'postdoc'")

    # Generate options
    options = "".join(
        f'<option value="{k}"{" selected" if k == karriere else ""}>{k}</option>'
        for k in KARRIEREN
    )

    return PAGE_TEMPLATE.format(
        heute=date.today().isoformat(),
        felder=html.escape(felder),
        optionen=options,
        inhalt=inhalt,
        katalog=len(PROGRAMME),
        stand=date.today().isoformat(),
    )


def _cards(felder: list[str], karriere: str) -> str:
    """Generate match result cards.

    Args:
        felder: List of research fields.
        karriere: Career level.

    Returns:
        HTML string with match cards or "no results" message.
    """
    matches = match_profile(PROGRAMME, felder, karriere, top=3)

    if not matches:
        return '<p>Keine Treffer – Felder oder Karrierestufe anpassen.</p>'

    cards = []
    for m in matches:
        status = _format_deadline(m.frist, m.rolling)
        urgent_class = "dringend" if status.urgent else ""

        # HTML escape all user-facing content
        name = html.escape(m.name).replace("{", "&#123;").replace("}", "&#125;")
        begr = html.escape(m.begruendung).replace("{", "&#123;").replace("}", "&#125;")
        quelle = html.escape(m.quelle).replace("{", "&#123;").replace("}", "&#125;")

        cards.append(CARD_TEMPLATE.format(
            kclass=urgent_class,
            name=name,
            kategorie=html.escape(m.kategorie),
            score=m.score,
            status=status.text,
            begruendung=begr,
            quelle=quelle,
            stand=html.escape(m.stand_datum),
        ))

    return "".join(cards)


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    """Render the main page with empty form."""
    return _render()


@app.post("/brief", response_class=HTMLResponse)
def brief(felder: str = Form(""), karriere: str = Form("postdoc")) -> str:
    """Process form submission and show match results.

    Args:
        felder: Comma-separated research fields.
        karriere: Selected career level.

    Returns:
        HTML page with match results.
    """
    # Parse fields (handle comma and whitespace)
    felder_liste = [f.strip() for f in felder.split(",") if f.strip()]

    # Generate results
    inhalt = f"<h2>Deine nächsten Chancen</h2>{_cards(felder_liste, karriere)}"

    return _render(felder=felder, karriere=karriere, inhalt=inhalt)
