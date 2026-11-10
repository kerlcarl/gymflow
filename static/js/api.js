// Zentrale AJAX-Aufrufe an die REST-Services (Präsentationsschicht -> Service Layer).
const API = {
    health: function () {
        return $.getJSON("/api/health");
    }
    // TODO: mitglieder, kurse, buchungen (GET/POST/PUT/DELETE via $.ajax)
};
