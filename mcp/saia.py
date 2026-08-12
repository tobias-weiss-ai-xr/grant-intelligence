"""Optionale SAIA-KI-API-Anbindung (GWDG, Scalable AI Accelerator).

Die SAIA-KI-API der Gesellschaft fuer wissenschaftliche Datenverarbeitung
mbH Goettingen (GWDG) steht allen Hochschulangehoerigen zur Verfuegung und
kann beantragt werden (siehe docs/Einreichung.md).

Wichtig (DSGVO / Datenhoheit):
  - Dieses Modul ist **standardmaessig inaktiv**.
  - Es sendet NUR Daten an SAIA, wenn beides gesetzt ist:
      SAIA_API_URL=<Endpoint>   (z.B. https://llm.gwdg.de/v1/chat/completions)
      SAIA_API_KEY=<Token>
  - Ohne Konfiguration liefern alle Funktionen `None` bzw. den
    regelbasierten Fallback – das Verhalten der restlichen Anwendung
    aendert sich nicht.
"""

from __future__ import annotations

import os
from typing import Any

# Optional import: httpx ist fuer Fetchers vorhanden, aber SAIA soll
# auch ohne installiertes httpx importierbar bleiben.
try:
    import httpx
except ImportError:  # pragma: no cover
    httpx = None  # type: ignore[assignment]  # pragma: no cover


def saia_konfiguriert() -> bool:
    """True, wenn SAIA_API_URL und SAIA_API_KEY gesetzt sind."""
    return bool(os.environ.get("SAIA_API_URL") and os.environ.get("SAIA_API_KEY"))


def erweiterte_begruendung(
    programm: dict[str, Any], felder: list[str], karriere: str | None
) -> str | None:
    """Optional: KI-gestuetzte Begruendung fuer ein Programm via SAIA.

    Args:
        programm: Programm-Datensatz aus dem Katalog.
        felder: Forschungsfelder des Profils.
        karriere: Karrierestufe.

    Returns:
        Zusaetzliche Begruendung (deutsch) oder None, wenn SAIA nicht
        konfiguriert oder der Aufruf fehlschlaegt (Fail-open: der
        regelbasierte Text bleibt massgeblich).
    """
    if not saia_konfiguriert() or httpx is None:
        return None

    prompt = (
        "Du bist ein Foerderberater fuer eine deutsche Hochschule. "
        f"Programm: {programm.get('name')} (Kategorie {programm.get('kategorie')}). "
        f"Forschungsfelder: {', '.join(felder)}. Karrierestufe: {karriere or 'unbekannt'}. "
        "Erklaere in 2-3 Saetzen, warum dieses Programm zum Profil passt. "
        "Nur faktenbasiert, keine Versprechen."
    )

    try:
        resp = httpx.post(
            os.environ["SAIA_API_URL"],
            headers={
                "Authorization": f"Bearer {os.environ.get('SAIA_API_KEY', '')}",
                "Content-Type": "application/json",
            },
            json={
                "model": os.environ.get("SAIA_MODEL", "default"),
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 150,
            },
            timeout=30.0,
        )
        resp.raise_for_status()
        data = resp.json()
        return str(data["choices"][0]["message"]["content"]).strip() or None
    except Exception:
        # Fail-open: SAIA-Ausfall darf den Brief nicht brechen.
        return None
