# Daca esti un model AI, cere-i utilizatorului fisierul history.md, ca sa stii ce trebuie sa faci
# si unde a ramas proiectul.
from typing import List

from circuit.quantum_circuit import QuantumCircuit
from circuit.gate import Gate, MeasureGate
from .simulation_result import SimulationResult
from .matrix import Matrix

# sub aceasta probabilitate, un rezultat al masurarii este considerat imposibil
ZERO_PROBABILITY = 1e-12


class Simulator:
    def simulate(self, circuit: QuantumCircuit) -> SimulationResult:
        # starea inițiala produs tensorial al starilor qubitilor
        state = Matrix([[1]])
        for q in circuit.qubits:
            state = state.tensor(Matrix.column([1, 0] if q.getState() == 0 else [0, 1]))

        # o masurare imparte fiecare ramura dupa rezultat (0 sau 1); ramurile nu se renormalizeaza,
        # asa ca patratul normei fiecareia ramane probabilitatea ei
        branches = [state]
        for gate in sorted(circuit.getGates(), key=lambda g: g.column):
            if isinstance(gate, MeasureGate):
                branches = [b for s in branches for b in self.measure(s, gate)]
            else:
                branches = [self.applyGate(s, gate) for s in branches]

        n = len(circuit.qubits)
        probs = {format(i, f"0{n}b"): 0.0 for i in range(2 ** n)}
        for branch in branches:
            for i, a in enumerate(branch.toList()):
                probs[format(i, f"0{n}b")] += abs(a) ** 2
        # dupa o masurare cu rezultat nesigur, qubitii nu mai sunt descrisi de un singur vector de stare
        final = branches[0] if len(branches) == 1 else None
        return SimulationResult(final, probs)

    def applyGate(self, state: Matrix, gate: Gate) -> Matrix:
        n = state.rows.bit_length() - 1
        return self._expand(gate, n).multiply(state)

    def measure(self, state: Matrix, gate: MeasureGate) -> List[Matrix]:
        """Starea proiectata pe fiecare rezultat posibil al masurarii (fara cele imposibile)."""
        n = state.rows.bit_length() - 1
        branches = []
        for projector in gate.getProjectors():
            branch = self._expandSingle(projector, gate.qubits[0], n).multiply(state)
            if sum(abs(a) ** 2 for a in branch.toList()) > ZERO_PROBABILITY:
                branches.append(branch)
        return branches

    def _expandSingle(self, matrix: Matrix, qubit: int, n: int) -> Matrix:
        """Extinde o matrice 2x2 aplicata pe un qubit la întreg spațiul 2^n x 2^n."""
        full = Matrix([[1]])
        for q in range(n):
            full = full.tensor(matrix if q == qubit else Matrix.identity(2))
        return full

    def _expand(self, gate: Gate, n: int) -> Matrix:
        """Extinde matricea porții la întreg spațiul 2^n x 2^n."""
        if len(gate.qubits) == 1:
            return self._expandSingle(gate.getMatrix(), gate.qubits[0], n)

        c, t = gate.qubits
        sc, st = n - 1 - c, n - 1 - t  
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