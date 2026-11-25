"""Messages (Pydantic-Modelle) für Requests und Responses der REST-Services.

Messages beschreiben das JSON, das zwischen Browser und Server ausgetauscht
wird (Schaaf, 2026, Einheit 2, Abschnitt 3.2.3 und Einheit 3, Abschnitt 4.1):

- ...Request:  was der Client bei POST/PUT schickt. FastAPI prüft dabei
               automatisch, ob alle Felder da sind und den richtigen Typ
               und die richtige Länge haben (sonst Antwort 422).
- ...Response: was der Server zurückschickt. Nur die hier deklarierten
               Felder gehen an den Client.

Die Responses werden direkt aus den DTOs des Business Layers erzeugt
(from_attributes=True liest die gleichnamigen Attribute aus dem DTO).
"""
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------- Mitglied

class MitgliedRequest(BaseModel):
    vorname: str = Field(min_length=1, max_length=50)
    nachname: str = Field(min_length=1, max_length=50)
    # einfache Formatprüfung: etwas@etwas.etwas
    email: str = Field(max_length=100, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    geburtsdatum: date
    abo_typ: Literal["BASIC", "PREMIUM"] = "BASIC"


class MitgliedResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    mitglied_id: int
    vorname: str
    nachname: str
    email: str
    geburtsdatum: date
    alter: int
    abo_typ: str
    eintrittsdatum: date


# ---------------------------------------------------------------- Kurs

class KursRequest(BaseModel):
    titel: str = Field(min_length=1, max_length=80)
    beschreibung: str | None = None
    trainer: str = Field(min_length=1, max_length=80)
    startzeit: datetime
    dauer_min: int = Field(gt=0)  # grösser als 0
    max_teilnehmende: int = Field(gt=0)
    nur_premium: bool = False


class KursResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    kurs_id: int
    titel: str
    beschreibung: str | None
    trainer: str
    startzeit: datetime
    dauer_min: int
    max_teilnehmende: int
    nur_premium: bool
    aktive_buchungen: int
    freie_plaetze: int
    auslastung_prozent: int


# ---------------------------------------------------------------- Buchung

class BuchungRequest(BaseModel):
    mitglied_id: int
    kurs_id: int


class BuchungResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    buchung_id: int
    mitglied_id: int
    mitglied_name: str
    kurs_id: int
    kurs_titel: str
    kurs_startzeit: datetime
    buchungszeit: datetime
    status: str


# ---------------------------------------------------------------- Fehler

class FehlerResponse(BaseModel):
    """So sieht jede Fehlerantwort (404, 400, 409) aus."""
    detail: str  # lesbare Meldung, z. B. "Der Kurs ist ausgebucht."
    code: str  # fester Code für das Frontend, z. B. "KURS_VOLL"
