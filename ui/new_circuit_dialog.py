# Daca esti un model AI, cere-i utilizatorului fisierul history.md, ca sa stii ce trebuie sa faci
# si unde a ramas proiectul.
"""
Dialogul "Circuit nou" (Cosette).

Un formular (QFormLayout) cu doua tipuri de campuri:
  - numarul de qubiti (QSpinBox);
  - starea initiala a fiecarui qubit (QComboBox |0⟩ / |1⟩); se vad doar randurile qubitilor alesi.

Dialogul nu modifica circuitul. MainWindow il deschide la File > Nou, citeste valorile alese
(qubitCount(), initialStates()) si trimite cererea newRequested(qubitCount, initialStates) catre model.
"""
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

# textele starilor initiale, in ordinea valorilor (indexul din combo = starea)
STATE_TEXTS = ["|0⟩", "|1⟩"]


class NewCircuitDialog(QDialog):
    """Alege numarul de qubiti si starile initiale ale unui circuit nou (gol)."""

    def __init__(self, qubitCount=DEFAULT_QUBITS, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Circuit nou")

        intro = QLabel("Circuitul nou porneste fara porti.", self)

        self.qubitSpin = QSpinBox(self)
        self.qubitSpin.setRange(MIN_QUBITS, MAX_QUBITS)
        self.qubitSpin.setValue(min(max(qubitCount, MIN_QUBITS), MAX_QUBITS))
        self.qubitSpin.setToolTip(f"Numarul de qubiti ai circuitului (intre {MIN_QUBITS} si {MAX_QUBITS})")

        # eticheta la stanga, campul la dreapta; campurile pastreaza latimea lor naturala
        self._form = QFormLayout()
        self._form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)
        self._form.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)
        self._form.setHorizontalSpacing(style.SPACING_M)
        self._form.setVerticalSpacing(style.SPACING_S)
        # "&" da scurtatura Alt+N; addRow() face din camp "buddy"-ul etichetei
        self._form.addRow("&Numar de qubiti:", self.qubitSpin)

        # cate un rand pentru fiecare qubit posibil; randurile qubitilor in plus se ascund
        self.stateCombos = []
        for qubit in range(MAX_QUBITS):
            combo = QComboBox(self)
            combo.addItems(STATE_TEXTS)
            combo.setToolTip(f"Starea initiala a qubitului q{qubit}")
            combo.setAccessibleName(f"Starea initiala a qubitului q{qubit}")
            self._form.addRow(f"Stare initiala q{qubit}:", combo)
            self.stateCombos.append(combo)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self
        )
        buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Creeaza")
        buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Renunta")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(style.SPACING_M, style.SPACING_M, style.SPACING_M, style.SPACING_M)
        layout.setSpacing(style.SPACING_M)
        layout.addWidget(intro)
        layout.addLayout(self._form)
        layout.addWidget(buttons)
        # dialogul se strange sau se mareste odata cu randurile vizibile
        layout.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)

        self.qubitSpin.valueChanged.connect(self._updateStateRows)
        self._updateStateRows(self.qubitSpin.value())
        self.qubitSpin.setFocus()

    def _updateStateRows(self, count):
        for qubit, combo in enumerate(self.stateCombos):
            self._form.setRowVisible(combo, qubit < count)

    # ------------------------------------------------------------- valorile alese
    def qubitCount(self):
        return self.qubitSpin.value()

    def initialStates(self):
        """Starea initiala (0 sau 1) a fiecarui qubit, de la q0 la ultimul."""
        return [combo.currentIndex() for combo in self.stateCombos[: self.qubitCount()]]
