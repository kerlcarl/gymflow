// View-Logik: Navigation zwischen den Bereichen ohne Neuladen der Seite.
$(document).ready(function () {
    $(".tab").on("click", function () {
        $(".tab").removeClass("active");
        $(this).addClass("active");
        $(".view").removeClass("active");
        $("#" + $(this).data("target")).addClass("active");
    });

    // Verbindung zum Server prüfen
    API.health()
        .done(function (data) { $("#server-status").text("Server: " + data.status); })
        .fail(function () { $("#server-status").text("Server: nicht erreichbar"); });
});
