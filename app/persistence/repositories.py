"""Repositories: alle Lese- und Schreibzugriffe auf die Datenbank.

Umsetzung des Repository Patterns nach Schaaf (2026, Einheit 3, Abschnitt 3.3):
Jedes Repository ist der zentrale Zugriffspunkt für eine Entitätsklasse. Der
Business Layer ruft nur diese Klassen auf und schreibt selbst kein SQL.
Jedes Repository bekommt die Session im Konstruktor (Dependency Injection),
damit alle Zugriffe eines Requests in derselben Session laufen.

Die Grundmethoden (find_by_id, find_all, save, delete) stehen einmal in der
generischen Basisklasse BaseRepository. Die konkreten Repositories enthalten
nur noch ihre speziellen Abfragen (Einheit 3, Abschnitt 3.3.2). Die Namen
folgen der Konvention aus dem Unterricht (find_..., save, delete), damit alle
Repositories einheitlich aufgebaut sind.

Hier stehen keine Geschäftsregeln. Ob z. B. ein Kurs noch Platz hat,
entscheidet der Business Layer; hier wird nur gezählt.

Transaktionen: Die Methoden rufen nur flush() auf (Änderungen gehen an die
DB, die neue ID ist danach bekannt), aber nie commit(). Wann eine Transaktion
abgeschlossen wird, ist fachlich bestimmt und gehört darum in den Business
Service (Einheit 3, Abschnitt 2.1.1 «Transaktionen»).

Eager Loading: Wo Listen von Buchungen zusammen mit Mitglied und Kurs
gebraucht werden, werden diese mit selectinload() gleich mitgeladen. Sonst
würde für jede Buchung eine eigene Abfrage abgesetzt (N+1-Problem,
Einheit 3, Abschnitt 3.2.2 «(Lazy) Loading»).
"""
from typing import Generic, TypeVar

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.persistence.entities import Buchung, BuchungStatus, Kurs, Mitglied

# T steht für die Entitätsklasse (Mitglied, Kurs oder Buchung).
# Generic[T] entspricht der Schreibweise BaseRepository[T] aus dem Skript,
# funktioniert aber auch mit Python-Versionen vor 3.12.
T = TypeVar("T")


class BaseRepository(Generic[T]):
    """Grundmethoden, die für jede Entitätsklasse gleich sind."""

    model: type[T]  # Entitätsklasse, wird in der Unterklasse gesetzt

    def __init__(self, session: Session):
        self.session = session

    def find_by_id(self, id: int) -> T | None:
        """Entität anhand des Primärschlüssels laden (oder None)."""
        return self.session.get(self.model, id)

    def find_all(self) -> list[T]:
        return list(self.session.scalars(select(self.model)))

    def save(self, entity: T) -> T:
        """Neue Entität anlegen oder geänderte Entität speichern."""
        self.session.add(entity)
        self.session.flush()  # schickt INSERT/UPDATE an die DB, noch ohne commit
        return entity

    def delete(self, entity: T) -> None:
        self.session.delete(entity)
        self.session.flush()  # schickt DELETE an die DB, noch ohne commit


class MitgliedRepository(BaseRepository[Mitglied]):
    model = Mitglied

    def find_all(self, suche: str | None = None) -> list[Mitglied]:
        """Alle Mitglieder nach Name sortiert, optional gefiltert nach Vorname, Nachname oder E-Mail."""
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
        return list(self.session.scalars(abfrage))

    def find_by_email(self, email: str) -> Mitglied | None:
        """Mitglied mit dieser E-Mail-Adresse, falls es eines gibt (für GR-5)."""
        return self.session.scalars(select(Mitglied).where(Mitglied.email == email)).first()


class KursRepository(BaseRepository[Kurs]):
    model = Kurs

    def find_all(self) -> list[Kurs]:
        """Alle Kurse, sortiert nach Startzeit."""
        return list(self.session.scalars(select(Kurs).order_by(Kurs.startzeit)))


class BuchungRepository(BaseRepository[Buchung]):
    model = Buchung

    def count_aktive(self, kurs_id: int) -> int:
        """Wie viele aktive Buchungen ein Kurs hat (für GR-1 und GR-7)."""
        abfrage = select(func.count()).select_from(Buchung).where(
            Buchung.kurs_id == kurs_id, Buchung.status == BuchungStatus.AKTIV
        )
        return self.session.scalar(abfrage) or 0

    def count_aktive_pro_kurs(self) -> dict[int, int]:
        """Aktive Buchungen aller Kurse mit EINER Abfrage, als {kurs_id: anzahl}.

        Für die Kursliste (GR-7): statt pro Kurs einmal count_aktive()
        aufzurufen (N+1-Problem), wird mit GROUP BY für alle Kurse gezählt.
        Kurse ohne aktive Buchung kommen im Ergebnis nicht vor.
        """
        abfrage = (
            select(Buchung.kurs_id, func.count())
            .where(Buchung.status == BuchungStatus.AKTIV)
            .group_by(Buchung.kurs_id)
        )
        return {kurs_id: anzahl for kurs_id, anzahl in self.session.execute(abfrage)}

    def find_aktive(self, mitglied_id: int, kurs_id: int) -> Buchung | None:
        """Die aktive Buchung eines Mitglieds für einen Kurs, falls es eine gibt (für GR-2)."""
        abfrage = select(Buchung).where(
            Buchung.mitglied_id == mitglied_id,
            Buchung.kurs_id == kurs_id,
            Buchung.status == BuchungStatus.AKTIV,
        )
        return self.session.scalars(abfrage).first()

    def find_by_kurs(self, kurs_id: int, nur_aktive: bool = True) -> list[Buchung]:
        """Buchungen eines Kurses, für die Teilnehmendenliste (Mitglied und Kurs gleich mitgeladen)."""
        abfrage = (
            select(Buchung)
            .options(selectinload(Buchung.mitglied), selectinload(Buchung.kurs))
            .where(Buchung.kurs_id == kurs_id)
            .order_by(Buchung.buchungszeit)
        )
        if nur_aktive:
            abfrage = abfrage.where(Buchung.status == BuchungStatus.AKTIV)
        return list(self.session.scalars(abfrage))

    def find_by_mitglied(self, mitglied_id: int) -> list[Buchung]:
        """Alle Buchungen eines Mitglieds, sortiert nach Kursbeginn (Mitglied und Kurs gleich mitgeladen)."""
        abfrage = (
            select(Buchung)
            .options(selectinload(Buchung.mitglied), selectinload(Buchung.kurs))
            .join(Buchung.kurs)
            .where(Buchung.mitglied_id == mitglied_id)
            .order_by(Kurs.startzeit)
        )
        return list(self.session.scalars(abfrage))
