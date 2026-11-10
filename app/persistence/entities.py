"""Domain Entities (SQLAlchemy-Modellklassen, abgeleitet von DeclarativeBase).

Geplant gemäss ER-Diagramm (docs/er-diagramm.png):
    Mitglied  (mitglied_id, vorname, nachname, email, geburtsdatum, abo_typ, eintrittsdatum)
    Kurs      (kurs_id, titel, beschreibung, trainer, startzeit, dauer_min,
               max_teilnehmende, nur_premium)
    Buchung   (buchung_id, mitglied_id -> Mitglied, kurs_id -> Kurs, buchungszeit, status)

Beziehungen: Mitglied 1:n Buchung n:1 Kurs (Auflösung der m:n-Beziehung «bucht»)

TODO: Klassen implementieren.
"""
