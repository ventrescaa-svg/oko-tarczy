# Model AI grota

Mała sieć (U-Net, ok. 0,7 mln wag, 2,8 MB) wskazuje grot na wycinku „przed/po” z eksportu Nauka AI.
W aplikacji: `model/grot.onnx`, uruchamiany przez onnxruntime-web (CDN jsdelivr, wersja 1.29.0), `aiRun`/`aiDart` w `oko-tarczy.html`.

Wejście: 9 kanałów 256×384 (RGB przed, RGB po, po − przed, wartości 0..1), wycinek w lewym górnym rogu, reszta zera.
Wyjście `heat` 128×192 (co 2 px): punkt = najwyższa wartość w obszarze wycinka, dokładniej średnia ważona w oknie 5×5;
pewność = część całej masy (softmax) w oknie 7×7 wokół szczytu.

Nauka od nowa (PyTorch z PyPI, na procesorze ok. 90 s na przebieg):
```
python3 narzedzia/rozpakuj.py cz1.zip cz2.zip cz3.zip /tmp/rz
python3 narzedzia/model_ai/prep.py /tmp/rz /tmp/dane.npz
FOLD=4/5 EP=10 python3 narzedzia/model_ai/train.py /tmp/dane.npz      # sprawdzian: ostatnia 1/5 rzutów (po czasie)
ALL=1 EP=20 SAVE=/tmp/grot.pt python3 narzedzia/model_ai/train.py /tmp/dane.npz
python3 narzedzia/model_ai/export.py /tmp/grot.pt model/grot.onnx     # potem podbić ?v= w AI_MODEL
```
Cel nauki: `label.tip` (ostateczne miejsce grota: po stuknięciu, inaczej to, co policzyła aplikacja). Poprawione stuknięciem mają wagę 3.
