"""Fachliche Fehler des Business Layers.

Der Business Layer kennt kein HTTP. Er meldet Probleme mit diesen Exceptions;
erst der Service Layer übersetzt sie in HTTP-Statuscodes:

    NichtGefunden            -> 404 Not Found
    UngueltigeEingabe        -> 400 Bad Request
    GeschaeftsregelVerletzt  -> 409 Conflict (gilt für alle Unterklassen)

Jede Klasse hat einen festen `code` (z. B. "KURS_VOLL"), den das Frontend
auswerten kann. Die lesbare Meldung erhält man mit str(fehler).
"""


class NichtGefunden(Exception):
    """Ein angefragtes Objekt existiert nicht."""
    code = "NICHT_GEFUNDEN"


class UngueltigeEingabe(Exception):
    """Eingabewerte sind fachlich unmöglich (z. B. Dauer 0 Minuten)."""
    code = "UNGUELTIGE_EINGABE"


class GeschaeftsregelVerletzt(Exception):
    """Basisklasse für Verstösse gegen eine Geschäftsregel."""
    code = "GESCHAEFTSREGEL_VERLETZT"


# GR-1 Kapazität
class KursAusgebuchtError(GeschaeftsregelVerletzt):
    code = "KURS_VOLL"


# GR-2 Keine Doppelbuchung
class DoppelbuchungError(GeschaeftsregelVerletzt):
    code = "BEREITS_GEBUCHT"


# GR-3 Premium-Kurse
class NurPremiumError(GeschaeftsregelVerletzt):
    code = "NUR_PREMIUM"


# GR-4 Zeitregeln
class KursVorbeiError(GeschaeftsregelVerletzt):
    code = "KURS_VORBEI"


class StornofristAbgelaufenError(GeschaeftsregelVerletzt):
    code = "STORNOFRIST_ABGELAUFEN"


# GR-5 Mitgliedsdaten
class ZuJungError(GeschaeftsregelVerletzt):
    code = "ZU_JUNG"


class EmailVergebenError(GeschaeftsregelVerletzt):
    code = "EMAIL_VERGEBEN"


# GR-6 Löschschutz
class HatAktiveBuchungenError(GeschaeftsregelVerletzt):
    code = "HAT_AKTIVE_BUCHUNGEN"


class KapazitaetZuKleinError(GeschaeftsregelVerletzt):
    code = "KAPAZITAET_ZU_KLEIN"
