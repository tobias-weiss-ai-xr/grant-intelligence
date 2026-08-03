"""Förder-Radar – Ein-Bildschirm-UI (MVP).

Lokal starten:  uvicorn app:app --port 8000   (aus mcp/)
Ein Profil eingeben -> 3 Karten: Score, Begruendung, Frist-Countdown.

Bewusst minimal: keine DB, keine Auth, lokaler Pilot-Einsatz.
"""
from __future__ import annotations

import html
from datetime import date, datetime

from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse

from match import load_catalog, match_profile, _frist_text

app = FastAPI(title="Förder-Radar (MVP)")
PROGRAMME = load_catalog()
KARRIEREN = ["postdoc", "junior", "prof"]

PAGE = """<!doctype html>
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

KARTE = """<div class="karte {kclass}">
  <h3>{name} <span class="badge">{kategorie}</span></h3>
  <div><span class="score">Score {score}/5</span> {status}</div>
  <div>{begruendung}</div>
  <div class="meta">Quelle: {quelle} · Stand: {stand}</div>
</div>"""


def _render(felder: str = "", karriere: str = "postdoc", inhalt: str = "") -> str:
    if karriere not in KARRIEREN:
        karriere = "postdoc"  # Whitelist: unbekannte Werte nicht ins HTML uebernehmen
    opt = "".join(
        f'<option value="{k}"{" selected" if k == karriere else ""}>{k}</option>'
        for k in KARRIEREN
    )
    return PAGE.format(
        heute=date.today().isoformat(), felder=html.escape(felder), optionen=opt, inhalt=inhalt,
        katalog=len(PROGRAMME), stand=date.today().isoformat(),
    )


def _cards(felder: list[str], karriere: str) -> str:
    m = match_profile(PROGRAMME, felder, karriere, top=3)
    out = []
    for r in m:
        f = r.get("frist")
        delta = None
        if f:
            try:
                delta = (datetime.strptime(f, "%Y-%m-%d").date() - date.today()).days
            except ValueError:
                delta = None
        dringend = delta is not None and delta <= 60
        status = f'<span class="warn">⚠ noch {delta} Tage</span>' if dringend else \
                 ('<span class="frist">Rolling</span>' if r.get("rolling") else
                  ('<span class="frist">' + _frist_text(f, False) + '</span>'))
        # Karten-Daten HTML-escaped und Format-Klammern neutralisiert
        name = html.escape(r["name"]).replace("{", "&#123;").replace("}", "&#125;")
        begr = html.escape(r["begruendung"]).replace("{", "&#123;").replace("}", "&#125;")
        quelle = html.escape(r["quelle"]).replace("{", "&#123;").replace("}", "&#125;")
        out.append(KARTE.format(
            kclass="dringend" if dringend else "",
            name=name, kategorie=r["kategorie"], score=r["score"], status=status,
            begruendung=begr, quelle=quelle, stand=r["standDatum"],
        ))
    if not out:
        return '<p>Keine Treffer – Felder oder Karrierestufe anpassen.</p>'
    return "".join(out)


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return _render()


@app.post("/brief", response_class=HTMLResponse)
def brief(felder: str = Form(""), karriere: str = Form("postdoc")) -> str:
    # Optionales Feld: leeres/fehlendes Profil -> freundliche Meldung, kein 422
    felder_liste = [f.strip() for f in felder.split(",") if f.strip()]
    inhalt = f"<h2>Deine nächsten Chancen</h2>{_cards(felder_liste, karriere)}"
    return _render(felder=felder, karriere=karriere, inhalt=inhalt)
