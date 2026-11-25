"""REST-Endpoints der Anwendung (Web/REST Service Layer).

Aufgaben dieser Schicht:
- HTTP-Anfragen entgegennehmen und JSON-Messages validieren (siehe messages.py)
- passenden Business Service aufrufen (Injection über FastAPI ``Depends``)
- Ergebnis bzw. fachliche Fehler in HTTP-Antworten übersetzen (201, 404, 409 ...)

Keine Geschäftslogik und keine Datenbankzugriffe in dieser Datei!

Endpunkte (siehe docs/projektbeschreibung.md, Tabelle 3):
    /api/mitglieder, /api/kurse, /api/buchungen
Alle Endpunkte mit Beschreibung zeigt FastAPI unter http://localhost:8000/docs.
"""
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, Request
from fastapi.responses import JSONResponse

from app.business.dtos import KursDaten, MitgliedDaten
from app.business.exceptions import GeschaeftsregelVerletzt, NichtGefunden, UngueltigeEingabe
from app.business.services import (
    BuchungService,
    KursService,
    MitgliedService,
    get_buchung_service,
    get_kurs_service,
    get_mitglied_service,
)
from app.web.messages import (
    BuchungRequest,
    BuchungResponse,
    FehlerResponse,
    KursRequest,
    KursResponse,
    MitgliedRequest,
    MitgliedResponse,
)

router = APIRouter()

# Kurzschreibweisen für die Dependency Injection: FastAPI erzeugt pro Request
# eine Session und damit den Business Service (siehe services.py, unten)
MitgliedSvc = Annotated[MitgliedService, Depends(get_mitglied_service)]
KursSvc = Annotated[KursService, Depends(get_kurs_service)]
BuchungSvc = Annotated[BuchungService, Depends(get_buchung_service)]

# Für die API-Doku unter /docs: welche Fehlerantworten es geben kann
FEHLER_404 = {404: {"model": FehlerResponse, "description": "Nicht gefunden"}}
FEHLER_400_409 = {
    400: {"model": FehlerResponse, "description": "Ungültige Eingabe"},
    409: {"model": FehlerResponse, "description": "Geschäftsregel verletzt"},
}


@router.get("/health", tags=["System"])
def health() -> dict:
    """Einfacher Test-Endpunkt: zeigt, dass der Server läuft."""
    return {"status": "ok", "app": "GymFlow"}


# ======================================================================
# Mitglieder
# ======================================================================

@router.get("/mitglieder", tags=["Mitglieder"])
def mitglieder_auflisten(service: MitgliedSvc, suche: str | None = None) -> list[MitgliedResponse]:
    """Alle Mitglieder, optional gefiltert nach Name oder E-Mail (?suche=...)."""
    return service.alle(suche)


@router.get("/mitglieder/{mitglied_id}", tags=["Mitglieder"], responses=FEHLER_404)
def mitglied_abrufen(mitglied_id: int, service: MitgliedSvc) -> MitgliedResponse:
    return service.nach_id(mitglied_id)


@router.post("/mitglieder", status_code=201, tags=["Mitglieder"], responses=FEHLER_400_409)
def mitglied_erfassen(daten: MitgliedRequest, service: MitgliedSvc) -> MitgliedResponse:
    # Message (Pydantic) -> DTO (Business Layer)
    return service.erstellen(MitgliedDaten(**daten.model_dump()))


@router.put("/mitglieder/{mitglied_id}", tags=["Mitglieder"], responses=FEHLER_404 | FEHLER_400_409)
def mitglied_aendern(mitglied_id: int, daten: MitgliedRequest, service: MitgliedSvc) -> MitgliedResponse:
    return service.aendern(mitglied_id, MitgliedDaten(**daten.model_dump()))


@router.delete("/mitglieder/{mitglied_id}", status_code=204, tags=["Mitglieder"],
               responses=FEHLER_404 | FEHLER_400_409)
def mitglied_loeschen(mitglied_id: int, service: MitgliedSvc) -> None:
    """Löscht ein Mitglied (nicht möglich bei aktiven, zukünftigen Buchungen, GR-6)."""
    service.loeschen(mitglied_id)


@router.get("/mitglieder/{mitglied_id}/buchungen", tags=["Mitglieder"], responses=FEHLER_404)
def buchungen_eines_mitglieds(mitglied_id: int, service: BuchungSvc) -> list[BuchungResponse]:
    """Alle Buchungen eines Mitglieds (aktive und stornierte)."""
    return service.fuer_mitglied(mitglied_id)


# ======================================================================
# Kurse
# ======================================================================

@router.get("/kurse", tags=["Kurse"])
def kurse_auflisten(service: KursSvc) -> list[KursResponse]:
    """Alle Kurse inkl. freier Plätze und Auslastung (GR-7)."""
    return service.alle()


@router.get("/kurse/{kurs_id}", tags=["Kurse"], responses=FEHLER_404)
def kurs_abrufen(kurs_id: int, service: KursSvc) -> KursResponse:
    return service.nach_id(kurs_id)


@router.post("/kurse", status_code=201, tags=["Kurse"], responses=FEHLER_400_409)
def kurs_erfassen(daten: KursRequest, service: KursSvc) -> KursResponse:
    return service.erstellen(KursDaten(**daten.model_dump()))


@router.put("/kurse/{kurs_id}", tags=["Kurse"], responses=FEHLER_404 | FEHLER_400_409)
def kurs_aendern(kurs_id: int, daten: KursRequest, service: KursSvc) -> KursResponse:
    return service.aendern(kurs_id, KursDaten(**daten.model_dump()))


@router.delete("/kurse/{kurs_id}", status_code=204, tags=["Kurse"], responses=FEHLER_404 | FEHLER_400_409)
def kurs_loeschen(kurs_id: int, service: KursSvc) -> None:
    """Löscht einen Kurs (nicht möglich bei aktiven Buchungen, GR-6)."""
    service.loeschen(kurs_id)


@router.get("/kurse/{kurs_id}/buchungen", tags=["Kurse"], responses=FEHLER_404)
def teilnehmende_eines_kurses(kurs_id: int, service: BuchungSvc, nur_aktive: bool = True) -> list[BuchungResponse]:
    """Teilnehmendenliste eines Kurses (mit ?nur_aktive=false auch stornierte)."""
    return service.fuer_kurs(kurs_id, nur_aktive)


# ======================================================================
# Buchungen
# ======================================================================

@router.post("/buchungen", status_code=201, tags=["Buchungen"], responses=FEHLER_404 | FEHLER_400_409)
def kurs_buchen(daten: BuchungRequest, service: BuchungSvc) -> BuchungResponse:
    """Bucht einen Kurs für ein Mitglied (prüft GR-1 bis GR-4)."""
    return service.buchen(daten.mitglied_id, daten.kurs_id)


@router.delete("/buchungen/{buchung_id}", tags=["Buchungen"], responses=FEHLER_404 | FEHLER_400_409)
def buchung_stornieren(buchung_id: int, service: BuchungSvc) -> BuchungResponse:
    """Storniert eine Buchung (Status -> STORNIERT, bis 2 h vor Kursbeginn, GR-4).

    Die Buchung wird nicht gelöscht (Soft Delete), darum kommt sie mit dem
    neuen Status zurück. Ein wiederholter Aufruf hat keinen weiteren Effekt
    (idempotent).
    """
    return service.stornieren(buchung_id)


# ======================================================================
# Fehlerbehandlung: fachliche Exceptions -> HTTP-Statuscodes
# ======================================================================
# Statt in jedem Endpunkt try/except zu schreiben, wird die Übersetzung
# einmal zentral bei der FastAPI-App registriert (Aufruf in main.py).
# Jede Fehlerantwort hat die Form {"detail": "...", "code": "..."}.

def _fehler(status: int, fehler: Exception) -> JSONResponse:
    return JSONResponse(status_code=status, content={"detail": str(fehler), "code": fehler.code})


def fehlerbehandlung_einrichten(app: FastAPI) -> None:
    @app.exception_handler(NichtGefunden)
    def nicht_gefunden(request: Request, fehler: NichtGefunden) -> JSONResponse:
        return _fehler(404, fehler)  # 404 Not Found

    @app.exception_handler(UngueltigeEingabe)
    def ungueltige_eingabe(request: Request, fehler: UngueltigeEingabe) -> JSONResponse:
        return _fehler(400, fehler)  # 400 Bad Request

    @app.exception_handler(GeschaeftsregelVerletzt)
    def geschaeftsregel_verletzt(request: Request, fehler: GeschaeftsregelVerletzt) -> JSONResponse:
        # gilt auch für alle Unterklassen (KursAusgebuchtError, ZuJungError, ...)
        return _fehler(409, fehler)  # 409 Conflict
