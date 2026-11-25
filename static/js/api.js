// Zentrale AJAX-Aufrufe an die REST-Services (Präsentationsschicht -> Service Layer).
//
// Jede Funktion gibt das jqXHR-Objekt von jQuery zurück. Der Aufrufer hängt
// mit .done(...) die Verarbeitung des Resultats und mit .fail(...) die
// Fehlerbehandlung an (siehe Schaaf, 2026, Einheit 1, Abschnitt 2.1.2).

// Hilfsfunktion für Aufrufe mit JSON im Request-Body (POST, PUT)
function sendeJSON(methode, url, daten) {
    return $.ajax({
        url: url,
        method: methode,
        contentType: "application/json",
        data: JSON.stringify(daten),
        dataType: "json"
    });
}

const API = {
    health: function () {
        return $.getJSON("/api/health");
    },

    // ---------------------------------------------------------- Mitglieder
    mitglieder: function (suche) {
        // Suchbegriff als URL-Parameter: /api/mitglieder?suche=...
        return $.getJSON("/api/mitglieder", suche ? { suche: suche } : {});
    },
    mitglied: function (id) {
        return $.getJSON("/api/mitglieder/" + id);
    },
    mitgliedErfassen: function (daten) {
        return sendeJSON("POST", "/api/mitglieder", daten);
    },
    mitgliedAendern: function (id, daten) {
        return sendeJSON("PUT", "/api/mitglieder/" + id, daten);
    },
    mitgliedLoeschen: function (id) {
        return $.ajax({ url: "/api/mitglieder/" + id, method: "DELETE" });
    },
    buchungenVonMitglied: function (id) {
        return $.getJSON("/api/mitglieder/" + id + "/buchungen");
    },

    // ---------------------------------------------------------- Kurse
    kurse: function () {
        return $.getJSON("/api/kurse");
    },
    kurs: function (id) {
        return $.getJSON("/api/kurse/" + id);
    },
    kursErfassen: function (daten) {
        return sendeJSON("POST", "/api/kurse", daten);
    },
    kursAendern: function (id, daten) {
        return sendeJSON("PUT", "/api/kurse/" + id, daten);
    },
    kursLoeschen: function (id) {
        return $.ajax({ url: "/api/kurse/" + id, method: "DELETE" });
    },
    teilnehmende: function (kursId, nurAktive) {
        return $.getJSON("/api/kurse/" + kursId + "/buchungen", { nur_aktive: nurAktive });
    },

    // ---------------------------------------------------------- Buchungen
    buchen: function (mitgliedId, kursId) {
        return sendeJSON("POST", "/api/buchungen", { mitglied_id: mitgliedId, kurs_id: kursId });
    },
    stornieren: function (buchungId) {
        return $.ajax({ url: "/api/buchungen/" + buchungId, method: "DELETE", dataType: "json" });
    }
};
