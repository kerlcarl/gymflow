"""REST-Endpoints der Anwendung.

Aufgaben dieser Schicht:
- HTTP-Anfragen entgegennehmen und JSON-Messages validieren (siehe messages.py)
- passenden Business Service aufrufen (Injection über FastAPI ``Depends``)
- Ergebnis bzw. fachliche Fehler in HTTP-Antworten übersetzen (201, 404, 409 ...)

Keine Geschäftslogik und keine Datenbankzugriffe in dieser Datei!

Geplante Endpunkte (siehe docs/projektbeschreibung.md, Tabelle 3):
    /api/mitglieder, /api/kurse, /api/buchungen
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health() -> dict:
    """Einfacher Test-Endpunkt: zeigt, dass der Server läuft."""
    return {"status": "ok", "app": "GymFlow"}


# TODO: Endpunkte für Mitglieder (CRUD)
# TODO: Endpunkte für Kurse (CRUD)
# TODO: Endpunkte für Buchungen (buchen / stornieren)
