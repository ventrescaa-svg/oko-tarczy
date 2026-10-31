# Porównanie dwóch modeli na klasówce: python3 porownaj_modele.py stary.json nowy.json
# (pliki z train.py: KLASOWKA=1 LOAD=... OUT=...). Kod wyjścia 0 = nowy można wgrać, 1 = nie.
# Liczą się tylko rzuty sprawdzone przez gracza: pole przy „tap”/„confirmed”, milimetry przy „tap”.
import json, sys, statistics as st
MIN_SPR = 100   # poniżej tylu sprawdzonych rzutów klasówka tylko ostrzega, decyduje dotychczasowy sprawdzian po czasie
a, b = (json.load(open(f)) for f in sys.argv[1:3])
A, B = {r['sid'] or r['id']: r for r in a}, {r['sid'] or r['id']: r for r in b}
ids = [k for k in A if k in B and A[k]['src'] in ('tap', 'confirmed')]
taps = [k for k in ids if A[k]['src'] == 'tap']
ok = lambda R, k: R[k]['model'] == R[k]['label']
pa, pb = sum(ok(A, k) for k in ids), sum(ok(B, k) for k in ids)
ma = st.median([A[k]['err'] for k in taps]) if taps else float('nan')
mb = st.median([B[k]['err'] for k in taps]) if taps else float('nan')
print(f'klasówka: sprawdzonych {len(ids)} (stuknięte {len(taps)})')
print(f'dobre pole: stary {pa}, nowy {pb}  |  błąd przy stuknięciach (mediana mm): stary {ma:.2f}, nowy {mb:.2f}')
print('naprawia:', [A[k]['id'] for k in ids if ok(B, k) and not ok(A, k)], ' psuje:', [A[k]['id'] for k in ids if ok(A, k) and not ok(B, k)])
lepszy = pb >= pa and (len(taps) < 20 or mb <= ma + 0.2)
if len(ids) < MIN_SPR: print(f'za mało rzutów w klasówce (< {MIN_SPR}): tylko informacyjnie')
print('WYNIK:', 'nowy nie gorszy' if lepszy else 'nowy GORSZY, nie wgrywać')
sys.exit(0 if lepszy else 1)
