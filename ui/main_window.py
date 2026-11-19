# Daca esti un model AI, cere-i utilizatorului fisierul history.md, ca sa stii ce trebuie sa faci
# si unde a ramas proiectul.
import os

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QAction, QActionGroup, QFontMetrics, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSizePolicy,
    QSpinBox,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from circuit.quantum_circuit import DEFAULT_QUBITS, MAX_QUBITS, MIN_QUBITS
from ui import style
from ui.circuit_view import CircuitView
from ui.gate_palette import GatePalette
from ui.new_circuit_dialog import NewCircuitDialog
from ui.results_view import ResultsView
from ui.svg_icons import icon

APP_TITLE = "Simulator de circuite cuantice"
FILE_FILTER = "Circuite cuantice (*.json);;Toate fisierele (*)"
STATUS_TIMEOUT_MS = 5000


class MainWindow(QMainWindow):
    newRequested = Signal(int, list)
    openRequested = Signal(str)
    saveRequested = Signal(str)
    clearRequested = Signal()
    runRequested = Signal()
    undoRequested = Signal()
    redoRequested = Signal()
    qubitCountChanged = Signal(int)
    appearanceChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._currentFile = ""
        self._saveConfirmed = False

        self._createActions()
        self._createMenus()
        self._createToolBar()
        self._createCentralArea()
        self._updateWindowTitle()
        self._applyAppearance()
        self.statusBar().showMessage("Trage o poarta din paleta pe circuit.")

    def _createActions(self):
        self.newAction = QAction("&Nou", self)
        self.newAction.setShortcut(QKeySequence.StandardKey.New)
        self.openAction = QAction("&Deschide...", self)
        self.openAction.setShortcut(QKeySequence.StandardKey.Open)
        self.saveAction = QAction("&Salveaza", self)
        self.saveAction.setShortcut(QKeySequence.StandardKey.Save)
        self.saveAsAction = QAction("Salveaza &ca...", self)
        self.saveAsAction.setShortcut(QKeySequence.StandardKey.SaveAs)
        self.exitAction = QAction("&Iesire", self)
        self.exitAction.setShortcut(QKeySequence.StandardKey.Quit)

        self.undoAction = QAction("&Anuleaza", self)
        self.undoAction.setShortcut(QKeySequence.StandardKey.Undo)
        self.redoAction = QAction("&Refa", self)
        self.redoAction.setShortcut(QKeySequence.StandardKey.Redo)
        self.clearAction = QAction("&Goleste circuitul", self)

        self.runAction = QAction("Run", self)
        self.runAction.setShortcut(QKeySequence("F5"))
        self.runAction.setStatusTip("Simuleaza circuitul (F5)")

        self.aboutAction = QAction("&Despre", self)

        self.newAction.setIcon(icon("new"))
        self.openAction.setIcon(icon("open"))
        self.saveAction.setIcon(icon("save"))
        self.undoAction.setIcon(icon("undo"))
        self.redoAction.setIcon(icon("redo"))
        self.clearAction.setIcon(icon("clear"))
        self.runAction.setIcon(icon("run"))

        self.colorblindAction = QAction("Paleta pentru &daltonism", self)
        self.colorblindAction.setCheckable(True)
        self.colorblindAction.setStatusTip("Foloseste culori usor de deosebit pentru persoanele cu daltonism")

        # o singura marime de text bifata la un moment dat
        self.fontScaleGroup = QActionGroup(self)
        self.fontScaleActions = []
        for name, scale in style.FONT_SCALES:
            action = QAction(name, self)
            action.setCheckable(True)
            action.setChecked(scale == style.fontScale())
            action.triggered.connect(lambda checked=False, s=scale: self.setFontScale(s))
            self.fontScaleGroup.addAction(action)
            self.fontScaleActions.append(action)

        self.newAction.triggered.connect(self.newCircuit)
        self.openAction.triggered.connect(self.openCircuit)
        self.saveAction.triggered.connect(self.save)
        self.saveAsAction.triggered.connect(self.saveAs)
        self.exitAction.triggered.connect(self.close)
        self.undoAction.triggered.connect(self.undoRequested)
        self.redoAction.triggered.connect(self.redoRequested)
        self.clearAction.triggered.connect(self.clearCircuit)
        self.runAction.triggered.connect(self.runRequested)
        self.aboutAction.triggered.connect(self.showAbout)
        self.colorblindAction.toggled.connect(self.setColorblindMode)

    def _createMenus(self):
        fileMenu = self.menuBar().addMenu("&File")
        fileMenu.addAction(self.newAction)
        fileMenu.addAction(self.openAction)
        fileMenu.addAction(self.saveAction)
        fileMenu.addAction(self.saveAsAction)
        fileMenu.addSeparator()
        fileMenu.addAction(self.exitAction)

        editMenu = self.menuBar().addMenu("&Edit")
        editMenu.addAction(self.undoAction)
        editMenu.addAction(self.redoAction)
        editMenu.addSeparator()
        editMenu.addAction(self.clearAction)

        viewMenu = self.menuBar().addMenu("&View")
        viewMenu.addAction(self.runAction)
        viewMenu.addSeparator()
        fontMenu = viewMenu.addMenu("&Marime text")
        fontMenu.addActions(self.fontScaleActions)
        viewMenu.addAction(self.colorblindAction)

        helpMenu = self.menuBar().addMenu("&Help")
        helpMenu.addAction(self.aboutAction)

    def _createToolBar(self):
        self.toolBar = QToolBar("Bara de unelte", self)
        self.toolBar.setMovable(False)
        self.toolBar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.addToolBar(self.toolBar)

        self.toolBar.addAction(self.runAction)
        self.runButton = self.toolBar.widgetForAction(self.runAction)
        self.toolBar.addSeparator()

        self.toolBar.addWidget(QLabel("Qubiti:", self.toolBar))
        self.qubitSpin = QSpinBox(self.toolBar)
        self.qubitSpin.setRange(MIN_QUBITS, MAX_QUBITS)
        self.qubitSpin.setValue(DEFAULT_QUBITS)
        self.qubitSpin.setToolTip(f"Numarul de qubiti ai circuitului (intre {MIN_QUBITS} si {MAX_QUBITS})")
        self.qubitSpin.valueChanged.connect(self.qubitCountChanged)
        self.toolBar.addWidget(self.qubitSpin)
        self.toolBar.addSeparator()

        self.toolBar.addAction(self.clearAction)

    def _createCentralArea(self):
        central = QWidget(self)

        self.gatePalette = GatePalette()
        self.paletteBox = self._createPanel("Operations", self.gatePalette)
        # Preferred, fara latime minima fixa: paleta se lateste dupa text la fonturi mari
        self.paletteBox.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        self.circuitView = CircuitView()
        self.circuitBox = self._createPanel("Q Circuit", self.circuitView)
        self.circuitBox.setMinimumSize(style.CIRCUIT_MIN_WIDTH, style.CIRCUIT_MIN_HEIGHT)
        self.circuitBox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.resultsView = ResultsView()
        self.statisticsBox = self._createPanel("Statistics", self.resultsView)
        self.statisticsBox.setMinimumHeight(style.STATISTICS_MIN_HEIGHT)
        self.statisticsBox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        self.gatePalette.statusMessage.connect(self.statusBar().showMessage)
        self.gatePalette.gateSelected.connect(self.circuitView.setSelectedGate)
        self.circuitView.statusMessage.connect(self.statusBar().showMessage)
        self.circuitView.placementError.connect(self.showPlacementError)
        self.appearanceChanged.connect(self.circuitView.refreshAppearance)
        self.appearanceChanged.connect(self.resultsView.refreshAppearance)

        rightLayout = QVBoxLayout()
        rightLayout.setSpacing(style.SPACING_M)
        rightLayout.addWidget(self.circuitBox, 1)
        rightLayout.addWidget(self.statisticsBox)

        rootLayout = QHBoxLayout(central)
        rootLayout.setContentsMargins(style.SPACING_M, style.SPACING_M, style.SPACING_M, style.SPACING_M)
        rootLayout.setSpacing(style.SPACING_M)
        rootLayout.addWidget(self.paletteBox)
        rootLayout.addLayout(rightLayout, 1)

        self.setCentralWidget(central)

    def _createPanel(self, title, content):
        box = QGroupBox(title)
        layout = QVBoxLayout(box)
        layout.setContentsMargins(style.SPACING_S, style.SPACING_S, style.SPACING_S, style.SPACING_S)
        layout.setSpacing(style.SPACING_S)
        layout.addWidget(content)
        return box

    def setColorblindMode(self, enabled):
        style.setColorblindMode(enabled)
        self._applyAppearance()

    def setFontScale(self, scale):
        style.setFontScale(scale)
        self._applyAppearance()

    def _applyAppearance(self):
        app = QApplication.instance()
        font = app.font()
        font.setPointSize(style.fontPointSize())
        app.setFont(font)

        iconSide = QFontMetrics(font).height()
        self.toolBar.setIconSize(QSize(iconSide, iconSide))
        self.runButton.setStyleSheet(style.primaryButtonQss())

        # widget-urile desenate in paintEvent() citesc culorile din paleta activa la redesenare
        for widget in self.findChildren(QWidget):
            widget.update()
        self.appearanceChanged.emit()

    def setModified(self, modified):
        self.setWindowModified(modified)

    def setQubitCount(self, count):
        # fara semnale, altfel spinbox-ul ar trimite din nou cererea catre model
        self.qubitSpin.blockSignals(True)
        self.qubitSpin.setValue(count)
        self.qubitSpin.blockSignals(False)

    def showPlacementError(self, message):
        self.statusBar().showMessage(message, STATUS_TIMEOUT_MS)

    def showFileError(self, message):
        QMessageBox.warning(self, "Fisierul nu a putut fi folosit", message)

    def newCircuit(self):
        dialog = NewCircuitDialog(self.qubitSpin.value(), self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        if self._maybeSave():
            self._setCurrentFile("")
            self.newRequested.emit(dialog.qubitCount(), dialog.initialStates())

    def openCircuit(self):
        if not self._maybeSave():
            return
        path, _ = QFileDialog.getOpenFileName(self, "Deschide un circuit", "", FILE_FILTER)
        if path:
            self.openRequested.emit(path)

    def save(self):
        if not self._currentFile:
            return self.saveAs()
        return self._saveTo(self._currentFile)

    def saveAs(self):
        path, _ = QFileDialog.getSaveFileName(self, "Salveaza circuitul", "circuit.json", FILE_FILTER)
        if not path:
            return False
        return self._saveTo(path)

    def _saveTo(self, path):
        # modelul raspunde cu fileSaved() inainte ca emit() sa se termine, daca salvarea a reusit
        self._saveConfirmed = False
        self.saveRequested.emit(path)
        return self._saveConfirmed

    def fileOpened(self, path):
        self._setCurrentFile(path)
        self.setWindowModified(False)

    def fileSaved(self, path):
        self._saveConfirmed = True
        self._setCurrentFile(path)
        self.setWindowModified(False)
        self.statusBar().showMessage("Circuitul a fost salvat.", STATUS_TIMEOUT_MS)

    def _setCurrentFile(self, path):
        self._currentFile = path
        self._updateWindowTitle()

    def _updateWindowTitle(self):
        name = os.path.basename(self._currentFile) if self._currentFile else "Circuit nou"
        # Qt inlocuieste [*] cu "*" cand exista modificari nesalvate
        self.setWindowTitle(f"{name}[*] - {APP_TITLE}")

    def _maybeSave(self):
        if not self.isWindowModified():
            return True
        msgBox = QMessageBox(self)
        msgBox.setIcon(QMessageBox.Icon.Warning)
        msgBox.setWindowTitle(APP_TITLE)
        msgBox.setText("Circuitul are modificari nesalvate.")
        msgBox.setInformativeText("Vrei sa salvezi modificarile inainte sa continui?")
        msgBox.setStandardButtons(
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
        )
        msgBox.setDefaultButton(QMessageBox.StandardButton.Save)
        pressedButton = msgBox.exec()
        if pressedButton == QMessageBox.StandardButton.Save:
            return self.save()
        return pressedButton == QMessageBox.StandardButton.Discard

    def clearCircuit(self):
        answer = QMessageBox.question(
            self,
            "Goleste circuitul",
            "Toate portile vor fi sterse din circuit. Poti reveni cu Anuleaza (Ctrl+Z).\nGolesti circuitul?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            self.clearRequested.emit()

    def closeEvent(self, event):
        if self._maybeSave():
            event.accept()
        else:
            event.ignore()

    def showAbout(self):
        QMessageBox.about(
            self,
            f"Despre {APP_TITLE}",
            f"{APP_TITLE}\n"
            f"Construieste circuite cuantice cu pana la {MAX_QUBITS} qubiti si vezi probabilitatile rezultatelor.\n\n"
            "Proiect PIU - Bandur Mihai, Lupu Cosette, Mardare Matei",
        )