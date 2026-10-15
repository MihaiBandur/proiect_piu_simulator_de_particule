"""
Fereastra principala - schelet (mockup in cod).

Zonele Operations, Q Circuit si Statistics sunt deocamdata etichete provizorii.
Fiecare membru isi inlocuieste zona cu widget-ul lui, fara sa modifice restul:
  - Operations (paleta de porti)  -> Cosette
  - Q Circuit (zona de circuit)   -> Matei
  - Statistics (histograma/tabel) -> Mihai
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
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

from ui import style
from ui.gate_palette import GatePalette

APP_TITLE = "Simulator de circuite cuantice"
FILE_FILTER = "Circuite cuantice (*.json);;Toate fisierele (*)"
STATUS_TIMEOUT_MS = 5000  # cat ramane afisat un mesaj temporar in bara de stare


class MainWindow(QMainWindow):
    """
    Fereastra principala. Nu tine starea circuitului: transmite cererile
    utilizatorului prin semnale, iar modelul (Mihai) si zona de circuit (Matei)
    le trateaza. Conexiunile se fac din exterior, in main.py.
    """

    # cereri catre model / simulator
    newRequested = Signal()
    openRequested = Signal(str)        # calea fisierului ales
    saveRequested = Signal(str)        # calea fisierului in care se salveaza
    clearRequested = Signal()
    runRequested = Signal()
    undoRequested = Signal()
    redoRequested = Signal()
    qubitCountChanged = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._currentFile = ""

        self._createActions()
        self._createMenus()
        self._createToolBar()
        self._createCentralArea()
        self._updateWindowTitle()
        self.statusBar().showMessage("Trage o poarta din paleta pe circuit.")

    # ------------------------------------------------------------------ actiuni
    def _createActions(self):
        # File
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
        self.exitAction.triggered.connect(self.close)

        # Edit (undo/redo vor fi inlocuite cu actiunile din QUndoStack-ul lui Mihai)
        self.undoAction = QAction("&Anuleaza", self)
        self.undoAction.setShortcut(QKeySequence.StandardKey.Undo)
        self.redoAction = QAction("&Refa", self)
        self.redoAction.setShortcut(QKeySequence.StandardKey.Redo)
        self.clearAction = QAction("&Goleste circuitul", self)

        # Simulare
        self.runAction = QAction("Run", self)
        self.runAction.setShortcut(QKeySequence("F5"))
        self.runAction.setStatusTip("Simuleaza circuitul (F5)")

        # Help
        self.aboutAction = QAction("&Despre", self)

        # legaturi: fiecare actiune fie deschide un dialog, fie emite o cerere
        self.newAction.triggered.connect(self.newCircuit)
        self.openAction.triggered.connect(self.openCircuit)
        self.saveAction.triggered.connect(self.save)
        self.saveAsAction.triggered.connect(self.saveAs)
        self.undoAction.triggered.connect(self.undoRequested)
        self.redoAction.triggered.connect(self.redoRequested)
        self.clearAction.triggered.connect(self.clearCircuit)
        self.runAction.triggered.connect(self.runRequested)
        self.aboutAction.triggered.connect(self.showAbout)

    def _createMenus(self):
        menuBar = self.menuBar()

        fileMenu = menuBar.addMenu("&File")
        fileMenu.addAction(self.newAction)
        fileMenu.addAction(self.openAction)
        fileMenu.addAction(self.saveAction)
        fileMenu.addAction(self.saveAsAction)
        fileMenu.addSeparator()
        fileMenu.addAction(self.exitAction)

        editMenu = menuBar.addMenu("&Edit")
        editMenu.addAction(self.undoAction)
        editMenu.addAction(self.redoAction)
        editMenu.addSeparator()
        editMenu.addAction(self.clearAction)

        viewMenu = menuBar.addMenu("&View")
        viewMenu.addAction(self.runAction)

        helpMenu = menuBar.addMenu("&Help")
        helpMenu.addAction(self.aboutAction)

    def _createToolBar(self):
        toolBar = QToolBar("Bara de unelte", self)
        toolBar.setMovable(False)
        self.addToolBar(toolBar)

        # actiunea principala in stanga, evidentiata
        toolBar.addAction(self.runAction)
        toolBar.widgetForAction(self.runAction).setStyleSheet(style.PRIMARY_BUTTON_QSS)
        toolBar.addSeparator()

        toolBar.addWidget(QLabel("Qubiti:", toolBar))
        self.qubitSpin = QSpinBox(toolBar)
        self.qubitSpin.setRange(1, 5)
        self.qubitSpin.setValue(3)
        self.qubitSpin.setToolTip("Numarul de qubiti ai circuitului (intre 1 si 5)")
        self.qubitSpin.valueChanged.connect(self.qubitCountChanged)
        toolBar.addWidget(self.qubitSpin)
        toolBar.addSeparator()

        # actiune secundara, aspect implicit (mai discret)
        toolBar.addAction(self.clearAction)

    # ------------------------------------------------------------- zona centrala
    def _createCentralArea(self):
        central = QWidget(self)

        # paleta de porti (Cosette)
        self.gatePalette = GatePalette()
        self.paletteBox = self._createPanel("Operations", self.gatePalette)
        self.paletteBox.setMinimumWidth(style.PALETTE_MIN_WIDTH)
        self.gatePalette.statusMessage.connect(self._showStatusMessage)

        # panouri provizorii (se inlocuiesc cu widget-urile reale)
        self.paletteBox.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        self.circuitBox = self._createPanel("Q Circuit", self._createPlaceholder("Zona de circuit"))
        self.circuitBox.setMinimumSize(style.CIRCUIT_MIN_WIDTH, style.CIRCUIT_MIN_HEIGHT)
        self.circuitBox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.statisticsBox = self._createPanel(
            "Statistics", self._createPlaceholder("Histograma / Tabel (tab Types)")
        )
        self.statisticsBox.setMinimumHeight(style.STATISTICS_MIN_HEIGHT)
        self.statisticsBox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        # dreapta: circuitul deasupra, rezultatele dedesubt
        rightLayout = QVBoxLayout()
        rightLayout.setSpacing(style.SPACING_M)
        rightLayout.addWidget(self.circuitBox, 1)
        rightLayout.addWidget(self.statisticsBox)

        # paleta in coloana din stanga
        rootLayout = QHBoxLayout(central)
        rootLayout.setContentsMargins(style.SPACING_M, style.SPACING_M, style.SPACING_M, style.SPACING_M)
        rootLayout.setSpacing(style.SPACING_M)
        rootLayout.addWidget(self.paletteBox)
        rootLayout.addLayout(rightLayout, 1)

        self.setCentralWidget(central)

    def _createPanel(self, title, content):
        """Un panou cu titlu care contine widget-ul primit (devine parintele lui)."""
        box = QGroupBox(title)
        layout = QVBoxLayout(box)
        layout.setContentsMargins(style.SPACING_S, style.SPACING_S, style.SPACING_S, style.SPACING_S)
        layout.setSpacing(style.SPACING_S)
        layout.addWidget(content)
        return box

    def _createPlaceholder(self, text):
        """Eticheta provizorie, pana cand colegii isi adauga widget-urile."""
        placeholder = QLabel(text)
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setStyleSheet(style.PLACEHOLDER_QSS)
        return placeholder

    # ------------------------------------------------------------- sloturi
    def _showStatusMessage(self, text):
        if text:
            self.statusBar().showMessage(text)
        else:
            self.statusBar().clearMessage()

    def setModified(self, modified):
        """Apelat de model cand circuitul are (sau nu mai are) modificari nesalvate."""
        self.setWindowModified(modified)

    def showPlacementError(self, message):
        """Eroare de plasare: doar in bara de stare, fara dialog care sa intrerupa lucrul."""
        self.statusBar().showMessage(message, STATUS_TIMEOUT_MS)

    def showFileError(self, message):
        """Eroare la deschiderea sau salvarea unui fisier: dialog, pentru ca a fost cerut de utilizator."""
        QMessageBox.warning(self, "Fisierul nu a putut fi folosit", message)

    # ------------------------------------------------------------- fisiere
    def newCircuit(self):
        if self._maybeSave():
            self._setCurrentFile("")
            self.newRequested.emit()

    def openCircuit(self):
        if not self._maybeSave():
            return
        path, _ = QFileDialog.getOpenFileName(self, "Deschide un circuit", "", FILE_FILTER)
        if path:
            self._setCurrentFile(path)
            self.openRequested.emit(path)

    def save(self):
        """Salveaza in fisierul curent; daca nu exista inca, cere un nume. Intoarce True la succes."""
        if not self._currentFile:
            return self.saveAs()
        self.saveRequested.emit(self._currentFile)
        self.setWindowModified(False)
        self.statusBar().showMessage("Circuitul a fost salvat.", STATUS_TIMEOUT_MS)
        return True

    def saveAs(self):
        path, _ = QFileDialog.getSaveFileName(self, "Salveaza circuitul", "circuit.json", FILE_FILTER)
        if not path:
            return False  # utilizatorul a renuntat
        self._setCurrentFile(path)
        return self.save()

    def _setCurrentFile(self, path):
        self._currentFile = path
        self._updateWindowTitle()

    def _updateWindowTitle(self):
        # [*] este inlocuit de Qt cu "*" cand fereastra are modificari nesalvate
        name = self._currentFile.replace("\\", "/").split("/")[-1] if self._currentFile else "Circuit nou"
        self.setWindowTitle(f"{name}[*] - {APP_TITLE}")

    # ------------------------------------------------------------- confirmari
    def _askSaveChanges(self):
        """Dialogul Save / Discard / Cancel. Intoarce butonul ales."""
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle(APP_TITLE)
        box.setText("Circuitul are modificari nesalvate.")
        box.setInformativeText("Vrei sa salvezi modificarile inainte sa continui?")
        box.setStandardButtons(
            QMessageBox.StandardButton.Save
            | QMessageBox.StandardButton.Discard
            | QMessageBox.StandardButton.Cancel
        )
        box.setDefaultButton(QMessageBox.StandardButton.Save)
        return box.exec()

    def _maybeSave(self):
        """True daca se poate continua (nimic nesalvat, salvat sau renuntat la modificari)."""
        if not self.isWindowModified():
            return True
        answer = self._askSaveChanges()
        if answer == QMessageBox.StandardButton.Save:
            return self.save()
        return answer == QMessageBox.StandardButton.Discard

    def clearCircuit(self):
        answer = QMessageBox.question(
            self,
            "Goleste circuitul",
            "Toate portile vor fi sterse din circuit. Poti reveni cu Anuleaza (Ctrl+Z).\n"
            "Golesti circuitul?",
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
            f"<b>{APP_TITLE}</b><br>"
            "Construieste circuite cuantice cu pana la 5 qubiti si vezi probabilitatile rezultatelor.<br><br>"
            "Proiect PIU - Bandur Mihai, Lupu Cosette, Mardare Matei",
        )