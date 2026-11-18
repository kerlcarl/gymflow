"""Testdaten für die Entwicklung.

Wird beim Start aufgerufen und füllt die Datenbank nur, wenn sie noch leer ist.
Die Kurszeiten werden relativ zu heute gesetzt, damit es immer Kurse in der
Zukunft gibt (nur diese sind buchbar, GR-4).
"""
from datetime import date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.persistence.entities import AboTyp, Buchung, Kurs, Mitglied


def testdaten_einfuegen(db: Session) -> None:
    if db.scalars(select(Mitglied)).first() is not None:
        return  # schon Daten vorhanden, nichts tun

    morgen = datetime.combine(date.today() + timedelta(days=1), datetime.min.time())

    anna = Mitglied(vorname="Anna", nachname="Meier", email="anna.meier@example.ch",
                    geburtsdatum=date(1998, 4, 12), abo_typ=AboTyp.PREMIUM)
    luca = Mitglied(vorname="Luca", nachname="Rossi", email="luca.rossi@example.ch",
                    geburtsdatum=date(2001, 9, 3), abo_typ=AboTyp.BASIC)
    sara = Mitglied(vorname="Sara", nachname="Keller", email="sara.keller@example.ch",
                    geburtsdatum=date(1990, 1, 27), abo_typ=AboTyp.BASIC)

    yoga = Kurs(titel="Yoga Flow", trainer="Nina Frei", startzeit=morgen + timedelta(hours=18),
                dauer_min=60, max_teilnehmende=12, beschreibung="Ruhiges Vinyasa für alle Levels")
    spinning = Kurs(titel="Spinning", trainer="Marco Huber", startzeit=morgen + timedelta(days=1, hours=7),
                    dauer_min=45, max_teilnehmende=2)
    hiit = Kurs(titel="HIIT Premium", trainer="Lea Baumann", startzeit=morgen + timedelta(days=2, hours=19),
                dauer_min=30, max_teilnehmende=8, nur_premium=True)

    db.add_all([anna, luca, sara, yoga, spinning, hiit])
    db.add_all([
        Buchung(mitglied=anna, kurs=yoga),
        Buchung(mitglied=luca, kurs=yoga),
        Buchung(mitglied=anna, kurs=spinning),
        Buchung(mitglied=sara, kurs=spinning),  # Spinning ist damit voll (2 von 2)
        Buchung(mitglied=anna, kurs=hiit),
    ])
    db.commit()
