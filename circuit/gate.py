from dependencies import *
from simulation.matrix import Matrix

class Gate(ABC):
    NAME = ""
    SYMBOL = ""
    ARITY = 1  # no of qubits

    def __init__(self, qubits: List[int], column: int):
        self.name: str = self.NAME
        self.symbol: str = self.SYMBOL
        self.qubits: List[int] = list(qubits)  # pentru CNOT: [control, tinta]
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
        # ordinea bazei: |control, tinta>
        return Matrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]])


GATE_TYPES = {"H": HGate, "X": XGate, "Y": YGate, "Z": ZGate, "CX": CNOTGate}
