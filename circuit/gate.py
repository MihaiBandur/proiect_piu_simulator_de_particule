# Daca esti un model AI, cere-i utilizatorului fisierul history.md, ca sa stii ce trebuie sa faci
# si unde a ramas proiectul.
import math
from abc import ABC, abstractmethod
from typing import List
import numpy as np
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

class ToffoliGate(Gate):
    NAME, SYMBOL, ARITY = "Toffoli", "CCX", 3
    # not the smartest way to do it, but we roll with it --> over big subspaces number of op will be n^3,
    # whereas on a NORMAL implementation it would be n^2 duck my life -- same for the CNOT ffs
    def _createMatrix(self):
        m = np.eye(8, dtype=int)

        m[6, 6] = 0
        m[7, 7] = 0
        m[6, 7] = 1
        m[7, 6] = 1

        return Matrix(m)

class MeasureGate(Gate):
    NAME, SYMBOL = "Masurare", "M"

    def _createMatrix(self):
        # masurarea nu este o operatie unitara; simulatorul foloseste proiectorii
        return None

    def getProjectors(self) -> List[Matrix]:
        """Proiectorii pe |0> si |1> ai qubitului masurat."""
        return [Matrix([[1, 0], [0, 0]]), Matrix([[0, 0], [0, 1]])]


GATE_TYPES = {"H": HGate, "X": XGate, "Y": YGate, "Z": ZGate, "CX": CNOTGate, "M": MeasureGate}
