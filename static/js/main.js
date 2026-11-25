// Start der Anwendung und Navigation zwischen den Bereichen ohne Neuladen
// der Seite. Wird als letzte Datei geladen (siehe index.html), damit alle
// Bereiche ihre Ladefunktion schon in «Ansichten» eingetragen haben.

// ------------------------------------------------------------------ Navigation

function zeigeBereich(ziel) {
    $(".tab").removeClass("active");
    $(".tab[data-target='" + ziel + "']").addClass("active");
    $(".view").removeClass("active");
    $("#" + ziel).addClass("active");
    // Daten beim Wechsel neu laden, damit sie aktuell sind
    if (Ansichten[ziel]) {
        Ansichten[ziel]();
    }
}

$(document).ready(function () {
    $(".tab").on("click", function () {
        zeigeBereich($(this).data("target"));
    });

    // Verbindung zum Server prüfen
    API.health()
        .done(function (data) { $("#server-status").text("Server: " + data.status); })
        .fail(function () { $("#server-status").text("Server: nicht erreichbar"); });

    // Startansicht laden
    zeigeBereich("mitglieder");
});
