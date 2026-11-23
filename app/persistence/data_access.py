"""Data Access: alle Lese- und Schreibzugriffe auf die Datenbank.

Der Business Layer ruft nur diese Klassen auf und schreibt selbst kein SQL.
Jede Klasse bekommt die Session von aussen (Dependency Injection), damit
alle Zugriffe eines Requests in derselben Session laufen.

Hier stehen keine Geschäftsregeln. Ob z. B. ein Kurs noch Platz hat,
entscheidet der Business Layer; hier wird nur gezählt.

Transaktionen: Die Methoden rufen nur flush() auf (Änderungen gehen an die
DB, die neue ID ist danach bekannt), aber nie commit(). Wann eine Transaktion
abgeschlossen wird, ist fachlich bestimmt und gehört darum in den Business
Service (Schaaf, 2026, Einheit 3, Abschnitt 2.1.1 «Transaktionen»).

Eager Loading: Wo Listen von Buchungen zusammen mit Mitglied und Kurs
gebraucht werden, werden diese mit selectinload() gleich mitgeladen. Sonst
würde für jede Buchung eine eigene Abfrage abgesetzt (N+1-Problem, Schaaf,
2026, Einheit 3, Abschnitt 3.2.2 «(Lazy) Loading»).
"""
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.persistence.entities import Buchung, BuchungStatus, Kurs, Mitglied


class MitgliedDataAccess:
    def __init__(self, db: Session):
        self.db = db

    def alle(self, suche: str | None = None) -> list[Mitglied]:
        """Alle Mitglieder, optional gefiltert nach Vorname, Nachname oder E-Mail."""
        abfrage = select(Mitglied).order_by(Mitglied.nachname, Mitglied.vorname)
        if suche:
            muster = f"%{suche}%"
            abfrage = abfrage.where(
                or_(
                    Mitglied.vorname.ilike(muster),
                    Mitglied.nachname.ilike(muster),
                    Mitglied.email.ilike(muster),
                )
            )
        return list(self.db.scalars(abfrage))

    def nach_id(self, mitglied_id: int) -> Mitglied | None:
        return self.db.get(Mitglied, mitglied_id)

    def nach_email(self, email: str) -> Mitglied | None:
        return self.db.scalars(select(Mitglied).where(Mitglied.email == email)).first()

    def speichern(self, mitglied: Mitglied) -> Mitglied:
        """Neues Mitglied anlegen oder geändertes Mitglied speichern."""
        self.db.add(mitglied)
        self.db.flush()  # schickt INSERT/UPDATE/DELETE an die DB, noch ohne commit
        return mitglied

    def loeschen(self, mitglied: Mitglied) -> None:
        self.db.delete(mitglied)
        self.db.flush()  # schickt INSERT/UPDATE/DELETE an die DB, noch ohne commit


class KursDataAccess:
    def __init__(self, db: Session):
        self.db = db

    def alle(self) -> list[Kurs]:
        return list(self.db.scalars(select(Kurs).order_by(Kurs.startzeit)))

    def nach_id(self, kurs_id: int) -> Kurs | None:
        return self.db.get(Kurs, kurs_id)

    def speichern(self, kurs: Kurs) -> Kurs:
        self.db.add(kurs)
        self.db.flush()  # schickt INSERT/UPDATE/DELETE an die DB, noch ohne commit
        return kurs

    def loeschen(self, kurs: Kurs) -> None:
        self.db.delete(kurs)
        self.db.flush()  # schickt INSERT/UPDATE/DELETE an die DB, noch ohne commit


class BuchungDataAccess:
    def __init__(self, db: Session):
        self.db = db

    def nach_id(self, buchung_id: int) -> Buchung | None:
        return self.db.get(Buchung, buchung_id)

    def anzahl_aktive(self, kurs_id: int) -> int:
        """Wie viele aktive Buchungen ein Kurs hat (für GR-1 und GR-7)."""
        abfrage = select(func.count()).select_from(Buchung).where(
            Buchung.kurs_id == kurs_id, Buchung.status == BuchungStatus.AKTIV
        )
        return self.db.scalar(abfrage) or 0

    def anzahl_aktive_pro_kurs(self) -> dict[int, int]:
        """Aktive Buchungen aller Kurse mit EINER Abfrage, als {kurs_id: anzahl}.

        Für die Kursliste (GR-7): statt pro Kurs einmal anzahl_aktive()
        aufzurufen (N+1-Problem), wird mit GROUP BY für alle Kurse gezählt.
        Kurse ohne aktive Buchung kommen im Ergebnis nicht vor.
        """
        abfrage = (
            select(Buchung.kurs_id, func.count())
            .where(Buchung.status == BuchungStatus.AKTIV)
            .group_by(Buchung.kurs_id)
        )
        return {kurs_id: anzahl for kurs_id, anzahl in self.db.execute(abfrage)}

    def aktive_buchung(self, mitglied_id: int, kurs_id: int) -> Buchung | None:
        """Die aktive Buchung eines Mitglieds für einen Kurs, falls es eine gibt (für GR-2)."""
        abfrage = select(Buchung).where(
            Buchung.mitglied_id == mitglied_id,
            Buchung.kurs_id == kurs_id,
            Buchung.status == BuchungStatus.AKTIV,
        )
        return self.db.scalars(abfrage).first()

    def fuer_kurs(self, kurs_id: int, nur_aktive: bool = True) -> list[Buchung]:
        """Buchungen eines Kurses, für die Teilnehmendenliste (Mitglied und Kurs gleich mitgeladen)."""
        abfrage = (
            select(Buchung)
            .options(selectinload(Buchung.mitglied), selectinload(Buchung.kurs))
            .where(Buchung.kurs_id == kurs_id)
            .order_by(Buchung.buchungszeit)
        )
        if nur_aktive:
            abfrage = abfrage.where(Buchung.status == BuchungStatus.AKTIV)
        return list(self.db.scalars(abfrage))

    def fuer_mitglied(self, mitglied_id: int) -> list[Buchung]:
        """Alle Buchungen eines Mitglieds, sortiert nach Kursbeginn (Mitglied und Kurs gleich mitgeladen)."""
        abfrage = (
            select(Buchung)
            .options(selectinload(Buchung.mitglied), selectinload(Buchung.kurs))
            .join(Buchung.kurs)
            .where(Buchung.mitglied_id == mitglied_id)
            .order_by(Kurs.startzeit)
        )
        return list(self.db.scalars(abfrage))

    def speichern(self, buchung: Buchung) -> Buchung:
        self.db.add(buchung)
        self.db.flush()  # schickt INSERT/UPDATE/DELETE an die DB, noch ohne commit
        return buchung
