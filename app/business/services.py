"""Business Services: MitgliedService, KursService, BuchungService.

Hier werden die Geschäftsregeln umgesetzt:
    GR-1 Kapazität            GR-5 Mindestalter 16 / E-Mail eindeutig
    GR-2 Keine Doppelbuchung  GR-6 Löschschutz bei aktiven Buchungen
    GR-3 Premium-Kurse        GR-7 Freie Plätze / Auslastung berechnen
    GR-4 Zeitregeln (nur zukünftige Kurse, Stornierung bis 2 h vorher)

Aufbau jedes Service (Schaaf, 2026, Einheit 3):
- bekommt die Session im Konstruktor (Constructor Injection)
- greift nur über die Repositories auf die DB zu, schreibt kein SQL
- prüft die Geschäftsregeln und wirft bei einem Verstoss eine Exception
- schliesst Änderungen mit commit() ab (Transaktionsgrenze); passiert vorher
  ein Fehler, wird nichts gespeichert
- gibt nur DTOs zurück, nie Entitäten
"""
from datetime import date, datetime, timedelta
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.business.dtos import BuchungDTO, KursDaten, KursDTO, MitgliedDaten, MitgliedDTO
from app.business.exceptions import (
    DoppelbuchungError,
    EmailVergebenError,
    HatAktiveBuchungenError,
    KapazitaetZuKleinError,
    KursAusgebuchtError,
    KursVorbeiError,
    NichtGefunden,
    NurPremiumError,
    StornofristAbgelaufenError,
    UngueltigeEingabe,
    ZuJungError,
)
from app.persistence.repositories import BuchungRepository, KursRepository, MitgliedRepository
from app.persistence.database import get_db
from app.persistence.entities import AboTyp, Buchung, BuchungStatus, Kurs, Mitglied

MINDESTALTER = 16  # GR-5
STORNOFRIST = timedelta(hours=2)  # GR-4


# ======================================================================
# Hilfsfunktionen
# ======================================================================

def berechne_alter(geburtsdatum: date, heute: date) -> int:
    """Alter in ganzen Jahren."""
    alter = heute.year - geburtsdatum.year
    # Hatte die Person dieses Jahr noch nicht Geburtstag, ist sie ein Jahr jünger
    if (heute.month, heute.day) < (geburtsdatum.month, geburtsdatum.day):
        alter -= 1
    return alter


def hat_aktive_zukuenftige_buchung(buchungen: list[Buchung], jetzt: datetime) -> bool:
    """GR-6: Gibt es eine aktive Buchung für einen Kurs, der noch nicht begonnen hat?"""
    for buchung in buchungen:
        if buchung.status == BuchungStatus.AKTIV and buchung.kurs.startzeit > jetzt:
            return True
    return False


def zu_mitglied_dto(mitglied: Mitglied) -> MitgliedDTO:
    """Entität -> DTO."""
    return MitgliedDTO(
        mitglied_id=mitglied.mitglied_id,
        vorname=mitglied.vorname,
        nachname=mitglied.nachname,
        email=mitglied.email,
        geburtsdatum=mitglied.geburtsdatum,
        alter=berechne_alter(mitglied.geburtsdatum, date.today()),
        abo_typ=mitglied.abo_typ.value,
        eintrittsdatum=mitglied.eintrittsdatum,
    )


def zu_buchung_dto(buchung: Buchung) -> BuchungDTO:
    """Entität -> DTO."""
    return BuchungDTO(
        buchung_id=buchung.buchung_id,
        mitglied_id=buchung.mitglied_id,
        mitglied_name=f"{buchung.mitglied.vorname} {buchung.mitglied.nachname}",
        kurs_id=buchung.kurs_id,
        kurs_titel=buchung.kurs.titel,
        kurs_startzeit=buchung.kurs.startzeit,
        buchungszeit=buchung.buchungszeit,
        status=buchung.status.value,
    )


# ======================================================================
# MitgliedService
# ======================================================================

class MitgliedService:
    def __init__(self, db: Session):
        self.db = db
        self.mitglieder = MitgliedRepository(db)

    def alle(self, suche: str | None = None) -> list[MitgliedDTO]:
        return [zu_mitglied_dto(m) for m in self.mitglieder.find_all(suche)]

    def nach_id(self, mitglied_id: int) -> MitgliedDTO:
        return zu_mitglied_dto(self._laden(mitglied_id))

    def erstellen(self, daten: MitgliedDaten) -> MitgliedDTO:
        abo_typ = self._pruefen(daten)
        mitglied = Mitglied(
            vorname=daten.vorname.strip(),
            nachname=daten.nachname.strip(),
            email=daten.email.strip().lower(),
            geburtsdatum=daten.geburtsdatum,
            abo_typ=abo_typ,
        )
        self.mitglieder.save(mitglied)
        self.db.commit()
        return zu_mitglied_dto(mitglied)

    def aendern(self, mitglied_id: int, daten: MitgliedDaten) -> MitgliedDTO:
        mitglied = self._laden(mitglied_id)
        abo_typ = self._pruefen(daten, mitglied_id=mitglied_id)
        mitglied.vorname = daten.vorname.strip()
        mitglied.nachname = daten.nachname.strip()
        mitglied.email = daten.email.strip().lower()
        mitglied.geburtsdatum = daten.geburtsdatum
        mitglied.abo_typ = abo_typ
        self.mitglieder.save(mitglied)
        self.db.commit()
        return zu_mitglied_dto(mitglied)

    def loeschen(self, mitglied_id: int) -> None:
        mitglied = self._laden(mitglied_id)
        # GR-6: nicht löschen, solange es noch aktive, zukünftige Buchungen gibt
        if hat_aktive_zukuenftige_buchung(mitglied.buchungen, datetime.now()):
            raise HatAktiveBuchungenError(
                "Das Mitglied hat noch aktive Buchungen für kommende Kurse. "
                "Bitte diese zuerst stornieren."
            )
        self.mitglieder.delete(mitglied)
        self.db.commit()

    # ---- intern ----

    def _laden(self, mitglied_id: int) -> Mitglied:
        mitglied = self.mitglieder.find_by_id(mitglied_id)
        if mitglied is None:
            raise NichtGefunden(f"Mitglied {mitglied_id} nicht gefunden.")
        return mitglied

    def _pruefen(self, daten: MitgliedDaten, mitglied_id: int | None = None) -> AboTyp:
        """Prüft GR-5 und den Abo-Typ. Gibt den Abo-Typ als Enum zurück.

        mitglied_id ist beim Ändern gesetzt, damit das Mitglied seine eigene
        E-Mail-Adresse behalten darf.
        """
        # GR-5: Mindestalter
        if berechne_alter(daten.geburtsdatum, date.today()) < MINDESTALTER:
            raise ZuJungError(f"Mitglieder müssen mindestens {MINDESTALTER} Jahre alt sein.")

        # GR-5: E-Mail eindeutig
        vorhanden = self.mitglieder.find_by_email(daten.email.strip().lower())
        if vorhanden is not None and vorhanden.mitglied_id != mitglied_id:
            raise EmailVergebenError(f"Die E-Mail-Adresse {daten.email} ist bereits vergeben.")

        # Abo-Typ muss BASIC oder PREMIUM sein
        try:
            return AboTyp(daten.abo_typ)
        except ValueError:
            raise UngueltigeEingabe(f"Unbekannter Abo-Typ: {daten.abo_typ}")


# ======================================================================
# KursService
# ======================================================================

class KursService:
    def __init__(self, db: Session):
        self.db = db
        self.kurse = KursRepository(db)
        self.buchungen = BuchungRepository(db)

    def alle(self) -> list[KursDTO]:
        # Aktive Buchungen aller Kurse mit einer einzigen Abfrage zählen,
        # statt einmal pro Kurs (N+1-Problem, Einheit 3, Abschnitt 3.2.2)
        anzahl_pro_kurs = self.buchungen.count_aktive_pro_kurs()
        return [self._zu_dto(k, anzahl_pro_kurs.get(k.kurs_id, 0)) for k in self.kurse.find_all()]

    def nach_id(self, kurs_id: int) -> KursDTO:
        return self._zu_dto(self._laden(kurs_id))

    def erstellen(self, daten: KursDaten) -> KursDTO:
        self._pruefen(daten)
        kurs = Kurs(
            titel=daten.titel.strip(),
            beschreibung=daten.beschreibung,
            trainer=daten.trainer.strip(),
            startzeit=daten.startzeit,
            dauer_min=daten.dauer_min,
            max_teilnehmende=daten.max_teilnehmende,
            nur_premium=daten.nur_premium,
        )
        self.kurse.save(kurs)
        self.db.commit()
        return self._zu_dto(kurs)

    def aendern(self, kurs_id: int, daten: KursDaten) -> KursDTO:
        kurs = self._laden(kurs_id)
        self._pruefen(daten)
        # GR-6: Kapazität nicht unter die Zahl der aktiven Buchungen senken
        aktive = self.buchungen.count_aktive(kurs_id)
        if daten.max_teilnehmende < aktive:
            raise KapazitaetZuKleinError(
                f"Es gibt bereits {aktive} aktive Buchungen. "
                f"Die maximale Teilnehmendenzahl darf nicht kleiner sein."
            )
        kurs.titel = daten.titel.strip()
        kurs.beschreibung = daten.beschreibung
        kurs.trainer = daten.trainer.strip()
        kurs.startzeit = daten.startzeit
        kurs.dauer_min = daten.dauer_min
        kurs.max_teilnehmende = daten.max_teilnehmende
        kurs.nur_premium = daten.nur_premium
        self.kurse.save(kurs)
        self.db.commit()
        return self._zu_dto(kurs)

    def loeschen(self, kurs_id: int) -> None:
        kurs = self._laden(kurs_id)
        # GR-6: nicht löschen, solange es noch aktive Buchungen gibt und der Kurs noch kommt
        if hat_aktive_zukuenftige_buchung(kurs.buchungen, datetime.now()):
            raise HatAktiveBuchungenError(
                "Der Kurs hat noch aktive Buchungen. Bitte diese zuerst stornieren."
            )
        self.kurse.delete(kurs)
        self.db.commit()

    # ---- intern ----

    def _laden(self, kurs_id: int) -> Kurs:
        kurs = self.kurse.find_by_id(kurs_id)
        if kurs is None:
            raise NichtGefunden(f"Kurs {kurs_id} nicht gefunden.")
        return kurs

    def _pruefen(self, daten: KursDaten) -> None:
        if daten.dauer_min <= 0:
            raise UngueltigeEingabe("Die Dauer muss grösser als 0 Minuten sein.")
        if daten.max_teilnehmende <= 0:
            raise UngueltigeEingabe("Die maximale Teilnehmendenzahl muss grösser als 0 sein.")

    def _zu_dto(self, kurs: Kurs, aktive: int | None = None) -> KursDTO:
        """Entität -> DTO, inklusive Kennzahlen (GR-7).

        aktive kann mitgegeben werden, wenn die Anzahl schon bekannt ist
        (Kursliste); sonst wird sie für diesen einen Kurs abgefragt.
        """
        if aktive is None:
            aktive = self.buchungen.count_aktive(kurs.kurs_id)
        freie_plaetze = max(kurs.max_teilnehmende - aktive, 0)
        auslastung = round(aktive * 100 / kurs.max_teilnehmende)
        return KursDTO(
            kurs_id=kurs.kurs_id,
            titel=kurs.titel,
            beschreibung=kurs.beschreibung,
            trainer=kurs.trainer,
            startzeit=kurs.startzeit,
            dauer_min=kurs.dauer_min,
            max_teilnehmende=kurs.max_teilnehmende,
            nur_premium=kurs.nur_premium,
            aktive_buchungen=aktive,
            freie_plaetze=freie_plaetze,
            auslastung_prozent=auslastung,
        )


# ======================================================================
# BuchungService
# ======================================================================

class BuchungService:
    def __init__(self, db: Session):
        self.db = db
        self.mitglieder = MitgliedRepository(db)
        self.kurse = KursRepository(db)
        self.buchungen = BuchungRepository(db)

    def buchen(self, mitglied_id: int, kurs_id: int) -> BuchungDTO:
        mitglied = self.mitglieder.find_by_id(mitglied_id)
        if mitglied is None:
            raise NichtGefunden(f"Mitglied {mitglied_id} nicht gefunden.")
        kurs = self.kurse.find_by_id(kurs_id)
        if kurs is None:
            raise NichtGefunden(f"Kurs {kurs_id} nicht gefunden.")

        # GR-4: nur zukünftige Kurse sind buchbar
        if kurs.startzeit <= datetime.now():
            raise KursVorbeiError("Der Kurs hat bereits begonnen oder ist vorbei.")

        # GR-3: Premium-Kurse nur mit Premium-Abo
        if kurs.nur_premium and mitglied.abo_typ != AboTyp.PREMIUM:
            raise NurPremiumError("Dieser Kurs ist nur für Mitglieder mit Premium-Abo.")

        # GR-2: keine Doppelbuchung (stornierte Buchungen zählen nicht)
        if self.buchungen.find_aktive(mitglied_id, kurs_id) is not None:
            raise DoppelbuchungError("Das Mitglied hat diesen Kurs bereits gebucht.")

        # GR-1: Kapazität
        if self.buchungen.count_aktive(kurs_id) >= kurs.max_teilnehmende:
            raise KursAusgebuchtError("Der Kurs ist ausgebucht.")

        # Alle Regeln erfüllt: Buchung anlegen (Buchungszeit und Status AKTIV
        # setzt die Entität automatisch über ihre Default-Werte)
        buchung = Buchung(mitglied=mitglied, kurs=kurs)
        self.buchungen.save(buchung)
        self.db.commit()
        return zu_buchung_dto(buchung)

    def stornieren(self, buchung_id: int) -> BuchungDTO:
        buchung = self.buchungen.find_by_id(buchung_id)
        if buchung is None:
            raise NichtGefunden(f"Buchung {buchung_id} nicht gefunden.")

        # Schon storniert: nichts tun. Dadurch ist die Operation idempotent,
        # ein wiederholter Aufruf hat keinen weiteren Effekt (Einheit 2, 2.2.4).
        if buchung.status == BuchungStatus.STORNIERT:
            return zu_buchung_dto(buchung)

        # GR-4: Stornierung nur bis 2 Stunden vor Kursbeginn
        if buchung.kurs.startzeit - datetime.now() < STORNOFRIST:
            raise StornofristAbgelaufenError(
                "Eine Stornierung ist nur bis 2 Stunden vor Kursbeginn möglich."
            )

        # Soft Delete: Status ändern statt löschen, die Historie bleibt erhalten
        buchung.status = BuchungStatus.STORNIERT
        self.buchungen.save(buchung)
        self.db.commit()
        return zu_buchung_dto(buchung)

    def fuer_kurs(self, kurs_id: int, nur_aktive: bool = True) -> list[BuchungDTO]:
        """Teilnehmendenliste eines Kurses."""
        if self.kurse.find_by_id(kurs_id) is None:
            raise NichtGefunden(f"Kurs {kurs_id} nicht gefunden.")
        return [zu_buchung_dto(b) for b in self.buchungen.find_by_kurs(kurs_id, nur_aktive)]

    def fuer_mitglied(self, mitglied_id: int) -> list[BuchungDTO]:
        """Alle Buchungen eines Mitglieds (aktive und stornierte)."""
        if self.mitglieder.find_by_id(mitglied_id) is None:
            raise NichtGefunden(f"Mitglied {mitglied_id} nicht gefunden.")
        return [zu_buchung_dto(b) for b in self.buchungen.find_by_mitglied(mitglied_id)]


# ======================================================================
# Provider-Funktionen für die Dependency Injection (FastAPI Depends)
# ======================================================================
# Der Service Layer schreibt z. B.:
#     service: Annotated[KursService, Depends(get_kurs_service)]
# FastAPI erzeugt dann pro Request eine Session (get_db) und damit den Service.

def get_mitglied_service(db: Annotated[Session, Depends(get_db)]) -> MitgliedService:
    return MitgliedService(db)


def get_kurs_service(db: Annotated[Session, Depends(get_db)]) -> KursService:
    return KursService(db)


def get_buchung_service(db: Annotated[Session, Depends(get_db)]) -> BuchungService:
    return BuchungService(db)
