"""Data Transfer Objects (DTOs) des Business Layers.

Der Business Layer gibt nie Entitäten (SQLAlchemy-Objekte) nach aussen,
sondern immer diese DTOs. So schlägt eine Änderung an der Datenbank nicht
direkt bis zum Service Layer durch (Schaaf, 2026, Einheit 3, Abschnitt 4.1
«Datenfluss über die Schichten»).

Umgesetzt als Dataclasses: Python erzeugt Konstruktor, Vergleich und
Textdarstellung automatisch.

Es gibt zwei Arten:
- ...Daten: Eingabe zum Erfassen oder Ändern (ohne ID, ohne berechnete Werte)
- ...DTO:   Ausgabe an den Service Layer (mit ID und berechneten Werten)
"""
from dataclasses import dataclass
from datetime import date, datetime


# ---------------------------------------------------------------- Mitglied

@dataclass
class MitgliedDaten:
    """Eingabe zum Erfassen oder Ändern eines Mitglieds."""
    vorname: str
    nachname: str
    email: str
    geburtsdatum: date
    abo_typ: str = "BASIC"  # "BASIC" oder "PREMIUM"


@dataclass
class MitgliedDTO:
    """Ein Mitglied, wie es der Business Layer zurückgibt."""
    mitglied_id: int
    vorname: str
    nachname: str
    email: str
    geburtsdatum: date
    alter: int  # berechnet, nicht gespeichert
    abo_typ: str
    eintrittsdatum: date


# ---------------------------------------------------------------- Kurs

@dataclass
class KursDaten:
    """Eingabe zum Erfassen oder Ändern eines Kurses."""
    titel: str
    trainer: str
    startzeit: datetime
    dauer_min: int
    max_teilnehmende: int
    beschreibung: str | None = None
    nur_premium: bool = False


@dataclass
class KursDTO:
    """Ein Kurs inklusive Kennzahlen (GR-7)."""
    kurs_id: int
    titel: str
    beschreibung: str | None
    trainer: str
    startzeit: datetime
    dauer_min: int
    max_teilnehmende: int
    nur_premium: bool
    aktive_buchungen: int  # GR-7, berechnet
    freie_plaetze: int  # GR-7, berechnet
    auslastung_prozent: int  # GR-7, berechnet


# ---------------------------------------------------------------- Buchung

@dataclass
class BuchungDTO:
    """Eine Buchung, mit Name und Kurstitel für die Anzeige."""
    buchung_id: int
    mitglied_id: int
    mitglied_name: str
    kurs_id: int
    kurs_titel: str
    kurs_startzeit: datetime
    buchungszeit: datetime
    status: str  # "AKTIV" oder "STORNIERT"
