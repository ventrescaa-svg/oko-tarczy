# Oko Tarczy – kontekst projektu (stan na 2026-10-24)

Aplikacja do automatycznego liczenia punktów w darta (501/301/701, Cricket, tryby treningowe) kamerą telefonu, w stylu Dartsmind.
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
   Stara „Korekta grota” (`offsetMm`) przesuwała wszystko o stałą liczbę mm i pogarszała wyniki; usunięta w 19z.
5. Gdy `locateTip` rzuci wyjątkiem, grotem zostaje przód baryłki (`tipBy` = `prior`). Stare `extendTip` (`tipModel:'walk'`) usunięte w 19z.

## Nauka AI (zbieranie danych)
- Każdy rzut z kamery zapisuje się w IndexedDB jako wycinek przed i po rzucie oraz wynik ostateczny
  (`auto`, `confirmed`, `tap` = poprawiony stuknięciem, `deleted`, `keypad`).
  Eksport ZIP: Menu, Ustawienia wykrywania, Nauka AI. ZIP zawiera `manifest.json` i JPEG-i.
  Od 2026.10.25a eksport dzieli się na części po ok. 25 MB (`-cz1z3` itd., każda z własnym `manifest.json`), bo czat przyjmuje maks. 30 MB; `rozpakuj.py a.zip b.zip … katalog` łączy części.
- Od 2026.10.26a wysyłanie na GitHub (`ghSync`): Ustawienia wykrywania, Nauka AI, „Wysyłaj rzuty na GitHub” (+ „też przez dane komórkowe”, `navigator.connection.type`), token i repozytorium (domyślnie prywatne `ventrescaa-svg/oko-tarczy-dane`), „Sprawdź połączenie”, „Wyślij teraz”.
  Token (fine-grained, tylko Contents tego repozytorium) wpisuje gracz; trzymany w `localStorage` `ghsync`, nigdy w kodzie strony. Co `GH_BATCH` = 15 nowych próbek (sprawdzane po `saveSample`) paczka `paczki/RRRRMMDD-GGMM-xxxx.zip` (to samo co eksport, `packDataset`, maks. 60 rzutów, części po 15 MB) przez API contents (PUT).
  Wysłane mają `r.up`; poprawka starego rzutu (`relabeled`) czyści `up`, więc rzut idzie jeszcze raz. `rozpakuj.py` bierze wiele plików i zostawia najnowszą wersję każdego `id`, rzuty układa według czasu.
- Naprawione 2026.10.17: zdjęcie „przed” bywało kopią „po”, bo `refA` aliasował `this.ref`. Dotyczyło 17 z 77 starych próbek.
- Nowe próbki mają też `det.nose`, `pointPx`, `pxPerMm`, `tipBy`, `pointMm`.
- Od 2026.10.26d (audyt 2026-10-26, zgoda Piotra) próbka ma też cały obraz przetwarzania przed/po (`_fullref.jpg`/`_fullcur.jpg`, JPEG 0,85, ok. 130 kB każdy) i pełną maskę (`_fullmask.png`), `full: {w, h}` oraz nauczone pierścienie `rings` [trebleIn, trebleOut, doubleIn].
  Powód: przy „złym obiekcie” (cień od lampy, nakładające się lotki) prawdziwa rzutka bywała poza wycinkiem, więc nie dało się tego sprawdzić offline. Rdzeń: `cfg.keepFull` / `det.keepFull` (= „Zbieraj dane”), `debugCrop` dokłada `full`.
  Rzut waży ok. 375 kB zamiast ok. 105 kB. `rozpakuj.py` rozpakowuje `fullref`/`fullcur`/`fullmask`, `test_rzutow.js` z `FULL=1` liczy na całym obrazie (występowanie `occ` wstawiane w miejsce wycinka) i zawsze ustawia `rings` z próbki.
  Sprawdzone: wynik na starych rzutach bez zmian (804/916); na 60 rzutach wklejonych w szare tło `FULL=1` daje te same miejsca co wycinek (mediana różnicy 0,4 mm; większe różnice z globalnego wzmocnienia/szumu liczonego z całego obrazu); Playwright: zapis próbki i ZIP mają nowe pliki.

## Zdjęcia z kalibracji w Nauka AI (od 2026.10.25d; wcześniej „zrzuty siatki” od 19)
- `gridShot` robi się sam po automatycznej kalibracji (`kalibracja`) i 6 s po „Gotowe, gramy” (`gra`), bez komunikatu. Zapisuje do IndexedDB (ten sam magazyn co rzuty, `kind: 'cal'`):
  pełne zdjęcie z kamery bez siatki (JPEG), `H` (tarcza mm → px wideo, w grze z macierzą śledzenia), `info` (rms, wzór, druty), `rings`. Trzymane ostatnie `CAL_KEEP` = 12 (`DS.del`).
- Eksport ZIP: `cal/NNN-tag.jpg` + `manifest.cals`, plus `dziennik.txt` (dziennik czasów). `rozpakuj.py` kopiuje je do `katalog/cal/` i `katalog/dziennik.txt`. Siatkę rysuje się z `H` przy sprawdzaniu.
- Usunięte (prośba Piotra, 2026-10-25): komunikat o zrzucie, `shareGridShots` i przycisk Menu „Wyślij zrzuty i dziennik”. Licznik Nauka AI liczy tylko rzuty.
- Piotr chciał, żeby dziennik sam szedł na GitHub; bez tokenu w publicznej stronie się nie da, więc dziennik jedzie w eksporcie (przycisk „Wyślij dziennik na GitHub” usunięty w 28b, dziennik jest w paczkach na GitHubie).

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

## Obraz przez kartę graficzną (od 2026.10.24e)
- Dzienniki Piotra (zgłoszenia #1, #2, Full HD): `śledzenie` ok. 45 ms i `kopiowanie klatki` ok. 45–50 ms na klatkę, a samo `wykrywanie` 20–29 ms. Czyli większość czasu to przenoszenie obrazu z kamery do procesora przez canvas 2D (`willReadFrequently`), w 4K ok. 4× więcej (stąd 2–3 kl/s).
- Teraz (`glInit`/`glWarp`/`glRead`, WebGL2): klatka idzie raz na rundę pętli do tekstury (`S.tick`), program na karcie przesuwa ją przez macierz śledzenia i uśrednia piksele wideo pod każdym pikselem wyniku (N×N próbek, N = ceil(skala), maks. 8), odczytywany jest tylko mały wynik:
  obraz do śledzenia (`stabGray`, cel `trk`), obraz przetwarzania (`processFrame`, `proc`), ostre zdjęcie „przed” (`hiCaptureRef`, `hiref`, zostaje na karcie, przy rzucie czytany tylko wycinek) i wycinek „po” (`hiRefine`, `hicur`).
- Ostry grot do 3× (było 2×): w 4K to własne piksele kamery. Wykrywanie dalej na ≤ 960 px (stałe w px są pod to dobrane).
- Ustawienia wykrywania, „Obraz przez kartę graficzną” (`S.settings.gpu`, domyślnie wł.). Błąd lub utrata kontekstu: `glFail`, wpis `!!` w dzienniku, do końca sesji stary canvas. Nagłówek dziennika: „karta graficzna tak/nie/błąd/wyłączona”.
- Sprawdzone w Playwright (atrapa kamery ze zdjęciem tarczy Piotra 4K, SwiftShader): obraz z karty różni się od canvasa średnio o 0,75–1,25 jasności, wycinek ostrego zdjęcia o 0,5; po utracie kontekstu gra działa dalej na canvasie. Prawdziwej szybkości na S26 jeszcze nie znamy (SwiftShader liczy na procesorze); rdzeń bez zmian, więc `test_rzutow.js` daje to samo.
- Następny krok, gdy będzie szybko: większy obraz wykrywania w 4K (np. 1280 px) albo różnica „przed/po” liczona na karcie.

## Szybsze wykrywanie i porządki (2026.10.28b)
- `envelope3` + `envDist`: otoczka 3×3 (min/maks każdego kanału) liczona raz na obraz zamiast 9 porównań na piksel; używają jej `motionMeasureHalf` i `diffMap`.
  Pomiar w Node (540×960): `motionMeasureHalf` 20,5 → 14,0 ms, `diffMap` z drganiem 104 → 56 ms, krok bez rzutu 22,6 → 15,5 ms, `analyze` z rzutką 162 → 118 ms.
  Wynik liczenia identyczny co do bajta (`OUT=` jsonl): 916 rzutów z HI, paczki 28.10 z FULL+HI, NOISE=4 SEED=1 i NOSTATE.
- Usunięte: „Jaśniejszy obraz z kamery” (`ev`, `applyEv`), „Wyślij dziennik na GitHub” (`sendLogGithub`, `logHead` zostaje), filtr `occDrop` w `findDart` (nic nie zmieniał).
- Dziennik: `śledzenie` rozbite na `śledzenie: obraz` (klatka na kartę i odczyt) i `śledzenie: liczenie` (sam Lucas–Kanade). W Playwright (Full HD, SwiftShader) obraz 31–39 ms, liczenie 1,2–1,5 ms,
  więc dalsze przyspieszanie dotyczy przenoszenia obrazu (asynchroniczny odczyt, `VideoFrame`), nie śledzenia. Najpierw dziennik z S26.
  Dziennik z S26 (28.10 wieczorem, 4K): `śledzenie: obraz` 40–57 ms, `śledzenie: liczenie` ok. 3 ms, `kopiowanie klatki` ok. 7 ms, `wykrywanie` 26–34 ms, 7–9 kl/s. Następny krok przyspieszenia: wgrywanie klatki 4K na kartę (np. mniejsza tekstura, `VideoFrame`).
- 2026.10.28e: na S26 w 4K wątek był prawie cały zajęty (śledzenie w wykrywaniu ok. 7,5×55 ms + „śledzenie między” ok. 4,5×55 ms + wykrywanie ok. 7,5×28 ms na sekundę), stąd 7–9 kl/s zamiast 10.
  Ustawienia wykrywania, „Oszczędne śledzenie” (`S.settings.lean`, domyślnie wł., `leanOn`): licznik nowych klatek kamery (`requestVideoFrameCallback`, `S.vf`), ta sama klatka nie jest drugi raz śledzona ani przetwarzana,
  a „śledzenie między” jest pomijane, gdy średni czas obrazu do śledzenia `S.trkMs` > 20 ms (siatka na ekranie odświeża się wtedy ok. 10×/s). Gdy licznik stoi > 0,5 s, działa jak dawniej.
  Dziennik: linia ma `kamera N kl/s` i `oszczędne tak/nie`, nowe kroki `karta: wgrywanie` (samo `texImage2D`) i `karta: odczyt` (`readPixels`, czeka na kartę). Playwright (atrapa 10 kl/s): wgrywania 18 → 10 na sekundę. Rdzeń bez zmian.
  Następnie: z dziennika S26 zobaczyć, czy drogie jest wgrywanie czy odczyt; potem ewentualnie większy obraz wykrywania w 4K.

## Menu główne (2026.10.30b)
- Piotr: po „Gotowe, gramy” aplikacja od razu liczyła, czy grał, czy nie. Nowy ekran `scr-home` (`renderHome`): Kontynuuj grę (gdy gra ma rzuty i nie jest skończona), Nowa gra, Statystyki, Kalibracja kamery, Ustawienia wykrywania, Licz ręcznie, Instrukcja.
- Start aplikacji: zawsze menu główne (od 2026.10.31d, Piotr; wcześniej bez zapisanej kalibracji instrukcja). Gra bez kalibracji najpierw kalibruje (`playFromHome`), instrukcja jest w kafelku. Kalibracja z menu albo z instrukcji kończy się w menu (`S.afterCal = 'home'`, przycisk „Gotowe”); kalibracja z gry albo przed grą (`playFromHome`) wchodzi do gry (`enterGame`: nowe `ref`, „Wyjmij lotki”).
- Wygląd: u góry zdjęcie oka z tarczą jako tęczówką (`grafika/oko.jpg`, wygenerowane przez Piotra w KlingAI, przycięte bez znaku wodnego, 1000×750, ok. 130 kB, brzegi rozmyte maską; od 2026.10.31b wersja bez liczb wokół tarczy). Gdy plik się nie wczyta: rysowane oko (pomysł Piotra; `eyeSvg` + `boardG`, prawdziwa kolejność pól, oko mruga i rozgląda się, wyłączone przy `prefers-reduced-motion`), karta „Kontynuuj grę”, szybki start (501, Cricket, Dookoła, Więcej → okno „Nowa gra” z wybranym trybem), kafelki narzędzi z ikonami. Klasy kart `q-*` (bo `.cr` jest już zajęte przez tabelę Cricketa).
- W menu kamera zostaje włączona, ale nic nie jest przetwarzane ani rysowane (pętla działa tylko w `cal`/`game`). W grze Menu, „Menu główne (przerwa w liczeniu)”.
- Playwright (scratchpad `pw_home.js`, `pw_home2.js`): w menu licznik klatek detektora stoi, przejścia menu/gra/kalibracja działają, Kontynuuj wraca do gry ręcznej.

## Oszczędzanie baterii (2026.10.30a)
- Piotr: telefon się grzeje, bateria szybko schodzi. Dziennik S26 w 4K: ok. 85 ms pracy na każde przetworzenie przy ok. 9,5 kl/s, także gdy nikt nie rzuca.
- Ustawienia wykrywania, „Oszczędzanie baterii” (`S.settings.eco`, domyślnie wł.): po 4 s bez zdarzeń (`S.busyAt`: zdarzenie detektora, `det.moving`, zgubione śledzenie, komunikat na ekranie, stan inny niż ready/pull) `ecoIdle` przetwarza co 300 ms zamiast 95 ms i pomija „śledzenie między”. Pierwszy ruch wraca do pełnego tempa.
  Kamera prosi o 20 kl/s zamiast 30 (`camAskFps`); przełącznik restartuje kamerę (`switchCamera`, to samo co przy 4K). Dziennik: `bateria czuwanie/pełna/wył.`.
- Rdzeń bez zmian. Test (scratchpad `eco_step.js`): rzutka pojawia się po klatkach co 300 ms zamiast 100 ms, to samo pole. Playwright: czuwanie 3,3 kl/s, po ruchu pełne tempo.

## Porządki w danych i stan „złego obiektu” (2026.10.29b, zalecenia 5 i 2 z audytu)
- Skrypt `ort.all.min.js` z jsdelivr ma sumę kontrolną (`AI_ORT_SRI`, sha384 z paczki npm onnxruntime-web 1.29.0, `crossOrigin`). Pliki `.wasm` (zapasowy silnik) nadal bez sumy. Przy zmianie wersji ORT policz nową: `npm pack onnxruntime-web@X`, `openssl dgst -sha384 -binary dist/ort.all.min.js | openssl base64 -A`.
  Playwright (CDN podstawiony plikiem z npm): dobry plik wczytuje model (webgl), zmieniony plik jest odrzucony.
- `ghSync`: licznik niewysłanych `S.dsUnsent` (start z `DS.all`, +1 w `saveSample` i przy poprawce wysłanego rzutu), automatyczne wysyłanie czyta bazę dopiero przy ≥ `GH_BATCH`; po błędzie przerwa 2 min (`GH.failAt`). „Wyślij teraz” bez zmian.
- `store.set`: błąd zapisu idzie do dziennika (`!!`) i raz na sesję na ekran.
- Zły obiekt (zalecenie 2) na 535 rzutach z całym zdjęciem (paczki 28–29.10): reguły na żywo > 25 mm od prawdy tylko 8 razy, model AI naprawił 5. Zostały 3: srebrna baryłka poza maską (tylko lotka, n28b 41), baryłka sklejona z kreską cienia w kształt L odrzucona jako poprzeczna (n29 109, `crossElong`), grupa lotek pod tarczą. Za mało, żeby ruszać `findDart`.
  Uwaga: odtworzenie `FULL=1` daje > 25 mm w 14 rzutach, ale żywa aplikacja w większości z nich miała dobre pole (test ≠ gra).

## Latarka telefonu (od 2026.10.26b)
- Piotr: systemowej latarki nie da się włączyć w trakcie gry, bo przeglądarka trzyma aparat. Ustawienia wykrywania, „Latarka telefonu” (`S.settings.torch`, `applyTorch`): `applyConstraints({advanced:[{torch}]})` na ścieżce kamery,
  ponownie po `startCamera` i w `restoreCam(all)`; po zmianie nowe `ref` po 1,5 s. Pod przełącznikiem komunikat (np. brak `torch` w `getCapabilities`). Nagłówek dziennika: „latarka tak/nie”.
- Cel: światło od strony aparatu chowa cień rzutki za rzutką (pomysł z recenzji 2026-10-24). Na S26 jeszcze nie sprawdzone (atrapa kamery Chromium nie ma latarki).

## Dziennik czasów (od 2026.10.19i)
- W grze `perfAdd`/`perfFlush` co 10 s zapisują linię: średni/najdłuższy czas (ms) i ile razy na sekundę dla kroków
  `śledzenie`, `śledzenie między`, `kopiowanie klatki`, `wyrównanie`, `wykrywanie`, `obsługa rzutu`, `rysowanie`, `odstęp klatek` (ostatnie 90 linii).
- Od 2026.10.25d wysyłany jako `dziennik.txt` w eksporcie Nauka AI.
- Od 2026.10.19k Menu, „Wyślij dziennik na GitHub” (`sendLogGithub`): otwiera gotowe zgłoszenie (issue). Od 19o link ma ≤ 3500 znaków (nagłówek + najnowsze linie; dłuższy dawał Piotrowi błąd), a pełny dziennik idzie do schowka (wkleić pod tekstem). Bez etykiety, bez tokenu w stronie (świadomie). Usunięte w 2026.10.28b (dziennik i tak jest w każdej paczce Nauka AI).
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
- Przy kolejnym zawieszeniu sprawdź `dziennik.txt` w najnowszej paczce (linie `!!` mówią, co się stało).
- Od 2026.10.24d `restoreCam`: po powrocie do aplikacji (`visibilitychange`, po 0,3/1,2/3 s) i co 3 s w `watchVideo` zoom wraca do zapisanego (`localStorage` `zoom`), gdy `getSettings().zoom` się różni (Android po wyjściu z aplikacji otwierał kamerę z domyślnym zoomem; Piotr, 2026-10-24). Po przywróceniu nowe `ref` po 1,5 s; przy „Blokuj ekspozycję” blokada też jest nakładana ponownie. Sprawdzone tylko na atrapie kamery.

## Cień zamiast rzutki (od 2026.10.19p, eksport Piotra z 20:51, 38 rzutów)
- Dwa rzuty w żywej aplikacji brały za rzutkę ciemną plamę (cień rzutki) kilkaset px od niej: 29 (D20 → T20, plama na czerwonym pierścieniu) i 32 (rzutka na 20 policzona jako 7 przez plamę przy bullu; etykieta `auto` była błędna).
- Przyczyna: rzutka rozpada się na kilka składowych maski (lotka 1866 px + baryłka 737 px, odstęp 1 px). `findDart` wyrzucał najpierw „najbardziej odstającą” składową; plama (519 px, 96 px dalej) przechylała oś PCA, więc wypadała baryłka, a zostawała plama.
  Teraz składowe stykające się z główną (`bboxGap` ≤ `gap`·0,15, ok. 5 px) są chronione, a odrzucanie po jednej dotyczy tylko dalszych.
- Test na 35 rzutach: dobre pole 28 (z ostrym grotem), z szumem 28–29; rzut 29 poprawiony, 32 też (test liczy go jako błąd, bo etykieta `auto` jest zła).
- Próba osobnego filtra „składowa to cień” (frakcja pikseli o jednakowym zaciemnieniu, bez limitu k > 0,3) nic nie dała przy progu 0,6, a przy 0,4 pogarszała (gubi lotki/wały): cofnięta.
- Uwaga: `test_rzutow.js` ma teraz domyślnie `pointMm` z próbki (nauczone z poprawek: 14 → 15,8 → 17,6 w ciągu dnia). Wynik prawie nie zależy od pointMm (8–16 daje 27–30 z 35), ale dryf w górę warto obserwować.
- Nie odtwarzało się offline: rzut 33 (żywa aplikacja wybrała plamę, test rzutkę), bo próbka nie miała stanu detektora. Od 2026.10.19q próbki mają `_mask.png` (żywa maska zmian) i `_occ.png` (poprzednie rzutki tury, gdy `dartsInTurn` > 1); `rozpakuj.py` je rozpakowuje, a `test_rzutow.js` ustawia z nich `det.occ` i `dartsInTurn` (`NOSTATE=1` wyłącza).

## Kierunek rzutki z geometrii kamery (od 2026.10.19t, eksport Piotra z 21:26, 60 rzutów)
- Cień rzutki to nie plama obok, tylko długi cień rzucony na tarczę: cienka linia od grota w dół, potem plama (cień lotki) ok. 100–120 px od grota, aż do bulla. Bywa bardzo ciemny (k ≈ 0,15 na kremowym), więc `isShadow` go nie łapie (czarna lotka też ma k ≈ 0,1).
- Przyczyna błędu: oś PCA po złączeniu głównej składowej z plamą robiła się pionowa (plama dominuje rozrzut), a grot lądował na dalekim końcu cienia (52, 55, 60, też 41, 54, 36, 44, 50).
- `findDart` dostaje `opts.axisAt(x, y)` z `Detector` (kierunek odwrotny do `heightStep`, czyli od lotki do grota). Daleka składowa (> 0,3·`gap` od środka głównej), której środek leży w kierunku poza oknem `axisWin` = [−35°, +45°] względem tej osi (mod 180°), jest odrzucana jeszcze przed PCA (od 24f okno [−35°, +35°], patrz niżej). Prawdziwe rzutki na eksporcie leżą 6–24° od przewidywanej osi, cienie 44–89°.
- Przewidywana oś ma sens tylko przy kamerze z boku (|J| > 0,3 px/mm), inaczej `axisAt` zwraca `null` i nic się nie zmienia. Wyłączenie: `det.dirPrior = false`.
- Wynik na 60 rzutach z `HI=1`: dobre pole 38 → 40, poprawiane stuknięciem 14/23 → 18/23, z szumem 40–41. Część etykiet `auto` w eksporcie jest błędna (cień zaakceptowany po cichu), więc prawdziwa poprawa jest większa niż w liczbach.
- Nadal nie obsługiwane: rzutka, której główna składowa to sam cień (większy od rzutki), oraz dwie rzutki, gdy lotka drugiej zasłania baryłkę pierwszej (próbka 30).

## Grot z cienia rzutki (od 2026.10.19v)
- Piotr (po 19u): czarny grot na czarnym polu jest nie do odróżnienia nawet po rozjaśnieniu, a Dartsmind nie miał z tym problemu. Faktura czarnego pola nie pomaga: ziarno nie jest stałym wzorem między zdjęciem „przed” i „po” (korelacja lokalna ≈ 0,2 na ciemnych polach).
- Pomysł, który działa: cień rzutki to prosta linia zaczynająca się dokładnie w grocie. Tam, gdzie przechodzi przez jasne lub kolorowe pole, widać go w masie zmian jako cienką kreskę w poprzek rzutki. Obraz osi rzutki i obraz linii cienia przecinają się w grocie, nawet gdy sam grot jest niewidoczny.
- `shadowLine(cc, w, det, occ)` (rdzeń): składowe 25–600 px, wydłużone (≥ 2,5, długość ≥ 14 px, pole/długość ≤ 9), pod kątem > 60° do osi, środek kreski ≤ 40 px od przecięcia, przecięcie 8 px przed końcem baryłki do 32 px za nim. Zwraca `det.shadow = {t, dist, len, ang, area}` (t = odległość za końcem baryłki wzdłuż osi, px).
- `fuseShadowTip(det, maxT)`: tylko gdy grot jest „zobaczony” (`seen`) i różni się od cienia o ≥ 6 px, grot przechodzi na przecięcie (t ograniczone do 0..`maxT`), `tipBy = 'shadow'`. Zgadnięty (`prior`) zostaje: typowa długość jest tak samo dobra jak cień (odchylenie ok. 4,5 px wobec ok. 7 px dla cienia).
- Wywołane w `Detector.analyze` po `locateTip`, a w aplikacji jeszcze raz po `hiRefine` (ostry obraz też potrafi „zobaczyć” fałszywy grot na czarnym). Wyłączenie: `cfg.shadowTip = false` (test: `NOSHADOW=1`).
- Wynik na 60 rzutach (`test_rzutow.js`): bez ostrego grotu dobre pole 39 → 43, poprawiane stuknięciem 16/23 → 20/23 (poprawione rzuty 13, 23, 57, 60, żadnego nie zepsuło); z `HI=1` 40 → 42, 18/23 → 20/23, z szumem 4: 42–43.
- Ograniczenie: cień musi być gdzieś widoczny. Gdy cały leży na czarnym polu, nic się nie zmienia (zostaje zgadywanie z długości).
- Od 2026.10.19w Ustawienia wykrywania, „Jaśniejszy obraz z kamery” (`S.settings.ev` 0–3, `applyEv`): kompensacja ekspozycji aparatu (`exposureCompensation`), a gdy jej nie ma, ręczny czas naświetlania × 2^ev (z auto-wartości `S.evBase`). Jasne pola się przepalają, w czerni jest więcej szczegółów. Funkcja próbna, domyślnie 0 (nic się nie zmienia); po zmianie nowe `ref` po 2,5 s. Przetestowane tylko na atrapie kamery Chromium (ścieżka z czasem naświetlania); na S26 nie wiadomo, co przeglądarka udostępnia (komunikat pod suwakiem to mówi). Nie sprawdzone, czy pomaga czarnemu grotowi. Usunięte w 2026.10.28b (przepalało pola, Piotr wrócił do 0).

## Eksport z 2026-10-21 i wersja 2026.10.19x
- Eksport `oko-tarczy-dane-20261021-1837.zip`: 233 próbki (108 z wersji 19w, id 126–233; reszta to stare próbki). Odtworzenie w scratchpadzie jako `rz4`.
  Na żywo 19w: grot z cienia zadziałał 8 razy na 108. Jedna tura (id 190–192, 16:21) z „Jaśniejszym obrazem”: 24–50% kadru przepalone, potem Piotr wrócił do 0.
- Rodzaj błędu A (zły obiekt): długi pionowy cień rzutki bywa największą składową (213) albo przechodzi przez bramkę kierunku z 19t (216). Od 19x `findDart` przed wyborem `main`
  odrzuca składowe wydłużone (≥ 3, `crossElong`) leżące pod kątem > 55° (`crossDeg`) do przewidywanej osi rzutki (`axisAt` w ich środku), o ile coś zostaje.
  Zgubione przy tym w teście tylko „rzuty” bez rzutki (ręka, przesunięty kadr: 80, 119, 78 dają teraz brak rzutki) i 93 (17 → 3, grot na drucie).
- Rodzaj błędu B (grot za krótki): kreska cienia była odrzucana, bo jej środek leżał > 40 px od przecięcia z osią (długa kreska). Od 19x `shadowLine` liczy odstęp od bliższego końca kreski: `gap = dist − len/2` ≤ 35 i `dist` ≤ 100, wybiera najmniejszy `gap`.
- Wynik (`test_rzutow.js`, HI=1): `rz4` dobre pole 158 → 164, poprawiane stuknięciem 47/79 → 54/79; bez HI 154 → 161; z NOISE=4 (ziarna 1–3) 161/156/158 → 163/160/163.
  `rz3` (60 rzutów z 21:26): HI 42 → 43, bez HI 43 → 42 (rzut 28: wykluczona kreska cienia trochę zmieniła oś, grot przeszedł z `seen` na `prior`), z szumem 43/42/42 → 43/42/43.
  Sztuczne rzuty (`sztuczne_rzuty.js`-podobny `synth.js`, 60 rzutów) bez zmian: 54/57.
- Sprawdzone: dla grota `prior` cień nadal nie jest lepszy (mediana błędu 2,3–2,5 px wobec 3,6–5,1 px), dla `seen` jest (1,7–2,4 wobec 3,7–5,9 px), więc reguła z 19v zostaje.
- Odrzucony pomysł: minimalna długość całej rzutki (od końca lotki do grota w mm wysokości, mediana ok. 131, IQR 125–137). Wiele dobrych rzutów ma krótszą (lotka zasłonięta, rzutka pochylona), więc ryzyko większe niż zysk.
- Nadal źle (id ≥ 126): srebrna baryłka na kremowym polu nie trafia do maski (wygląda jak cień), więc koniec baryłki jest za wcześnie i grot za krótki o 20–65 px (146, 163, 187, 201, 203, 207);
  grot za krótki o 8–10 px na czarnym (149, 156, 176, 189); ostry grot (HI) psuje 132, 171, 215, a poprawia 128, 131, 165, 175, 220, 224.

## Eksport z 2026-10-22 i wersja 2026.10.19y
- Eksport `oko-tarczy-dane-20261022-2130.zip`: 302 próbki, w tym 69 z 19x (id 234–302, 19:04–19:23); scratchpad `rz5` (zawiera też wszystkie próbki z `rz4`). Na żywo 59/69 dobrze.
- Najczęstszy błąd: grot o 5–9 px za krótki przy drucie 20/1/5 (`seen`, długość ≈ 0). Profil `locateTip` pokazał, że czarny grot na kremowym polu jest w małej rozdzielczości rozmyty w szare,
  równomierne przyciemnienie, więc `isShadow` brał go za cień, a cień liczył się jak „nietknięte jasne pole” = „grota tu nie ma”.
  Od 19y w `locateTip` piksel zmieniony (> tau), ale uznany za cień (`SH`), jest: „grot jest”, gdy ciemniejszy niż `darkK`·przed, inaczej neutralny (`opt.shadowMode`: 0 = stare, 1 = tylko neutralny, 2 = domyślne).
- `findDart`: próg wydłużenia składowej w poprzek (`crossElong`) 3 → 2,4 (kawałki cienia stykające się z grotem, np. 288, 152, 218). 2,0 psuło 250; kąt 48° zamiast 55° dawał tylko +1, zostało 55°.
- `test_rzutow.js` z `HI=1` przyjmuje teraz ostry grot na tych samych warunkach co aplikacja (≤ 8 mm, a zgadnięty zamiast widzianego ≤ 3 mm; wcześniej 15 mm bez drugiego warunku). Wyniki HI sprzed tej zmiany nie są porównywalne.
- Wynik `rz5` (275 rzutów do odtworzenia): HI 224 → 233, poprawiane stuknięciem 77/108 → 84/108; bez HI 220 → 234; nowe (68 do odtworzenia): HI 59 → 62, bez HI 59 → 64.
  Z NOISE=4 (stary warunek HI) 220/214/222 → 228/225/225. `rz3`: HI 41 → 42, bez HI 42 → 43. Sztuczne rzuty: 54/57 → 54/58.
- Na tych danych ostry grot nic już nie daje (bez HI 234, z HI 233); zostaje włączony, bo na sztucznych rzutach pomaga.
- Nadal źle w nowych: 284 (grot przy drucie; 251 i 260 tylko z HI), 286 i 292 (cień lotki jako duża plama wybrany zamiast rzutki, a prawdziwa rzutka jest poza wycinkiem próbki, więc nie da się tego odtworzyć), 261 (etykieta `auto` 5 jest prawdopodobnie zła, rzutka wisi poza podwójną).

## Cień od lampy pod sufitem (2026.10.24f, eksport z 2026-10-24, 434 próbki)
- Piotr: „cień zamiast grota” zdarza się głównie przy sztucznym świetle, które u niego pada z góry. Pomiar na eksporcie (`rz6` w scratchpadzie, zawiera wszystkie wcześniejsze próbki):
  cień rzutki leży na tarczy prosto w dół od grota (−95…−115° w układzie tarczy, tak samo 21.10, 22.10 i 24.10): cienka kreska, potem plama cienia lotki ok. 90–120 mm pod grotem.
  Od 19w 21 z 309 rzutów na żywo trafiło właśnie w tę plamę (punkt 50–140 mm pod prawdziwym grotem); drugi częsty błąd to grot za krótki wzdłuż rzutki.
- Plama wygrywała na dwa sposoby:
  1. Główna składowa to lotka (dobrze), ale plama leżała w oknie kierunku z 19t (od lotki +40…+47°, okno sięgało +45°), więc była doklejana i grot szedł w plamę (146, 197, 390).
     Teraz `axisWin` = [−35°, +35°] (+ = w stronę dołu obrazu). Całe rzutki leżą −35…+15°, ich kawałki do +34° (przy +25° psuło `rz3` #58, kawałek baryłki pod +28°).
  2. Główna składowa to sama plama (rzutka cienka, rozbita na czarnym). `castSource` porównuje dwa odczytania głównej składowej: jako rzutka (linia długości rzutki od jej przodu, kierunek z `heightStep`)
     i jako cień (grot 8–200 mm wyżej na tarczy, prosto w górę albo do 30° w bok, od niego linia rzutki przez inne zmiany). Miara: część linii pokryta zmianą, najlepsze z przechyleń −20…+20°.
     Gdy cień ≥ 0,5 i o ≥ 0,15 lepszy, główną staje się składowa na tej linii, a plama wypada. `det.cast` (też w próbkach Nauka AI); wyłączenie `det.castShadow = false`.
- Wynik `test_rzutow.js` na `rz6` (405 do odtworzenia): HI 343 → 347, bez HI 344 → 348, poprawiane stuknięciem 92 → 96 / 94 → 98 ze 129 (146, 197, 390, 423); z NOISE=4 SEED=1: 335 → 339.
  `rz3` bez zmian (42/43). `castSource` zadziałał tylko na 423 (0,69 wobec 0,24); u każdego innego rzutu odczytanie „cień” ≤ 0,29.
- Większość plam z 24.10 (411, 414, 418, 427, też 292) ma prawdziwą rzutkę poza wycinkiem próbki, więc offline ich nie widać. Dlatego sztuczne rzuty z cieniem
  (`synth2.js` w scratchpadzie: `synth.js` + cień od lampy, 0,8 mm przesunięcia na mm wysokości pod −105°, lotka cienia r = 18 mm): ciemna rzutka (czarny shaft i lotka, cień 70%) dobre pole 36/57 → 55/59, średni błąd 31,9 → 5,2 mm.
  Zwykłe sztuczne rzuty bez cienia bez zmian (54/58).
- Nie zrobione: uczenie kierunku światła z rzutów (na danych Piotra stały, więc niepotrzebne) i sprawdzanie kierunku kreski w `shadowLine`.

## Porządki w kodzie (2026.10.19z)
- Usunięte nieużywane funkcje rdzenia: `boardOutline`, `quickChange`, `envelopeDist2`, `motionMeasure` (zastąpione `motionMeasureHalf`), `warpAffineRGBA` (aplikacja używa canvasa), `lim.motion`.
- Usunięte stare `extendTip` z `tipModel:'walk'` i `offsetMm`/`applyOffset` (oraz tryby `walk`/`old` w `test_rzutow.js`).
- Usunięty przycisk „Zapisz obraz do analizy” w oknie „Popraw rzut” (`exportDebug`, PNG jednego rzutu): eksport Nauka AI (ZIP) ma to samo i więcej.
- Sprawdzone: `test_rzutow.js` na `rz5` i `rz3` (z HI i bez) daje identyczne listy jak przed porządkami; Playwright t17/t18/t21 bez błędów.

## Okno „Popraw rzut”: jasność, lupa, siatka (od 2026.10.19u)
- Piotr: czarny grot na czarnym polu jest prawie niewidoczny, a on sam ma ocenić miejsce wbicia na powiększeniu.
- Nad obrazem trzy przyciski: „Jasność 0/1/2” (`brightenDark`: ciemne piksele < 90 jasności rozciągane na pełny zakres, od 2. do 92. lub 70. percentyla, więc czarne pole pokazuje fakturę), „Lupa ×1/×2/×3” (okno `fixView` wokół zielonego kółka, a bez niego wokół wykrytego grota; stuknięcie przelicza `fixMap` z uwzględnieniem lupy) i „Siatka wł./wył.” (żółte druty zasłaniały grot).
- Jasność i siatka zostają między rzutami. Od 2026.10.28c zbliżenie otwiera się od razu z lupą ×3 wokół wykrytego grota (prośba Piotra), widok całej tarczy z ×1 (przełączanie zbliżenie/cała tarcza ustawia to samo). Obraz całej tarczy ma teraz 800 px szerokości (było 600, tyle co natywne wideo), żeby lupa miała z czego powiększać.
- Test Playwright (scratchpad `t18.js`/`t19.js`): stuknięcie w środku okna lupy ×1/×2/×3 trafia w to samo miejsce, jasność podnosi średnią jasność obrazu. Na prawdziwym zdjęciu grota (`hicur` rzutu 57) czarne pole po „Jasność 1” pokazuje fakturę, ale grot nadal bywa tak samo ciemny jak pole.

## Poprawka rzutu: cała tarczą (od 2026.10.19s)
- Okno „Popraw rzut” pokazywało tylko wycinek ±70 mm wokół wykrytego grota. Gdy wykrycie trafiło w cień daleko od rzutki, prawdziwego miejsca nie było na obrazie i nie dało się go zaznaczyć (Piotr, 2026-10-19).
- `captureSnap` robi teraz też `snap.wide` (`captureWide`: cała tarcza r = 185 mm w prostokącie 600 px szerokości, proporcje z homografii; `null` przy nieprawdopodobnej kalibracji). Przycisk „Pokaż całą tarczę” / „Pokaż zbliżenie” przełącza widok; w widoku całej tarczy kreskowane czerwone kółko = miejsce wykryte przez aplikację.
- `fixMap` ma osobne `sw/sh/cw/ch`; stuknięcie przelicza się przez wybrany widok. Test Playwright: stuknięcie w widoku całej tarczy daje poprawny wynik.

## Tryby gry i statystyki (od 2026.10.24)
- Rdzeń: `MODES` (x01, cricket, atc = Dookoła tarczy, bob27, score = Wysoki wynik, shanghai). Każdy tryb: `init`, `turn(g, st, p, darts, runda)` → widok tury
  (`after`, `state` open/bust/win, `flags` ok/nohit/void/bust, `total`), opcjonalnie `rounds` (stała liczba rund, wtedy `modeTurn` sam kończy grę stanem `done`
  i wybiera zwycięzcę po `score`), `out` (Bob's 27: odpada przy wyniku ≤ 0, `commitTurn` pomija go w kolejce).
- `replay(g)` odtwarza zapisane tury (stany graczy, liczba rozegranych tur), `currentView` = replay + bieżąca tura. Gra ma `g.mode` i `g.opts`
  (atc: `ring` any/d/t, `bull`, `skip`; score/shanghai: `rounds`). Stare zapisane gry bez `mode` to x01.
- Tura kończąca grę (wygrana albo ostatnia runda) nie jest zatwierdzana (`winner` ustawiane już przy rzucie, jak wcześniej w 501).
- Statystyki: `gameStats(g)` (x01: średnia, pierwsze 9, najlepsza tura, 180/140+/100+, zamknięcie; cricket: znaczniki, MPR; atc: trafienia, skuteczność; reszta: wynik).
  `recordGame` w `afterChange` zapisuje skończoną grę do `localStorage` `history` (maks. 1000), `g.rec` = id; Cofnij usuwa wpis, poprawka przelicza go.
  Menu, „Statystyki”: wybór gracza (po nazwie), kafelki dla każdego trybu, słupki średniej z ostatnich 30 legów, ostatnie 20 gier, „Usuń historię”.
- Okno „Nowa gra” pamięta ostatnie wybory (`localStorage` `newgame`). Głos: `turnSay` (koniec tury/gry), `turnPrompt` (kto i w co celuje).
- Od 2026.10.24b w X01 głos podpowiada zakończenie (`sayRoute` = `C.checkout` → `sayDart`): na początku tury („zostało 121. potrójne 20, potrójne 7, podwójne 20”) i po każdej lotce, jeśli da się zamknąć resztą lotek. Wyłącznik: Ustawienia wykrywania, „Mów podpowiedź zakończenia” (`S.settings.coVoice`).
- Od 2026.10.24c Ustawienia wykrywania: „Głos” (`S.settings.voiceName` = `voiceURI` polskiego głosu z `speechSynthesis.getVoices()`, `fillVoices`), „Tempo mowy” (`S.settings.rate`), „Posłuchaj”, oraz „Śmieszne komentarze po turach” (`S.settings.fun`, domyślnie wył.; `funSay`/`FUN`: 180, 140+, 100+, 26, zero, przerzut, wygrana, trzy trafienia w treningach; bez powtórki tej samej linii). Inne silniki mowy (RHVoice, Acapela, Vocalizer, Google) instaluje się w Androidzie i pojawiają się na liście.
- Od 2026.10.24g w „Dookoła tarczy” po każdym trafieniu głos od razu mówi następny cel („1. Teraz 2”), też przy starcie gry („cel 1”), żeby nie trzeba było podchodzić do tarczy.
- Test: scratchpad `tgame.js` (rdzeń w Node) i `pw.js` (Playwright, liczenie ręczne we wszystkich trybach). Na prawdziwej tarczy z kamerą jeszcze nie sprawdzone.
- Od 2026.10.28d koniec tury (wyjęcie lotek albo „Dalej”) dopisuje brakujące lotki jako pudło (`bounce: true`), o ile tura jest otwarta (nie po przerzucie/wygranej). Odbita lotka albo lotka poza tarczą nie zostawia zmiany na obrazie, więc wcześniej tura miała mniej lotek (Piotr, 2026-10-28).
- Od 2026.10.31c styl czytania (przegląd z Piotrem): `speak` zamienia liczby na słowa (`numPl`, `sayNums`), bo lektor czytał „1.” jak „pierwsze”. Koniec tury: sama liczba („sto!”), przy zerze „Bez punktów”.
  Podpowiedź zakończenia tylko na początku tury i po 2. lotce. Kilku graczy: „Piotr, zostało 81”, wygrana w X01/Cricket „Leg wygrywa …”. Cricket: „22 punkty” (odmiana), sam gracz słyszy „Otwarte: 15, 16, bull”.
  Ustawienia wykrywania, „Czytaj każdą lotkę” (`S.settings.sayEach`, domyślnie wł.; wyłączone: przy lotkach z kamery tylko wynik tury, podpowiedź, następny cel, przerzut i wygrana; `dartLine`). Wpisywanie ręczne zawsze czyta lotkę.
- Od 2026.10.31e lektor ElevenLabs (Piotr; głosy Edge nie są dostępne dla stron na Androidzie): Ustawienia wykrywania, „Lektor ElevenLabs”, klucz API gracza w `localStorage` `eleven` (nigdy w kodzie), „Sprawdź klucz” (`/v1/voices`, `/v1/user/subscription`), głos, jakość (`eleven_flash_v2_5` domyślnie z `language_code: 'pl'`, albo `eleven_multilingual_v2`).
  `speak` → `elSay` (kolejka `EL.q`): zdanie (po `sayNums`) z pamięci Cache API `lektor-el` (klucz: głos/model/tempo/tekst), inaczej pobranie; odpowiedź > `EL_WAIT` = 2,5 s, brak sieci albo błąd → `sysSpeak` (lektor telefonu), błąd daje przerwę 2 min (401/403: 1 h) i wpis `!!`. `speak('')` nadal odblokowuje mowę Androida. Dziennik: `lektor ElevenLabs z pamięci N, pobrane M`.
  Playwright (atrapa API): zły klucz 401, pamięć działa też po odświeżeniu, wolna odpowiedź i brak sieci → lektor telefonu. Na S26 i z prawdziwym API jeszcze nie sprawdzone (CORS, odtwarzanie dźwięku bez stuknięcia).
- Pomysły na dalej: Killer, Cricket „cut-throat”, statystyki trafień (mapa tarczy), eksport historii.

## Model AI grota (od 2026.10.25b)
- Próba na eksporcie z 2026-10-25 (691 próbek, 624 do nauki), sprawdzian po czasie w 5 częściach (każdy rzut ocenia model, który go nie widział):
  model 90% dobrych pól wobec 86% aplikacji na żywo; poprawiane stuknięciem 82% wobec 41%; najnowsze (24e–24g) 227 vs 229 z 247. Model naprawia 61, psuje 40, więc najlepsze będzie łączenie z regułami.
- Łączenie (2026.10.25c, `AI_TRUST` = 0,6): weź model, gdy jego pole różni się od reguł, a pewność ≥ 0,6. Na sprawdzianie 569/624 (91%) wobec reguł 539 i samego modelu 560 (naprawia 54, psuje 24); próg 0,5: 566, 0,7: 566, 0,8: 556.
  Ale na najnowszych rzutach (24e–24g) prawie bez zysku: 230 wobec 229 z 247. Dlatego domyślnie `bg`; korzyść ma przyjść z bardziej różnorodnych danych.
- Wycinek próbki jest ustawiony wokół wykrycia reguł (`debugCrop`), więc model to drugi etap po obecnym wykrywaniu, nie samodzielny detektor.
- Aplikacja: Ustawienia wykrywania, „Model AI grota” (`S.settings.ai`: `off`, `bg` = domyślnie, tylko zapisuje odpowiedź w próbce jako `ai`, `on` = zastępuje wynik reguł, gdy pewność ≥ `AI_TRUST` i gracz nie ruszał rzutki; mówi „Poprawka: …”).
  `aiForDart` po `addDart`, kolejka jednego naraz; `labelOf` liczy przesunięcie od `d.aiTip`, więc zmiana przez model nie jest „tap”. Dziennik: nagłówek „model AI …”, wpisy `!!` przy błędzie wczytania.
- onnxruntime-web 1.29.0 z jsdelivr (`ort.all.min.js`), najpierw `webgl`, potem `wasm`. W Playwright (SwiftShader) ok. 5 s na rzut i wynik identyczny z Pythonem; prawdziwej szybkości na S26 jeszcze nie znamy.
- 2026.10.26c (`?v=2`): douczony na 864 rzutach (eksporty z 25.10 + paczki z GitHuba do 26.10 17:41). Sprawdzian na dwóch najnowszych częściach po 123 rzuty: nowy 114 + 117, stary 113 + 115, reguły 107 + 109; mediana błędu 2,2 mm (stary 2,4–2,5). Paczki z 25–26.10 na żywo: reguły 210/240, model 224, łączenie 222; model zmienił 19 rzutów, 14 dobrze. `train.py` z `LOAD=model.pt` ocenia gotowy model na tym samym sprawdzianie. Nauka 20 przebiegów na procesorze ok. 35 min.
- Od 2026.10.28a domyślnie `on` (decyzja Piotra 2026-10-28). Paczki z 28.10 (151 rzutów z 26d, model 26c ich nie widział, 134 sprawdzone stuknięciem lub potwierdzeniem): reguły na żywo 128/151, model 144; na 146 z odpowiedzią modelu reguły 123, łączenie przy 0,6: 144 (naprawia 21, psuje 0; 0,7: 140, 0,8: 137). Na żywo model zmienił 22 rzuty, 21 dobrze. Mediana błędu przy stuknięciach: model 1,9 mm, reguły 3,8 mm.
  Zmiana dotyczy tylko nowych ustawień: `saveSettings` zapisuje cały obiekt, więc kto już zapisał ustawienia, ma swoje `ai`.
- Od 2026.10.29a przy pewności ≥ `AI_TRUST` punkt modelu jest brany zawsze, także gdy pole się nie zmienia (wtedy po cichu, `d.ai.moved`; `d.ai.used` nadal tylko przy zmianie pola, mówi „Poprawka”).
  Powód (Piotr: „prawie każdy rzut poprawiam o parę mm”): paczki z 29.10, 219 stuknięć, odległość od stuknięcia: reguły mediana 3,4 mm (> 5 mm: 63), model 1,5 mm (> 5 mm: 14), a pokazywany punkt na żywo 3,2 mm, bo przy tym samym polu zostawał punkt reguł. Pole zmieniło stuknięcie tylko w 4 z 219.
- 2026.10.29c (`?v=3`): douczony na 1462 rzutach (eksporty + paczki do 29.10 21:23). Sprawdzian na dwóch najnowszych częściach po 146 rzutów (model `v=2` ich nie widział): nowy 145 + 144, stary 145 + 143, reguły 138 + 130; stuknięte 216 vs 215 ze 219; mediana błędu 1,0–1,2 mm (stary 1,3–1,4), 90% 2,4–2,9 mm (stary 3,4–4,3). Próba z 28.10 (1181 rzutów) dała 289 vs 290 pól i nie była wgrana. Paczki z 29.10 na żywo: reguły 257/281, model 277.
- Od 2026-10-31 (zalecenie 3 audytu, zgoda Piotra) „klasówka”: co czwarta tura po nauce v3 (`narzedzia/model_ai/klasowka.py`) nigdy nie idzie do nauki; nocne zadanie porównuje nowy i stary model na klasówce (`porownaj_modele.py`), wgrywa tylko nie gorszy. Uczciwe są tylko pola przy tap/confirmed i mm przy tap.
- Narzędzia i opis nauki: `narzedzia/model_ai/README.md`. Nie ma tu sztucznych rzutów ani danych z innych tarcz (plan: różne światło, strona kamery, groty, tarcze znajomych).

## Test na prawdziwych rzutach
```
python3 narzedzia/rozpakuj.py eksport.zip /tmp/rzuty
node narzedzia/test_rzutow.js oko-tarczy.html /tmp/rzuty          # V=1: lista, NOISE=4: szum kamery
```
Od 2026-10-26 test pisze też drugą linię (2. i 3. rzutka w turze, grot < 3 mm od drutu, błąd w mm przy stuknięciach), a z `OUT=plik.jsonl` jeden wiersz na rzut.
`python3 narzedzia/porownaj.py przed.jsonl po.jsonl` porównuje dwa przebiegi: osobno rzuty z wersji sprzed 25.10 (do strojenia) i nowsze (sprawdzian), z listą naprawionych i zepsutych.
Audyt z 2026-10-26 (916 rzutów, HI=1): 804 dobrze, stuknięcia 220/277, 2.–3. rzutka 479/557, przy drucie 202/249, mediana błędu przy stuknięciach 4,1 mm; `occ` nic nie zmienia (`occDrop` = 2; filtr usunięty w 28b, sama maska `occ` zostaje w próbkach), strojenie długości grota nic nie daje.
Wynik na eksporcie z 2026-10-17 (77 rzutów, 59 da się odtworzyć), historycznie (tryby `walk`/`old` testu usunięte w 19z):

| Wersja | Dobre pole | Poprawiane stuknięciem | Z szumem kamery |
|---|---|---|---|
| Nowa (17.10) | 43 | 15/22 | 43–44 |
| Stara (`walk`/`old`) | 41 | 13/22 | 39–41, wynik skacze |

Obecne punkty odniesienia: `rz6` (eksport 2026-10-24, 405 rzutów do odtworzenia, zawiera `rz5`) i `rz3` (60 rzutów z 2026-10-19), patrz sekcje 19x/19y i 24f.

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
