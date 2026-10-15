"""
Fereastra principala - schelet (mockup in cod).

Zonele Operations, Q Circuit si Statistics sunt deocamdata etichete provizorii.
Fiecare membru isi inlocuieste zona cu widget-ul lui, fara sa modifice restul:
  - Operations (paleta de porti)  -> Cosette
  - Q Circuit (zona de circuit)   -> Matei
  - Statistics (histograma/tabel) -> Mihai
"""
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QSizePolicy,
    QSpinBox,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from ui import style
from ui.gate_palette import GatePalette


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Simulator de circuite cuantice")

        self._createActions()
        self._createMenus()
        self._createToolBar()
        self._createCentralArea()
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