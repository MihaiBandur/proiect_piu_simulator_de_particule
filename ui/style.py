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
PALETTE_MIN_WIDTH = 160      # px - paleta de porti
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