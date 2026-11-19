# Testul de redimensionare a ferestrei

## Metoda

Fereastra a fost micsorata pana la dimensiunea minima permisa, la fiecare dintre cele trei marimi de text din meniul View (Normal, Mare, Foarte mare).
La fiecare pas s-a verificat:

- daca apare text trunchiat;
- daca se suprapun widget-uri;
- daca dispar panouri sau actiuni din toolbar.

## Primul test: paleta de porti

Stadiu testat: fereastra principala cu paleta de porti; zona de circuit si histograma erau inca provizorii.

| Marime text | Dimensiune minima | Problema gasita |
| --- | --- | --- |
| Normal | 573 × 506 px | – |
| Mare | 596 × 517 px | – |
| Foarte mare | 608 × 531 px (inainte) | titlurile grupurilor din paleta sunt taiate („Porti pe un qub…”) |
| Foarte mare | 626 × 531 px (dupa) | – |

Capturi: `capturi/redimensionare_inainte.png` si `capturi/redimensionare_dupa.png`.

**Cauza.** Panoul paletei avea politica de dimensiune `Fixed` si o latime minima fixa, setata cu `setMinimumWidth(160)`.
O latime minima setata explicit inlocuieste minimul pe care layout-ul il calculeaza din continut.
Cand textul a crescut, panoul a ramas la 160 px, iar etichetele au fost taiate.
Este aceeasi situatie ca exemplul din curs cu butonul taiat de `setFixedWidth`.

**Corectura.**

- politica orizontala a panoului a devenit `Preferred`;
- latimea minima fixa a fost eliminata, iar minimul se calculeaza acum din continut (`minimumSizeHint()`);
- spatiul liber merge in continuare la zona de circuit, care are factor de intindere 1.

## Al doilea test: aplicatia integrata

Stadiu testat: toate panourile reale (paleta cu Toffoli, zona de circuit, histograma si tabelul), cu 3 si cu 5 qubiti.

| Marime text | Dimensiune minima | Text taiat | Zona de circuit la minim |
| --- | --- | --- | --- |
| Normal | 573 × 506 px | – | 378 × 159 px |
| Mare | 596 × 518 px | – | 378 × 155 px |
| Foarte mare | 626 × 566 px | – | 378 × 151 px |

Capturi: `capturi/redimensionare_minim_5qubiti.png` (minim, text Foarte mare) si `capturi/redimensionare_pornire_5qubiti.png` (fereastra de pornire, 1100 × 720 px).

**Rezultate.**

- Nu apare text taiat si nu se suprapun widget-uri la nicio marime de text; paleta isi pastreaza latimea calculata din continut (125, 148, respectiv 178 px).
- Circuitul si histograma nu se taie: cand nu incap, apar bare de derulare (zona de circuit si histograma cu 32 de stari).
- La dimensiunea minima, zona de circuit arata doar circa un qubit, restul se vede prin derulare.
- Chiar la fereastra de pornire, cu 5 qubiti, zona de circuit primeste 272 px in inaltime, desi are nevoie de 382 px; q4 se vede doar prin derulare. Cauza: panoul Statistics isi pastreaza mereu inaltimea preferata (circa 284 px), chiar si cand histograma are spatiu liber.

## Concluzie

Dimensiunea minima a ferestrei nu se fixeaza manual cu o valoare constanta: ea rezulta din `minimumSizeHint()`-ul panourilor si se adapteaza la marimea textului (intre 573 × 506 si 626 × 566 px).
Fereastra porneste la 1100 × 720 px.

De rezolvat: impartirea spatiului vertical intre zona de circuit si panoul Statistics, astfel incat un circuit cu 5 qubiti sa incapa fara derulare la fereastra de pornire.