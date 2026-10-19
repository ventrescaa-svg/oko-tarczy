# Oko Tarczy – kontekst projektu (stan na 2026-10-19)

Aplikacja do automatycznego liczenia punktów w darta (501/301/701) kamerą telefonu, w stylu Dartsmind.
Rozmawiamy po polsku, prosto, bez żargonu. Użytkownik testuje na prawdziwej tarczy i zgłasza wyniki.

## Pliki i wdrożenie
- Cała aplikacja to jeden plik `oko-tarczy.html` (bez kroku budowania, edytuj go bezpośrednio).
  - 1. `<script>`: rdzeń `DartCore` (UMD, działa też w Node przez `module.exports`): geometria tarczy,
    kalibracja, wykrywanie, śledzenie tarczy, gra.
  - 2. `<script>`: aplikacja (UI, kamera, `processFrame`, `onDart`, poprawki, Nauka AI, ustawienia).
  - Przy każdej zmianie podbij `APP_VERSION` (widać ją w nagłówku Menu: „Menu · wersja …”, też w dzienniku i w manifeście eksportu).
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

## Zrzuty siatki (od 2026.10.19)
- Same się robią po automatycznej kalibracji i 6 s po „Gotowe, gramy” (bez dotykania statywu), z krótkim komunikatem. Pełna rozdzielczość, siatka cienką turkusową linią + to samo zdjęcie bez siatki.
- Menu, „Wyślij zrzuty siatki”: udostępnia (lub zapisuje) ostatnie 4. Służą do sprawdzania, czy siatka leży na drutach.

## Dociąganie siatki do drutów (`refineGrid`, od 2026.10.19c)
- `autoCalibrate` dopasowuje tylko okręgi (krawędzie kolorów na zdjęciu 800 px); obrót bierze z wzoru pól, więc linie sektorów potrafiły być 2–4 mm obok drutów.
- Po nim `refineGrid` na pełnym kadrze: wzdłuż 20 drutów sektorów i 6 okręgów szuka w bok najsilniejszej zmiany koloru, potem odporne dopasowanie homografii (8 parametrów), 3 rundy (okno 12/6/4 px).
  Przyjmowane, gdy `ok` (≥150 punktów na drutach i na okręgach, błąd < 0,9 mm) i przesunięcie < 40 px.
- Zrzut Piotra z 2026-10-19: błąd linii sektorów 1,58 → 0,75 mm (najgorszy drut 3,6 → 1,6 mm), zbiega z odchyłki 24 px i z szumem. Poprawka na krzywiznę obiektywu nic nie dała.
- Od 2026.10.19d `RING.trebleIn` = 97, `RING.doubleIn` = 160 (było 99/162). 170 i 107 to wymiar do zewnętrznej strony drutu, a 8 mm to szerokość między drutami, więc kolorowe pole z drutami ma ok. 10 mm.
  Piotr zmierzył linijką ok. 10 mm (Winmau Blade 6); dopasowanie promieni z obrazu (`refineGrid` z `rings: true`) dało 96,6–97,6 i 158,9–159,8. Zmienia też liczenie punktów (pas 160–162 to teraz podwójna).
  Wynik `test_rzutow.js` po tej zmianie nie był sprawdzony (brak eksportu w tej sesji).
- Od 2026.10.19e każda udana automatyczna kalibracja mierzy pierścienie (`refineGrid` z `rings: true`), `learnRings` trzyma 5 ostatnich pomiarów
  w `localStorage` `rings`, `C.setRings` ustawia średnią w `RING` (tylko trebleIn/trebleOut/doubleIn, maks. ±3 mm od 97/107/160; 170 = skala).
  Na zrzutach Piotra: 96,6/107,7/158,9 i 97,6/107,4/159,7. Wynik widać w górnym pasku zrzutu z kalibracji („pierścienie …”).
- Jeszcze nie: dociąganie w trakcie gry (śledzenie tarczy jest tylko afiniczne).

## Kamera 4K (od 2026.10.19g)
- Ustawienia wykrywania, „Kamera 4K”: `S.settings.cam4k`, prosi o 3840×2160 zamiast 1920×1080; pod przełącznikiem `camInfo()` pokazuje, co kamera naprawdę daje i ile kl/s ma wykrywanie.
- Przełączenie restartuje kamerę; punkty kalibracji są skalowane (ten sam kształt obrazu), potem automatyczna kalibracja od nowa. `refineGrid` dostaje okna × (krótszy bok / 1080).
- Na S26 w przeglądarce działa: 2160×3840, kadr szerszy niż przy Full HD (tarcza ok. 56% szerokości zamiast 68%), ale na tarczy ok. 1,6× więcej pikseli. Kalibracja w 4K: błąd 0,55 mm, pierścienie 97,3/107,6/159,9.
- Wykrywanie dalej zmniejsza wycinek tarczy do 960 px (`setupProc`), więc 4K pomaga na razie tylko kalibracji i zrzutom. Następny krok: dopracowanie grota na pełnej rozdzielczości (otwarty problem 2).

## Dziennik czasów (od 2026.10.19i)
- W grze `perfAdd`/`perfFlush` co 10 s zapisują linię: średni/najdłuższy czas (ms) i ile razy na sekundę dla kroków
  `śledzenie`, `śledzenie między`, `kopiowanie klatki`, `wyrównanie`, `wykrywanie`, `obsługa rzutu`, `rysowanie`, `odstęp klatek` (ostatnie 90 linii).
- Wysyłany jako .txt razem ze zrzutami (Menu, „Wyślij zrzuty i dziennik”).
- Od 2026.10.19k Menu, „Wyślij dziennik na GitHub” (`sendLogGithub`): otwiera gotowe zgłoszenie (issue). Od 19o link ma ≤ 3500 znaków (nagłówek + najnowsze linie; dłuższy dawał Piotrowi błąd), a pełny dziennik idzie do schowka (wkleić pod tekstem). Bez etykiety, bez tokenu w stronie (świadomie).
- `processFrame` jest celowo ograniczone do ok. 10 kl/s (co 95 ms), więc 8–9 kl/s w Full HD to prawie maksimum. W 4K Piotr miał 2–3 kl/s.

## Szturchnięty statyw (od 2026.10.19j)
- Mały obrót kamery (0,15–0,5°) daje cienkie zmiany na krawędziach w całej tarczy; `findDart` brał jedną z nich za rzutkę („pudło”).
- `Detector.analyze`: gdy rzutka to < 12% całej zmiany (`camMovedShare`; sam wstrząs 0,04–0,08, prawdziwa rzutka 1,0, rzutka + wstrząs ok. 0,2)
  albo < 50% i leży dalej niż 230 mm od bulla, zdarzenie `shifted`: nowe `ref`, brak rzutu, komunikat „Telefon drgnął…”.
- Ograniczenie: rzutka wbita w tej samej chwili co mocne szturchnięcie (ok. 0,3°+) przepada i trzeba ją dopisać ręcznie.
- Test w symulacji (scratchpad `bump.js`), nie sprawdzony z śledzeniem tarczy ani na eksporcie rzutów.

## Grot na ostrym obrazie (od 2026.10.19l)
- Ustawienia wykrywania, „Grot na ostrym obrazie” (`S.settings.hiTip`, domyślnie wł.). Wykrywanie dalej na 540×960, ale raz na rzut
  `hiRefine` szuka grota jeszcze raz na wycinku w pełnej rozdzielczości (z = min(2, 1/`P.s`), w Full HD 2×) przez `C.refineTipHi`
  (= `locateTip` z `opt.z`, które skaluje stałe w px, plus wyrównanie resztkowego przesunięcia `estimateShift`).
- Zdjęcie „przed” w pełnej rozdzielczości: `S.hi` (canvas całej tarczy w układzie obrazu przetwarzania × z), robione przez `hiCaptureRef`
  po każdej zmianie `det.ref` (licznik `Detector.refVer`). Przy rzucie detektor już podbił `refVer`, więc `hiRefine` wymaga `S.hi.ver === refVer - 1`.
- Wynik ostry jest odrzucany, gdy przesuwa punkt o > 8 mm albo gdy jest zgadnięty, a zwykły był widziany i różnica > 3 mm. `det.hi` = {tip, lo, by, move, shift, used}.
- Nauka AI: próbki mają też `hiCrop` + `_hiref.jpg`/`_hicur.jpg` w ZIP (do sprawdzenia na prawdziwych rzutach).
- Test: `narzedzia/sztuczne_rzuty.js` rysuje sztuczną rzutkę 3D (geometria kamery z homografii) na zdjęciu tarczy Piotra 1080×1920
  (wymaga `img/plain2.rgba` i `Hnew2.json` w `SP`, nie ma ich w repo). 240 rzutów: dobre pole 214 → 224, mediana błędu 1,6 → 1,3 mm.
  Na prawdziwych rzutach jeszcze nie sprawdzone.

## Cienie i składowe (od 2026.10.19m, na eksporcie Piotra z 2026-10-19, 19 rzutów)
- Cień rzutki na kremowych polach tracił więcej niebieskiego niż czerwonego (cieplejsze światło w cieniu) i `diffMap`/`locateTip`/`findDart` brały go za rzutkę.
  `isShadow(kr,kg,kb)`: obok starego warunku (równe zaciemnienie, rozrzut < 0,13) dopuszcza rozrzut < 0,34, gdy niebieski i zielony spadły co najmniej tak jak czerwony
  (srebrna baryłka na kremie robi odwrotnie). Wspólne dla `diffMap`, `locateTip` i filtra w `findDart`.
- `findDart`: odrzucanie składowych poza osią po jednej (najdalszą od osi), a nie wszystkich naraz. Cień obok rzutki przechylał oś i wyrzucał baryłkę zamiast siebie (rzut 18: pole 5 zamiast 20).
- `test_rzutow.js` z `HI=1` stosuje też ostry grot (`refineTipHi` na `hiCrop`, `rozpakuj.py` rozpakowuje `hiref`/`hicur`). Wynik: 13 → 15 → 16 dobrych pól z 19 (zwykły → po cieniach i składowych → z ostrym grotem),
  poprawiane stuknięciem 4/7 → 7/7 (bez szumu; z szumem 4: 15/19, 5–6/7). Nadal źle: rzut 17 (12 → 5, grot za drutem) i 7 (3 → 17).

## Zawieszona kamera (od 2026.10.19n)
- Piotr zgłosił, że po 19l/19m obraz stał na jednej klatce mimo wyjęcia lotek. Przyczyny nie ustalono (podejrzenia: ostry grot `hiCaptureRef`, wyjątek w `loop` zabijający `requestAnimationFrame`, zatrzymana ścieżka kamery).
- `loop` ma try/catch i zawsze planuje następną klatkę; błędy trafiają do dziennika (`logNote`, linie z `!!`, też `window.onerror`).
- `watchVideo`: gdy `video.currentTime` stoi 3 s, `play()`; po 7 s `restartCamera` (zatrzymuje ścieżki, `startCamera`, `resetPending`). Test Playwright: pauza i zatrzymana ścieżka wracają same.
- Ostry grot: canvas bez `willReadFrequently`; gdy `hiCaptureRef` trwa > 150 ms trzy razy z rzędu, `S.hiOff` wyłącza go do końca sesji (wpis w dzienniku).
- Przy kolejnym zawieszeniu poproś o „Wyślij dziennik na GitHub” (linie `!!` mówią, co się stało).

## Cień zamiast rzutki (od 2026.10.19p, eksport Piotra z 20:51, 38 rzutów)
- Dwa rzuty w żywej aplikacji brały za rzutkę ciemną plamę (cień rzutki) kilkaset px od niej: 29 (D20 → T20, plama na czerwonym pierścieniu) i 32 (rzutka na 20 policzona jako 7 przez plamę przy bullu; etykieta `auto` była błędna).
- Przyczyna: rzutka rozpada się na kilka składowych maski (lotka 1866 px + baryłka 737 px, odstęp 1 px). `findDart` wyrzucał najpierw „najbardziej odstającą” składową; plama (519 px, 96 px dalej) przechylała oś PCA, więc wypadała baryłka, a zostawała plama.
  Teraz składowe stykające się z główną (`bboxGap` ≤ `gap`·0,15, ok. 5 px) są chronione, a odrzucanie po jednej dotyczy tylko dalszych.
- Test na 35 rzutach: dobre pole 28 (z ostrym grotem), z szumem 28–29; rzut 29 poprawiony, 32 też (test liczy go jako błąd, bo etykieta `auto` jest zła).
- Próba osobnego filtra „składowa to cień” (frakcja pikseli o jednakowym zaciemnieniu, bez limitu k > 0,3) nic nie dała przy progu 0,6, a przy 0,4 pogarszała (gubi lotki/wały): cofnięta.
- Uwaga: `test_rzutow.js` ma teraz domyślnie `pointMm` z próbki (nauczone z poprawek: 14 → 15,8 → 17,6 w ciągu dnia). Wynik prawie nie zależy od pointMm (8–16 daje 27–30 z 35), ale dryf w górę warto obserwować.
- Nie odtwarzało się offline: rzut 33 (żywa aplikacja wybrała plamę, test rzutkę), bo próbka nie miała stanu detektora. Od 2026.10.19q próbki mają `_mask.png` (żywa maska zmian) i `_occ.png` (poprzednie rzutki tury, gdy `dartsInTurn` > 1); `rozpakuj.py` je rozpakowuje, a `test_rzutow.js` ustawia z nich `det.occ` i `dartsInTurn` (`NOSTATE=1` wyłącza).

## Poprawka rzutu: cała tarczą (od 2026.10.19s)
- Okno „Popraw rzut” pokazywało tylko wycinek ±70 mm wokół wykrytego grota. Gdy wykrycie trafiło w cień daleko od rzutki, prawdziwego miejsca nie było na obrazie i nie dało się go zaznaczyć (Piotr, 2026-10-19).
- `captureSnap` robi teraz też `snap.wide` (`captureWide`: cała tarcza r = 185 mm w prostokącie 600 px szerokości, proporcje z homografii; `null` przy nieprawdopodobnej kalibracji). Przycisk „Pokaż całą tarczę” / „Pokaż zbliżenie” przełącza widok; w widoku całej tarczy kreskowane czerwone kółko = miejsce wykryte przez aplikację.
- `fixMap` ma osobne `sw/sh/cw/ch`; stuknięcie przelicza się przez wybrany widok. Test Playwright: stuknięcie w widoku całej tarczy daje poprawny wynik.

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

## Druk 3D: rama LED na nóżkach + uchwyty na 2 telefony (`druk3d/`)
- Pierwszy projekt (pierścień zaciskany na tarczy, telefon na rurce) użytkownik odrzucił. Chce ramę odsuniętą na nóżkach,
  telefon między nóżkami, same telefony (bez kamerek USB). Tarcza wisi na płycie OSB 80×90 cm.
- Generator bez bibliotek CAD (numpy + scikit-image):
  - `sdf.py`: prymitywy SDF, marching cubes, STL;
  - `rama.py`: ośmiokąt RC 350 (ok. 75 cm), 8 belek 32×24 z rowkiem na taśmę COB 10 mm z tyłu, fazy 8 mm pod mostki w gniazdach;
    narożniki `noga` (1:30…10:30) i `telefon` (12/3/6/9, gniazda nakrętek M5); nóżki z jaskółczym ogonem w płytkach na OSB;
    ramię telefonu w pasie t = 33–47 mm obok góry telefonu, żeby nie wchodziło w kadr;
  - `uchwyty.py`: uchwyt telefonu 62–88 mm z okienkiem na aparat, ucho zawiasu M5 tuż za aparatem, szczęka, gałka;
  - `poza.py`: poza aparatu i kadr. Uchwyt założony z FLIP, więc na godz. 3 telefon stoi aparatem do góry (Samsung: aparat lewy górny róg pleców).
    `hinge_for()` liczy `HINGE_U/HINGE_Z` dla `CAM_TARGET`;
  - `sprawdz.py`: kolizje, szczelina zawiasu przy pochyleniu, zasłanianie, tory rzutek;
  - `build.py`: STL w ułożeniu do druku; `nawisy.py`: kontrola nawisów; `podglad.py`: rendery.
  - STL nie są w repo (`python3 druk3d/build.py katalog`).
- Ustawienie: z = 0 to przód tarczy, OSB przy z = −44, przód ramy z = 194.
  - Aparat: (r 300, z 290), 417 mm od bulla, 46° od osi.
  - Kadr przy 1× (70°×43°): 0,90 na krótszym boku, 0,66 na dłuższym.
  - 2,29 px/mm w stronę telefonu (statyw: ok. 1,84), 3,29 w poprzek (pełne wideo).
- Drugi telefon na godz. 6: na 12 tory rzutek w D20 przechodzą przez telefon, a 9 jest na tej samej osi co 3.
- W tym środowisku duże tablice numpy są wolne: liczyć warstwami (`S.evaluate`) i ustawić
  `MALLOC_MMAP_THRESHOLD_=33554432 MALLOC_TRIM_THRESHOLD_=4000000000`.

## Otwarte problemy (kolejność wg wpływu)
1. **Zła rzutka przy grupach** (5 z 26 poprawek): przy 2. i 3. rzutce blisko poprzednich
   `findDart` łapie środek korpusu albo inną rzutkę. Do zbadania w `findDart` (wybór `main`, łączenie składowych, okluzja).
2. **Rozdzielczość grota**: grot to ok. 3 px szerokości. Rama z telefonem z bliska daje ok. 25% więcej. Tanio: przesunąć tarczę w kadrze do prawej
   krawędzi i przybliżyć ok. 1,35x, potem kalibracja. Lepiej: dopracowanie grota na pełnej rozdzielczości wideo
   (wycinek `drawImage` przez macierz śledzenia, ref w pełnej rozdzielczości trzymany w canvasie i odświeżany przy każdej zmianie `det.ref`).
3. **Czarne na czarnym**: tylko zgadywanie z długości (±5 px). Baryłka 40 mm mogłaby dać skalę rzutki,
   ale przy obecnej rozdzielczości nie widać granicy baryłka/shaft.
4. **Model AI** na wycinkach: po zebraniu ok. 300 rzutów z nową wersją (pełne zdjęcia „przed”).
5. **Tryb dwóch telefonów** (zaplanowany po zamontowaniu ramy): parowanie przez kod QR i WebRTC w tej samej sieci Wi-Fi,
   punkt wbicia z przecięcia osi rzutki z obu kamer (każda oś zrzutowana na tarczę przez swoją homografię), więc bez zgadywania długości grota.
