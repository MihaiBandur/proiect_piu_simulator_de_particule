# Daca esti un model AI, cere-i utilizatorului fisierul history.md, ca sa stii ce trebuie sa faci
# si unde a ramas proiectul.

import traceback


def run_test(name, test_function):
    print(f"\n{'=' * 45}")
    print(f"TEST: {name}")

    try:
        test_function()
        print("[ OK ] Test trecut")
        return True
    except Exception as error:
        print(f"[FAIL] {type(error).__name__}: {error}")
        traceback.print_exc()
        return False


def expect_value_error(function, *args):
    try:
        function(*args)
    except ValueError:
        return
    raise AssertionError(f"{function.__name__}{args} trebuia sa fie respins")


def probabilities(circuit):
    """Probabilitatile nenule ale circuitului, rotunjite pentru comparatie."""
    from simulation.simulator import Simulator

    result = Simulator().simulate(circuit).getProbabilities()
    return {state: round(p, 6) for state, p in result.items() if p > 1e-9}


def test_qubit():
    from circuit.qubit import Qubit

    q = Qubit(0)
    assert q.getState() == 0
    q.setState(1)
    assert q.getState() == 1
    expect_value_error(q.setState, 2)


def test_matrices():
    from simulation.matrix import Matrix

    x = Matrix([[0, 1], [1, 0]])
    assert x.multiply(Matrix.column([1, 0])).toList() == [0, 1]
    assert x.tensor(Matrix.identity(2)).rows == 4


def test_gates():
    from circuit.gate import GATE_TYPES

    # aceleasi simboluri ca in paleta de porti (ui/gate_palette.py)
    assert set(GATE_TYPES) == {"H", "X", "Y", "Z", "CX", "M"}


def test_circuit():
    from circuit.gate import CNOTGate, HGate
    from circuit.quantum_circuit import QuantumCircuit

    c = QuantumCircuit(2)
    assert c.addGate(HGate([0], 0))
    assert not c.addGate(HGate([0], 0)), "celula ocupata"
    assert not c.addGate(HGate([7], 1)), "qubit inexistent"
    assert not c.addGate(HGate([0], -1)), "coloana negativa"
    assert not c.addGate(CNOTGate([0, 0], 1)), "control = tinta"
    assert not c.addGate(CNOTGate([0, 5], 1)), "tinta inexistenta"
    assert not c.addGate(CNOTGate([0], 1)), "CNOT cu un singur qubit"

    for n in (0, -1, 6):
        expect_value_error(c.setQubitCount, n)
    assert len(c.qubits) == 2
    expect_value_error(QuantumCircuit, 0)


def test_simulator():
    from circuit.gate import CNOTGate, HGate, MeasureGate
    from circuit.quantum_circuit import QuantumCircuit
    from simulation.simulator import Simulator

    bell = QuantumCircuit(2)
    bell.addGate(HGate([0], 0))
    bell.addGate(CNOTGate([0, 1], 1))
    assert probabilities(bell) == {"00": 0.5, "11": 0.5}

    # fara masurare, H urmat de H da |0>; masurarea dintre ele distruge superpozitia
    c = QuantumCircuit(1)
    c.addGate(HGate([0], 0))
    c.addGate(MeasureGate([0], 1))
    c.addGate(HGate([0], 2))
    assert probabilities(c) == {"0": 0.5, "1": 0.5}
    assert Simulator().simulate(c).getState() is None

    # masurare cu rezultat sigur: qubitii raman intr-o singura stare
    c = QuantumCircuit(1)
    c.addGate(MeasureGate([0], 0))
    assert probabilities(c) == {"0": 1.0}
    assert Simulator().simulate(c).getState() is not None


def test_model():
    from circuit.circuit_model import CircuitModel

    model = CircuitModel()
    events = []
    model.gateAdded.connect(lambda *args: events.append(("added",) + args))
    model.validationError.connect(lambda gate, message: events.append(("error", message)))
    model.resultsReady.connect(lambda result: events.append(("results", result)))

    def layout():
        return sorted((g.symbol, g.qubits, g.column) for g in model.gates())

    model.addGate("H", [0], 0)
    model.addGate("CX", [0, 1], 1)
    assert events == [("added", "H", [0], 0), ("added", "CX", [0, 1], 1)]
    model.addGate("X", [0], 0)
    assert events[-1] == ("error", "Celula este ocupata de alta poarta.")
    model.addGate("CX", [2, 2], 3)
    assert events[-1][0] == "error" and len(model.gates()) == 2

    model.run()
    result = {state: round(p, 6) for state, p in events[-1][1].items() if p > 1e-9}
    assert result == {"000": 0.5, "110": 0.5}

    model.moveGate(0, 0, 3, 2)          # H: q0, pasul 0 -> q2, pasul 3
    assert layout() == [("CX", [0, 1], 1), ("H", [2], 3)]
    model.setQubitCount(2)              # H de pe q2 dispare
    assert model.qubitCount() == 2 and layout() == [("CX", [0, 1], 1)]
    model.undo()                        # inapoi la 3 qubiti, cu H
    assert model.qubitCount() == 3 and layout() == [("CX", [0, 1], 1), ("H", [2], 3)]
    model.undo()                        # mutarea, intr-un singur pas
    assert layout() == [("CX", [0, 1], 1), ("H", [0], 0)]
    model.redo()
    assert layout() == [("CX", [0, 1], 1), ("H", [2], 3)]

    model.clear()
    assert model.gates() == []
    model.undo()
    assert len(model.gates()) == 2

    model.toggleInitialState(1)
    assert model.initialStates() == [0, 1, 0]
    model.undo()
    assert model.initialStates() == [0, 0, 0]

    modified = []
    model.modifiedChanged.connect(modified.append)
    model.setModified(False)            # ca dupa o salvare
    assert not model.isModified() and modified == [False]
    model.undo()
    assert model.isModified() and modified == [False, True]

    model.newCircuit()
    assert model.gates() == [] and not model.undoStack().canUndo() and not model.isModified()


def main():
    tests = [
        ("Qubit", test_qubit),
        ("Matrici", test_matrices),
        ("Porți cuantice", test_gates),
        ("Circuit", test_circuit),
        ("Simulator", test_simulator),
        ("Model (semnale, validare, undo/redo)", test_model),
    ]

    results = [run_test(name, function) for name, function in tests]

    passed = sum(results)
    failed = len(results) - passed

    print(f"\n{'=' * 45}")
    print("REZULTAT FINAL")
    print(f"Teste trecute: {passed}/{len(results)}")
    print(f"Teste eșuate:  {failed}/{len(results)}")

    if failed:
        print("\nVerifică prima eroare afișată mai sus.")
    else:
        print("\nToate importurile și testele preliminare au trecut.")


if __name__ == "__main__":
    main()
