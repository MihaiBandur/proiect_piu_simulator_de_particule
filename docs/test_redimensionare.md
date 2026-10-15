# Testul de redimensionare a ferestrei

**Responsabil:** Lupu Cosette
**Stadiu testat:** fereastra principală cu paleta de porți; zona de circuit și histograma sunt încă provizorii.

## Metodă

Fereastra a fost micșorată până la dimensiunea minimă permisă, la fiecare dintre cele trei mărimi de text din meniul View (Normal, Mare, Foarte mare).
La fiecare pas s-a verificat:

- dacă apare text trunchiat;
- dacă se suprapun widget-uri;
- dacă dispar panouri sau acțiuni din toolbar.

## Rezultate

| Mărime text | Dimensiune minimă | Problemă găsită |
| --- | --- | --- |
| Normal | 573 × 506 px | – |
| Mare | 596 × 517 px | – |
| Foarte mare | 608 × 531 px (înainte) | titlurile grupurilor din paletă sunt tăiate („Porti pe un qub…”) |
| Foarte mare | 626 × 531 px (după) | – |

Capturi: `capturi/redimensionare_inainte.png` și `capturi/redimensionare_dupa.png`.

## Cauza problemei

Panoul paletei avea politica de dimensiune `Fixed` și o lățime minimă fixă, setată cu `setMinimumWidth(160)`.
O lățime minimă setată explicit înlocuiește minimul pe care layout-ul îl calculează din conținut.
Când textul a crescut, panoul a rămas la 160 px, iar etichetele au fost tăiate.
Este aceeași situație ca exemplul din curs cu butonul tăiat de `setFixedWidth`.

## Corectura

- politica orizontală a panoului a devenit `Preferred`;
- lățimea minimă fixă a fost eliminată, iar minimul se calculează acum din conținut (`minimumSizeHint()`);
- spațiul liber merge în continuare la zona de circuit, care are factor de întindere 1.

## Concluzie: dimensiunea minimă a ferestrei

Dimensiunea minimă nu se fixează manual cu o valoare constantă.
Ea rezultă din layout-uri, din `minimumSizeHint()`-ul fiecărui panou, și se adaptează la mărimea textului aleasă (între 573 × 506 și 626 × 531 px în stadiul actual).
Fereastra pornește la 1100 × 720 px.

**De refăcut testul** după integrarea zonei de circuit (Matei) și a histogramei (Mihai).
Atunci minimul va fi dat în special de circuitul cu 5 qubiți și de histograma cu 32 de bare.