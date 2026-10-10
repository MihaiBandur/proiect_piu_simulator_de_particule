from dependencies import *
from .qubit import Qubit
from .gate import Gate


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
        """Adauga poarta daca celulele sunt libere. Returneaza True la succes."""
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