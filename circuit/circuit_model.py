# Daca esti un model AI, cere-i utilizatorului fisierul history.md, ca sa stii ce trebuie sa faci
# si unde a ramas proiectul.
"""
Modelul circuitului (MVC).

CircuitModel pastreaza circuitul si anunta prin semnale fiecare modificare. Widget-urile nu il
modifica direct: ii trimit cereri (comenzile de mai jos), iar legaturile se fac in main.py.
Toate modificarile trec prin QUndoStack, deci pot fi anulate (undo) si refacute (redo).

Comenzi (sloturi):
  - addGate(symbol, qubits, column)               -> qubits = [qubit], [control, tinta] (CNOT)
                                                     sau [control1, control2, tinta] (Toffoli)
  - removeGate(column, qubit)                     -> poarta care ocupa celula data
  - moveGate(column, qubit, newColumn, newQubit)  -> celula apucata ajunge in celula noua (un pas de undo)
  - clear(), setQubitCount(count), setInitialState(qubit, state), toggleInitialState(qubit)
  - newCircuit(qubitCount, initialStates)         -> circuit gol; fara argumente: 3 qubiti in |0>
  - undo(), redo(), run()
  - saveFile(path), openFile(path)                -> raspuns: fileSaved / fileOpened, sau fileError
  - setModified(False)                            -> starea curenta devine cea salvata (saveFile o face singur)

Semnale:
  - gateAdded(symbol, qubits, column), gateRemoved(symbol, qubits, column)
  - gateMoved(symbol, oldQubits, oldColumn, newQubits, newColumn)
  - circuitReset()                    -> s-a schimbat tot circuitul (golire, numar de qubiti, circuit nou, fisier)
  - qubitCountChanged(count), initialStateChanged(qubit, state)
  - modifiedChanged(modified)         -> circuitul are (sau nu mai are) modificari nesalvate
  - validationError(gate, message)    -> gate = poarta respinsa (Gate) sau None
  - resultsReady(probabilities)       -> {stare: probabilitate}; starea e un sir de biti, cu q0 primul
  - fileSaved(path), fileOpened(path) -> fisierul a fost scris / incarcat
  - fileError(message)                -> fisierul nu a putut fi scris sau citit; circuitul ramane neschimbat

Formatul fisierului (JSON, UTF-8):
  {"format": "simulator-circuite-cuantice", "version": 1, "qubits": 3, "initialStates": [0, 0, 0],
   "gates": [{"symbol": "H", "qubits": [0], "column": 0}, {"symbol": "CX", "qubits": [0, 1], "column": 1}]}
La deschidere, fisierul este verificat complet inainte sa inlocuiasca circuitul curent.
"""
import json
import os

from PySide6.QtCore import QIODevice, QObject, QSaveFile, Signal, Slot
from PySide6.QtGui import QUndoCommand, QUndoStack

from simulation.simulator import Simulator
from .gate import GATE_TYPES
from .quantum_circuit import DEFAULT_QUBITS, MAX_COLUMNS, MAX_QUBITS, MIN_QUBITS, QuantumCircuit

FILE_FORMAT = "simulator-circuite-cuantice"
FILE_VERSION = 1
# un circuit cu toti cei 5 qubiti ocupati pe toti pasii are sub 500 KB; peste limita, fisierul nu e al aplicatiei
MAX_FILE_BYTES = 1024 * 1024


class CircuitFileError(ValueError):
    """Continutul unui fisier nu descrie un circuit valid; mesajul spune ce anume este gresit."""


def _isInt(value):
    # in JSON, true/false devin bool, iar bool este si int in Python
    return isinstance(value, int) and not isinstance(value, bool)


def circuitToDict(qubitCount, gates, initialStates):
    """Continutul fisierului pentru un circuit; portile sunt ordonate dupa pas, apoi dupa qubit."""
    ordered = sorted(gates, key=lambda g: (g.column, g.qubits))
    return {
        "format": FILE_FORMAT,
        "version": FILE_VERSION,
        "qubits": qubitCount,
        "initialStates": list(initialStates),
        "gates": [{"symbol": g.symbol, "qubits": list(g.qubits), "column": g.column} for g in ordered],
    }


def formatCircuitJson(data):
    """Textul fisierului: JSON obisnuit, cu cate o poarta pe rand, usor de citit si de comparat."""
    parts = [f"  {json.dumps(key)}: {json.dumps(value)}" for key, value in data.items() if key != "gates"]
    gates = ",\n".join(f"    {json.dumps(gate)}" for gate in data["gates"])
    parts.append(f'  "gates": [\n{gates}\n  ]' if gates else '  "gates": []')
    return "{\n" + ",\n".join(parts) + "\n}\n"


def circuitFromDict(data):
    """(qubitCount, gates, initialStates) din continutul unui fisier. Ridica CircuitFileError."""
    if not isinstance(data, dict) or data.get("format") != FILE_FORMAT:
        raise CircuitFileError("nu este un circuit salvat de aceasta aplicatie.")
    if not _isInt(data.get("version")) or data.get("version") != FILE_VERSION:
        raise CircuitFileError(f"versiunea fisierului ({data.get('version')}) nu este cunoscuta.")

    qubitCount = data.get("qubits")
    if not _isInt(qubitCount) or not MIN_QUBITS <= qubitCount <= MAX_QUBITS:
        raise CircuitFileError(f"numarul de qubiti trebuie sa fie intre {MIN_QUBITS} si {MAX_QUBITS}.")

    states = data.get("initialStates")
    if (not isinstance(states, list) or len(states) != qubitCount
            or not all(_isInt(s) and s in (0, 1) for s in states)):
        raise CircuitFileError("fiecare qubit trebuie sa aiba starea initiala 0 sau 1.")

    items = data.get("gates")
    if not isinstance(items, list):
        raise CircuitFileError("lista de porti lipseste.")
    circuit = QuantumCircuit(qubitCount)
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            raise CircuitFileError(f"poarta {index} nu este descrisa corect.")
        symbol, qubits, column = item.get("symbol"), item.get("qubits"), item.get("column")
        gateType = GATE_TYPES.get(symbol) if isinstance(symbol, str) else None
        if gateType is None:
            raise CircuitFileError(f"poarta {index} ({symbol}) nu exista.")
        if not isinstance(qubits, list) or not all(_isInt(q) for q in qubits) or not _isInt(column):
            raise CircuitFileError(f"poarta {index} ({symbol}) are qubitii sau pasul scrisi gresit.")
        gate = gateType(qubits, column)
        if not circuit.isValidGate(gate):
            raise CircuitFileError(
                f"poarta {index} ({gate.name}) nu incape in circuit: qubiti gresiti sau pas in afara "
                f"intervalului 1-{MAX_COLUMNS}."
            )
        if not circuit.addGate(gate):
            raise CircuitFileError(f"poarta {index} ({gate.name}) se suprapune cu alta poarta la pasul {column + 1}.")
    return qubitCount, circuit.getGates(), states


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
    fileSaved = Signal(str)
    fileOpened = Signal(str)
    fileError = Signal(str)

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

    @Slot(int, list)
    def newCircuit(self, qubitCount=DEFAULT_QUBITS, initialStates=None):
        """Circuit gol, cu numarul de qubiti si starile initiale date; istoricul de undo se sterge."""
        states = [0] * qubitCount if initialStates is None else list(initialStates)
        if not MIN_QUBITS <= qubitCount <= MAX_QUBITS:
            self.validationError.emit(None, f"Circuitul poate avea intre {MIN_QUBITS} si {MAX_QUBITS} qubiti.")
            return
        if len(states) != qubitCount or any(s not in (0, 1) for s in states):
            self.validationError.emit(None, "Fiecare qubit trebuie sa aiba starea initiala |0⟩ sau |1⟩.")
            return
        self._undoStack.clear()
        self._restore(qubitCount, [], states)

    # ------------------------------------------------------------- fisiere
    @Slot(str)
    def saveFile(self, path):
        """Scrie circuitul in fisier. Fisierul vechi ramane intact daca scrierea esueaza (QSaveFile)."""
        text = formatCircuitJson(circuitToDict(self.qubitCount(), self.gates(), self.initialStates()))
        # in mesaje apare doar numele fisierului: utilizatorul tocmai l-a ales in dialog
        message = f"Circuitul nu a putut fi salvat in {os.path.basename(path)}."
        file = QSaveFile(path)
        if not file.open(QIODevice.OpenModeFlag.WriteOnly):
            self.fileError.emit(f"{message}\n{file.errorString()}")
            return
        file.write(text.encode("utf-8"))
        if not file.commit():
            self.fileError.emit(f"{message}\n{file.errorString()}")
            return
        self.setModified(False)
        self.fileSaved.emit(path)

    @Slot(str)
    def openFile(self, path):
        """Incarca circuitul din fisier, doar daca fisierul este valid in intregime."""
        name = os.path.basename(path)
        try:
            if os.path.getsize(path) > MAX_FILE_BYTES:
                raise CircuitFileError("este prea mare pentru un circuit.")
            with open(path, encoding="utf-8") as file:
                data = json.load(file)
            qubitCount, gates, states = circuitFromDict(data)
        except CircuitFileError as error:
            self.fileError.emit(f"Fisierul {name} nu poate fi deschis: {error}")
            return
        except (UnicodeDecodeError, json.JSONDecodeError, RecursionError):
            self.fileError.emit(f"Fisierul {name} nu poate fi deschis: nu este un circuit salvat de aceasta aplicatie.")
            return
        except OSError as error:
            self.fileError.emit(f"Fisierul {name} nu poate fi citit.\n{error.strerror or error}")
            return
        # ca la un circuit nou: istoricul de undo incepe de la circuitul incarcat, care este cel salvat
        self._undoStack.clear()
        self._restore(qubitCount, gates, states)
        self.setModified(False)
        self.fileOpened.emit(path)

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
            if gate.ARITY == 2:
                return "Qubitul de control si qubitul tinta trebuie sa fie diferiti."
            return f"Poarta {gate.name} are nevoie de {gate.ARITY} qubiti diferiti."
        if not 0 <= gate.column < MAX_COLUMNS or not all(0 <= q < self.qubitCount() for q in gate.qubits):
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
