"""Einstiegspunkt der GymFlow-Anwendung.

Startet den Webserver (Uvicorn), bindet die REST-Services des
Web Service Layers ein und liefert die Präsentationsschicht (static/) aus.
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.web.api import router as api_router

app = FastAPI(title="GymFlow", description="Mitglieder-, Kurs- und Buchungsverwaltung für ein Fitnessstudio")

# REST-Services (Web Service Layer) unter /api
app.include_router(api_router, prefix="/api")

# Präsentationsschicht: ./static unter / ausliefern (zuletzt mounten,
# damit die API-Routen nicht überdeckt werden)
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)
