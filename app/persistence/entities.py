"""Domain Entities: die SQLAlchemy-Modellklassen von GymFlow.

Jede Klasse entspricht einer Tabelle, jedes Attribut mit mapped_column
einer Spalte (siehe ER-Diagramm in docs/er-diagramm.png).

Die m:n-Beziehung "Mitglied bucht Kurs" ist über die Entität Buchung
aufgelöst, weil die Beziehung eigene Attribute hat (Buchungszeit, Status):

    Mitglied 1 --- n Buchung n --- 1 Kurs
"""
import enum
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.persistence.database import Base


class AboTyp(enum.Enum):
    BASIC = "BASIC"
    PREMIUM = "PREMIUM"


class BuchungStatus(enum.Enum):
    AKTIV = "AKTIV"
    STORNIERT = "STORNIERT"


class Mitglied(Base):
    __tablename__ = "mitglied"

    mitglied_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vorname: Mapped[str] = mapped_column(String(50), nullable=False)
    nachname: Mapped[str] = mapped_column(String(50), nullable=False)
    # unique=True: die Datenbank selbst verhindert doppelte E-Mail-Adressen
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    geburtsdatum: Mapped[date] = mapped_column(Date, nullable=False)
    abo_typ: Mapped[AboTyp] = mapped_column(Enum(AboTyp), nullable=False, default=AboTyp.BASIC)
    eintrittsdatum: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)

    # 1:n zu Buchung. cascade: wird ein Mitglied gelöscht, werden seine
    # (alten oder stornierten) Buchungen mitgelöscht. Ob das Löschen
    # überhaupt erlaubt ist (GR-6), entscheidet der Business Layer.
    buchungen: Mapped[list["Buchung"]] = relationship(
        back_populates="mitglied", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Mitglied {self.mitglied_id} {self.vorname} {self.nachname}>"


class Kurs(Base):
    __tablename__ = "kurs"

    kurs_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    titel: Mapped[str] = mapped_column(String(80), nullable=False)
    beschreibung: Mapped[str | None] = mapped_column(Text, nullable=True)
    trainer: Mapped[str] = mapped_column(String(80), nullable=False)
    startzeit: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    dauer_min: Mapped[int] = mapped_column(Integer, nullable=False)
    max_teilnehmende: Mapped[int] = mapped_column(Integer, nullable=False)
    nur_premium: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    buchungen: Mapped[list["Buchung"]] = relationship(
        back_populates="kurs", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Kurs {self.kurs_id} {self.titel} {self.startzeit:%d.%m.%Y %H:%M}>"


class Buchung(Base):
    __tablename__ = "buchung"

    buchung_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # Fremdschlüssel auf die beiden Tabellen
    mitglied_id: Mapped[int] = mapped_column(ForeignKey("mitglied.mitglied_id"), nullable=False)
    kurs_id: Mapped[int] = mapped_column(ForeignKey("kurs.kurs_id"), nullable=False)
    buchungszeit: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.now)
    status: Mapped[BuchungStatus] = mapped_column(
        Enum(BuchungStatus), nullable=False, default=BuchungStatus.AKTIV
    )

    # n:1 zurück zu Mitglied und Kurs (buchung.mitglied, buchung.kurs)
    mitglied: Mapped["Mitglied"] = relationship(back_populates="buchungen")
    kurs: Mapped["Kurs"] = relationship(back_populates="buchungen")

    def __repr__(self) -> str:
        return f"<Buchung {self.buchung_id} M{self.mitglied_id} K{self.kurs_id} {self.status.value}>"
