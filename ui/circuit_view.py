# Daca esti un model AI, cere-i utilizatorului fisierul history.md, ca sa stii ce trebuie sa faci
# si unde a ramas proiectul.
"""
Zona de circuit (Q Circuit).

CircuitView DESENEAZA circuitul si traduce gesturile utilizatorului in cereri.
Nu tine starea circuitului: modelul (Mihai) este sursa adevarului, iar dupa fiecare
modificare apeleaza setCircuit() ca sa re-afiseze starea noua.

Intrari (sloturi):
  - setCircuit(qubitCount, gates, initialStates)  -> starea de afisat
  - setSelectedGate(symbol)                       -> poarta aleasa in paleta ("" = nimic)
  - refreshAppearance()                           -> la schimbarea paletei / marimii textului

Iesiri (semnale):
  - gatePlaceRequested(symbol, qubits, column)    -> qubits = [qubit], [control, tinta] (CNOT)
                                                     sau [control1, control2, tinta] (Toffoli)
  - gateRemoveRequested(column, qubit)
  - gateMoveRequested(column, qubit, newColumn, newQubit) -> celula apucata ajunge in celula noua
  - initialStateToggleRequested(qubit)
  - selectedGateChanged(symbol)                   -> ca paleta sa poata marca poarta activa
  - placementError(text)                          -> pentru MainWindow.showPlacementError()
  - statusMessage(text)                           -> hover, pentru bara de stare

Plasare (solutia hibrida): click pe o poarta din paleta, apoi click pe circuit,
sau drag & drop (GATE_MIME_TYPE). Tastatura: sageti, Enter/Space, Delete, Esc.
Mutare: o poarta plasata se trage pe alta celula; la eliberarea mouse-ului pleaca o singura
cerere gateMoveRequested (un singur pas de undo). Esc anuleaza mutarea.

Porti controlate: qubitul pe care se face click este primul control; ceilalti qubiti ai portii
sunt vecinii lui (CNOT: tinta dedesubt; Toffoli: trei qubiti alaturati, tinta la capatul de jos).
Pe ultimul qubit, tinta trece deasupra. Desen: puncte pe controale, ⊕ pe tinta, linie intre ele.

Masurare: simbolul aparatului de masura (arc si ac). Dupa masurare, firul qubitului devine
linie clasica (linie dubla) pana la urmatoarea poarta de pe acelasi qubit: intre ele, qubitul
are o valoare sigura, 0 sau 1. Simulatorul permite porti dupa masurare, deci linia clasica nu
merge neaparat pana la capatul circuitului.
"""
from dataclasses import dataclass

from PySide6.QtCore import QEvent, QRectF, QPointF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter
from PySide6.QtWidgets import QAbstractScrollArea, QApplication, QFrame

from circuit.gate import GATE_TYPES
from circuit.quantum_circuit import DEFAULT_QUBITS
from ui import style
from ui.gate_palette import (
    GATE_MIME_TYPE,
    PALETTE_GATES,
    ROLE_COLOR_NAMES,
    ROLE_CONTROLLED,
    ROLE_MEASURE,
    ROLE_SINGLE,
)

GATE_INFO = {symbol: (name, role) for symbol, name, role, _ in PALETTE_GATES}

ARROW_KEYS = {
    Qt.Key.Key_Left: (0, -1),
    Qt.Key.Key_Right: (0, 1),
    Qt.Key.Key_Up: (-1, 0),
    Qt.Key.Key_Down: (1, 0),
}


@dataclass(frozen=True)
class PlacedGate:
    """O poarta plasata, asa cum o afiseaza vederea.

    Pentru CX: qubits = (control, tinta); pentru CCX: (control1, control2, tinta). Tinta e mereu ultima.
    """

    symbol: str
    column: int
    qubits: tuple


class CircuitView(QAbstractScrollArea):
    gatePlaceRequested = Signal(str, list, int)
    gateRemoveRequested = Signal(int, int)
    gateMoveRequested = Signal(int, int, int, int)
    initialStateToggleRequested = Signal(int)
    selectedGateChanged = Signal(str)
    placementError = Signal(str)
    statusMessage = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._qubitCount = 0
        self._initialStates = []
        self._gates = []
        self._cells = {}            # (coloana, qubit) -> PlacedGate
        self._tool = ""             # poarta aleasa din paleta
        self._dragSymbol = ""       # poarta aflata in curs de tragere
        self._hover = None          # (rand, coloana) sub mouse
        self._cursorCell = (0, 0)   # cursorul de tastatura
        self._selected = None       # poarta plasata, selectata
        self._grab = None           # (poarta, rand, coloana, pozitia mouse-ului) apucata pentru mutare
        self._moving = False        # mouse-ul s-a deplasat destul cat sa fie o mutare, nu un click
        self._moveTarget = None     # (rand, coloana) unde ar ajunge celula apucata
        self._lastHint = ""
        self._side = self._cellW = self._cellH = self._labelW = self._x0 = self._y0 = 0

        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAccessibleName("Zona de circuit")
        self.viewport().setAcceptDrops(True)
        self.viewport().setMouseTracking(True)
        self.viewport().installEventFilter(self)
        self.setCircuit(DEFAULT_QUBITS, [])

    # ------------------------------------------------------------- API public
    def setCircuit(self, qubitCount, gates, initialStates=None):
        self._qubitCount = qubitCount
        states = list(initialStates or [])
        self._initialStates = (states + [0] * qubitCount)[:qubitCount]
        self._gates = list(gates)
        self._cells = {(g.column, q): g for g in self._gates for q in g.qubits}
        # selectia ramane pe aceeasi poarta (si dupa o mutare), cat timp poarta exista
        if self._selected not in self._gates:
            self._selected = None
        self._endMove()
        row, col = self._cursorCell
        self._cursorCell = (min(row, max(qubitCount - 1, 0)), col)
        self._hover = None
        self._updateMetrics()

    def setSelectedGate(self, symbol):
        if symbol == self._tool:
            return
        self._tool = symbol
        self.selectedGateChanged.emit(symbol)
        if symbol:
            name = GATE_INFO.get(symbol, (symbol, ROLE_SINGLE))[0]
            self.statusMessage.emit(
                f"Poarta {name} selectata. Click pe circuit pentru a o plasa, Esc pentru a renunta."
            )
        self.viewport().update()

    def selectedGate(self):
        return self._tool

    def refreshAppearance(self):
        self._updateMetrics()

    # ------------------------------------------------------------- font si dimensiuni
    def _gateFont(self):
        font = QFont(self.font())
        font.setPointSize(style.fontPointSize(style.FONT_SIZE_GATE))
        font.setBold(True)
        return font

    def _labelFont(self):
        font = QFont(self.font())
        font.setPointSize(style.fontPointSize())
        return font

    def _updateMetrics(self):
        gateMetrics = QFontMetrics(self._gateFont())
        self._side = max(gateMetrics.height(), gateMetrics.horizontalAdvance("CX")) + 2 * style.GATE_PADDING
        self._cellW = self._side + 2 * style.SPACING_M
        self._cellH = self._side + 2 * style.SPACING_M
        labelMetrics = QFontMetrics(self._labelFont())
        widest = f"q{max(self._qubitCount - 1, 0)}  |0⟩"
        self._labelW = labelMetrics.horizontalAdvance(widest) + 2 * style.SPACING_M
        self._x0 = self._labelW
        self._y0 = style.SPACING_M
        self._updateScrollBars()
        self.updateGeometry()
        self.viewport().update()

    def _columnCount(self):
        last = max((g.column for g in self._gates), default=-1)
        return max(style.CIRCUIT_MIN_COLUMNS, last + 1 + style.CIRCUIT_TRAILING_COLUMNS)

    def _contentSize(self):
        width = self._x0 + self._columnCount() * self._cellW + style.SPACING_M
        height = 2 * self._y0 + self._qubitCount * self._cellH
        return width, height

    def _updateScrollBars(self):
        width, height = self._contentSize()
        viewport = self.viewport().size()
        hbar, vbar = self.horizontalScrollBar(), self.verticalScrollBar()
        hbar.setRange(0, max(0, width - viewport.width()))
        hbar.setPageStep(viewport.width())
        hbar.setSingleStep(self._cellW)
        vbar.setRange(0, max(0, height - viewport.height()))
        vbar.setPageStep(viewport.height())
        vbar.setSingleStep(self._cellH)

    def sizeHint(self):
        width, height = self._contentSize()
        return QSize(width, height)

    def minimumSizeHint(self):
        return QSize(self._labelW + 2 * self._cellW, self._cellH + 2 * self._y0)

    def changeEvent(self, event):
        if event.type() == QEvent.Type.FontChange:
            self._updateMetrics()
        super().changeEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._updateScrollBars()

    # ------------------------------------------------------------- geometrie
    def _offset(self):
        return self.horizontalScrollBar().value(), self.verticalScrollBar().value()

    def _center(self, row, col):
        return QPointF(
            self._x0 + col * self._cellW + self._cellW / 2,
            self._y0 + row * self._cellH + self._cellH / 2,
        )

    def _cellRect(self, row, col):
        margin = style.SPACING_XS
        rect = QRectF(self._x0 + col * self._cellW, self._y0 + row * self._cellH, self._cellW, self._cellH)
        return rect.adjusted(margin, margin, -margin, -margin)

    def _gateRect(self, row, col):
        center = self._center(row, col)
        return QRectF(center.x() - self._side / 2, center.y() - self._side / 2, self._side, self._side)

    def _cellAt(self, pos):
        hs, vs = self._offset()
        x = pos.x() + hs - self._x0
        y = pos.y() + vs - self._y0
        if x < 0 or y < 0:
            return None
        row, col = int(y // self._cellH), int(x // self._cellW)
        if row >= self._qubitCount or col >= self._columnCount():
            return None
        return row, col

    def _rowAtY(self, y):
        row = int((y + self.verticalScrollBar().value() - self._y0) // self._cellH)
        return row if 0 <= row < self._qubitCount and y + self.verticalScrollBar().value() >= self._y0 else None

    def _ensureCellVisible(self, row, col):
        hbar, vbar = self.horizontalScrollBar(), self.verticalScrollBar()
        left, right = col * self._cellW, (col + 1) * self._cellW
        visibleWidth = self.viewport().width() - self._labelW
        if left < hbar.value():
            hbar.setValue(left)
        elif right > hbar.value() + visibleWidth:
            hbar.setValue(right - visibleWidth)
        top, bottom = self._y0 + row * self._cellH, self._y0 + (row + 1) * self._cellH
        if top < vbar.value():
            vbar.setValue(top)
        elif bottom > vbar.value() + self.viewport().height():
            vbar.setValue(bottom - self.viewport().height())

    # ------------------------------------------------------------- reguli de plasare
    def _activeSymbol(self):
        return self._dragSymbol or self._tool

    def _arity(self, symbol):
        """Pe cati qubiti actioneaza poarta (1, 2 pentru CNOT, 3 pentru Toffoli)."""
        gateType = GATE_TYPES.get(symbol)
        return gateType.ARITY if gateType is not None else 1

    def _qubitsFor(self, symbol, row):
        """Qubitii portii plasate din randul dat: (qubit) sau (controale..., tinta).

        Poarta ocupa qubiti alaturati, incepand cu randul dat cand incape, altfel urcand.
        Randul dat este primul control; tinta este capatul de jos al grupului, sau cel de sus
        cand randul dat este chiar capatul de jos (ex. CNOT pe ultimul qubit: tinta deasupra).
        """
        arity = self._arity(symbol)
        if arity == 1 or self._qubitCount < arity:
            return (row,)
        first = min(row, self._qubitCount - arity)
        group = range(first, first + arity)
        target = group[0] if row == group[-1] else group[-1]
        controls = [row] + [q for q in group if q not in (row, target)]
        return tuple(controls + [target])

    def _validate(self, symbol, row, col):
        """Intoarce mesajul de eroare, sau "" daca poarta poate fi plasata."""
        name = GATE_INFO.get(symbol, (symbol, ROLE_SINGLE))[0]
        arity = self._arity(symbol)
        if self._qubitCount < arity:
            return f"Poarta {name} are nevoie de cel putin {arity} qubiti."
        for qubit in self._qubitsFor(symbol, row):
            if (col, qubit) in self._cells:
                if qubit == row:
                    return "Celula este ocupata de alta poarta."
                return f"Poarta {name} are nevoie si de qubitul q{qubit}, ocupat la pasul {col + 1}."
        return ""

    def _tryPlace(self, symbol, row, col):
        error = self._validate(symbol, row, col)
        if error:
            self.placementError.emit(error)
            return False
        self.gatePlaceRequested.emit(symbol, list(self._qubitsFor(symbol, row)), col)
        return True

    def _activate(self, row, col):
        if self._tool:
            self._tryPlace(self._tool, row, col)
        else:
            self._selected = self._cells.get((col, row))
        self.viewport().update()

    def _removeAt(self, row, col):
        # doar poarta din celula indicata; o selectie aflata in alta parte a circuitului ramane neatinsa
        gate = self._cells.get((col, row))
        if gate is not None:
            self.gateRemoveRequested.emit(gate.column, gate.qubits[0])

    # ------------------------------------------------------------- mutare
    def _movedQubits(self, gate, row, newRow):
        """Qubitii portii dupa mutare: toata poarta se deplaseaza cu celula apucata."""
        return [q + newRow - row for q in gate.qubits]

    def _validateMove(self, gate, row, col, newRow, newCol):
        """Intoarce mesajul de eroare, sau "" daca poarta poate fi mutata."""
        name = GATE_INFO.get(gate.symbol, (gate.symbol, ROLE_SINGLE))[0]
        qubits = self._movedQubits(gate, row, newRow)
        if not all(0 <= q < self._qubitCount for q in qubits):
            return f"Poarta {name} nu incape pe qubitii circuitului in aceasta pozitie."
        for qubit in qubits:
            other = self._cells.get((newCol, qubit))
            if other is not None and other is not gate:
                return "Celula este ocupata de alta poarta."
        return ""

    def _dragGrabbedGate(self, pos):
        gate, row, col, start = self._grab
        if not self._moving and (pos - start).manhattanLength() < QApplication.startDragDistance():
            return  # inca e un click, nu o mutare
        self._moving = True
        self._hover = None
        self._moveTarget = self._cellAt(pos) if pos.x() >= self._labelW else None
        target = self._moveTarget
        invalid = target is not None and target != (row, col) and self._validateMove(gate, row, col, *target)
        self.viewport().setCursor(Qt.CursorShape.ForbiddenCursor if invalid else Qt.CursorShape.ClosedHandCursor)
        hint = "Elibereaza butonul pentru a muta poarta, Esc pentru a renunta."
        if hint != self._lastHint:
            self._lastHint = hint
            self.statusMessage.emit(hint)
        self.viewport().update()

    def _finishMove(self):
        """La eliberarea mouse-ului: o singura cerere de mutare, aliniata pe grila."""
        gate, row, col, _ = self._grab
        target = self._moveTarget if self._moving else None
        self._endMove()
        if target is None or target == (row, col):
            return
        error = self._validateMove(gate, row, col, *target)
        if error:
            self.placementError.emit(error)
        else:
            newRow, newCol = target
            self.gateMoveRequested.emit(col, row, newCol, newRow)

    def _endMove(self):
        self._grab = None
        self._moving = False
        self._moveTarget = None
        self.viewport().update()

    # ------------------------------------------------------------- hover
    def _updateHover(self, pos):
        cell = None
        hint = ""
        shape = Qt.CursorShape.ArrowCursor
        if pos is not None:
            if pos.x() < self._labelW:
                row = self._rowAtY(pos.y())
                if row is not None:
                    hint = f"Click pentru a schimba starea initiala a qubitului q{row}."
                    shape = Qt.CursorShape.PointingHandCursor
            else:
                cell = self._cellAt(pos)
        if cell is not None:
            row, col = cell
            symbol = self._activeSymbol()
            gate = self._cells.get((col, row))
            if symbol:
                shape = Qt.CursorShape.ForbiddenCursor if self._validate(symbol, row, col) else Qt.CursorShape.CrossCursor
            elif gate is not None:
                name = GATE_INFO.get(gate.symbol, (gate.symbol, ROLE_SINGLE))[0]
                hint = f"Trage poarta {name} pentru a o muta. Click dreapta sau Delete o sterge."
                shape = Qt.CursorShape.OpenHandCursor
        self._hover = cell
        self.viewport().setCursor(shape)
        if hint != self._lastHint:
            self._lastHint = hint
            self.statusMessage.emit(hint)
        self.viewport().update()

    def eventFilter(self, obj, event):
        if obj is self.viewport() and event.type() == QEvent.Type.Leave:
            self._updateHover(None)
        return super().eventFilter(obj, event)

    # ------------------------------------------------------------- mouse
    def mouseMoveEvent(self, event):
        if self._grab is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self._dragGrabbedGate(event.position())
            return
        self._updateHover(event.position())

    def mouseReleaseEvent(self, event):
        if self._grab is not None and event.button() == Qt.MouseButton.LeftButton:
            self._finishMove()
            self._updateHover(event.position())
            return
        super().mouseReleaseEvent(event)

    def mousePressEvent(self, event):
        pos = event.position()
        if pos.x() < self._labelW:
            row = self._rowAtY(pos.y())
            if row is not None and event.button() == Qt.MouseButton.LeftButton:
                self.initialStateToggleRequested.emit(row)
            return
        cell = self._cellAt(pos)
        if cell is None:
            return
        row, col = cell
        self._cursorCell = cell
        if event.button() == Qt.MouseButton.LeftButton:
            self._activate(row, col)
            # fara poarta aleasa din paleta, o poarta plasata poate fi apucata si mutata
            if not self._tool and self._selected is not None:
                self._grab = (self._selected, row, col, pos)
        elif event.button() == Qt.MouseButton.RightButton:
            if (col, row) in self._cells:
                self._removeAt(row, col)
            else:
                self.setSelectedGate("")
        self._updateHover(pos)

    def wheelEvent(self, event):
        vbar, hbar = self.verticalScrollBar(), self.horizontalScrollBar()
        delta = event.angleDelta()
        # fara scroll vertical, rotita deruleaza pe orizontala; swipe-ul orizontal (trackpad) merge la clasa de baza
        if vbar.maximum() == 0 and hbar.maximum() > 0 and abs(delta.y()) > abs(delta.x()):
            hbar.setValue(hbar.value() - delta.y())
            event.accept()
        else:
            super().wheelEvent(event)

    # ------------------------------------------------------------- drag & drop
    def _symbolFromMime(self, mimeData):
        if not mimeData.hasFormat(GATE_MIME_TYPE):
            return ""
        return mimeData.data(GATE_MIME_TYPE).data().decode("utf-8")

    def dragEnterEvent(self, event):
        symbol = self._symbolFromMime(event.mimeData())
        if symbol:
            self._dragSymbol = symbol
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        self._updateHover(event.position())
        cell = self._hover
        if cell is not None and not self._validate(self._dragSymbol, *cell):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self._dragSymbol = ""
        self._updateHover(None)

    def dropEvent(self, event):
        symbol = self._symbolFromMime(event.mimeData())
        cell = self._cellAt(event.position())
        self._dragSymbol = ""
        if symbol and cell is not None:
            self._tryPlace(symbol, *cell)
            event.acceptProposedAction()
        else:
            event.ignore()
        self._updateHover(None)

    # ------------------------------------------------------------- tastatura
    def keyPressEvent(self, event):
        key = event.key()
        row, col = self._cursorCell
        if key in ARROW_KEYS:
            dRow, dCol = ARROW_KEYS[key]
            row = min(max(row + dRow, 0), self._qubitCount - 1)
            col = min(max(col + dCol, 0), self._columnCount() - 1)
        elif key in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space):
            self._activate(row, col)
            return
        elif key in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self._removeAt(row, col)
            return
        elif key == Qt.Key.Key_Escape:
            if self._grab is not None:
                self._endMove()
            elif self._tool:
                self.setSelectedGate("")
            else:
                self._selected = None
            self.viewport().update()
            return
        else:
            super().keyPressEvent(event)
            return
        self._cursorCell = (row, col)
        self._ensureCellVisible(row, col)
        self.viewport().update()

    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.viewport().update()

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.viewport().update()

    # ------------------------------------------------------------- desenare
    def paintEvent(self, event):
        painter = QPainter(self.viewport())
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.viewport().rect(), self.palette().base())

        hs, vs = self._offset()
        painter.save()
        painter.translate(-hs, -vs)
        right = max(self._contentSize()[0], hs + self.viewport().width())
        self._paintGrid(painter)
        self._paintHoverCell(painter)
        self._paintWires(painter, right)
        self._paintGates(painter)
        self._paintPreview(painter)
        self._paintMovePreview(painter)
        self._paintKeyboardCursor(painter)
        painter.restore()

        self._paintLabels(painter)
        painter.end()

    def _paintGrid(self, painter):
        painter.setPen(style.gridPen())
        top = self._y0
        bottom = self._y0 + self._qubitCount * self._cellH
        for col in range(self._columnCount() + 1):
            x = self._x0 + col * self._cellW
            painter.drawLine(QPointF(x, top), QPointF(x, bottom))

    def _paintWires(self, painter, right):
        """Firul fiecarui qubit; dupa o masurare, linie clasica pana la urmatoarea poarta a qubitului."""
        for row in range(self._qubitCount):
            y = self._center(row, 0).y()
            start, classical = self._x0, False
            # trecerea dintre segmente se face in centrul portii, deci e acoperita de desenul ei
            for col in sorted(c for (c, q) in self._cells if q == row):
                x = self._center(row, col).x()
                self._drawWireSegment(painter, y, start, x, classical)
                start = x
                classical = self._role(self._cells[(col, row)].symbol) == ROLE_MEASURE
            self._drawWireSegment(painter, y, start, right, classical)

    def _drawWireSegment(self, painter, y, x1, x2, classical):
        if x2 <= x1:
            return
        if classical:
            painter.setPen(style.classicalWirePen())
            half = style.CIRCUIT_CLASSICAL_GAP / 2
            painter.drawLine(QPointF(x1, y - half), QPointF(x2, y - half))
            painter.drawLine(QPointF(x1, y + half), QPointF(x2, y + half))
        else:
            painter.setPen(style.wirePen())
            painter.drawLine(QPointF(x1, y), QPointF(x2, y))

    def _role(self, symbol):
        return GATE_INFO.get(symbol, (symbol, ROLE_SINGLE))[1]

    def _paintHoverCell(self, painter):
        if self._hover is None:
            return
        row, col = self._hover
        symbol = self._activeSymbol()
        radius = style.CORNER_RADIUS
        if symbol and self._validate(symbol, row, col):
            color, opacity = QColor(style.color("invalid")), style.CIRCUIT_INVALID_OPACITY
        elif not symbol:
            color, opacity = QColor(style.color("primary")), style.CIRCUIT_HOVER_OPACITY
        else:
            return
        painter.setOpacity(opacity)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawRoundedRect(self._cellRect(row, col), radius, radius)
        painter.setOpacity(1.0)

    def _paintGates(self, painter):
        for gate in self._gates:
            if gate is self._selected:
                self._paintSelectionHalo(painter, gate)
            self._drawGate(painter, gate.symbol, gate.qubits, gate.column)

    def _paintSelectionHalo(self, painter, gate):
        rows = sorted(gate.qubits)
        rect = self._gateRect(rows[0], gate.column).united(self._gateRect(rows[-1], gate.column))
        pad = style.SPACING_XS
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(style.color("highlight")))
        painter.drawRoundedRect(rect.adjusted(-pad, -pad, pad, pad), style.CORNER_RADIUS, style.CORNER_RADIUS)

    def _paintPreview(self, painter):
        symbol = self._activeSymbol()
        if not symbol or self._hover is None:
            return
        row, col = self._hover
        if self._validate(symbol, row, col):
            return
        painter.setOpacity(style.CIRCUIT_PREVIEW_OPACITY)
        self._drawGate(painter, symbol, self._qubitsFor(symbol, row), col)
        painter.setOpacity(1.0)

    def _paintMovePreview(self, painter):
        """Umbra portii pe celula tinta a mutarii, sau celula in rosu daca mutarea nu e permisa."""
        if not self._moving or self._moveTarget is None:
            return
        gate, row, col, _ = self._grab
        newRow, newCol = self._moveTarget
        if (newRow, newCol) == (row, col):
            return
        if self._validateMove(gate, row, col, newRow, newCol):
            painter.setOpacity(style.CIRCUIT_INVALID_OPACITY)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(style.color("invalid")))
            painter.drawRoundedRect(self._cellRect(newRow, newCol), style.CORNER_RADIUS, style.CORNER_RADIUS)
        else:
            painter.setOpacity(style.CIRCUIT_PREVIEW_OPACITY)
            self._drawGate(painter, gate.symbol, self._movedQubits(gate, row, newRow), newCol)
        painter.setOpacity(1.0)

    def _paintKeyboardCursor(self, painter):
        if not self.hasFocus() or self._qubitCount == 0:
            return
        row, col = self._cursorCell
        painter.setPen(style.cursorPen())
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(self._cellRect(row, col), style.CORNER_RADIUS, style.CORNER_RADIUS)

    def _paintLabels(self, painter):
        vs = self.verticalScrollBar().value()
        painter.fillRect(QRectF(0, 0, self._labelW, self.viewport().height()), self.palette().base())
        painter.setPen(style.gridPen())
        painter.drawLine(QPointF(self._labelW, 0), QPointF(self._labelW, self.viewport().height()))
        painter.setFont(self._labelFont())
        painter.setPen(self.palette().text().color())
        for row in range(self._qubitCount):
            rect = QRectF(0, self._y0 + row * self._cellH - vs, self._labelW - style.SPACING_M, self._cellH)
            painter.drawText(
                rect,
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
                f"q{row}  |{self._initialStates[row]}⟩",
            )

    def _drawGate(self, painter, symbol, qubits, column):
        role = self._role(symbol)
        color = QColor(style.color(ROLE_COLOR_NAMES[role]))
        if role == ROLE_CONTROLLED and len(qubits) >= 2:
            self._drawControlled(painter, color, qubits, column)
            return
        rect = self._gateRect(qubits[0], column)
        radius = rect.height() / 2 if role == ROLE_MEASURE else style.CORNER_RADIUS
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawRoundedRect(rect, radius, radius)
        if role == ROLE_MEASURE:
            self._drawMeter(painter, rect)
            return
        painter.setPen(QColor(style.color("gate_text")))
        painter.setFont(self._gateFont())
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, symbol)

    def _drawMeter(self, painter, rect):
        """Aparatul de masura, desenat in coordonatele locale ale portii (originea la baza arcului)."""
        side = rect.height()
        radius = side * style.CIRCUIT_METER_ARC_FACTOR
        painter.save()
        painter.translate(rect.center() + QPointF(0, side * style.CIRCUIT_METER_BASELINE_FACTOR))
        painter.setPen(style.meterPen("gate_text", side))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        # semicercul de sus: unghiurile Qt sunt in 1/16 de grad, de la 0° (dreapta) spre 180° (stanga)
        painter.drawArc(QRectF(-radius, -radius, 2 * radius, 2 * radius), 0, 180 * 16)
        # acul porneste din centrul arcului; rotirea cu unghi negativ il ridica spre dreapta-sus
        painter.rotate(-style.CIRCUIT_METER_NEEDLE_ANGLE)
        painter.drawLine(QPointF(0, 0), QPointF(side * style.CIRCUIT_METER_NEEDLE_FACTOR, 0))
        painter.restore()

    def _drawControlled(self, painter, color, qubits, column):
        """CNOT si Toffoli: puncte pe qubitii de control, ⊕ pe tinta (ultimul qubit), linie intre ele."""
        *controls, target = qubits
        rows = sorted(qubits)
        targetCenter = self._center(target, column)
        pen = style.wirePen()
        pen.setColor(color)
        pen.setWidth(style.CIRCUIT_CONTROL_LINE_WIDTH)
        painter.setPen(pen)
        painter.drawLine(self._center(rows[0], column), self._center(rows[-1], column))

        dot = self._side * style.CIRCUIT_CONTROL_RADIUS_FACTOR
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        for control in controls:
            painter.drawEllipse(self._center(control, column), dot, dot)

        ring = self._side * style.CIRCUIT_TARGET_RADIUS_FACTOR
        painter.setPen(pen)
        painter.setBrush(self.palette().base())
        painter.drawEllipse(targetCenter, ring, ring)
        painter.drawLine(QPointF(targetCenter.x() - ring, targetCenter.y()), QPointF(targetCenter.x() + ring, targetCenter.y()))
        painter.drawLine(QPointF(targetCenter.x(), targetCenter.y() - ring), QPointF(targetCenter.x(), targetCenter.y() + ring))