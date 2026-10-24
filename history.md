# Istoricul proiectului

Evoluția proiectului, pas cu pas: ce s-a făcut, de cine, în ce commit și când a ajuns pe GitHub.
Fișierul este scris pentru membrii echipei și pentru agenții AI care continuă lucrul.

Surse: `git log` (toate commit-urile din `main`) și reflog-ul copiei locale a lui Mihai (push-uri și pull-uri).
Commit-urile cu mesaje vagi („modificare”, „ceva”) sunt descrise după conținutul lor real.

---

## Pe scurt (la 24.10.2026)

- **Tema:** simulator de circuite cuantice (până la 5 qubiți), cu interfață grafică în **Python + PySide6**.
  Repository-ul se numește încă `proiect_piu_simulator_de_particule`, de la tema inițială (vezi commit-ul `3bbcaf4`).
- **Repository:** `github.com/MihaiBandur/proiect_piu_simulator_de_particule`, un singur branch: `main`.
- **Ultimul commit de pe GitHub:** `02d37b2` (22.10.2026). Peste el există **modificări necomise** importante, descrise în [Etapa 5](#etapa-5--reparări-și-modelul-mvc-24-octombrie-2026-necomis).
- **Ce funcționează (cu modificările necomise):** plasarea porților prin clic și drag & drop, ștergerea, undo/redo,
  numărul de qubiți, starea inițială |0⟩/|1⟩, Run (rezultatele apar provizoriu în bara de stare).
- **Ce lipsește:** histograma și tabelul de rezultate, salvarea și încărcarea, mutarea porților cu mouse-ul, logarea.

### Echipa

Împărțirea sarcinilor vine din documentul „Organizare PIU.pdf” (nu este în repository), unde membrii apar cu alte nume.

| Persoană | Identitate în git | Nume în PDF | Responsabilități | Unde lucrează |
| --- | --- | --- | --- | --- |
| Bandur Mihai | `MihaiBandur` | Miami | modelul, simularea, rezultatele (histogramă, tabel), undo/redo, salvare, logare | `circuit/`, `simulation/`, `main.py` |
| Mardare Matei | `mateimardare` | Maitreyi | zona de circuit (desenare, mouse, drag & drop) | `ui/circuit_view.py` |
| Lupu Cosette | `Cosette`, `Cosette195` | Cosette | fereastra principală, paleta de porți, dialogurile, ghidul de stil | `ui/`, `docs/` |

Matei a scris și prima versiune a logicii (`circuit/`, `simulation/`) și diagrama UML inițială (Etapa 2).

---

## Cronologie

### Etapa 1 — Pornirea repository-ului (1–8 octombrie 2026)

| Commit | Data | Autor | Mesaj | Ce conține |
| --- | --- | --- | --- | --- |
| `f8b0922` | 01.10 12:28 | MihaiBandur | first commit | `README.md` cu tema inițială, „proiect_piu_simulator_de_particule” |
| `3bbcaf4` | 07.10 15:20 | Cosette195 | Rename project from particle simulator to quantum circuit | tema se schimbă în circuit cuantic (`README.md`) |
| `3051bd8` | 08.10 12:50 | mateimardare | Initial commit | `README.md` într-un istoric separat, creat local de Matei (a doua rădăcină a istoricului) |
| `36e30cd` | 08.10 12:56 | MihaiBandur | version 0.1 | `.gitignore` (Python, Qt, macOS), `history.md` gol, `requirments.txt` (PySide6), `main.py` cu exemplul „Hello World” din PySide6 |
| `ff526d4` | 08.10 12:57 | mateimardare | Merge branch 'main' of github.com:… | unește istoricul lui Matei (`3051bd8`) cu cel de pe GitHub |
| `554486b` | 08.10 13:11 | Cosette | modificare | `.gitignore`: ignoră folderul `piu/` (mediul virtual) |

Observație: istoricul are două commit-uri fără părinte (`f8b0922` și `3051bd8`), unite prin merge-ul `ff526d4`.

### Etapa 2 — Diagrama UML și logica de simulare (10 octombrie 2026, Matei)

| Commit | Data | Autor | Mesaj | Ce conține |
| --- | --- | --- | --- | --- |
| `7a6c2c2` | 10.10 20:47 | mateimardare | diagrama uml pentru proiect -- pentru inceput | `diagram.uml` (PlantUML): pachetele GUI, Circuit, Simulation, Statistics, gândite pentru PyQt6 |
| `e93b54d` | 10.10 20:48 | mateimardare | Merge branch 'main' of github.com:… | aduce commit-ul `554486b` al lui Cosette |
| `0916772` | 10.10 21:56 | mateimardare | o implementare a logicii (urmeaza si gui-ul) dupoa diagrama uml initiala | `quantum_simulator.py`: prototip complet într-un singur fișier, pe **PyQt6** (571 de linii); `simulation/matrix.py`, `simulation/simulator.py`, `simulation/simulation_result.py`; fereastra din `main.py` mărită la 1200 × 800 |
| `0f1ca56` | 10.10 22:09 | mateimardare | si un mic test de verificare a modulelor; urmeaza testarea logicii | `circuit/gate.py` (H, X, Y, Z, CNOT, `GATE_TYPES`), `circuit/quantum_circuit.py`, `circuit/qubit.py`, `dependencies.py` (importuri comune, inclusiv PyQt6), `test_logic.py` (doar importuri); `quantum_simulator.py` adăugat în `.gitignore` |

Consecințe descoperite mai târziu (reparate în Etapa 5):
- `dependencies.py` importa PyQt6, deci modelul nu se putea importa în proiectul bazat pe PySide6.
- `quantum_simulator.py` a fost pus în `.gitignore`, dar era deja urmărit de git, așa că regula nu avea efect.

### Etapa 3 — Interfața: fereastra, paleta, dialogurile, stilul (15 octombrie 2026, Cosette)

| Commit | Data | Autor | Mesaj | Ce conține |
| --- | --- | --- | --- | --- |
| `7f738a6` | 15.10 12:20 | Cosette | Fereastra principala si folderul ui | `ui/main_window.py`: scheletul ferestrei (meniuri, toolbar cu Run / qubiți / Clear, panourile Operations, Q Circuit, Statistics ca placeholder-e); `ui/style.py`; `main.py` pornește `MainWindow`; `.vscode/settings.json` |
| `52fec05` | 15.10 12:31 | Cosette | Paleta de porti | `ui/gate_palette.py`: `GateButton` (derivat din `QAbstractButton`), porțile grupate după rol, drag cu `QDrag` și tipul MIME `application/x-quantum-gate` |
| `6935e19` | 15.10 12:38 | Cosette | Dialoguri si legarea actiunilor | confirmarea la închidere (Save / Discard / Cancel), confirmarea la golire, dialogurile Open/Save, semnalele ferestrei către model |
| `6489b18` | 15.10 12:45 | Cosette | Ghidul de stil | `ui/style.py`: culori, paletă pentru daltonism (Okabe-Ito), scara de spațieri, minim 10 pt, font scalabil (meniul View); `docs/glosar.md` |
| `de3eff3` | 15.10 13:10 | Cosette | Testul de redimensionare si diagrama ierarhiei de widgeturi | `docs/test_redimensionare.md` cu capturi; paleta trece de la `Fixed` la `Preferred` (titlurile erau tăiate la font mare); `docs/capturi/ierarhie_widgeturi.png` și `docs/ierarhie_widgeturi.dot` (din greșeală, `.dot` conținea textul testului) |

### Etapa 4 — Zona de circuit (22 octombrie 2026, Matei)

| Commit | Data | Autor | Mesaj | Ce conține |
| --- | --- | --- | --- | --- |
| `02d37b2` | 22.10 12:08 | mateimardare | ceva | `ui/circuit_view.py` (551 de linii): `CircuitView`, desenat în `paintEvent`, cu grilă, fire, porți, CNOT, hover, previzualizare, drag & drop, tastatură, `sizeHint`; stilurile de desenare în `ui/style.py`; zona de circuit înlocuiește placeholder-ul din `MainWindow` |

Starea după acest commit: interfața arăta circuitul, dar porțile nu se puteau plasa.
Zona de circuit trimitea cererea `gatePlaceRequested`, însă nu exista încă un model care s-o primească.

### Etapa 5 — Reparări și modelul MVC (24 octombrie 2026, necomis)

Lucru făcut de Mihai împreună cu Claude Code. **Nu este încă în niciun commit.**

**Reparări de bug-uri:**
1. `circuit/gate.py` și `circuit/quantum_circuit.py` importă direct din biblioteca standard. `dependencies.py` (care importa PyQt6) a fost șters.
2. `QuantumCircuit.addGate()` respinge porțile invalide (`isValidGate()`): qubiți inexistenți, CNOT cu controlul egal cu ținta, număr greșit de qubiți, coloană negativă.
   Înainte, unele dintre ele opreau simularea cu eroare (`negative shift count`) sau dădeau probabilități cu suma 0.
3. `setQubitCount()` și constructorul aruncă `ValueError` în afara intervalului 1–5. Limitele sunt constante: `MIN_QUBITS`, `MAX_QUBITS`, `DEFAULT_QUBITS`.
4. Măsurarea („M”, `MeasureGate`) există acum și în `GATE_TYPES`, nu doar în paletă.
   Simulatorul o tratează cu proiectori, separând starea în ramuri, deci e corectă și la mijlocul circuitului.
   `SimulationResult.getState()` întoarce `None` când rezultatul măsurării nu e sigur.
5. `MainWindow`: Save, Save As și Open schimbă fișierul curent și anunță succesul doar după confirmarea modelului (`fileSaved()`, `fileOpened()`).
   Înainte, mesajul „salvat” apărea chiar dacă salvarea eșua, iar aplicația se putea închide pierzând modificările.
6. `MainWindow.setQubitCount()`: slot nou, prin care modelul actualizează spinbox-ul fără să retrimită cererea.
7. `CircuitView`: swipe-ul orizontal pe trackpad derulează circuitul; Delete șterge doar poarta din celula cursorului; valorile fixe din cod au devenit constante (`style.CIRCUIT_CONTROL_LINE_WIDTH`).
8. `requirments.txt` → `requirements.txt`; `quantum_simulator.py` scos din git (rămâne pe disc și e ignorat); `docs/ierarhie_widgeturi.dot` refăcut ca sursă Graphviz.

**Modelul MVC (sarcinile lui Mihai):**
- `circuit/circuit_model.py` (nou): `CircuitModel`, derivat din `QObject`.
  - **Semnale:** `gateAdded`, `gateRemoved`, `gateMoved`, `circuitReset`, `qubitCountChanged`, `initialStateChanged`, `modifiedChanged`, `validationError(poartă, mesaj)`, `resultsReady`.
  - **Comenzi:** `addGate`, `removeGate`, `moveGate`, `clear`, `setQubitCount`, `setInitialState`, `toggleInitialState`, `newCircuit`, `undo`, `redo`, `run`.
  - Toate modificările trec prin `QUndoStack`, fiecare operație fiind un pas de undo.
- `main.py`: funcția `connectModel()` leagă modelul de fereastră și de zona de circuit, doar prin semnale și sloturi.
  Funcția `showResultsPreview()` afișează provizoriu rezultatele în bara de stare, până la histogramă.
- `test_logic.py`: teste reale pentru qubit, matrice, porți, circuit, simulator și model.
  Rezultat: 6/6 cu PySide6 instalat (fără PySide6 trec 5/6). Interfața a fost verificată separat, fără fereastră vizibilă (`offscreen`), cu scripturi temporare care nu sunt în repository.

**Modificări locale care nu fac parte din sesiunea cu Claude Code:**
- `.vscode/settings.json`: mediul Python din VS Code, schimbat din conda în Python de sistem + pip.
- `requirements.txt`: linia `PyQt6` a fost activată. Aplicația nu mai folosește PyQt6; o folosește doar prototipul vechi `quantum_simulator.py`.

**Fișiere atinse:** nou `circuit/circuit_model.py`; modificate `circuit/gate.py`, `circuit/quantum_circuit.py`, `simulation/simulator.py`, `simulation/simulation_result.py`, `main.py`, `test_logic.py`, `ui/main_window.py`, `ui/circuit_view.py`, `ui/style.py`, `docs/ierarhie_widgeturi.dot`, `history.md`; șterse `dependencies.py` și `quantum_simulator.py` (doar din git); redenumit `requirments.txt`.
Fișierele din `ui/` aparțin lui Cosette și lui Matei, deci trebuie anunțați înainte de commit.

---

## Push-uri și pull-uri

Git nu păstrează pe server cine și când a făcut push. Tabelul vine din reflog-ul copiei locale a lui Mihai.
Pentru commit-urile colegilor, push-ul lor a avut loc între data commit-ului și pull-ul în care apar.

| Data | Operație | `main` după operație | Ce a adus |
| --- | --- | --- | --- |
| 08.10 12:26 | clone de pe GitHub | `3bbcaf4` | `f8b0922`, `3bbcaf4` |
| 08.10 12:56 | **push** (Mihai) | `36e30cd` | trimite pe GitHub „version 0.1” |
| 08.10 13:12 | pull | `554486b` | `3051bd8`, `ff526d4` (Matei), `554486b` (Cosette) |
| 15.10 12:07 | pull | `0f1ca56` | `7a6c2c2`, `e93b54d`, `0916772`, `0f1ca56` (Matei, 10.10) |
| 15.10 12:22 | pull | `7f738a6` | `7f738a6` (Cosette) |
| 15.10 12:39 | pull | `6935e19` | `52fec05`, `6935e19` (Cosette) |
| 15.10 13:23 | pull | `de3eff3` | `6489b18`, `de3eff3` (Cosette) |
| 22.10 12:08 | pull | `02d37b2` | `02d37b2` (Matei) |

Toate pull-urile au fost fast-forward. La 24.10.2026, `main` local și `origin/main` erau la același commit, `02d37b2`.

---

## Unde se află lucrurile acum

| Fișier | Rol |
| --- | --- |
| `main.py` | pornește aplicația și leagă modelul de interfață (`connectModel`) |
| `circuit/circuit_model.py` | modelul MVC: semnale, comenzi, validare, undo/redo, Run |
| `circuit/quantum_circuit.py`, `circuit/qubit.py`, `circuit/gate.py` | structura circuitului, `GATE_TYPES`, limitele numărului de qubiți |
| `simulation/` | `Matrix`, `Simulator` (vectori de stare, măsurare prin proiectori), `SimulationResult` |
| `ui/main_window.py` | fereastra principală: meniuri, toolbar, dialoguri, bara de stare |
| `ui/gate_palette.py` | paleta de porți, `GATE_MIME_TYPE`, `PALETTE_GATES` |
| `ui/circuit_view.py` | zona de circuit |
| `ui/style.py` | ghidul de stil (culori, fonturi, spațieri, stiluri de desenare) |
| `docs/` | glosarul, testul de redimensionare, diagrama ierarhiei de widget-uri |
| `diagram.uml` | diagrama UML inițială; **învechită** (PyQt6, clasele vechi `CircuitWidget`, `GatesWidget`) |
| `test_logic.py` | testele logicii și ale modelului (`python test_logic.py`) |

Contractele dintre componente (semnale, sloturi, formatul datelor) sunt descrise în docstring-ul de la începutul fiecărui modul:
`circuit/circuit_model.py`, `ui/circuit_view.py`, `ui/gate_palette.py`, `ui/main_window.py`.

---

## Ce a rămas de făcut

- **Mihai:**
  - histograma (`paintEvent`, `QRectF`, etichete în hexa rotite, maximul evidențiat, `sizeHint`) și tabelul, într-un `QStackedWidget`;
  - salvarea și încărcarea, inclusiv validarea fișierelor corupte; după o salvare reușită se apelează `model.setModified(False)` și `window.fileSaved(path)`;
  - logarea: timpul de construire a circuitului, numărul de erori și numărul de undo-uri;
  - convențiile Qt în clasele vechi (`getGates()`, `getState()` etc.);
  - documentarea: UML actualizat, diagrama de secvență, chestionarul, testele la scalare.
- **Matei:**
  - mutarea porților cu mouse-ul (comanda `moveGate` există deja în model);
  - simbolul de măsurare și linia clasică;
  - porțile desenate în coordonate locale (`save`/`translate`/`restore`);
  - tooltip pe porțile din circuit;
  - evidențierea porții primite prin `validationError`;
  - stilurile `QPen` cerute (linie clasică, `DashLine`, `RoundCap`).
- **Cosette:**
  - iconițe SVG;
  - dialoguri cu `QFormLayout`;
  - diacritice în textele din interfață, ca în glosar;
  - justificarea designului în raport;
  - refacerea testului de redimensionare după integrare.
- **Toți:** câte un branch pentru fiecare persoană (acum toată lumea lucrează pe `main`) și șablonul raportului.

---

## Cum se actualizează acest fișier

- După fiecare commit sau push, adaugă un rând în etapa curentă: hash, dată, autor, mesaj și **ce conține de fapt**.
- O etapă nouă începe când se schimbă direcția lucrului, de exemplu „Histograma”.
- Când modificările necomise din Etapa 5 ajung într-un commit, trece hash-ul lui în titlul etapei și scoate mențiunea „necomis”.
- Actualizează secțiunea „Pe scurt” când se schimbă ce funcționează sau ce lipsește.
- **Pentru agenți AI:**
  - citește întâi „Pe scurt” și ultima etapă;
  - verifică apoi ce s-a schimbat după ultimul hash menționat aici, cu `git log <hash>..HEAD`;
  - nu considera adevărat ce scrie aici fără să verifici în cod.
