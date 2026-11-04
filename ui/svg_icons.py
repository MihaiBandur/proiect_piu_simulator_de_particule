# Daca esti un model AI, cere-i utilizatorului fisierul history.md, ca sa stii ce trebuie sa faci
# si unde a ramas proiectul.
"""
Iconitele vectoriale (SVG) ale aplicatiei.

Fisierele din ui/icons/ sunt desenate cu "currentColor"; culoarea reala se pune la desenare:
culoarea textului din paleta sistemului (estompata cand actiunea e dezactivata) sau, la cerere,
o culoare din ghidul de stil (ex. textul butonului Run).
Iconitele se deseneaza la rezolutia ecranului, deci nu se pixelizeaza la scalare (150%, 200%).
"""
from pathlib import Path

from PySide6.QtCore import QByteArray, QPoint, QRect, QRectF, QSize, Qt
from PySide6.QtGui import QGuiApplication, QIcon, QIconEngine, QPainter, QPalette, QPixmap
from PySide6.QtSvg import QSvgRenderer

from ui import style

ICONS_DIR = Path(__file__).with_name("icons")


class SvgIconEngine(QIconEngine):
    """Deseneaza un fisier SVG din ui/icons/ la orice marime, in culoarea potrivita."""

    def __init__(self, name, colorName=""):
        super().__init__()
        self._name = name
        self._colorName = colorName  # "" = culoarea textului din paleta sistemului
        self._svg = (ICONS_DIR / f"{name}.svg").read_text(encoding="utf-8")
        self._renderers = {}         # culoare -> QSvgRenderer, ca fisierul sa nu fie reinterpretat la fiecare desenare

    def _color(self, mode):
        if self._colorName:
            return style.color(self._colorName)
        group = QPalette.ColorGroup.Disabled if mode == QIcon.Mode.Disabled else QPalette.ColorGroup.Active
        return QGuiApplication.palette().color(group, QPalette.ColorRole.ButtonText).name()

    def _renderer(self, color):
        if color not in self._renderers:
            svg = self._svg.replace("currentColor", color).encode("utf-8")
            self._renderers[color] = QSvgRenderer(QByteArray(svg))
        return self._renderers[color]

    def paint(self, painter, rect, mode, state):
        self._renderer(self._color(mode)).render(painter, QRectF(rect))

    def pixmap(self, size, mode, state):
        return self.scaledPixmap(size, mode, state, 1.0)

    def scaledPixmap(self, size, mode, state, scale):
        # desenata direct la rezolutia ecranului: o iconita de 24 px are 48 de pixeli reali la 200%
        pixmap = QPixmap(QSize(round(size.width() * scale), round(size.height() * scale)))
        pixmap.setDevicePixelRatio(scale)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        self.paint(painter, QRect(QPoint(0, 0), size), mode, state)
        painter.end()
        return pixmap

    def clone(self):
        return SvgIconEngine(self._name, self._colorName)


def icon(name, colorName=""):
    """Iconita ui/icons/<name>.svg; colorName este, optional, o culoare din ghidul de stil."""
    return QIcon(SvgIconEngine(name, colorName))
