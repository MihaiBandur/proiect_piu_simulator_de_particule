from dependencies import *
from circuit.quantum_circuit import QuantumCircuit


class CircuitWidget(QWidget):
    message = pyqtSignal(str)

    LEFT, TOP = 90, 30
    COL_W, ROW_H = 64, 60
    BOX = 38

    def __init__(self, circuit: QuantumCircuit):
        super().__init__()
        self.circuit = circuit
        self.selectedGate = "H"
        self.refresh()

    def setSelectedGate(self, symbol: str):
        self.selectedGate = symbol

    def refresh(self):
        w = self.LEFT + self.circuit.numColumns * self.COL_W + 20
        h = self.TOP + len(self.circuit.qubits) * self.ROW_H + 10
        self.setMinimumSize(w, h)
        self.update()

    # ---- geometrie -------------------------------------------------
    def _cx(self, col):  # centrul coloanei
        return self.LEFT + col * self.COL_W + self.COL_W / 2

    def _cy(self, row):  # centrul rândului
        return self.TOP + row * self.ROW_H + self.ROW_H / 2

    def _cell(self, pos):
        col = int((pos.x() - self.LEFT) // self.COL_W)
        row = int((pos.y() - self.TOP) // self.ROW_H)
        return row, col

    # ---- acțiuni ---------------------------------------------------
    def addGate(self, qubit: int, column: int):
        cls = GATE_TYPES[self.selectedGate]
        n = len(self.circuit.qubits)
        if cls.ARITY == 2:
            if n < 2:
                self.message.emit("CNOT necesită cel puțin 2 qubiți.")
                return
            target = qubit + 1 if qubit + 1 < n else qubit - 1
            qubits = [qubit, target]
        else:
            qubits = [qubit]
        if self.circuit.addGate(cls(qubits, column)):
            self.message.emit(f"Adăugat {cls.NAME} pe qubit {qubits}, coloana {column}.")
        else:
            self.message.emit("Celulă ocupată.")
        self.update()

    def removeGate(self, qubit: int, column: int):
        gate = self.circuit.gateAt(qubit, column)
        if gate:
            self.circuit.removeGate(gate)
            self.update()

    # ---- evenimente ------------------------------------------------
    def mousePressEvent(self, event):
        pos = event.position()
        row, col = self._cell(pos)
        if not (0 <= row < len(self.circuit.qubits)):
            return
        if pos.x() < self.LEFT:  # click pe eticheta qubit-ului
            q = self.circuit.qubits[row]
            q.setState(1 - q.getState())
            self.update()
            return
        if not (0 <= col < self.circuit.numColumns):
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self.addGate(row, col)
        elif event.button() == Qt.MouseButton.RightButton:
            self.removeGate(row, col)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        text_color = self.palette().text().color()
        wire_pen = QPen(QColor("#888888"), 1.5)
        n = len(self.circuit.qubits)

        # fire + etichete qubiți
        font = QFont(self.font())
        font.setPointSize(11)
        p.setFont(font)
        for i, q in enumerate(self.circuit.qubits):
            y = self._cy(i)
            p.setPen(wire_pen)
            p.drawLine(QPointF(self.LEFT, y), QPointF(self.LEFT + self.circuit.numColumns * self.COL_W, y))
            p.setPen(text_color)
            p.drawText(QRectF(5, y - 15, self.LEFT - 15, 30),
                       Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
                       f"q{i}  |{q.getState()}⟩")

        # porți
        font.setBold(True)
        p.setFont(font)
        for g in self.circuit.getGates():
            x = self._cx(g.column)
            if len(g.qubits) == 1:
                self._drawBox(p, x, self._cy(g.qubits[0]), g.symbol)
            else:
                c, t = g.qubits
                p.setPen(QPen(QColor("#2a6fdb"), 2))
                p.drawLine(QPointF(x, self._cy(c)), QPointF(x, self._cy(t)))
                p.setBrush(QBrush(QColor("#2a6fdb")))
                p.drawEllipse(QPointF(x, self._cy(c)), 5, 5)  # control
                p.setBrush(QBrush(self.palette().base().color()))
                p.drawEllipse(QPointF(x, self._cy(t)), 14, 14)  # țintă ⊕
                p.drawLine(QPointF(x - 14, self._cy(t)), QPointF(x + 14, self._cy(t)))
                p.drawLine(QPointF(x, self._cy(t) - 14), QPointF(x, self._cy(t) + 14))
        p.end()

    def _drawBox(self, p: QPainter, x, y, symbol):
        rect = QRectF(x - self.BOX / 2, y - self.BOX / 2, self.BOX, self.BOX)
        p.setPen(QPen(QColor("#1d4f9c"), 2))
        p.setBrush(QBrush(QColor("#4a90e2")))
        p.drawRoundedRect(rect, 6, 6)
        p.setPen(QColor("white"))
        p.drawText(rect, Qt.AlignmentFlag.AlignCenter, symbol)
