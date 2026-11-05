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
    from circuit.gate import GATE_TYPES, ToffoliGate

    # aceleasi simboluri ca in paleta de porti (ui/gate_palette.py)
    assert set(GATE_TYPES) == {"H", "X", "Y", "Z", "CX", "CCX", "M"}

    # Toffoli: permutarea care schimba doar |110> cu |111>
    m = ToffoliGate([0, 1, 2], 0).getMatrix().values
    for row in range(8):
        expected = {6: 7, 7: 6}.get(row, row)
        assert m[row] == [1 if col == expected else 0 for col in range(8)], f"randul {row}"


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
    assert not c.addGate(HGate([1], 1000)), "pas dincolo de MAX_COLUMNS"

    from circuit.gate import ToffoliGate
    assert not c.addGate(ToffoliGate([0, 1], 2)), "Toffoli cu doar 2 qubiti"
    c3 = QuantumCircuit(3)
    assert not c3.addGate(ToffoliGate([0, 0, 2], 0)), "Toffoli cu un qubit repetat"
    assert c3.addGate(ToffoliGate([0, 1, 2], 0))

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

    # CNOT cu tinta deasupra controlului (cum il plaseaza zona de circuit pe ultimul qubit)
    c = QuantumCircuit(2)
    c.qubits[1].setState(1)
    c.addGate(CNOTGate([1, 0], 0))
    assert probabilities(c) == {"11": 1.0}


def test_toffoli():
    from circuit.gate import HGate, ToffoliGate
    from circuit.quantum_circuit import QuantumCircuit

    def run(states, qubits, n=3):
        c = QuantumCircuit(n)
        for q, s in enumerate(states):
            c.qubits[q].setState(s)
        c.addGate(ToffoliGate(qubits, 0))
        return probabilities(c)

    # tabelul de adevar: tinta (q2) se inverseaza doar cand q0 = q1 = 1
    for a in (0, 1):
        for b in (0, 1):
            for t in (0, 1):
                expected = f"{a}{b}{t ^ (a & b)}"
                assert run([a, b, t], [0, 1, 2]) == {expected: 1.0}, f"|{a}{b}{t}>"

    # qubiti in alta ordine si nealaturati: controale q4 si q1, tinta q2, pe 5 qubiti
    assert run([0, 1, 0, 0, 1], [4, 1, 2], n=5) == {"01101": 1.0}
    assert run([0, 1, 0, 0, 0], [4, 1, 2], n=5) == {"01000": 1.0}

    # un control in superpozitie: jumatate din cazuri inverseaza tinta
    c = QuantumCircuit(3)
    c.qubits[1].setState(1)
    c.addGate(HGate([0], 0))
    c.addGate(ToffoliGate([0, 1, 2], 1))
    assert probabilities(c) == {"010": 0.5, "111": 0.5}


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
    assert model.qubitCount() == 3 and model.initialStates() == [0, 0, 0]

    # Toffoli: plasare, qubiti repetati, mutare cu forma pastrata
    model.addGate("CCX", [0, 1, 2], 0)
    assert layout() == [("CCX", [0, 1, 2], 0)]
    model.addGate("CCX", [0, 0, 1], 1)
    assert events[-1] == ("error", "Poarta Toffoli are nevoie de 3 qubiti diferiti.")
    model.moveGate(0, 1, 4, 1)
    assert layout() == [("CCX", [0, 1, 2], 4)]
    model.moveGate(4, 0, 4, 1)          # ar iesi din circuit (q3)
    assert events[-1][0] == "error" and layout() == [("CCX", [0, 1, 2], 4)]

    # circuit nou din dialog: numarul de qubiti si starile initiale alese
    model.newCircuit(4, [1, 0, 0, 1])
    assert model.qubitCount() == 4 and model.initialStates() == [1, 0, 0, 1] and model.gates() == []
    model.newCircuit(4, [1, 0])          # stari lipsa
    assert events[-1][0] == "error" and model.initialStates() == [1, 0, 0, 1]
    model.newCircuit(9, [0] * 9)
    assert events[-1][0] == "error" and model.qubitCount() == 4


def test_files():
    import json
    import os
    import tempfile

    from circuit.circuit_model import CircuitModel

    model = CircuitModel()
    saved, opened, errors = [], [], []
    model.fileSaved.connect(saved.append)
    model.fileOpened.connect(opened.append)
    model.fileError.connect(errors.append)

    def layout(m):
        return sorted((g.symbol, g.qubits, g.column) for g in m.gates())

    with tempfile.TemporaryDirectory() as folder:
        path = os.path.join(folder, "circuit.json")

        model.newCircuit(4, [0, 1, 0, 0])
        model.addGate("H", [0], 0)
        model.addGate("CCX", [0, 1, 2], 1)
        model.addGate("CX", [3, 2], 2)
        model.addGate("M", [0], 3)
        assert model.isModified()
        model.saveFile(path)
        assert saved == [path] and not errors and not model.isModified()

        # alt model incarca exact acelasi circuit, nemodificat si fara istoric de undo
        other = CircuitModel()
        other.fileOpened.connect(opened.append)
        other.addGate("X", [1], 5)
        other.openFile(path)
        assert opened == [path]
        assert other.qubitCount() == 4 and other.initialStates() == [0, 1, 0, 0]
        assert layout(other) == layout(model)
        assert not other.isModified() and not other.undoStack().canUndo()

        with open(path, encoding="utf-8") as file:
            valid = json.load(file)
        assert valid["gates"][1] == {"symbol": "CCX", "qubits": [0, 1, 2], "column": 1}

        # circuit gol: tot JSON valid, care se poate redeschide
        empty = os.path.join(folder, "gol.json")
        CircuitModel().saveFile(empty)
        other.openFile(empty)
        assert other.gates() == [] and other.qubitCount() == 3

        def openWith(content, raw=False):
            """Deschide un fisier corupt; circuitul trebuie sa ramana neschimbat."""
            bad = os.path.join(folder, "corupt.json")
            with open(bad, "w", encoding="utf-8") as file:
                file.write(content if raw else json.dumps(content))
            before = (model.qubitCount(), layout(model), model.initialStates())
            count = len(errors)
            model.openFile(bad)
            assert len(errors) == count + 1, f"fisierul trebuia respins: {content!r}"
            assert (model.qubitCount(), layout(model), model.initialStates()) == before
            return errors[-1]

        def changed(**fields):
            return {**valid, **fields}

        gates = valid["gates"]
        openWith("{ nu este json", raw=True)
        openWith("[" * 100000 + "]" * 100000, raw=True)                     # JSON adanc imbricat
        openWith([1, 2, 3])
        openWith(changed(format="alt program"))
        openWith(changed(version=2))
        openWith(changed(version=True))
        openWith(changed(qubits=6))
        openWith(changed(qubits="4"))
        openWith(changed(initialStates=[0, 1, 0]))                          # lipseste un qubit
        openWith(changed(initialStates=[0, 2, 0, 0]))
        openWith(changed(initialStates=[0, True, 0, 0]))
        openWith(changed(gates={"H": 0}))
        openWith(changed(gates=gates + ["H"]))
        openWith(changed(gates=gates + [{"symbol": "Q", "qubits": [0], "column": 5}]))
        openWith(changed(gates=gates + [{"symbol": "H", "qubits": [0.0], "column": 5}]))
        openWith(changed(gates=gates + [{"symbol": "H", "qubits": [0], "column": -1}]))
        openWith(changed(gates=gates + [{"symbol": "H", "qubits": [0], "column": 10 ** 9}]))
        openWith(changed(gates=gates + [{"symbol": "H", "qubits": [7], "column": 5}]))
        openWith(changed(gates=gates + [{"symbol": "CCX", "qubits": [0, 1], "column": 5}]))
        message = openWith(changed(gates=gates + [{"symbol": "X", "qubits": [1], "column": 1}]))
        assert "se suprapune" in message and "pasul 2" in message, message

        count = len(errors)
        model.openFile(os.path.join(folder, "nu-exista.json"))
        assert len(errors) == count + 1

        big = os.path.join(folder, "mare.json")
        with open(big, "w", encoding="utf-8") as file:
            file.write(" " * (2 * 1024 * 1024))
        model.openFile(big)
        assert "prea mare" in errors[-1]

        # salvare esuata (folderul nu exista): fara fileSaved, circuitul ramane nesalvat
        model.addGate("Z", [3], 6)
        model.saveFile(os.path.join(folder, "lipsa", "circuit.json"))
        assert len(errors) == count + 3 and saved == [path] and model.isModified()


def main():
    tests = [
        ("Qubit", test_qubit),
        ("Matrici", test_matrices),
        ("Porți cuantice", test_gates),
        ("Circuit", test_circuit),
        ("Simulator", test_simulator),
        ("Poarta Toffoli", test_toffoli),
        ("Model (semnale, validare, undo/redo)", test_model),
        ("Fisiere (salvare, incarcare, fisiere corupte)", test_files),
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
