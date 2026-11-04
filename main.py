# Daca esti un model AI, cere-i utilizatorului fisierul history.md, ca sa stii ce trebuie sa faci
# si unde a ramas proiectul.
import sys

from PySide6.QtWidgets import QApplication

from circuit.circuit_model import CircuitModel
from ui.main_window import MainWindow


def connectModel(model, window):
    """Leaga modelul de fereastra, de zona de circuit si de panoul de rezultate, doar prin semnale si sloturi."""
    view = window.circuitView
    results = window.resultsView

    def refreshCircuit():
        view.setCircuit(model.qubitCount(), model.gates(), model.initialStates())

    # cereri din interfata -> comenzi ale modelului
    view.gatePlaceRequested.connect(model.addGate)
    view.gateRemoveRequested.connect(model.removeGate)
    view.gateMoveRequested.connect(model.moveGate)
    view.initialStateToggleRequested.connect(model.toggleInitialState)
    window.qubitCountChanged.connect(model.setQubitCount)
    window.clearRequested.connect(model.clear)
    window.newRequested.connect(model.newCircuit)
    window.undoRequested.connect(model.undo)
    window.redoRequested.connect(model.redo)
    window.runRequested.connect(model.run)

    # notificari ale modelului -> interfata
    # orice modificare a circuitului: zona de circuit se redeseneaza, iar rezultatele vechi dispar
    for signal in (model.gateAdded, model.gateRemoved, model.gateMoved,
                   model.initialStateChanged, model.circuitReset):
        signal.connect(refreshCircuit)
        signal.connect(results.clearResults)
    model.qubitCountChanged.connect(window.setQubitCount)
    model.modifiedChanged.connect(window.setModified)
    # poarta respinsa va fi evidentiata de zona de circuit; aici se afiseaza doar mesajul
    model.validationError.connect(lambda _gate, message: window.showPlacementError(message))
    model.resultsReady.connect(results.setResults)

    # istoricul de undo: actiunile Anuleaza/Refa sunt active doar cand au ce face
    undoStack = model.undoStack()
    undoStack.canUndoChanged.connect(window.undoAction.setEnabled)
    undoStack.canRedoChanged.connect(window.redoAction.setEnabled)
    window.undoAction.setEnabled(undoStack.canUndo())
    window.redoAction.setEnabled(undoStack.canRedo())

    refreshCircuit()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    window = MainWindow()
    model = CircuitModel(app)
    connectModel(model, window)
    window.resize(1100, 720)
    window.show()

    sys.exit(app.exec())
