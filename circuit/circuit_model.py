# Daca esti un model AI, cere-i utilizatorului fisierul history.md, ca sa stii ce trebuie sa faci
# si unde a ramas proiectul.
"""
Modelul circuitului (MVC).

CircuitModel pastreaza circuitul si anunta prin semnale fiecare modificare. Widget-urile nu il
modifica direct: ii trimit cereri (comenzile de mai jos), iar legaturile se fac in main.py.
Toate modificarile trec prin QUndoStack, deci pot fi anulate (undo) si refacute (redo).

Comenzi (sloturi):
  - addGate(symbol, qubits, column)               -> qubits = [qubit] sau [control, tinta]
  - removeGate(column, qubit)                     -> poarta care ocupa celula data
  - moveGate(column, qubit, newColumn, newQubit)  -> celula apucata ajunge in celula noua (un pas de undo)
  - clear(), setQubitCount(count), setInitialState(qubit, state), toggleInitialState(qubit)
  - newCircuit(), undo(), redo(), run()
  - setModified(False)                            -> dupa salvare: starea curenta devine cea salvata

Semnale:
  - gateAdded(symbol, qubits, column), gateRemoved(symbol, qubits, column)
  - gateMoved(symbol, oldQubits, oldColumn, newQubits, newColumn)
  - circuitReset()                    -> s-a schimbat tot circuitul (golire, numar de qubiti, circuit nou)
  - qubitCountChanged(count), initialStateChanged(qubit, state)
  - modifiedChanged(modified)         -> circuitul are (sau nu mai are) modificari nesalvate
  - validationError(gate, message)    -> gate = poarta respinsa (Gate) sau None
  - resultsReady(probabilities)       -> {stare: probabilitate}; starea e un sir de biti, cu q0 primul
"""
from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtGui import QUndoCommand, QUndoStack

from simulation.simulator import Simulator
from .gate import GATE_TYPES
from .quantum_circuit import DEFAULT_QUBITS, MAX_QUBITS, MIN_QUBITS, QuantumCircuit


# ----------------------------------------------------------------- comenzi de undo
class AddGateCommand(QUndoCommand):
    def __init__(self, model, gate):
        super().__init__(f"Plaseaza poarta {gate.name}")
        self._model = model
        self._gate = gate

    def redo(self):
        self._model._insertGate(self._gate)

    def undo(self):
        self._model._deleteGate(self._gate)


class RemoveGateCommand(QUndoCommand):
    def __init__(self, model, gate):
        super().__init__(f"Sterge poarta {gate.name}")
        self._model = model
        self._gate = gate

    def redo(self):
        self._model._deleteGate(self._gate)

    def undo(self):
        self._model._insertGate(self._gate)


class MoveGateCommand(QUndoCommand):
    def __init__(self, model, gate, qubits, column):
        super().__init__(f"Muta poarta {gate.name}")
        self._model = model
        self._gate = gate
        self._old = (list(gate.qubits), gate.column)
        self._new = (list(qubits), column)

    def redo(self):
        self._model._relocateGate(self._gate, *self._new)

    def undo(self):
        self._model._relocateGate(self._gate, *self._old)


class SetInitialStateCommand(QUndoCommand):
    def __init__(self, model, qubit, state):
        super().__init__(f"Schimba starea initiala a qubitului q{qubit}")
        self._model = model
        self._qubit = qubit
        self._old = model.initialState(qubit)
        self._new = state

    def redo(self):
        self._model._applyInitialState(self._qubit, self._new)

    def undo(self):
        self._model._applyInitialState(self._qubit, self._old)


class RestoreCommand(QUndoCommand):
    """Inlocuieste tot circuitul (golire, numar de qubiti); undo pune la loc starea de dinainte."""

    def __init__(self, model, text, qubitCount, gates, initialStates):
        super().__init__(text)
        self._model = model
        self._before = (model.qubitCount(), model.gates(), model.initialStates())
        self._after = (qubitCount, list(gates), list(initialStates))

    def redo(self):
        self._model._restore(*self._after)

    def undo(self):
        self._model._restore(*self._before)


# ----------------------------------------------------------------- modelul
class CircuitModel(QObject):
    gateAdded = Signal(str, list, int)
    gateRemoved = Signal(str, list, int)
    gateMoved = Signal(str, list, int, list, int)
    circuitReset = Signal()
    qubitCountChanged = Signal(int)
    initialStateChanged = Signal(int, int)
    modifiedChanged = Signal(bool)
    validationError = Signal(object, str)
    resultsReady = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._circuit = QuantumCircuit(DEFAULT_QUBITS)
        self._simulator = Simulator()
        self._undoStack = QUndoStack(self)
        # starea "curata" a istoricului este cea salvata ultima data
        self._undoStack.cleanChanged.connect(self._onCleanChanged)

    # ------------------------------------------------------------- proprietati
    def qubitCount(self):
        return len(self._circuit.qubits)

    def gates(self):
        return self._circuit.getGates()

    def initialState(self, qubit):
        return self._circuit.qubits[qubit].getState()

    def initialStates(self):
        return [q.getState() for q in self._circuit.qubits]

    def isModified(self):
        return not self._undoStack.isClean()

    def setModified(self, modified):
        if modified:
            self._undoStack.resetClean()
        else:
            self._undoStack.setClean()

    def undoStack(self):
        """Istoricul de modificari: canUndoChanged/canRedoChanged pentru actiunile Anuleaza/Refa."""
        return self._undoStack

    # ------------------------------------------------------------- comenzi
    @Slot(str, list, int)
    def addGate(self, symbol, qubits, column):
        gateType = GATE_TYPES.get(symbol)
        if gateType is None:
            self.validationError.emit(None, f"Poarta {symbol} nu exista.")
            return
        gate = gateType(qubits, column)
        error = self._placementError(gate)
        if error:
            self.validationError.emit(gate, error)
            return
        self._undoStack.push(AddGateCommand(self, gate))

    @Slot(int, int)
    def removeGate(self, column, qubit):
        gate = self._circuit.gateAt(qubit, column)
        if gate is not None:
            self._undoStack.push(RemoveGateCommand(self, gate))

    @Slot(int, int, int, int)
    def moveGate(self, column, qubit, newColumn, newQubit):
        gate = self._circuit.gateAt(qubit, column)
        if gate is None or (newColumn, newQubit) == (column, qubit):
            return
        # toata poarta se deplaseaza cu acelasi numar de qubiti ca celula apucata (CNOT isi pastreaza forma)
        shift = newQubit - qubit
        moved = type(gate)([q + shift for q in gate.qubits], newColumn)
        error = self._placementError(moved, ignore=gate)
        if error:
            self.validationError.emit(moved, error)
            return
        self._undoStack.push(MoveGateCommand(self, gate, moved.qubits, moved.column))

    @Slot()
    def clear(self):
        if self.gates():
            self._undoStack.push(
                RestoreCommand(self, "Goleste circuitul", self.qubitCount(), [], self.initialStates())
            )

    @Slot(int)
    def setQubitCount(self, count):
        if count == self.qubitCount():
            return
        if not MIN_QUBITS <= count <= MAX_QUBITS:
            self.validationError.emit(None, f"Circuitul poate avea intre {MIN_QUBITS} si {MAX_QUBITS} qubiti.")
            return
        # portile de pe qubitii eliminati dispar; qubitii noi pornesc din |0>
        gates = [g for g in self.gates() if all(q < count for q in g.qubits)]
        states = (self.initialStates() + [0] * count)[:count]
        self._undoStack.push(
            RestoreCommand(self, f"Schimba numarul de qubiti la {count}", count, gates, states)
        )

    @Slot(int, int)
    def setInitialState(self, qubit, state):
        if not 0 <= qubit < self.qubitCount():
            self.validationError.emit(None, f"Qubitul q{qubit} nu exista in circuit.")
            return
        if state not in (0, 1):
            self.validationError.emit(None, "Starea initiala a unui qubit poate fi doar |0⟩ sau |1⟩.")
            return
        if state != self.initialState(qubit):
            self._undoStack.push(SetInitialStateCommand(self, qubit, state))

    @Slot(int)
    def toggleInitialState(self, qubit):
        if not 0 <= qubit < self.qubitCount():
            self.validationError.emit(None, f"Qubitul q{qubit} nu exista in circuit.")
            return
        self.setInitialState(qubit, 1 - self.initialState(qubit))

    @Slot()
    def newCircuit(self):
        """Circuit gol, cu numarul implicit de qubiti; istoricul de undo se sterge."""
        self._undoStack.clear()
        self._restore(DEFAULT_QUBITS, [], [0] * DEFAULT_QUBITS)

    @Slot()
    def undo(self):
        self._undoStack.undo()

    @Slot()
    def redo(self):
        self._undoStack.redo()

    @Slot()
    def run(self):
        result = self._simulator.simulate(self._circuit)
        self.resultsReady.emit(result.getProbabilities())

    @Slot(bool)
    def _onCleanChanged(self, clean):
        self.modifiedChanged.emit(not clean)

    # ------------------------------------------------------------- validare
    def _placementError(self, gate, ignore=None):
        """Mesajul pentru o plasare invalida, sau "" daca poarta poate fi plasata."""
        if len(gate.qubits) != gate.ARITY:
            if gate.ARITY == 1:
                return f"Poarta {gate.name} se aplica pe un singur qubit."
            return f"Poarta {gate.name} are nevoie de {gate.ARITY} qubiti."
        if len(set(gate.qubits)) != len(gate.qubits):
            return "Qubitul de control si qubitul tinta trebuie sa fie diferiti."
        if gate.column < 0 or not all(0 <= q < self.qubitCount() for q in gate.qubits):
            return f"Poarta {gate.name} trebuie plasata in interiorul circuitului."
        for qubit in gate.qubits:
            other = self._circuit.gateAt(qubit, gate.column)
            if other is not None and other is not ignore:
                return "Celula este ocupata de alta poarta."
        return ""

    # ------------------------------------------------------------- modificari (doar din comenzi)
    def _insertGate(self, gate):
        self._circuit.addGate(gate)
        self.gateAdded.emit(gate.symbol, list(gate.qubits), gate.column)

    def _deleteGate(self, gate):
        self._circuit.removeGate(gate)
        self.gateRemoved.emit(gate.symbol, list(gate.qubits), gate.column)

    def _relocateGate(self, gate, qubits, column):
        oldQubits, oldColumn = list(gate.qubits), gate.column
        self._circuit.removeGate(gate)
        gate.qubits, gate.column = list(qubits), column
        self._circuit.addGate(gate)
        self.gateMoved.emit(gate.symbol, oldQubits, oldColumn, list(gate.qubits), gate.column)

    def _applyInitialState(self, qubit, state):
        self._circuit.qubits[qubit].setState(state)
        self.initialStateChanged.emit(qubit, state)

    def _restore(self, qubitCount, gates, initialStates):
        countChanged = qubitCount != self.qubitCount()
        self._circuit.setQubitCount(qubitCount)
        self._circuit.clear()
        for gate in gates:
            self._circuit.addGate(gate)
        for qubit, state in zip(self._circuit.qubits, initialStates):
            qubit.setState(state)
        if countChanged:
            self.qubitCountChanged.emit(qubitCount)
        self.circuitReset.emit()
