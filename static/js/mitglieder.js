// Bereich «Mitglieder»: anzeigen, suchen, erfassen, ändern, löschen (CRUD).

function ladeMitglieder() {
    API.mitglieder($("#mitglied-suche").val().trim())
        .done(zeigeMitglieder)
        .fail(zeigeFehler);
}

function zeigeMitglieder(mitglieder) {
    const $tabelle = $("#mitglied-tabelle").empty();
    if (mitglieder.length === 0) {
        $tabelle.append($("<tr>").append($("<td colspan='6' class='leer'>").text("Keine Mitglieder gefunden.")));
        return;
    }
    mitglieder.forEach(function (m) {
        // .text() statt HTML-Strings: Eingaben werden nie als HTML interpretiert
        const $abo = $("<span class='badge'>").text(m.abo_typ === "PREMIUM" ? "Premium" : "Basic");
        if (m.abo_typ === "PREMIUM") {
            $abo.addClass("premium");
        }
        $("<tr>")
            .append($("<td>").text(m.vorname + " " + m.nachname))
            .append($("<td>").text(m.email))
            .append($("<td>").text(m.alter))
            .append($("<td>").append($abo))
            .append($("<td>").text(formatDatum(m.eintrittsdatum)))
            .append($("<td class='zeilen-aktionen'>")
                .append(aktionsButton("Buchungen", "", function () { zeigeBuchungenVon("mitglied", m.mitglied_id); }))
                .append(aktionsButton("Bearbeiten", "", function () { bearbeiteMitglied(m); }))
                .append(aktionsButton("Löschen", "gefahr", function () { loescheMitglied(m); })))
            .appendTo($tabelle);
    });
}

function oeffneMitgliedFormular(titel) {
    $("#mitglied-form-titel").text(titel);
    $("#mitglied-form").prop("hidden", false).find("[name=vorname]").focus();
}

function schliesseMitgliedFormular() {
    $("#mitglied-form").prop("hidden", true)[0].reset();
    $("#mitglied-form [name=mitglied_id]").val("");
}

function bearbeiteMitglied(m) {
    const $form = $("#mitglied-form");
    $form.find("[name=mitglied_id]").val(m.mitglied_id);
    $form.find("[name=vorname]").val(m.vorname);
    $form.find("[name=nachname]").val(m.nachname);
    $form.find("[name=email]").val(m.email);
    $form.find("[name=geburtsdatum]").val(m.geburtsdatum);
    $form.find("[name=abo_typ]").val(m.abo_typ);
    oeffneMitgliedFormular("Mitglied bearbeiten");
}

function speichereMitglied(event) {
    event.preventDefault();  // Formular nicht klassisch absenden (kein Neuladen der Seite)
    const $form = $("#mitglied-form");
    if (!formularGueltig($form)) {
        return;
    }
    const daten = formularDaten($form);
    const id = daten.mitglied_id;
    delete daten.mitglied_id;  // gehört in die URL, nicht in den Body

    const anfrage = id ? API.mitgliedAendern(id, daten) : API.mitgliedErfassen(daten);
    anfrage
        .done(function (m) {
            zeigeErfolg("Mitglied " + m.vorname + " " + m.nachname + " gespeichert.");
            schliesseMitgliedFormular();
            ladeMitglieder();
        })
        .fail(zeigeFehler);
}

function loescheMitglied(m) {
    if (!confirm("Mitglied " + m.vorname + " " + m.nachname + " wirklich löschen?")) {
        return;
    }
    API.mitgliedLoeschen(m.mitglied_id)
        .done(function () {
            zeigeErfolg("Mitglied gelöscht.");
            ladeMitglieder();
        })
        .fail(zeigeFehler);
}

$(document).ready(function () {
    Ansichten.mitglieder = ladeMitglieder;

    $("#mitglied-neu").on("click", function () {
        schliesseMitgliedFormular();
        oeffneMitgliedFormular("Neues Mitglied");
    });
    $("#mitglied-form").on("submit", speichereMitglied);
    $("#mitglied-form .abbrechen").on("click", schliesseMitgliedFormular);

    // Suche: kurz nach der letzten Eingabe neu laden
    let suchTimer = null;
    $("#mitglied-suche").on("input", function () {
        clearTimeout(suchTimer);
        suchTimer = setTimeout(ladeMitglieder, 250);
    });
});
