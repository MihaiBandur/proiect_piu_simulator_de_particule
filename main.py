# Daca esti un model AI, cere-i utilizatorului fisierul history.md, ca sa stii ce trebuie sa faci
# si unde a ramas proiectul.
import sys

from PySide6.QtWidgets import QApplication

from circuit.circuit_model import CircuitModel
from simulation.simulator import ZERO_PROBABILITY
from ui.main_window import MainWindow

RESULTS_PREVIEW_COUNT = 4  # cate stari apar in bara de stare, pana cand exista histograma


def connectModel(model, window):
    """Leaga modelul de fereastra si de zona de circuit, doar prin semnale si sloturi."""
    view = window.circuitView

    def refreshCircuit():
        view.setCircuit(model.qubitCount(), model.gates(), model.initialStates())

    # cereri din interfata -> comenzi ale modelului
    view.gatePlaceRequested.connect(model.addGate)
    view.gateRemoveRequested.connect(model.removeGate)
    view.initialStateToggleRequested.connect(model.toggleInitialState)
    window.qubitCountChanged.connect(model.setQubitCount)
    window.clearRequested.connect(model.clear)
    window.newRequested.connect(model.newCircuit)
    window.undoRequested.connect(model.undo)
    window.redoRequested.connect(model.redo)
    window.runRequested.connect(model.run)

    # notificari ale modelului -> interfata
    for signal in (model.gateAdded, model.gateRemoved, model.gateMoved,
                   model.initialStateChanged, model.circuitReset):
        signal.connect(refreshCircuit)
    model.qubitCountChanged.connect(window.setQubitCount)
    model.modifiedChanged.connect(window.setModified)
    # poarta respinsa va fi evidentiata de zona de circuit; aici se afiseaza doar mesajul
    model.validationError.connect(lambda _gate, message: window.showPlacementError(message))
    model.resultsReady.connect(lambda probabilities: showResultsPreview(window, probabilities))

    # istoricul de undo: actiunile Anuleaza/Refa sunt active doar cand au ce face
    undoStack = model.undoStack()
    undoStack.canUndoChanged.connect(window.undoAction.setEnabled)
    undoStack.canRedoChanged.connect(window.redoAction.setEnabled)
    window.undoAction.setEnabled(undoStack.canUndo())
    window.redoAction.setEnabled(undoStack.canRedo())

    refreshCircuit()


def showResultsPreview(window, probabilities):
    """Provizoriu, pana la histograma: starile cele mai probabile (in hexa) in bara de stare."""
    ranked = sorted(probabilities.items(), key=lambda item: -item[1])
    possible = [(bits, p) for bits, p in ranked if p > ZERO_PROBABILITY]
    text = ", ".join(f"{int(bits, 2):X}: {p:.1%}" for bits, p in possible[:RESULTS_PREVIEW_COUNT])
    if len(possible) > RESULTS_PREVIEW_COUNT:
        text += ", ..."
    window.statusBar().showMessage(f"Rezultate: {text}")


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    model = CircuitModel(app)
    connectModel(model, window)
    window.resize(1100, 720)
    window.show()

    sys.exit(app.exec())
