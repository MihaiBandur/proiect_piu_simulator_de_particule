# Daca esti un model AI, cere-i utilizatorului fisierul history.md, ca sa stii ce trebuie sa faci
# si unde a ramas proiectul.
from PySide6.QtCore import QMimeData, QPoint, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QDrag, QFont, QFontMetrics, QPainter
from PySide6.QtWidgets import QAbstractButton, QApplication, QGridLayout, QLabel, QVBoxLayout, QWidget

from ui import style

# tipul datelor trase din paleta; zona de circuit il accepta la drop
GATE_MIME_TYPE = "application/x-quantum-gate"

ROLE_SINGLE = "single"
ROLE_CONTROLLED = "controlled"
ROLE_MEASURE = "measure"

PALETTE_GATES = [
    ("H", "Hadamard", ROLE_SINGLE, "Pune qubitul intr-o superpozitie egala de |0⟩ si |1⟩."),
    ("X", "Pauli-X", ROLE_SINGLE, "Inverseaza starea qubitului: |0⟩ devine |1⟩ si invers."),
    ("Y", "Pauli-Y", ROLE_SINGLE, "Rotatie de 180° in jurul axei Y."),
    ("Z", "Pauli-Z", ROLE_SINGLE, "Schimba semnul componentei |1⟩."),
    ("CX", "CNOT", ROLE_CONTROLLED, "Inverseaza qubitul tinta daca qubitul de control este |1⟩."),
    ("CCX", "Toffoli", ROLE_CONTROLLED, "Inverseaza qubitul tinta daca ambii qubiti de control sunt |1⟩."),
    ("M", "Masurare", ROLE_MEASURE, "Masoara qubitul si obtine rezultatul 0 sau 1."),
]

GROUP_TITLES = {
    ROLE_SINGLE: "Porti pe un qubit",
    ROLE_CONTROLLED: "Porti controlate",
    ROLE_MEASURE: "Masurare",
}

ROLE_COLOR_NAMES = {
    ROLE_SINGLE: "gate_single",
    ROLE_CONTROLLED: "gate_controlled",
    ROLE_MEASURE: "gate_measure",
}


class GateButton(QAbstractButton):
    statusMessage = Signal(str)

    def __init__(self, symbol, name, role, description, parent=None):
        super().__init__(parent)
        self._name = name
        self._role = role
        self._description = description
        self._dragStartPos = QPoint()

        self.setText(symbol)
        self.setToolTip(f"{name}: {description}")
    

    def _labelFont(self, pointSize):
        font = QFont(self.font())
        font.setPointSize(pointSize)
        font.setBold(True)
        return font

    def _gateSize(self, pointSize, padding):
        metrics = QFontMetrics(self._labelFont(pointSize))
        side = max(metrics.height(), metrics.horizontalAdvance("CX")) + padding
        if self._role == ROLE_CONTROLLED:
            return QSize(side * style.GATE_CONTROLLED_WIDTH_FACTOR, side)
        return QSize(side, side)

    def sizeHint(self):
        return self._gateSize(style.fontPointSize(style.FONT_SIZE_GATE), 2 * style.GATE_PADDING)

    def minimumSizeHint(self):
        return self._gateSize(style.FONT_SIZE_MIN, style.GATE_PADDING)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        color = QColor(style.color(ROLE_COLOR_NAMES[self._role]))
        if self.isDown():
            color = color.darker(style.GATE_PRESSED_DARKER)
        elif self.underMouse():
            color = color.lighter(style.GATE_HOVER_LIGHTER)

        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        radius = rect.height() / 2 if self._role == ROLE_MEASURE else style.CORNER_RADIUS

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawRoundedRect(rect, radius, radius)

        painter.setPen(QColor(style.color("gate_text")))
        painter.setFont(self._labelFont(style.fontPointSize(style.FONT_SIZE_GATE)))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.text())

    def enterEvent(self, event):
        self.statusMessage.emit(f"{self._name}: {self._description} Trage poarta pe circuit.")
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.statusMessage.emit("")
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragStartPos = event.position().toPoint()
        # implementarea din clasa de baza emite pressed() si clicked()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        distance = (event.position().toPoint() - self._dragStartPos).manhattanLength()
        if event.buttons() & Qt.MouseButton.LeftButton and distance >= QApplication.startDragDistance():
            self._startDrag()
        else:
            super().mouseMoveEvent(event)

    def _startDrag(self):
        mimeData = QMimeData()
        mimeData.setData(GATE_MIME_TYPE, self.text().encode("utf-8"))

        drag = QDrag(self)
        drag.setMimeData(mimeData)
        drag.setPixmap(self.grab())
        drag.setHotSpot(QPoint(self.width() // 2, self.height() // 2))
        drag.exec(Qt.DropAction.CopyAction)
        # dupa drag butonul nu mai primeste mouseReleaseEvent
        self.setDown(False)


class GatePalette(QWidget):
    gateSelected = Signal(str)
    statusMessage = Signal(str)

    SINGLE_COLUMNS = 2

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(style.SPACING_M)

        for role in (ROLE_SINGLE, ROLE_CONTROLLED, ROLE_MEASURE):
            gates = [gate for gate in PALETTE_GATES if gate[2] == role]
            layout.addLayout(self._createGroup(GROUP_TITLES[role], gates))
        layout.addStretch()

    def _createGroup(self, title, gates):
        groupLayout = QVBoxLayout()
        groupLayout.setSpacing(style.SPACING_S)
        groupLayout.addWidget(QLabel(title, self))

        grid = QGridLayout()
        grid.setSpacing(style.SPACING_S)
        grid.setColumnStretch(self.SINGLE_COLUMNS, 1)
        for index, (symbol, name, role, description) in enumerate(gates):
            button = GateButton(symbol, name, role, description, self)
            button.clicked.connect(lambda checked=False, s=symbol: self.gateSelected.emit(s))
            button.statusMessage.connect(self.statusMessage)
            if role == ROLE_SINGLE:
                row, col = divmod(index, self.SINGLE_COLUMNS)
                grid.addWidget(button, row, col, Qt.AlignmentFlag.AlignLeft)
            else:
                grid.addWidget(button, index, 0, 1, self.SINGLE_COLUMNS, Qt.AlignmentFlag.AlignLeft)
        groupLayout.addLayout(grid)
        return groupLayout