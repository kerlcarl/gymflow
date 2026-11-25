// Gemeinsame Hilfsfunktionen der View-Logik, welche alle Bereiche nutzen:
// Meldungen anzeigen, Werte formatieren, Formulare auslesen.

// Jeder Bereich (mitglieder.js, kurse.js, buchungen.js) trägt hier eine
// Funktion ein, welche seine Daten neu vom Server lädt.
const Ansichten = {};

// ------------------------------------------------------------------ Meldungen

let meldungTimer = null;

function zeigeMeldung(text, art) {
    // art: "erfolg" oder "fehler"
    clearTimeout(meldungTimer);
    $("#meldung")
        .text(text)
        .removeClass("erfolg fehler")
        .addClass(art)
        .prop("hidden", false);
    meldungTimer = setTimeout(function () {
        $("#meldung").prop("hidden", true);
    }, art === "fehler" ? 8000 : 4000);
}

function zeigeErfolg(text) {
    zeigeMeldung(text, "erfolg");
}

// Wird bei .fail(...) eines AJAX-Aufrufs verwendet.
// Der Server schickt bei fachlichen Fehlern (404, 400, 409)
// {"detail": "Meldung", "code": "..."}, bei ungültigen Eingaben (422)
// eine Liste in "detail" (Prüfung durch Pydantic im Service Layer).
function zeigeFehler(xhr) {
    let text = "Der Server ist nicht erreichbar.";
    const antwort = xhr.responseJSON;
    if (antwort && typeof antwort.detail === "string") {
        text = antwort.detail;
    } else if (antwort && Array.isArray(antwort.detail)) {
        const felder = antwort.detail.map(function (f) {
            return f.loc[f.loc.length - 1];
        });
        text = "Ungültige Eingabe bei: " + felder.join(", ");
    } else if (xhr.status) {
        text = "Fehler " + xhr.status + " vom Server.";
    }
    zeigeMeldung(text, "fehler");
}

// ------------------------------------------------------------------ Formatierung

// "2026-11-26" -> "26.11.2026"
function formatDatum(isoDatum) {
    const teile = isoDatum.substring(0, 10).split("-");
    return teile[2] + "." + teile[1] + "." + teile[0];
}

// "2026-11-26T18:00:00" -> "26.11.2026 18:00"
function formatDatumZeit(isoZeit) {
    return formatDatum(isoZeit) + " " + isoZeit.substring(11, 16);
}

// Liest alle Felder eines Formulars in ein Objekt {name: wert}
function formularDaten($form) {
    const daten = {};
    $form.serializeArray().forEach(function (feld) {
        daten[feld.name] = feld.value.trim();
    });
    return daten;
}

// Clientseitige Prüfung der Pflichtfelder (nur für die Benutzerfreundlichkeit,
// die verbindliche Prüfung macht der Server). Zeigt die Meldungen des Browsers.
function formularGueltig($form) {
    return $form[0].reportValidity();
}

// Button für eine Aktion in einer Tabellenzeile
function aktionsButton(text, klasse, aktion) {
    return $("<button>").text(text).addClass(klasse).on("click", aktion);
}
