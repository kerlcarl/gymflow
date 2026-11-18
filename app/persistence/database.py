"""Datenbankverbindung (Engine, Session) für den Persistence Layer.

Die Verbindungsadresse kommt aus der Umgebungsvariable DATABASE_URL
(Datei .env, Vorlage: .env.example). Ohne Angabe wird eine lokale
SQLite-Datei gymflow.db verwendet. Für MySQL reicht es, DATABASE_URL
anzupassen; der übrige Code bleibt gleich, weil SQLAlchemy beide
Datenbanken über dieselbe Schnittstelle anspricht.
"""
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()  # liest .env ein, falls vorhanden

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///gymflow.db")

# SQLite erlaubt eine Verbindung standardmässig nur im Thread, der sie
# geöffnet hat. FastAPI bearbeitet Requests in mehreren Threads, darum
# wird diese Prüfung für SQLite abgeschaltet. MySQL braucht das nicht.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

# Fabrik für Sessions. Eine Session ist eine "Arbeitseinheit" mit der DB:
# Objekte laden, ändern, und mit commit() alles zusammen speichern.
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    """Basisklasse aller Entitäten. SQLAlchemy erzeugt daraus die Tabellen."""


def get_db():
    """Stellt pro HTTP-Request eine Session bereit (für FastAPI Depends).

    Nach dem Request wird die Session in jedem Fall geschlossen,
    auch wenn unterwegs ein Fehler auftritt.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Erzeugt alle Tabellen, die noch nicht existieren."""
    from app.persistence import entities  # noqa: F401  (registriert die Klassen bei Base)

    Base.metadata.create_all(bind=engine)
