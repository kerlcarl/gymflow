"""Fachliche Fehler des Business Layers.

Der Service Layer übersetzt diese Exceptions in HTTP-Statuscodes (z. B. 404, 409).
"""


class GeschaeftsregelVerletzt(Exception):
    """Basisklasse für Verstösse gegen eine Geschäftsregel."""


class NichtGefunden(Exception):
    """Ein angefragtes Objekt existiert nicht."""
