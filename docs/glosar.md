# Glosar de terminologie

Termenii de mai jos se folosesc **exact la fel** in toata interfata (meniuri, tooltip-uri, mesaje, bara de stare) si in raport.
Daca ai nevoie de un termen nou, adauga-l aici inainte sa-l folosesti in cod.

| Termen in interfata | Inseamna | Nu folosi |
| --- | --- | --- |
| qubit / qubiti | unitatea de informatie cuantica; un fir orizontal in circuit | bit cuantic, fir, linie |
| poarta / porti | operatia aplicata pe unul sau mai multi qubiti (H, X, Y, Z, CNOT, Toffoli) | operator, gate, bloc |
| poarta pe un qubit | H, X, Y, Z | poarta simpla |
| poarta controlata | CNOT (un qubit de control) si Toffoli (doi qubiti de control), fiecare cu un qubit tinta | poarta dubla, poarta tripla |
| qubit de control | qubitul care decide daca se aplica operatia | sursa |
| qubit tinta | qubitul asupra caruia se aplica operatia | destinatie |
| masurare | operatia care citeste un qubit si da 0 sau 1 | citire, measure |
| linie clasica | firul dublu desenat dupa o masurare, pana la urmatoarea poarta de pe acelasi qubit: qubitul are atunci o valoare sigura, 0 sau 1 | fir dublu, bit clasic |
| pas | o coloana a circuitului; portile de pe acelasi pas se aplica in acelasi timp | coloana, moment |
| circuit nou | circuitul gol creat din File > Nou, cu numarul de qubiti si starile initiale alese in dialog | proiect nou, document nou |
| circuit | ansamblul de qubiti si porti construit de utilizator | schema, diagrama |
| stare initiala | valoarea de pornire a unui qubit: \|0⟩ sau \|1⟩ | valoare initiala |
| simulare | calculul rezultatelor circuitului (butonul Run) | rulare, executie |
| rezultate | probabilitatile starilor obtinute dupa simulare | output, statistici |
| stare | o combinatie posibila de valori ale qubitilor, afisata in hexazecimal | combinatie, valoare |
| probabilitate | sansa unei stari, afisata in procente | frecventa |
| paleta de porti | panoul Operations din stanga | meniul de porti, toolbox |
| zona de circuit | panoul Q Circuit | canvas, editor |

## Actiuni (verbele din meniuri si mesaje)

| Actiune | Termen folosit |
| --- | --- |
| adauga o poarta in circuit | „trage” (drag) sau „plaseaza” |
| scoate o poarta | „sterge” |
| scoate toate portile | „goleste circuitul” |
| anuleaza ultima actiune | „Anuleaza” (Ctrl+Z) |
| refa actiunea anulata | „Refa” (Ctrl+Y) |
| salveaza in fisier | „Salveaza” / „Salveaza ca...” |
| incarca din fisier | „Deschide...” |

## Numele portilor (aceleasi in paleta, tooltip-uri si raport)

| Simbol | Nume |
| --- | --- |
| H | Hadamard |
| X | Pauli-X |
| Y | Pauli-Y |
| Z | Pauli-Z |
| CX | CNOT |
| CCX | Toffoli |
| M | Masurare |