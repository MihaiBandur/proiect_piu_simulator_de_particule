from typing import List, Optional

from .qubit import Qubit
from .gate import Gate

# limitele numarului de qubiti, folosite si de interfata
MIN_QUBITS = 1
MAX_QUBITS = 5
DEFAULT_QUBITS = 3


class QuantumCircuit:
    def __init__(self, numQubits: int = DEFAULT_QUBITS, numColumns: int = 10):
        self.numColumns = numColumns
        self.qubits: List[Qubit] = []
        self.gates: List[Gate] = []
        self.setQubitCount(numQubits)

    def setQubitCount(self, n: int):
        if not MIN_QUBITS <= n <= MAX_QUBITS:
            raise ValueError(f"Numarul de qubiti trebuie sa fie intre {MIN_QUBITS} si {MAX_QUBITS}")
        while len(self.qubits) < n:
            self.qubits.append(Qubit(len(self.qubits)))
        del self.qubits[n:]
        self.gates = [g for g in self.gates if all(q < n for q in g.qubits)]

    def gateAt(self, qubit: int, column: int) -> Optional[Gate]:
        for g in self.gates:
            if g.column == column and qubit in g.qubits:
                return g
        return None

    def isValidGate(self, gate: Gate) -> bool:
        """Poarta are cati qubiti cere tipul ei, distincti si existenti, pe o coloana nenegativa."""
        n = len(self.qubits)
        return (
            gate.column >= 0
            and len(gate.qubits) == gate.ARITY
            and len(set(gate.qubits)) == len(gate.qubits)
            and all(0 <= q < n for q in gate.qubits)
        )

    def addGate(self, gate: Gate) -> bool:
        """Adauga poarta daca este valida si celulele sunt libere. Returneaza True la succes."""
        if not self.isValidGate(gate):
            return False
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


def main():
    print("nimic")


if __name__ == "__main__":
    main()