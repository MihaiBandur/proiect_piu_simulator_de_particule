"""
Paleta de porti (Operations).

- GateButton: o poarta din paleta, widget propriu derivat din QAbstractButton.
- GatePalette: panoul cu portile grupate dupa rol.

Comunicarea cu restul aplicatiei se face doar prin semnale:
  - gateSelected(symbol)    -> la click pe o poarta (solutia hibrida: click in loc de drag)
  - statusMessage(text)     -> la hover, pentru bara de stare
Drag & drop: datele trase au tipul GATE_MIME_TYPE si contin simbolul portii.
Zona de circuit (Matei) accepta acest tip in dragEnterEvent()/dropEvent().
"""
from PySide6.QtCore import QEvent, QMimeData, QPoint, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QDrag, QFont, QFontMetrics, QPainter
from PySide6.QtWidgets import (
    QAbstractButton,
    QApplication,
    QGridLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from ui import style

# Formatul stabilit pentru drag & drop (contract comun cu zona de circuit)
GATE_MIME_TYPE = "application/x-quantum-gate"

# Rolurile portilor, folosite pentru grupare si pentru culoare/dimensiune/forma
ROLE_SINGLE = "single"
ROLE_CONTROLLED = "controlled"
ROLE_MEASURE = "measure"

# Simbolurile sunt aceleasi chei ca in GATE_TYPES (circuit/gate.py).
# Numele si descrierile sunt textele de ajutor din interfata (terminologia din glosar).
PALETTE_GATES = [
    ("H", "Hadamard", ROLE_SINGLE, "Pune qubitul intr-o superpozitie egala de |0⟩ si |1⟩."),
    ("X", "Pauli-X", ROLE_SINGLE, "Inverseaza starea qubitului: |0⟩ devine |1⟩ si invers."),
    ("Y", "Pauli-Y", ROLE_SINGLE, "Rotatie de 180° in jurul axei Y."),
    ("Z", "Pauli-Z", ROLE_SINGLE, "Schimba semnul componentei |1⟩."),
    ("CX", "CNOT", ROLE_CONTROLLED, "Inverseaza qubitul tinta daca qubitul de control este |1⟩."),
    ("M", "Masurare", ROLE_MEASURE, "Masoara qubitul si obtine rezultatul 0 sau 1."),
]

GROUP_TITLES = {
    ROLE_SINGLE: "Porti pe un qubit",
    ROLE_CONTROLLED: "Porti controlate",
    ROLE_MEASURE: "Masurare",
}

# numele culorii din ghidul de stil pentru fiecare rol (culoarea se citeste la desenare)
ROLE_COLOR_NAMES = {
    ROLE_SINGLE: "gate_single",
    ROLE_CONTROLLED: "gate_controlled",
    ROLE_MEASURE: "gate_measure",
}


class GateButton(QAbstractButton):
    """O poarta din paleta. Primeste gata semnalele clicked(), pressed(), toggled()."""

    statusMessage = Signal(str)

    def __init__(self, symbol, name, role, description, parent=None):
        super().__init__(parent)
        self._symbol = symbol
        self._name = name
        self._role = role
        self._description = description
        self._dragStartPos = QPoint()

        self.setText(symbol)
        self.setToolTip(f"<b>{name}</b><br>{description}")
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    # ------------------------------------------------------------- proprietati
    def symbol(self):
        return self._symbol

    def name(self):
        return self._name

    def role(self):
        return self._role

    # ------------------------------------------------------------- font
    def _labelFont(self, pointSize):
        """Fontul etichetei: pornit din fontul widget-ului (care urmeaza fontul aplicatiei)."""
        font = QFont(self.font())
        font.setPointSize(pointSize)
        font.setBold(True)
        return font

    def _widthFactor(self):
        if self._role == ROLE_CONTROLLED:
            return style.GATE_CONTROLLED_WIDTH_FACTOR
        return style.GATE_SINGLE_WIDTH_FACTOR

    # ------------------------------------------------------------- dimensiuni
    def sizeHint(self):
        metrics = QFontMetrics(self._labelFont(style.fontPointSize(style.FONT_SIZE_GATE)))
        side = max(metrics.height(), metrics.horizontalAdvance("CX")) + 2 * style.GATE_PADDING
        return QSize(side * self._widthFactor(), side)

    def minimumSizeHint(self):
        # nu poate deveni mai mica decat eticheta la fontul minim
        metrics = QFontMetrics(self._labelFont(style.FONT_SIZE_MIN))
        side = max(metrics.height(), metrics.horizontalAdvance("CX")) + style.GATE_PADDING
        return QSize(side * self._widthFactor(), side)

    def changeEvent(self, event):
        # la schimbarea fontului aplicatiei, layout-ul trebuie sa recalculeze dimensiunea
        if event.type() == QEvent.Type.FontChange:
            self.updateGeometry()
        super().changeEvent(event)

    # ------------------------------------------------------------- desenare
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        color = QColor(style.color(ROLE_COLOR_NAMES[self._role]))
        if self.isDown():
            color = color.darker(style.GATE_PRESSED_DARKER)
        elif self.underMouse():
            color = color.lighter(style.GATE_HOVER_LIGHTER)

        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        # forma (al treilea criteriu): masurarea are capetele complet rotunjite
        radius = rect.height() / 2 if self._role == ROLE_MEASURE else style.CORNER_RADIUS

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawRoundedRect(rect, radius, radius)

        painter.setPen(QColor(style.color("gate_text")))
        painter.setFont(self._labelFont(style.fontPointSize(style.FONT_SIZE_GATE)))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.text())

    # ------------------------------------------------------------- hover
    def enterEvent(self, event):
        self.statusMessage.emit(f"{self._name}: {self._description} Trage poarta pe circuit.")
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.statusMessage.emit("")
        self.update()
        super().leaveEvent(event)

    # ------------------------------------------------------------- drag
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragStartPos = event.position().toPoint()
        # apelul catre clasa de baza pastreaza semnalele pressed()/clicked()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            super().mouseMoveEvent(event)
            return
        distance = (event.position().toPoint() - self._dragStartPos).manhattanLength()
        if distance < QApplication.startDragDistance():
            super().mouseMoveEvent(event)
            return
        self._startDrag()

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)

    def createMimeData(self):
        mimeData = QMimeData()
        mimeData.setData(GATE_MIME_TYPE, self._symbol.encode("utf-8"))
        return mimeData

    def _startDrag(self):
        drag = QDrag(self)
        drag.setMimeData(self.createMimeData())
        drag.setPixmap(self.grab())
        drag.setHotSpot(QPoint(self.width() // 2, self.height() // 2))
        drag.exec(Qt.DropAction.CopyAction)
        # butonul nu mai primeste mouseReleaseEvent dupa drag, deci il ridicam manual
        self.setDown(False)


class GatePalette(QWidget):
    """Panoul Operations: portile grupate dupa rol."""

    gateSelected = Signal(str)
    statusMessage = Signal(str)

    SINGLE_COLUMNS = 2  # portile pe un qubit sunt asezate pe 2 coloane

    def __init__(self, parent=None):
        super().__init__(parent)
        self._buttons = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(style.SPACING_M)  # spatiere mare intre grupuri

        for role in (ROLE_SINGLE, ROLE_CONTROLLED, ROLE_MEASURE):
            gates = [g for g in PALETTE_GATES if g[2] == role]
            layout.addLayout(self._createGroup(GROUP_TITLES[role], gates))

        layout.addStretch()

    def _createGroup(self, title, gates):
        groupLayout = QVBoxLayout()
        groupLayout.setSpacing(style.SPACING_S)  # spatiere mica in interiorul grupului

        # titlul grupului foloseste fontul aplicatiei (deja la minim 10 pt si scalabil)
        titleLabel = QLabel(title, self)
        groupLayout.addWidget(titleLabel)

        grid = QGridLayout()
        grid.setSpacing(style.SPACING_S)
        # spatiul ramas merge intr-o coloana goala din dreapta, ca portile sa stea apropiate
        grid.setColumnStretch(self.SINGLE_COLUMNS, 1)
        for index, (symbol, name, role, description) in enumerate(gates):
            button = GateButton(symbol, name, role, description, self)
            button.clicked.connect(lambda checked=False, s=symbol: self.gateSelected.emit(s))
            button.statusMessage.connect(self.statusMessage)
            self._buttons.append(button)
            if role == ROLE_SINGLE:
                row, col = divmod(index, self.SINGLE_COLUMNS)
                grid.addWidget(button, row, col, Qt.AlignmentFlag.AlignLeft)
            else:
                grid.addWidget(button, index, 0, 1, self.SINGLE_COLUMNS, Qt.AlignmentFlag.AlignLeft)
        groupLayout.addLayout(grid)
        return groupLayout

    def buttons(self):
        return list(self._buttons)