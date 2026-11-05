# Glosar de terminologie

Termenii de mai jos se folosesc **exact la fel** în toată interfața (meniuri, tooltip-uri, mesaje, bara de stare) și în raport.
Dacă ai nevoie de un termen nou, adaugă-l aici înainte să-l folosești în cod.

| Termen în interfață | Înseamnă | Nu folosi |
| --- | --- | --- |
| qubit / qubiți | unitatea de informație cuantică; un fir orizontal în circuit | bit cuantic, fir, linie |
| poartă / porți | operația aplicată pe unul sau mai mulți qubiți (H, X, Y, Z, CNOT, Toffoli) | operator, gate, bloc |
| poartă pe un qubit | H, X, Y, Z | poartă simplă |
| poartă controlată | CNOT (un qubit de control) și Toffoli (doi qubiți de control), fiecare cu un qubit țintă | poartă dublă, poartă triplă |
| qubit de control | qubitul care decide dacă se aplică operația | sursă |
| qubit țintă | qubitul asupra căruia se aplică operația | destinație |
| măsurare | operația care citește un qubit și dă 0 sau 1 | citire, measure |
| linie clasică | firul dublu desenat după o măsurare, până la următoarea poartă de pe același qubit: qubitul are atunci o valoare sigură, 0 sau 1 | fir dublu, bit clasic |
| pas | o coloană a circuitului; porțile de pe același pas se aplică în același timp | coloană, moment |
| circuit nou | circuitul gol creat din File > Nou, cu numărul de qubiți și stările inițiale alese în dialog | proiect nou, document nou |
| circuit | ansamblul de qubiți și porți construit de utilizator | schemă, diagramă |
| stare inițială | valoarea de pornire a unui qubit: \|0⟩ sau \|1⟩ | valoare inițială |
| simulare | calculul rezultatelor circuitului (butonul Run) | rulare, execuție |
| rezultate | probabilitățile stărilor obținute după simulare | output, statistici |
| stare | o combinație posibilă de valori ale qubiților, afișată în hexazecimal | combinație, valoare |
| probabilitate | șansa unei stări, afișată în procente | frecvență |
| paleta de porți | panoul Operations din stânga | meniul de porți, toolbox |
| zona de circuit | panoul Q Circuit | canvas, editor |

## Acțiuni (verbele din meniuri și mesaje)

| Acțiune | Termen folosit |
| --- | --- |
| adaugă o poartă în circuit | „trage” (drag) sau „plasează” |
| scoate o poartă | „șterge” |
| scoate toate porțile | „golește circuitul” |
| anulează ultima acțiune | „Anulează” (Ctrl+Z) |
| refă acțiunea anulată | „Refă” (Ctrl+Y) |
| salvează în fișier | „Salvează” / „Salvează ca...” |
| încarcă din fișier | „Deschide...” |

## Numele porților (aceleași în paletă, tooltip-uri și raport)

| Simbol | Nume |
| --- | --- |
| H | Hadamard |
| X | Pauli-X |
| Y | Pauli-Y |
| Z | Pauli-Z |
| CX | CNOT |
| CCX | Toffoli |
| M | Măsurare |