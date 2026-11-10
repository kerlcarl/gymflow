"""Business Services: MitgliedService, KursService, BuchungService.

Hier werden die Geschäftsregeln umgesetzt:
    GR-1 Kapazität            GR-5 Mindestalter 16 / E-Mail eindeutig
    GR-2 Keine Doppelbuchung  GR-6 Löschschutz bei aktiven Buchungen
    GR-3 Premium-Kurse        GR-7 Freie Plätze / Auslastung berechnen
    GR-4 Zeitregeln (nur zukünftige Kurse, Stornierung bis 2 h vorher)

TODO: Klassen implementieren, sobald Persistence Layer steht.
"""
