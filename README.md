# GymFlow – Webanwendung für ein Fitnessstudio

Projekt im Modul «Webbasierte Anwendungen» (FHNW, HS 2026).
Mitglieder-, Kurs- und Buchungsverwaltung mit Schichtenarchitektur:
HTML/CSS/JS (jQuery) → REST (FastAPI) → Business Layer → Persistenz (SQLAlchemy, MySQL).

Die Projektbeschreibung inkl. ER-Diagramm liegt in [`docs/projektbeschreibung.md`](docs/projektbeschreibung.md).

## Projektstruktur

```
main.py                 Einstiegspunkt (startet Server, bindet API + static ein)
app/web/                Web/REST Service Layer (FastAPI-Endpoints, Messages)
app/business/           Business Service Layer (Geschäftslogik, DTOs)
app/persistence/        Persistence Layer (SQLAlchemy-Entitäten, DB-Zugriff)
static/                 Präsentationsschicht (HTML, CSS, JavaScript/jQuery)
docs/                   Dokumentation
```

## Lokal starten

1. Virtual Environment erstellen: `python -m venv .venv` (auf dem Mac oft `python3 -m venv .venv`)
2. Aktivieren:
   - macOS/Linux: `source .venv/bin/activate`
   - Windows: `.venv\Scripts\activate`
3. Abhängigkeiten installieren: `pip install -r requirements.txt`
4. Optional: `.env.example` nach `.env` kopieren. Ohne `.env` läuft die App mit SQLite (Datei `gymflow.db`, wird automatisch erstellt).
5. Starten: `python main.py`
6. Im Browser öffnen: http://localhost:8000 (API-Doku: http://localhost:8000/docs)

Beim ersten Start werden die Tabellen angelegt und Testdaten eingefügt (3 Mitglieder, 3 Kurse, 5 Buchungen).
Zum Zurücksetzen die Datei `gymflow.db` löschen und neu starten.

In VS Code danach mit `Cmd/Ctrl+Shift+P` → «Python: Select Interpreter» die `.venv` auswählen.

## Zusammenarbeit mit Git

```bash
git pull                      # vor dem Arbeiten immer aktuellen Stand holen
git checkout -b feature/kurse # eigener Branch pro Aufgabe
git add . && git commit -m "Kurs-Endpoints ergänzt"
git push -u origin feature/kurse   # danach Pull Request auf GitHub
```

Zugangsdaten zur Datenbank gehören in eine eigene `.env` (Vorlage: `.env.example`) und werden nicht committed.
