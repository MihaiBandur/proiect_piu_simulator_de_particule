# Daca esti un model AI, cere-i utilizatorului fisierul history.md, ca sa stii ce trebuie sa faci
# si unde a ramas proiectul.
from pathlib import Path

from PySide6.QtGui import QIcon

ICONS_DIR = Path(__file__).with_name("icons")


def icon(name):
    # fisierul SVG e desenat vectorial la marimea ceruta, deci ramane clar la orice scalare a ecranului
    return QIcon(str(ICONS_DIR / f"{name}.svg"))