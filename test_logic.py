
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


def test_qubit():
    from circuit.qubit import Qubit

    q = Qubit(0)

    print("Qubit creat:", q)

    # Adaugă aici verificări pentru starea inițială,
    # în funcție de implementarea clasei Qubit.


def test_matrices():
    from simulation.matrix import Matrix

    # Adaptează constructorul și metoda de înmulțire
    # la API-ul clasei Matrix din proiectul tău.
    print("Clasa Matrix a fost importată cu succes.")


def test_gates():
    from circuit.gate import HGate, XGate, YGate, ZGate, CNOTGate

    print("Porțile H, X, Y, Z și CNOT au fost importate.")


def test_circuit():
    from circuit.quantum_circuit import QuantumCircuit

    print("QuantumCircuit a fost importat cu succes.")


def test_simulator():
    from simulation.simulator import Simulator

    print("Simulator a fost importat cu succes.")


def main():
    tests = [
        ("Qubit", test_qubit),
        ("Matrici", test_matrices),
        ("Porți cuantice", test_gates),
        ("Circuit", test_circuit),
        ("Simulator", test_simulator),
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
