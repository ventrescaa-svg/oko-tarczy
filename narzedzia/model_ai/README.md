# Model AI grota

Mała sieć (U-Net, ok. 0,7 mln wag, 2,8 MB) wskazuje grot na wycinku „przed/po” z eksportu Nauka AI.
W aplikacji: `model/grot.onnx`, uruchamiany przez onnxruntime-web (CDN jsdelivr, wersja 1.29.0), `aiRun`/`aiDart` w `oko-tarczy.html`.

Wejście: 9 kanałów 256×384 (RGB przed, RGB po, po − przed, wartości 0..1), wycinek w lewym górnym rogu, reszta zera.
Wyjście `heat` 128×192 (co 2 px): punkt = najwyższa wartość w obszarze wycinka, dokładniej średnia ważona w oknie 5×5;
pewność = część całej masy (softmax) w oknie 7×7 wokół szczytu.

Nauka od nowa (PyTorch z PyPI, na procesorze ok. 90 s na przebieg):
```
BEZ_PELNYCH=1 python3 narzedzia/rozpakuj.py cz1.zip cz2.zip cz3.zip /tmp/rz   # bez całych obrazów z 26d (niepotrzebne do nauki)
python3 narzedzia/model_ai/prep.py /tmp/rz /tmp/dane.npz
FOLD=4/5 EP=10 python3 narzedzia/model_ai/train.py /tmp/dane.npz      # sprawdzian: ostatnia 1/5 rzutów (po czasie)
FOLD=4/5 LOAD=stary.pt python3 narzedzia/model_ai/train.py /tmp/dane.npz # ten sam sprawdzian dla obecnego modelu
ALL=1 EP=20 SAVE=/tmp/grot.pt python3 narzedzia/model_ai/train.py /tmp/dane.npz
python3 narzedzia/model_ai/export.py /tmp/grot.pt model/grot.onnx     # potem podbić ?v= w AI_MODEL
```
Cel nauki: `label.tip` (ostateczne miejsce grota: po stuknięciu, inaczej to, co policzyła aplikacja). Poprawione stuknięciem mają wagę 3.

## Klasówka: stały sprawdzian (od 2026-10-31)
Co czwarta tura rzucona po nauce modelu v3 (ts > `KL_OD`, paczka 20261029-2123) jest na zawsze w klasówce (`klasowka.py`, wybór po czasie tury, więc zawsze ten sam).
`train.py` nigdy nie uczy na klasówce (też przy `ALL=1` i `FOLD`), a `KLASOWKA=1` ocenia na niej. Dane trzeba przygotować nowym `prep.py` (znacznik `hold`).
```
python3 narzedzia/model_ai/klasowka.py /tmp/rz                                   # ile rzutów w klasówce
KLASOWKA=1 LOAD=stary.pt OUT=/tmp/stary.json python3 narzedzia/model_ai/train.py /tmp/dane.npz
KLASOWKA=1 LOAD=/tmp/grot.pt OUT=/tmp/nowy.json python3 narzedzia/model_ai/train.py /tmp/dane.npz
python3 narzedzia/model_ai/porownaj_modele.py /tmp/stary.json /tmp/nowy.json    # kod 0 = można wgrać
```
Liczą się tylko rzuty sprawdzone przez gracza: pole przy „tap” i „confirmed”, milimetry tylko przy „tap”.
Przy „auto” i „confirmed” punkt etykiety to punkt aplikacji (od 29a zwykle punkt modelu), więc obecny model ma tam błąd ≈ 0 mm sam ze sobą.
Do ok. 100 sprawdzonych rzutów klasówka jest informacyjna; potem nowy model wgrywa się tylko, gdy na klasówce ma co najmniej tyle dobrych pól co stary i mediana mm przy stuknięciach nie gorsza o więcej niż 0,2 mm.
30.10 (51 rzutów): w klasówce 10 (7 sprawdzonych), v3 6/7, v2 6/7, mm przy stuknięciach 2,6 vs 3,1 (2 stuknięcia).

Kamera z lewej strony (`cal.side = "left"`, od 31.10): `prep.py` odbija wycinek w poziomie (ref, cur, x grota → w−1−x) i dokłada to odbicie do `Hc`, więc model zawsze widzi rzutkę jak z prawej, a ocena w `train.py` działa bez zmian. Paczka 20261031-1108 (16 rzutów z lewej): v3 na odbitych 11/11 sprawdzonych, mediana 2,0 mm.
