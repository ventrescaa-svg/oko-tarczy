# Oko Tarczy – kontekst projektu (stan na 2026-10-17)

Aplikacja do automatycznego liczenia punktów w darta (501/301/701) kamerą telefonu, w stylu Dartsmind.
Rozmawiamy po polsku, prosto, bez żargonu. Użytkownik testuje na prawdziwej tarczy i zgłasza wyniki.

## Pliki i wdrożenie
- Cała aplikacja to jeden plik `oko-tarczy.html` (bez kroku budowania, edytuj go bezpośrednio).
  - 1. `<script>`: rdzeń `DartCore` (UMD, działa też w Node przez `module.exports`): geometria tarczy,
    kalibracja, wykrywanie, śledzenie tarczy, gra.
  - 2. `<script>`: aplikacja (UI, kamera, `processFrame`, `onDart`, poprawki, Nauka AI, ustawienia).
  - Przy każdej zmianie podbij `APP_VERSION`.
- Wdrożenie: push na `main` w `ventrescaa-svg/oko-tarczy`, GitHub Pages:
  https://ventrescaa-svg.github.io/oko-tarczy/oko-tarczy.html (ok. 1–2 min). Użytkownik oczekuje,
  że gotowa poprawka zostanie od razu wypchnięta. Pracuj w jednym czacie naraz (dwa czaty nadpisywały sobie zmiany).
- `narzedzia/`: test na prawdziwych rzutach (opis niżej).

## Sprzęt i ustawienie użytkownika
- Galaxy S26, przeglądarka (Chrome/Brave), telefon pionowo na statywie z PRAWEJ strony tarczy,
  ok. 48° do tarczy, ok. 1 m od bulla, na wysokości bulla. Statyw drga (jest śledzenie tarczy).
- Wideo 1080x1920, przetwarzanie w skali 0,5 (540x960): ok. 0,92 px/mm w poziomie, 1,59 px/mm w pionie.
  Tarcza zajmuje ok. 58% szerokości kadru, z prawej ok. 1/3 kadru to pusta ściana.
- Rzutki: srebrna baryłka (wolfram) 40 mm, CZARNY stalowy grot 25 mm. Rzutka na obrazie biegnie
  prawie poziomo, grot jest po prawej (strona kamery), lotka po lewej.

## Wykrywanie (Detector.analyze)
1. Ruch, uspokojenie obrazu, różnica względem `ref` (odporna na drgnięcie o 1 px i cienie).
2. `findDart`: składowe maski, PCA, prosta baryłki z RANSAC. `det.tip` to przód baryłki.
3. `locateTip` (od 2026.10.17, zastąpiło `extendTip`): profil w poprzek osi.
   - Nos baryłki = koniec szerokiego odcinka.
   - Dalej wzdłuż osi: ciemny grot na jasnym polu oznacza „grot jest”, nietknięte jasne pole oznacza „grota nie ma”, czarne pole nic nie mówi.
   - Wybór długości = dowody + rozkład wokół typowej długości `pointMm` (domyślnie 14 mm wysokości nad tarczą), zamieniony na px geometrią kamery.
   - Geometria kamery: `cameraFromH` i `heightStep`, poza kamery odzyskana z homografii, punkt główny = środek wideo (`cfg.pp`).
   - Limit: `pointMaxMm` = 25 (zmierzony grot).
   - `det.tipBy` = `seen` albo `prior` (zgadnięty, czarne na czarnym). Tip `prior` blisko drutu (< 2,5 mm) daje rzut „niepewny” (przerywana ramka).
4. Długość grota uczy się z poprawek stuknięciem: `learnPoint`, `localStorage` `point`, mediana z 15, w zakresie 8..23 mm.
   Stara „Korekta grota” (`offsetMm`) jest wyłączona: przesuwała wszystko o stałą liczbę mm i pogarszała wyniki.
5. Fallback `tipModel:'walk'` = stare `extendTip`.

## Nauka AI (zbieranie danych)
- Każdy rzut z kamery zapisuje się w IndexedDB jako wycinek przed i po rzucie oraz wynik ostateczny
  (`auto`, `confirmed`, `tap` = poprawiony stuknięciem, `deleted`, `keypad`).
  Eksport ZIP: Menu, Ustawienia wykrywania, Nauka AI. ZIP zawiera `manifest.json` i JPEG-i.
- Naprawione 2026.10.17: zdjęcie „przed” bywało kopią „po”, bo `refA` aliasował `this.ref`. Dotyczyło 17 z 77 starych próbek.
- Nowe próbki mają też `det.nose`, `pointPx`, `pxPerMm`, `tipBy`, `pointMm`.

## Test na prawdziwych rzutach
```
python3 narzedzia/rozpakuj.py eksport.zip /tmp/rzuty
node narzedzia/test_rzutow.js oko-tarczy.html /tmp/rzuty          # V=1: lista, NOISE=4: szum kamery
```
Wynik na eksporcie z 2026-10-17 (77 rzutów, 59 da się odtworzyć):

| Wersja | Dobre pole | Poprawiane stuknięciem | Z szumem kamery |
|---|---|---|---|
| Nowa | 43 | 15/22 | 43–44 |
| Stara (`walk`/`old`) | 41 | 13/22 | 39–41, wynik skacze |

Zawsze porównuj z wersją przed zmianą i sprawdzaj z `NOISE`.

## Otwarte problemy (kolejność wg wpływu)
1. **Zła rzutka przy grupach** (5 z 26 poprawek): przy 2. i 3. rzutce blisko poprzednich
   `findDart` łapie środek korpusu albo inną rzutkę. Do zbadania w `findDart` (wybór `main`, łączenie składowych, okluzja).
2. **Rozdzielczość grota**: grot to ok. 3 px szerokości. Tanio: przesunąć tarczę w kadrze do prawej
   krawędzi i przybliżyć ok. 1,35x, potem kalibracja. Lepiej: dopracowanie grota na pełnej rozdzielczości wideo
   (wycinek `drawImage` przez macierz śledzenia, ref w pełnej rozdzielczości trzymany w canvasie i odświeżany przy każdej zmianie `det.ref`).
3. **Czarne na czarnym**: tylko zgadywanie z długości (±5 px). Baryłka 40 mm mogłaby dać skalę rzutki,
   ale przy obecnej rozdzielczości nie widać granicy baryłka/shaft.
4. **Model AI** na wycinkach: po zebraniu ok. 300 rzutów z nową wersją (pełne zdjęcia „przed”).
