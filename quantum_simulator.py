"""
Quantum Circuit Simulator - PyQt6
Implementare a diagramei UML (pachete: GUI, Circuit, Simulation, Statistics).

Rulare:  pip install PyQt6
         python quantum_simulator.py

Utilizare:
  - Alege o poartă din panoul din stânga.
  - Click stânga pe o celulă a circuitului = adaugă poarta.
      (pentru CNOT: control = qubit-ul apăsat, țintă = qubit-ul următor)
  - Click dreapta pe o poartă = o șterge.
  - Click pe eticheta unui qubit (q0, q1, ...) = comută starea inițială |0> / |1>.
  - "Run" simulează circuitul și afișează probabilitățile.
Convenție: qubit-ul q0 este cel mai semnificativ (primul din șirul de biți, ex. "01").
"""
import math
import sys
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from PyQt6.QtCore import QPointF, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


# =====================================================================
# Pachetul "Simulation" - Matrix
# =====================================================================
class Matrix:
    """Matrice complexă simplă (liste de liste)."""

    def __init__(self, values):
        self.values: List[List[complex]] = [[complex(v) for v in row] for row in values]

    @property
    def rows(self) -> int:
        return len(self.values)

    @property
    def cols(self) -> int:
        return len(self.values[0]) if self.values else 0

    @staticmethod
    def identity(n: int) -> "Matrix":
        return Matrix([[1 if i == j else 0 for j in range(n)] for i in range(n)])

    @staticmethod
    def column(vector) -> "Matrix":
        return Matrix([[v] for v in vector])

    def multiply(self, other: "Matrix") -> "Matrix":
        if self.cols != other.rows:
            raise ValueError("Dimensiuni incompatibile pentru înmulțire")
        other_cols = list(zip(*other.values))
        return Matrix(
            [[sum(a * b for a, b in zip(row, col)) for col in other_cols] for row in self.values]
        )

    def tensor(self, other: "Matrix") -> "Matrix":
        return Matrix(
            [[a * b for a in ra for b in rb] for ra in self.values for rb in other.values]
        )

    def toList(self) -> List[complex]:
        """Pentru vectori coloană: returnează lista de amplitudini."""
        return [row[0] for row in self.values]


# =====================================================================
# Pachetul "Circuit" - Qubit, Gate (+ subclase), QuantumCircuit
# =====================================================================
class Qubit:
    def __init__(self, index: int, state: int = 0):
        self.index = index
        self.state = state

    def setState(self, state: int):
        if state not in (0, 1):
            raise ValueError("Starea unui qubit trebuie să fie 0 sau 1")
        self.state = state

    def getState(self) -> int:
        return self.state


class Gate(ABC):
    NAME = ""
    SYMBOL = ""
    ARITY = 1  # câți qubiți folosește

    def __init__(self, qubits: List[int], column: int):
        self.name: str = self.NAME
        self.symbol: str = self.SYMBOL
        self.qubits: List[int] = list(qubits)  # pentru CNOT: [control, țintă]
        self.column: int = column
        self.matrix: Matrix = self._createMatrix()

    @abstractmethod
    def _createMatrix(self) -> Matrix:
        ...

    def getMatrix(self) -> Matrix:
        return self.matrix


class HGate(Gate):
    NAME, SYMBOL = "Hadamard", "H"

    def _createMatrix(self):
        s = 1 / math.sqrt(2)
        return Matrix([[s, s], [s, -s]])


class XGate(Gate):
    NAME, SYMBOL = "Pauli-X", "X"

    def _createMatrix(self):
        return Matrix([[0, 1], [1, 0]])


class YGate(Gate):
    NAME, SYMBOL = "Pauli-Y", "Y"

    def _createMatrix(self):
        return Matrix([[0, -1j], [1j, 0]])


class ZGate(Gate):
    NAME, SYMBOL = "Pauli-Z", "Z"

    def _createMatrix(self):
        return Matrix([[1, 0], [0, -1]])


class CNOTGate(Gate):
    NAME, SYMBOL, ARITY = "CNOT", "CX", 2

    def _createMatrix(self):
        # ordinea bazei: |control, țintă>
        return Matrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]])


GATE_TYPES = {"H": HGate, "X": XGate, "Y": YGate, "Z": ZGate, "CX": CNOTGate}


class QuantumCircuit:
    def __init__(self, numQubits: int = 3, numColumns: int = 10):
        self.numColumns = numColumns
        self.qubits: List[Qubit] = [Qubit(i) for i in range(numQubits)]
        self.gates: List[Gate] = []

    def setQubitCount(self, n: int):
        while len(self.qubits) < n:
            self.qubits.append(Qubit(len(self.qubits)))
        del self.qubits[n:]
        self.gates = [g for g in self.gates if all(q < n for q in g.qubits)]

    def gateAt(self, qubit: int, column: int) -> Optional[Gate]:
        for g in self.gates:
            if g.column == column and qubit in g.qubits:
                return g
        return None

    def addGate(self, gate: Gate) -> bool:
        """Adaugă poarta dacă celulele sunt libere. Returnează True la succes."""
        if any(self.gateAt(q, gate.column) for q in gate.qubits):
            return False
        self.gates.append(gate)
        return True

    def removeGate(self, gate: Gate):
        if gate in self.gates:
            self.gates.remove(gate)

    def getGates(self) -> List[Gate]:
        return list(self.gates)

    def clear(self):
        self.gates.clear()


# =====================================================================
# Pachetul "Simulation" - SimulationResult, Simulator
# =====================================================================
class SimulationResult:
    def __init__(self, state: Matrix, probabilities: Dict[str, float]):
        self.state = state
        self.probabilities = probabilities

    def getState(self) -> Matrix:
        return self.state

    def getProbabilities(self) -> Dict[str, float]:
        return self.probabilities


class Simulator:
    def simulate(self, circuit: QuantumCircuit) -> SimulationResult:
        # starea inițială: produs tensorial al stărilor qubiților
        state = Matrix([[1]])
        for q in circuit.qubits:
            state = state.tensor(Matrix.column([1, 0] if q.getState() == 0 else [0, 1]))

        for gate in sorted(circuit.getGates(), key=lambda g: g.column):
            state = self.applyGate(state, gate)

        n = len(circuit.qubits)
        amps = state.toList()
        probs = {format(i, f"0{n}b"): abs(a) ** 2 for i, a in enumerate(amps)}
        return SimulationResult(state, probs)

    def applyGate(self, state: Matrix, gate: Gate) -> Matrix:
        n = state.rows.bit_length() - 1  # numărul de qubiți
        return self._expand(gate, n).multiply(state)

    def _expand(self, gate: Gate, n: int) -> Matrix:
        """Extinde matricea porții la întreg spațiul 2^n x 2^n."""
        if len(gate.qubits) == 1:
            full = Matrix([[1]])
            for q in range(n):
                full = full.tensor(gate.getMatrix() if q == gate.qubits[0] else Matrix.identity(2))
            return full

        # poartă pe 2 qubiți (control, țintă) - construcție generică pe biți
        c, t = gate.qubits
        sc, st = n - 1 - c, n - 1 - t  # poziția bitului în index
        dim = 2 ** n
        u = gate.getMatrix().values
        full = [[0j] * dim for _ in range(dim)]
        for col in range(dim):
            bc, bt = (col >> sc) & 1, (col >> st) & 1
            base = col & ~(1 << sc) & ~(1 << st)
            for oc in (0, 1):
                for ot in (0, 1):
                    row = base | (oc << sc) | (ot << st)
                    full[row][col] = u[oc * 2 + ot][bc * 2 + bt]
        return Matrix(full)


# =====================================================================
# Pachetul "Statistics"
# =====================================================================
class Statistics:
    def __init__(self):
        self.probabilities: Dict[str, float] = {}

    def calculate(self, result: SimulationResult):
        self.probabilities = dict(result.getProbabilities())

    def probability(self, state: str) -> float:
        return self.probabilities.get(state, 0.0)

    def mostProbableState(self) -> Optional[str]:
        if not self.probabilities:
            return None
        return max(self.probabilities, key=self.probabilities.get)


# =====================================================================
# Pachetul "GUI - PyQt6"
# =====================================================================
class GatesWidget(QGroupBox):
    gateSelected = pyqtSignal(str)

    def __init__(self):
        super().__init__("Porți")
        self.selected = "H"
        layout = QVBoxLayout(self)
        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        for symbol, cls in GATE_TYPES.items():
            btn = QPushButton(f"{cls.SYMBOL}  -  {cls.NAME}")
            btn.setCheckable(True)
            btn.setMinimumHeight(34)
            btn.clicked.connect(lambda _, s=symbol: self.selectGate(s))
            self.group.addButton(btn)
            layout.addWidget(btn)
            if symbol == self.selected:
                btn.setChecked(True)
        layout.addStretch()
        self.setFixedWidth(170)

    def selectGate(self, symbol: str):
        self.selected = symbol
        self.gateSelected.emit(symbol)


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


class BarChart(QWidget):
    """Mic grafic cu bare pentru probabilități."""

    def __init__(self):
        super().__init__()
        self.data: Dict[str, float] = {}
        self.setMinimumHeight(170)

    def setData(self, data: Dict[str, float]):
        self.data = data
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if not self.data:
            p.setPen(self.palette().text().color())
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Apasă Run pentru a simula circuitul")
            return
        margin_b, margin_t = 28, 18
        h = self.height() - margin_b - margin_t
        slot = self.width() / len(self.data)
        bar_w = min(slot * 0.7, 50)
        for i, (state, prob) in enumerate(self.data.items()):
            x = i * slot + (slot - bar_w) / 2
            bh = h * prob
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(QColor("#4a90e2")))
            p.drawRect(QRectF(x, margin_t + h - bh, bar_w, bh))
            p.setPen(self.palette().text().color())
            p.drawText(QRectF(x - 10, margin_t + h - bh - 16, bar_w + 20, 16),
                       Qt.AlignmentFlag.AlignCenter, f"{prob * 100:.1f}%")
            p.drawText(QRectF(x - 10, self.height() - margin_b + 4, bar_w + 20, 20),
                       Qt.AlignmentFlag.AlignCenter, f"|{state}⟩")
        p.end()


class StatisticsWidget(QGroupBox):
    def __init__(self):
        super().__init__("Statistici")
        layout = QVBoxLayout(self)
        self.summary = QLabel("—")
        self.chart = BarChart()
        layout.addWidget(self.summary)
        layout.addWidget(self.chart)
        self.statistics: Optional[Statistics] = None

    def showResults(self, statistics: Statistics):
        self.statistics = statistics
        self.updateStatistics()

    def updateStatistics(self):
        s = self.statistics
        if s is None or not s.probabilities:
            self.summary.setText("—")
            self.chart.setData({})
            return
        best = s.mostProbableState()
        self.summary.setText(
            f"Cea mai probabilă stare: |{best}⟩  (P = {s.probability(best) * 100:.2f}%)"
        )
        self.chart.setData(s.probabilities)

    def clear(self):
        self.statistics = None
        self.updateStatistics()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Quantum Circuit Simulator")

        # model + logică
        self.circuit = QuantumCircuit(numQubits=3)
        self.simulator = Simulator()
        self.statistics = Statistics()

        # widget-uri
        self.circuitWidget = CircuitWidget(self.circuit)
        self.gatesWidget = GatesWidget()
        self.statisticsWidget = StatisticsWidget()

        self.gatesWidget.gateSelected.connect(self.circuitWidget.setSelectedGate)
        self.circuitWidget.message.connect(lambda m: self.statusBar().showMessage(m, 4000))

        # bară de control
        self.qubitSpin = QSpinBox()
        self.qubitSpin.setRange(1, 5)
        self.qubitSpin.setValue(len(self.circuit.qubits))
        self.qubitSpin.valueChanged.connect(self.changeQubitCount)
        runBtn = QPushButton("▶ Run")
        runBtn.clicked.connect(self.runSimulation)
        clearBtn = QPushButton("Clear")
        clearBtn.clicked.connect(self.clearCircuit)

        top = QHBoxLayout()
        top.addWidget(QLabel("Qubiți:"))
        top.addWidget(self.qubitSpin)
        top.addStretch()
        top.addWidget(runBtn)
        top.addWidget(clearBtn)

        center = QVBoxLayout()
        center.addLayout(top)
        center.addWidget(self.circuitWidget, 1)

        row = QHBoxLayout()
        row.addWidget(self.gatesWidget)
        row.addLayout(center, 1)

        root = QVBoxLayout()
        root.addLayout(row, 1)
        root.addWidget(self.statisticsWidget)

        container = QWidget()
        container.setLayout(root)
        self.setCentralWidget(container)
        self.resize(1000, 650)
        self.statusBar().showMessage("Alege o poartă și apasă pe circuit.")

    def changeQubitCount(self, n: int):
        self.circuit.setQubitCount(n)
        self.circuitWidget.refresh()
        self.statisticsWidget.clear()

    def runSimulation(self):
        result = self.simulator.simulate(self.circuit)
        self.statistics.calculate(result)
        self.statisticsWidget.showResults(self.statistics)

    def clearCircuit(self):
        self.circuit.clear()
        for q in self.circuit.qubits:
            q.setState(0)
        self.circuitWidget.update()
        self.statisticsWidget.clear()


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
