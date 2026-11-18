"""Einstiegspunkt der GymFlow-Anwendung.

Startet den Webserver (Uvicorn), legt beim Start die Datenbanktabellen an,
bindet die REST-Services des Web Service Layers ein und liefert die
Präsentationsschicht (static/) aus.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.persistence.database import SessionLocal, init_db
from app.persistence.testdaten import testdaten_einfuegen
from app.web.api import router as api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Läuft einmal beim Start des Servers
    init_db()
    with SessionLocal() as db:
        testdaten_einfuegen(db)
    yield


app = FastAPI(
    title="GymFlow",
    description="Mitglieder-, Kurs- und Buchungsverwaltung für ein Fitnessstudio",
    lifespan=lifespan,
)

# REST-Services (Web Service Layer) unter /api
app.include_router(api_router, prefix="/api")

# Präsentationsschicht: ./static unter / ausliefern (zuletzt mounten,
# damit die API-Routen nicht überdeckt werden)
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
