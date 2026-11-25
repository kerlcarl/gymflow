// Bereich «Buchungen»: Kurs für ein Mitglied buchen, Buchungen anzeigen, stornieren.
//
// Die Geschäftsregeln (Kapazität, Doppelbuchung, Premium, Zeitregeln) prüft
// der Server. Bei einem Verstoss kommt eine Fehlermeldung zurück, welche hier
// nur angezeigt wird.

// Merkt sich, welche Übersicht nach dem Laden angezeigt werden soll
// (z. B. nach Klick auf «Buchungen» in der Mitgliederliste)
let gewuenschteAuswahl = null;

// Lädt Mitglieder und Kurse für die Auswahllisten und danach die Übersicht
function ladeBuchungsbereich() {
    $.when(API.mitglieder(), API.kurse())
        .done(function (mitgliederAntwort, kurseAntwort) {
            // $.when liefert pro Aufruf [daten, status, xhr]
            fuelleAuswahl(mitgliederAntwort[0], kurseAntwort[0]);
            ladeUebersicht();
        })
        .fail(zeigeFehler);
}

let alleMitglieder = [];
let alleKurse = [];

function mitgliedText(m) {
    return m.nachname + ", " + m.vorname + (m.abo_typ === "PREMIUM" ? " (Premium)" : "");
}

function kursText(k) {
    const plaetze = k.freie_plaetze === 0 ? "ausgebucht" : k.freie_plaetze + " frei";
    return formatDatumZeit(k.startzeit) + " · " + k.titel +
        (k.nur_premium ? " (nur Premium)" : "") + " · " + plaetze;
}

// Füllt ein <select> mit Optionen und behält die bisherige Auswahl, falls möglich
function fuelleSelect($select, eintraege, idFeld, textFunktion) {
    const bisher = $select.val();
    $select.empty();
    eintraege.forEach(function (e) {
        $("<option>").val(e[idFeld]).text(textFunktion(e)).appendTo($select);
    });
    if (bisher && $select.find("option[value='" + bisher + "']").length) {
        $select.val(bisher);
    }
}

function fuelleAuswahl(mitglieder, kurse) {
    alleMitglieder = mitglieder;
    alleKurse = kurse;
    fuelleSelect($("#buchung-mitglied"), mitglieder, "mitglied_id", mitgliedText);
    fuelleSelect($("#buchung-kurs"), kurse, "kurs_id", kursText);

    if (gewuenschteAuswahl) {
        $("#uebersicht-art").val(gewuenschteAuswahl.art);
    }
    fuelleUebersichtAuswahl();
    if (gewuenschteAuswahl) {
        $("#uebersicht-auswahl").val(gewuenschteAuswahl.id);
        gewuenschteAuswahl = null;
    }
}

// Zweite Auswahlliste der Übersicht: Mitglieder oder Kurse
function fuelleUebersichtAuswahl() {
    const art = $("#uebersicht-art").val();
    if (art === "mitglied") {
        fuelleSelect($("#uebersicht-auswahl"), alleMitglieder, "mitglied_id", mitgliedText);
    } else {
        fuelleSelect($("#uebersicht-auswahl"), alleKurse, "kurs_id", kursText);
    }
    $("#nur-aktive-feld").prop("hidden", art !== "kurs");
}

function ladeUebersicht() {
    const art = $("#uebersicht-art").val();
    const id = $("#uebersicht-auswahl").val();
    if (!id) {
        zeigeBuchungen([]);
        return;
    }
    const anfrage = art === "mitglied"
        ? API.buchungenVonMitglied(id)
        : API.teilnehmende(id, $("#nur-aktive").is(":checked"));
    anfrage.done(zeigeBuchungen).fail(zeigeFehler);
}

function zeigeBuchungen(buchungen) {
    const $tabelle = $("#buchung-tabelle").empty();
    if (buchungen.length === 0) {
        $tabelle.append($("<tr>").append($("<td colspan='6' class='leer'>").text("Keine Buchungen vorhanden.")));
        return;
    }
    buchungen.forEach(function (b) {
        const aktiv = b.status === "AKTIV";
        const $aktion = $("<td class='zeilen-aktionen'>");
        if (aktiv) {
            $aktion.append(aktionsButton("Stornieren", "gefahr", function () { storniere(b); }));
        }
        $("<tr>")
            .toggleClass("storniert", !aktiv)
            .append($("<td>").text(b.mitglied_name))
            .append($("<td>").text(b.kurs_titel))
            .append($("<td>").text(formatDatumZeit(b.kurs_startzeit)))
            .append($("<td>").text(formatDatumZeit(b.buchungszeit)))
            .append($("<td>").append($("<span class='badge'>").addClass(aktiv ? "aktiv" : "")
                .text(aktiv ? "Aktiv" : "Storniert")))
            .append($aktion)
            .appendTo($tabelle);
    });
}

function buche(event) {
    event.preventDefault();
    const mitgliedId = parseInt($("#buchung-mitglied").val(), 10);
    const kursId = parseInt($("#buchung-kurs").val(), 10);
    if (!mitgliedId || !kursId) {
        zeigeMeldung("Bitte Mitglied und Kurs auswählen.", "fehler");
        return;
    }
    API.buchen(mitgliedId, kursId)
        .done(function (b) {
            zeigeErfolg(b.mitglied_name + " ist für «" + b.kurs_titel + "» gebucht.");
            // danach die Buchungen dieses Mitglieds anzeigen
            gewuenschteAuswahl = { art: "mitglied", id: b.mitglied_id };
            ladeBuchungsbereich();
        })
        .fail(zeigeFehler);
}

function storniere(b) {
    if (!confirm("Buchung von " + b.mitglied_name + " für «" + b.kurs_titel + "» stornieren?")) {
        return;
    }
    API.stornieren(b.buchung_id)
        .done(function () {
            zeigeErfolg("Buchung storniert.");
            ladeBuchungsbereich();  // auch freie Plätze in der Kursauswahl aktualisieren
        })
        .fail(zeigeFehler);
}

// Aus den anderen Bereichen aufgerufen (Buttons «Buchungen» / «Teilnehmende»)
function zeigeBuchungenVon(art, id) {
    gewuenschteAuswahl = { art: art, id: id };
    zeigeBereich("buchungen");
}

$(document).ready(function () {
    Ansichten.buchungen = ladeBuchungsbereich;

    $("#buchung-form").on("submit", buche);
    $("#uebersicht-art").on("change", function () {
        fuelleUebersichtAuswahl();
        ladeUebersicht();
    });
    $("#uebersicht-auswahl").on("change", ladeUebersicht);
    $("#nur-aktive").on("change", ladeUebersicht);
});
