# Oko Tarczy: pierścień LED i uchwyty na 2 telefony (druk 3D)

Pierścień zakłada się na tarczę Winmau Blade 6 (średnica 451 mm) i trzyma się na 4 pokrętłach dociskających bok tarczy.
Nic nie przykręcasz do ściany: odkręcasz 4 pokrętła i zdejmujesz pierścień razem z telefonami.
Taśma LED świeci od brzegu nisko nad tarczą (tak jak w ringach „Corona”). Daszek zasłania ją od strony gracza i kamery.

![zlozenie](podglad/zlozenie.png)

## Części do druku (Zortrax M300 Plus, wszystko bez podpór)

| Plik STL | Ile sztuk | Uwagi |
|---|---|---|
| `ring_segment_zwykly.stl` | 3 | |
| `ring_segment_z_dociskiem.stl` | 4 | z gniazdem nakrętki M5 i nóżką opartą o tarczę |
| `ring_segment_z_przewodem.stl` | 1 | z otworem na przewód zasilania |
| `zacisk_na_ring.stl` | 2 | uchwyt rurki na pierścieniu |
| `koncowka_rurki.stl` | 2 | przegub typu GoPro |
| `uchwyt_telefonu.stl` | 2 | telefony 62–88 mm szerokości, do 13 mm grubości z etui |
| `szczeka_telefonu.stl` | 2 | przesuwna szczęka uchwytu |
| `galka_M5.stl` | 16 | pokrętła na śruby i nakrętki M5 |

Pliki są już obrócone tak, jak mają leżeć na stole: segmenty przodem do stołu, a pozostałe części w pozycji bez nawisów.

**Ustawienia w Z-Suite:**
- **Materiał:** Z-PETG albo Z-ULTRAT. Nie PLA, bo taśma LED grzeje się do ok. 40–50°C.
- **Warstwa:** 0,19 mm dla małych części, 0,29 mm dla segmentów (szybciej).
- **Wypełnienie:** średnie (ok. 20–30%).
- **Podpory:** wyłączone. Raft zostaw domyślny.
- **Zużycie:** ok. 0,8–1 kg filamentu. Segment drukuje się kilka godzin.

Pasowanie wypustu w gnieździe ma 0,25 mm luzu na stronę. Jeśli po druku wchodzi za ciasno, przeszlifuj wypust papierem ściernym.

## Lista zakupów

- **Taśma LED COB 24 V, 10 mm, neutralna biel 4000–5000 K, CRI 90 lub więcej:** 2 m (potrzeba ok. 1,45 m).
- **Zasilacz 24 V, co najmniej 1,5 A (36 W)**, z wtykiem 5,5/2,1 mm. Do tego gniazdo DC z zaciskami śrubowymi albo złączka. Nie bierz taniego ściemniacza, bo migotanie przeszkadza kamerze.
- **Śruby M5 i nakrętki:**
  - M5×45 – 4 szt. (dociski do tarczy)
  - M5×20 – 6 szt. (zaciski i rurki)
  - M5×30 – 2 szt. (przeguby)
  - M5×50 – 2 szt. (szczęki telefonów)
  - nakrętki M5 – 14 szt.
- **Wkręty do tworzyw lub drewna 3,5×25:** 16 szt. (łączenie segmentów).
- **Kołek drewniany albo rurka aluminiowa Ø20 mm:** 2 kawałki po ok. 30 cm.
- Opcjonalnie: kawałki filcu albo gumy na końcówki śrub dociskowych.

## Montaż

1. **Nakrętki.** Wciśnij nakrętki M5 w sześciokątne gniazda:
   - w 4 segmentach z dociskiem (wsuwa się je od tyłu pierścienia),
   - w zaciskach, końcówkach rurek i uchwytach telefonów.
2. **Pokrętła.** Śruby wciśnij łbem w sześciokątne gniazdo pokrętła. Przy przegubie GoPro jedno pokrętło trzyma łeb śruby, a drugie nakrętkę.
3. **Złóż pierścień.** Wypust każdego segmentu wchodzi w gniazdo następnego. Każde łączenie skręć 2 wkrętami od zewnętrznej strony. Kolejność dookoła tarczy, patrząc od przodu:
   - zwykły na godzinie 3, z dociskiem na 1:30, zwykły na 12, z dociskiem na 10:30,
   - zwykły na 9, z dociskiem na 7:30, z przewodem na 6, z dociskiem na 4:30.
4. **Taśma LED.** Przyklej taśmę w rowek na wewnętrznej ścianie, dookoła całego pierścienia. Zacznij i skończ przy otworze na przewód na dole. Przewód przełóż przez otwór i podłącz do gniazda DC.
5. **Załóż na tarczę.** Wkręć 4 śruby M5×45 z pokrętłami w segmenty z dociskiem, ale nie dokręcaj. Nasuń pierścień na tarczę tak, żeby 4 nóżki pod daszkiem oparły się o przód tarczy (czarny brzeg). Dokręcaj pokrętła na zmianę, lekko, aż pierścień siedzi równo i się nie rusza.
6. **Uchwyt telefonu.**
   - Zacisk nasuń na pierścień z boku i dokręć pokrętłem od tyłu. Nie zakładaj go na łączenie segmentów ani przy pokrętle docisku.
   - Wsuń rurkę i ustaw ją tak, żeby telefon był ok. 30 cm przed tarczą.
   - Na rurkę nałóż końcówkę i obróć ją tak, żeby oś przegubu biegła wzdłuż pierścienia.
   - Przykręć uchwyt telefonu.
   - Telefon wkładasz ekranem do siebie, aparatem w stronę tarczy. Dosuń szczękę śrubą i obróć przegub tak, żeby aparat celował w bulla.

**Zdejmowanie:** odkręć 4 pokrętła docisku i zdejmij pierścień do przodu. Uchwyty telefonów mogą zostać na pierścieniu.

## Gdzie stawiać telefony

- **Pierwszy telefon:** godzina 3, z prawej strony, tak jak teraz. Kąt wychodzi ok. 43°, a cała tarcza mieści się w kadrze przy zoomie 1×.
- **Drugi telefon:** najlepiej mniej więcej 90° dalej po obwodzie, np. na godzinie 12. Wtedy dwa widoki przecinają się pod dobrym kątem. Dokładne miejsce ustalimy przy przeróbce aplikacji na dwa telefony.
  - Na godzinie 12 skróć rurkę albo wysuń telefon wyżej, bo rzutki lecące w podwójną 20 przechodzą niedaleko.
  - Na godzinie 9 drugi telefon prawie nic nie wnosi, bo patrzy z tej samej osi co pierwszy.

## Uwagi

- Rzutki, które trafią poza tarczę, uderzą w pierścień. Z-PETG to wytrzyma, ale z czasem zostaną ślady.
- Po założeniu pierścienia skalibruj tarczę od nowa w aplikacji. W ustawieniach przywróć długość grota do 14 mm.
- Zmiana wymiarów: wszystkie wymiary są na górze pliku `ring.py` (np. `BOARD_R`, jeśli tarcza ma inną średnicę). Nowe pliki STL tworzy `python3 build.py katalog`.
