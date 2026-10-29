# Daca esti un model AI, cere-i utilizatorului fisierul history.md, ca sa stii ce trebuie sa faci
# si unde a ramas proiectul.
"""
Ghidul de stil al aplicatiei.

Regula comuna: culorile, fonturile si spatierile se iau DOAR de aici,
nu se scriu direct in codul widget-urilor.
Culorile se citesc cu style.color("nume") in momentul desenarii (in paintEvent),
ca sa se schimbe imediat cand utilizatorul activeaza paleta pentru daltonism.

Sectiuni si proprietari:
  - culori, fonturi, spatieri, colturi, accesibilitate -> Cosette
  - stiluri de desenare circuit (QPen/QBrush, alpha)   -> Matei (se adauga la final)
"""

# --- Scara de spatieri (multipli ai valorii de baza 4 px) -------------------
SPACING_BASE = 4
SPACING_XS = SPACING_BASE * 1   # 4  px
SPACING_S = SPACING_BASE * 2    # 8  px  - intre widget-uri din acelasi grup
SPACING_M = SPACING_BASE * 4    # 16 px  - intre panouri (grupuri diferite)
SPACING_L = SPACING_BASE * 6    # 24 px
SPACING_XL = SPACING_BASE * 8   # 32 px

# --- Colturi rotunjite --------------------------------------------------------
CORNER_RADIUS = 6       # px - porti, butoane, panouri

# --- Fonturi si font scalabil -------------------------------------------------
FONT_SIZE_MIN = 10      # pt - minimul pentru orice text din interfata
FONT_SIZE_BASE = 10     # pt - textul obisnuit la scara "Normal"
FONT_SIZE_GATE = 11     # pt - etichetele portilor la scara "Normal"

# scarile de text alese din meniul View (nume afisat, factor)
FONT_SCALES = [
    ("Normal", 1.0),
    ("Mare", 1.25),
    ("Foarte mare", 1.5),
]

# --- Paletele de culori -------------------------------------------------------
# Paleta pentru daltonism foloseste culorile Okabe-Ito, distinctibile
# pentru protanopie, deuteranopie si tritanopie.
PALETTE_NORMAL = {
    "primary": "#2a6fdb",          # actiunea principala (Run)
    "primary_text": "#ffffff",
    "gate_single": "#4a90e2",      # porti pe un qubit (H, X, Y, Z)
    "gate_controlled": "#2bb39b",  # porti controlate (CNOT)
    "gate_measure": "#7d8590",     # masurare
    "gate_text": "#ffffff",
    "invalid": "#d64545",          # plasare invalida, erori
    "highlight": "#f2b134",        # starea cea mai probabila, selectie
    "panel_border": "#c8ccd2",
    "placeholder_text": "#7a808a",
}

PALETTE_COLORBLIND = {
    "primary": "#0072b2",          # albastru
    "primary_text": "#ffffff",
    "gate_single": "#0072b2",      # albastru
    "gate_controlled": "#e69f00",  # portocaliu
    "gate_measure": "#555555",     # gri inchis
    "gate_text": "#ffffff",
    "invalid": "#d55e00",          # vermillion
    "highlight": "#f0e442",        # galben
    "panel_border": "#c8ccd2",
    "placeholder_text": "#666666",
}

# --- Variatii de culoare la interactiune -------------------------------------
GATE_HOVER_LIGHTER = 120          # % - cat de mult se deschide culoarea la hover
GATE_PRESSED_DARKER = 120         # % - cat de mult se inchide culoarea la apasare

# --- Dimensiunile portilor din paleta (al doilea criteriu: dimensiunea) --------
GATE_PADDING = SPACING_S          # spatiul dintre eticheta si marginea portii
GATE_SINGLE_WIDTH_FACTOR = 1      # poarta pe un qubit: patrat
GATE_CONTROLLED_WIDTH_FACTOR = 2  # poarta controlata: de doua ori mai lata

# --- Dimensiuni minime ale panourilor ----------------------------------------
STATISTICS_MIN_HEIGHT = 180  # px - panoul de rezultate
CIRCUIT_MIN_WIDTH = 400      # px
CIRCUIT_MIN_HEIGHT = 200     # px


# =============================================================================
# Starea curenta a aspectului (schimbata din meniul View)
# =============================================================================
_colorblindMode = False
_fontScale = 1.0


def color(name):
    """Culoarea cu numele dat din paleta activa (ex. color("gate_single"))."""
    palette = PALETTE_COLORBLIND if _colorblindMode else PALETTE_NORMAL
    return palette[name]


def isColorblindMode():
    return _colorblindMode


def setColorblindMode(enabled):
    global _colorblindMode
    _colorblindMode = bool(enabled)


def fontScale():
    return _fontScale


def setFontScale(scale):
    global _fontScale
    _fontScale = scale


def fontPointSize(baseSize=FONT_SIZE_BASE):
    """Dimensiunea in pt pentru textul de baza dat, la scara curenta, dar niciodata sub minim."""
    return max(FONT_SIZE_MIN, round(baseSize * _fontScale))


# --- Stiluri Qt construite din paleta activa ---------------------------------
def primaryButtonQss():
    """Butonul actiunii principale (Run), evidentiat."""
    return (
        f"QToolButton {{ background-color: {color('primary')}; color: {color('primary_text')};"
        f" font-weight: bold; border-radius: {CORNER_RADIUS}px;"
        f" padding: {SPACING_XS}px {SPACING_M}px; }}"
    )


def placeholderQss():
    """Panourile provizorii din mockup."""
    return (
        f"QLabel {{ border: 1px dashed {color('panel_border')}; border-radius: {CORNER_RADIUS}px;"
        f" color: {color('placeholder_text')}; }}"
    )

# =============================================================================
# Zona de circuit (Matei) - sectiune adaugata la final, nu modifica restul fisierului
# =============================================================================
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPen

CIRCUIT_MIN_COLUMNS = 8            # pasi (coloane) vizibili chiar si intr-un circuit gol
CIRCUIT_TRAILING_COLUMNS = 2       # coloane libere pastrate dupa ultima poarta plasata
CIRCUIT_WIRE_WIDTH = 2             # px - firul unui qubit
CIRCUIT_CONTROL_LINE_WIDTH = 3     # px - linia verticala si cercul tinta ale portii CNOT
CIRCUIT_GRID_WIDTH = 1             # px - separatorul dintre pasi
CIRCUIT_CURSOR_WIDTH = 2           # px - cursorul de tastatura
CIRCUIT_PREVIEW_OPACITY = 0.55     # poarta "fantoma" afisata inainte de plasare
CIRCUIT_INVALID_OPACITY = 0.30     # celula la care plasarea nu este permisa
CIRCUIT_HOVER_OPACITY = 0.10       # celula de sub mouse cand nu e aleasa nicio poarta
CIRCUIT_CONTROL_RADIUS_FACTOR = 0.14   # raza punctului de control, ca fractie din latura portii
CIRCUIT_TARGET_RADIUS_FACTOR = 0.32    # raza cercului tinta (⊕), ca fractie din latura portii

# culorile specifice circuitului; restul (porti, invalid, highlight) vin din paletele de mai sus
CIRCUIT_COLORS_NORMAL = {
    "wire": "#8a9099",
    "grid": "#e3e6ea",
    "cursor": "#2a6fdb",
}

CIRCUIT_COLORS_COLORBLIND = {
    "wire": "#555555",
    "grid": "#d9dce0",
    "cursor": "#0072b2",
}


def circuitColor(name):
    """Culoarea circuitului cu numele dat, din paleta activa."""
    palette = CIRCUIT_COLORS_COLORBLIND if _colorblindMode else CIRCUIT_COLORS_NORMAL
    return palette[name]


def wirePen():
    return QPen(QColor(circuitColor("wire")), CIRCUIT_WIRE_WIDTH)


def gridPen():
    return QPen(QColor(circuitColor("grid")), CIRCUIT_GRID_WIDTH)


def cursorPen():
    return QPen(QColor(circuitColor("cursor")), CIRCUIT_CURSOR_WIDTH, Qt.PenStyle.DashLine)