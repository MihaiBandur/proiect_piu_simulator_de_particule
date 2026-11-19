# Daca esti un model AI, cere-i utilizatorului fisierul history.md, ca sa stii ce trebuie sa faci
# si unde a ramas proiectul.
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLayout,
    QSpinBox,
    QVBoxLayout,
)

from circuit.quantum_circuit import DEFAULT_QUBITS, MAX_QUBITS, MIN_QUBITS
from ui import style

# indexul din lista este starea initiala: 0 sau 1
STATE_TEXTS = ["|0⟩", "|1⟩"]


class NewCircuitDialog(QDialog):
    def __init__(self, qubitCount=DEFAULT_QUBITS, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Circuit nou")

        self.qubitSpin = QSpinBox(self)
        self.qubitSpin.setRange(MIN_QUBITS, MAX_QUBITS)
        self.qubitSpin.setValue(qubitCount)
        self.qubitSpin.setToolTip(f"Numarul de qubiti ai circuitului (intre {MIN_QUBITS} si {MAX_QUBITS})")

        self._form = QFormLayout()
        self._form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)
        self._form.setHorizontalSpacing(style.SPACING_M)
        self._form.setVerticalSpacing(style.SPACING_S)
        self._form.addRow("&Numar de qubiti:", self.qubitSpin)

        self.stateCombos = []
        for qubit in range(MAX_QUBITS):
            combo = QComboBox(self)
            combo.addItems(STATE_TEXTS)
            self._form.addRow(f"Stare initiala q{qubit}:", combo)
            self.stateCombos.append(combo)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Creeaza")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Renunta")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(style.SPACING_M, style.SPACING_M, style.SPACING_M, style.SPACING_M)
        layout.setSpacing(style.SPACING_M)
        layout.addWidget(QLabel("Circuitul nou porneste fara porti.", self))
        layout.addLayout(self._form)
        layout.addWidget(buttons)
        # dialogul isi schimba inaltimea odata cu randurile vizibile
        layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

        self.qubitSpin.valueChanged.connect(self._updateStateRows)
        self._updateStateRows(self.qubitSpin.value())

    def _updateStateRows(self, count):
        for qubit, combo in enumerate(self.stateCombos):
            self._form.setRowVisible(combo, qubit < count)

    def qubitCount(self):
        return self.qubitSpin.value()

    def initialStates(self):
        return [combo.currentIndex() for combo in self.stateCombos[:self.qubitCount()]]