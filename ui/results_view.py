# Daca esti un model AI, cere-i utilizatorului fisierul history.md, ca sa stii ce trebuie sa faci
# si unde a ramas proiectul.
"""
Panoul de rezultate (Statistics).

- HistogramView: histograma probabilitatilor, widget propriu desenat in paintEvent().
- ResultsView: comutatorul (tab-urile Types) si QStackedWidget-ul cu histograma si tabelul.

Intrari (sloturi):
  - setResults(probabilities)  -> {stare: probabilitate}, starea ca sir de biti cu q0 primul
                                  (formatul semnalului CircuitModel.resultsReady)
  - clearResults()             -> rezultatele nu mai corespund circuitului
  - refreshAppearance()        -> la schimbarea paletei / marimii textului

Starile se afiseaza in hexa; q0 este bitul cel mai semnificativ (ex. 3 qubiti: "110" -> 6).
Vederea nu se comuta singura: utilizatorul alege histograma sau tabelul.
"""
import math

from PySide6.QtCore import QEvent, QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFont, QFontMetricsF, QPainter
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHeaderView,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QTabBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ui import style

EMPTY_TEXT = "Apasa Run pentru a simula circuitul si a vedea rezultatele."
EQUAL_TOLERANCE = 1e-9  # probabilitati egale pana la erorile de rotunjire


def stateLabel(bits):
    """Starea in hexa, cu atatea cifre cate cer qubitii (q0 este bitul cel mai semnificativ)."""
    digits = (len(bits) + 3) // 4
    return f"{int(bits, 2):0{digits}X}"


def rankResults(probabilities):
    """[(biti, eticheta hexa, probabilitate, este maxima)], in ordinea starilor.

    Cand toate starile au aceeasi probabilitate, niciuna nu este evidentiata.
    """
    states = sorted(probabilities.items())  # sirurile de biti au aceeasi lungime: ordinea starilor
    if not states:
        return []
    best = max(p for _, p in states)
    allEqual = min(p for _, p in states) >= best - EQUAL_TOLERANCE
    return [(bits, stateLabel(bits), p, not allEqual and p >= best - EQUAL_TOLERANCE) for bits, p in states]


class HistogramView(QWidget):
    """Histograma probabilitatilor. Geometria se calculeaza in _relayout(); paintEvent() doar deseneaza."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._results = []
        self._bars = []              # (dreptunghi, este maxima)
        self._valueLabels = []       # (dreptunghi, text) - procentul deasupra barei, cand incape
        self._stateLabels = []       # (dreptunghi sau ancora, text) - starea sub bara
        self._ticks = []             # (y, dreptunghiul etichetei, text) - axa verticala
        self._rotated = False        # etichetele starilor nu incap orizontal si sunt rotite
        self._rotatedRect = QRectF()
        self._plotRect = QRectF()

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setAccessibleName("Histograma rezultatelor")

    # ------------------------------------------------------------- API public
    def setResults(self, probabilities):
        self._results = rankResults(probabilities)
        self._resultsChanged()

    def clearResults(self):
        self._results = []
        self._resultsChanged()

    def refreshAppearance(self):
        self._resultsChanged()

    def _resultsChanged(self):
        self._relayout()
        self.updateGeometry()  # sizeHint() depinde de numarul de bare si de font

    # ------------------------------------------------------------- font si dimensiuni
    def _labelFont(self):
        """Fontul etichetelor si al axelor: urmeaza marimea textului aleasa, niciodata sub 10 pt."""
        font = QFont(self.font())
        font.setPointSize(style.fontPointSize())
        return font

    def _labelWidth(self, metrics):
        return max((metrics.horizontalAdvance(label) for _, label, _, _ in self._results), default=0.0)

    def sizeHint(self):
        # etichetele starilor stau orizontal, iar procentele incap deasupra fiecarei bare
        return self._hint(rotated=False, plotHeight=2 * style.HISTOGRAM_MIN_PLOT_HEIGHT)

    def minimumSizeHint(self):
        # etichetele rotite: fiecare stare are nevoie doar de inaltimea unui rand de text
        return self._hint(rotated=True, plotHeight=style.HISTOGRAM_MIN_PLOT_HEIGHT)

    def _hint(self, rotated, plotHeight):
        """Dimensiunea data de numarul de bare si de fontul etichetelor."""
        metrics = QFontMetricsF(self._labelFont())
        left = metrics.horizontalAdvance("100%") + style.SPACING_S
        top = metrics.height() + style.SPACING_XS
        labelWidth = self._labelWidth(metrics)
        if rotated:
            slot = metrics.height() + style.SPACING_XS
            labelArea = labelWidth + style.SPACING_S
        else:
            slot = max(labelWidth, metrics.horizontalAdvance("100.0%")) + style.SPACING_S
            labelArea = metrics.height() + style.SPACING_S
        width = left + len(self._results) * slot + style.SPACING_S
        if not self._results and not rotated:
            width = metrics.horizontalAdvance(EMPTY_TEXT) + 2 * style.SPACING_M  # mesajul pe un rand
        return QSize(math.ceil(width), math.ceil(top + plotHeight + labelArea))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._relayout()

    def changeEvent(self, event):
        if event.type() == QEvent.Type.FontChange:
            self._resultsChanged()
        super().changeEvent(event)

    # ------------------------------------------------------------- geometrie
    def _relayout(self):
        """Pozitiile barelor si ale etichetelor pentru dimensiunea curenta, calculate in virgula mobila."""
        metrics = QFontMetricsF(self._labelFont())
        textHeight = metrics.height()
        left = metrics.horizontalAdvance("100%") + style.SPACING_S
        top = textHeight + style.SPACING_XS
        plotWidth = max(self.width() - left - style.SPACING_S, 1.0)
        slot = plotWidth / max(len(self._results), 1)
        labelWidth = self._labelWidth(metrics)
        self._rotated = labelWidth + style.SPACING_S > slot
        labelArea = (labelWidth if self._rotated else textHeight) + style.SPACING_S
        plotHeight = max(self.height() - top - labelArea, 1.0)
        bottom = top + plotHeight
        self._plotRect = QRectF(left, top, plotWidth, plotHeight)

        self._ticks = []
        for k in range(style.HISTOGRAM_TICK_COUNT + 1):
            fraction = k / style.HISTOGRAM_TICK_COUNT
            y = bottom - fraction * plotHeight
            labelRect = QRectF(0, y - textHeight / 2, left - style.SPACING_XS, textHeight)
            self._ticks.append((y, labelRect, f"{fraction:.0%}"))

        # eticheta rotita, in coordonatele locale ale ancorei: se termina chiar sub axa
        self._rotatedRect = QRectF(-labelWidth, -textHeight / 2, labelWidth, textHeight)
        barWidth = min(slot * style.HISTOGRAM_BAR_FILL, style.HISTOGRAM_MAX_BAR_WIDTH)
        self._bars, self._valueLabels, self._stateLabels = [], [], []
        for i, (_, label, p, best) in enumerate(self._results):
            x = left + i * slot
            bar = QRectF(x + (slot - barWidth) / 2, bottom - p * plotHeight, barWidth, p * plotHeight)
            self._bars.append((bar, best))
            value = f"{p:.1%}"
            if p > EQUAL_TOLERANCE and metrics.horizontalAdvance(value) <= slot:
                self._valueLabels.append((QRectF(x, bar.top() - textHeight, slot, textHeight), value))
            if self._rotated:
                self._stateLabels.append((QPointF(x + slot / 2, bottom + style.SPACING_XS), label))
            else:
                self._stateLabels.append((QRectF(x, bottom + style.SPACING_XS, slot, textHeight), label))
        self.update()

    # ------------------------------------------------------------- desenare
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), self.palette().base())  # acelasi fundal ca zona de circuit
        painter.setFont(self._labelFont())
        textColor = self.palette().text().color()

        if not self._bars:
            painter.setPen(textColor)
            flags = int(Qt.AlignmentFlag.AlignCenter) | int(Qt.TextFlag.TextWordWrap)
            painter.drawText(QRectF(self.rect()), flags, EMPTY_TEXT)
            painter.end()
            return

        # liniile orizontale si valorile axei verticale
        for y, labelRect, text in self._ticks:
            painter.setPen(style.histogramGridPen())
            painter.drawLine(QPointF(self._plotRect.left(), y), QPointF(self._plotRect.right(), y))
            painter.setPen(textColor)
            painter.drawText(labelRect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, text)

        # barele; rezultatul cel mai probabil are culoarea de evidentiere si contur
        for bar, best in self._bars:
            painter.setPen(style.histogramAxisPen() if best else Qt.PenStyle.NoPen)
            painter.setBrush(QColor(style.color("highlight") if best else style.resultsColor("bar")))
            painter.drawRect(bar)

        painter.setPen(style.histogramAxisPen())
        painter.drawLine(self._plotRect.bottomLeft(), self._plotRect.bottomRight())

        painter.setPen(textColor)
        for rect, text in self._valueLabels:
            painter.drawText(rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom, text)

        for anchor, text in self._stateLabels:
            if self._rotated:
                painter.save()
                # in cod: translate, apoi rotate; asupra punctelor se aplica intai rotatia, apoi translatia
                painter.translate(anchor)
                painter.rotate(-90)
                painter.drawText(self._rotatedRect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, text)
                painter.restore()
            else:
                painter.drawText(anchor, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, text)
        painter.end()


class ResultsView(QWidget):
    """Panoul Statistics: tab-urile Types comuta intre histograma si tabel, pagini ale unui QStackedWidget."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._results = []

        # comutatorul (tab-urile Types); ordinea tab-urilor este ordinea paginilor din stiva
        self.typesTabs = QTabBar(self)
        self.typesTabs.addTab("Histograma")
        self.typesTabs.addTab("Tabel")
        self.typesTabs.setToolTip("Alege cum vezi rezultatele: histograma sau tabelul cu valorile exacte.")

        self.histogram = HistogramView()
        histogramScroll = QScrollArea()
        histogramScroll.setWidget(self.histogram)
        # sub latimea minima a histogramei apare bara de derulare, in loc sa se suprapuna etichetele
        histogramScroll.setWidgetResizable(True)
        histogramScroll.setFrameShape(QFrame.Shape.NoFrame)

        self.table = QTableWidget(0, 3)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.stack = QStackedWidget()
        self.stack.addWidget(histogramScroll)
        self.stack.addWidget(self.table)
        self.typesTabs.currentChanged.connect(self.stack.setCurrentIndex)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(style.SPACING_S)
        layout.addWidget(self.typesTabs)
        layout.addWidget(self.stack, 1)

        self._fillTable()

    # ------------------------------------------------------------- API public
    def setResults(self, probabilities):
        self._results = rankResults(probabilities)
        self.histogram.setResults(probabilities)
        self._fillTable()

    def clearResults(self):
        if self._results:
            self._results = []
            self.histogram.clearResults()
            self._fillTable()

    def refreshAppearance(self):
        self.histogram.refreshAppearance()
        self._fillTable()  # culoarea randurilor evidentiate vine din paleta activa

    # ------------------------------------------------------------- tabel
    def _fillTable(self):
        qubits = len(self._results[0][0]) if self._results else 0
        valuesTitle = f"Valori q0…q{qubits - 1}" if qubits > 1 else "Valoare q0"
        self.table.setHorizontalHeaderLabels(["Stare (hexa)", valuesTitle, "Probabilitate"])
        self.table.setRowCount(len(self._results))
        highlight = QColor(style.color("highlight"))
        for row, (bits, label, p, best) in enumerate(self._results):
            for column, text in enumerate((label, bits, f"{p:.4%}")):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if best:
                    item.setBackground(highlight)
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                self.table.setItem(row, column, item)
