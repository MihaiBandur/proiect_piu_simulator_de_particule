"""
Ghidul de stil al aplicatiei (schelet cu valori provizorii).
 
Regula comuna: culorile, fonturile si spatierile se iau DOAR de aici,
nu se scriu direct in codul widget-urilor.
Sectiuni si proprietari:
  - culori, fonturi, spatieri, colturi  -> Cosette
  - stiluri de desenare circuit (QPen/QBrush, alpha) -> Matei (se adauga mai jos)
"""
 
# --- Scara de spatieri (multipli ai valorii de baza 4 px) -------------------
SPACING_BASE = 4
SPACING_XS = SPACING_BASE * 1   # 4  px
SPACING_S = SPACING_BASE * 2    # 8  px  - intre widget-uri din acelasi grup
SPACING_M = SPACING_BASE * 4    # 16 px  - intre panouri (grupuri diferite)
SPACING_L = SPACING_BASE * 6    # 24 px
SPACING_XL = SPACING_BASE * 8   # 32 px
 
# --- Fonturi -----------------------------------------------------------------
FONT_SIZE_MIN = 10      # pt - minimul pentru orice text din interfata
FONT_SIZE_NORMAL = 11   # pt
FONT_SIZE_TITLE = 12    # pt - titlurile panourilor
 
# --- Colturi rotunjite --------------------------------------------------------
CORNER_RADIUS = 6       # px - porti, butoane, panouri
 
# --- Paleta de culori (provizorie) -------------------------------------------
COLOR_PRIMARY = "#2a6fdb"        # actiunea principala (Run), porti pe un qubit
COLOR_PRIMARY_TEXT = "#ffffff"
COLOR_PANEL_BORDER = "#c8ccd2"   # conturul panourilor
COLOR_PLACEHOLDER_TEXT = "#7a808a"
 
# --- Dimensiuni minime ale panourilor (provizorii) ---------------------------
PALETTE_MIN_WIDTH = 160      # px - paleta de porti
STATISTICS_MIN_HEIGHT = 180  # px - panoul de rezultate
CIRCUIT_MIN_WIDTH = 400      # px
CIRCUIT_MIN_HEIGHT = 200     # px
 
# --- Stil pentru butonul principal (Run) --------------------------------------
PRIMARY_BUTTON_QSS = (
    f"QToolButton {{ background-color: {COLOR_PRIMARY}; color: {COLOR_PRIMARY_TEXT};"
    f" font-weight: bold; border-radius: {CORNER_RADIUS}px;"
    f" padding: {SPACING_XS}px {SPACING_M}px; }}"
)
 
# --- Stil pentru panourile provizorii (doar pentru mockup) --------------------
PLACEHOLDER_QSS = (
    f"QLabel {{ border: 1px dashed {COLOR_PANEL_BORDER}; border-radius: {CORNER_RADIUS}px;"
    f" color: {COLOR_PLACEHOLDER_TEXT}; }}"
)
 

