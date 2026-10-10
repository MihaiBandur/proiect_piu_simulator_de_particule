from circuit.quantum_circuit import QuantumCircuit
from circuit.gate import Gate
from .simulation_result import SimulationResult
from .matrix import Matrix


class Simulator:
    def simulate(self, circuit: QuantumCircuit) -> SimulationResult:
        # starea inițiala produs tensorial al starilor qubitilor
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
        n = state.rows.bit_length() - 1  
        return self._expand(gate, n).multiply(state)

    def _expand(self, gate: Gate, n: int) -> Matrix:
        """Extinde matricea porții la întreg spațiul 2^n x 2^n."""
        if len(gate.qubits) == 1:
            full = Matrix([[1]])
            for q in range(n):
                full = full.tensor(gate.getMatrix() if q == gate.qubits[0] else Matrix.identity(2))
            return full

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