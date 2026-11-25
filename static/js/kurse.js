// Bereich «Kurse»: anzeigen (inkl. Auslastung), erfassen, ändern, löschen (CRUD).

function ladeKurse() {
    API.kurse()
        .done(zeigeKurse)
        .fail(zeigeFehler);
}

// Balken für die Auslastung (GR-7, vom Server berechnet)
function auslastungsBalken(k) {
    const $balken = $("<div class='balken'>").append(
        $("<div class='balken-fuellung'>").css("width", k.auslastung_prozent + "%")
    );
    if (k.freie_plaetze === 0) {
        $balken.addClass("voll");
    } else if (k.auslastung_prozent >= 75) {
        $balken.addClass("fast-voll");
    }
    const text = k.aktive_buchungen + " / " + k.max_teilnehmende +
        (k.freie_plaetze === 0 ? " · ausgebucht" : " · " + k.freie_plaetze + " frei");
    return $("<div class='auslastung'>").append($balken).append($("<small>").text(text));
}

function zeigeKurse(kurse) {
    const $tabelle = $("#kurs-tabelle").empty();
    if (kurse.length === 0) {
        $tabelle.append($("<tr>").append($("<td colspan='6' class='leer'>").text("Noch keine Kurse erfasst.")));
        return;
    }
    kurse.forEach(function (k) {
        const $titel = $("<td>").append($("<strong>").text(k.titel));
        if (k.nur_premium) {
            $titel.append(" ").append($("<span class='badge premium'>").text("Premium"));
        }
        if (k.beschreibung) {
            $titel.append($("<div class='nebentext'>").text(k.beschreibung));
        }
        $("<tr>")
            .append($("<td>").text(formatDatumZeit(k.startzeit)))
            .append($titel)
            .append($("<td>").text(k.trainer))
            .append($("<td>").text(k.dauer_min + " Min."))
            .append($("<td>").append(auslastungsBalken(k)))
            .append($("<td class='zeilen-aktionen'>")
                .append(aktionsButton("Teilnehmende", "", function () { zeigeBuchungenVon("kurs", k.kurs_id); }))
                .append(aktionsButton("Bearbeiten", "", function () { bearbeiteKurs(k); }))
                .append(aktionsButton("Löschen", "gefahr", function () { loescheKurs(k); })))
            .appendTo($tabelle);
    });
}

function oeffneKursFormular(titel) {
    $("#kurs-form-titel").text(titel);
    $("#kurs-form").prop("hidden", false).find("[name=titel]").focus();
}

function schliesseKursFormular() {
    $("#kurs-form").prop("hidden", true)[0].reset();
    $("#kurs-form [name=kurs_id]").val("");
}

function bearbeiteKurs(k) {
    const $form = $("#kurs-form");
    $form.find("[name=kurs_id]").val(k.kurs_id);
    $form.find("[name=titel]").val(k.titel);
    $form.find("[name=trainer]").val(k.trainer);
    $form.find("[name=startzeit]").val(k.startzeit.substring(0, 16));  // Format für datetime-local
    $form.find("[name=dauer_min]").val(k.dauer_min);
    $form.find("[name=max_teilnehmende]").val(k.max_teilnehmende);
    $form.find("[name=nur_premium]").prop("checked", k.nur_premium);
    $form.find("[name=beschreibung]").val(k.beschreibung || "");
    oeffneKursFormular("Kurs bearbeiten");
}

function speichereKurs(event) {
    event.preventDefault();
    const $form = $("#kurs-form");
    if (!formularGueltig($form)) {
        return;
    }
    const felder = formularDaten($form);
    const id = felder.kurs_id;
    // Werte in die Typen umwandeln, welche die REST-Schnittstelle erwartet
    const daten = {
        titel: felder.titel,
        trainer: felder.trainer,
        // Lokalzeit ohne Zeitzone senden (kein toISOString(), das würde nach UTC umrechnen)
        startzeit: felder.startzeit,
        dauer_min: parseInt(felder.dauer_min, 10),
        max_teilnehmende: parseInt(felder.max_teilnehmende, 10),
        nur_premium: $form.find("[name=nur_premium]").is(":checked"),
        beschreibung: felder.beschreibung || null
    };

    const anfrage = id ? API.kursAendern(id, daten) : API.kursErfassen(daten);
    anfrage
        .done(function (k) {
            zeigeErfolg("Kurs «" + k.titel + "» gespeichert.");
            schliesseKursFormular();
            ladeKurse();
        })
        .fail(zeigeFehler);
}

function loescheKurs(k) {
    if (!confirm("Kurs «" + k.titel + "» wirklich löschen?")) {
        return;
    }
    API.kursLoeschen(k.kurs_id)
        .done(function () {
            zeigeErfolg("Kurs gelöscht.");
            ladeKurse();
        })
        .fail(zeigeFehler);
}

$(document).ready(function () {
    Ansichten.kurse = ladeKurse;

    $("#kurs-neu").on("click", function () {
        schliesseKursFormular();
        oeffneKursFormular("Neuer Kurs");
    });
    $("#kurs-form").on("submit", speichereKurs);
    $("#kurs-form .abbrechen").on("click", schliesseKursFormular);
});
