"""Porównuje dwa przebiegi test_rzutow.js (OUT=plik.jsonl) na tym samym zbiorze rzutów.
Użycie: python3 narzedzia/porownaj.py przed.jsonl po.jsonl [RRRR.MM.DD]
Dzieli rzuty na część do strojenia (wersja aplikacji starsza niż podana data, domyślnie 2026.10.25)
i sprawdzian (nowsze). Zmianę stroi się tylko na pierwszej części; sprawdzian ma potwierdzić,
że to nie przypadek. Dla każdej części: dobre pole przed -> po, ile rzutów naprawia (+) i psuje (-)."""
import json, sys

def load(f):
    rows = (json.loads(l) for l in open(f) if l.strip())
    return {(r.get('sid') or r['id']): r for r in rows}

A, B = load(sys.argv[1]), load(sys.argv[2])
cut = sys.argv[3] if len(sys.argv) > 3 else '2026.10.25'
common = [k for k in A if k in B]
if len(common) != len(A) or len(common) != len(B):
    print(f'UWAGA: różne zbiory rzutów ({len(A)} i {len(B)}, wspólnych {len(common)}); porównuję tylko wspólne.')

def line(name, keys):
    if not keys: return
    a = sum(A[k]['good'] for k in keys); b = sum(B[k]['good'] for k in keys)
    fx = [A[k]['id'] for k in keys if B[k]['good'] and not A[k]['good']]
    br = [A[k]['id'] for k in keys if A[k]['good'] and not B[k]['good']]
    t = [k for k in keys if A[k]['src'] == 'tap']
    ta = sum(A[k]['good'] for k in t); tb = sum(B[k]['good'] for k in t)
    g = [k for k in keys if A[k].get('dartsInTurn', 1) > 1]
    w = [k for k in keys if A[k].get('wire') is not None and A[k]['wire'] < 3]
    print(f"{name}: {len(keys)} rzutów | dobre pole {a} -> {b} (naprawia {len(fx)}, psuje {len(br)}) | stuknięcia {ta} -> {tb}/{len(t)}"
          f" | 2.-3. w turze {sum(A[k]['good'] for k in g)} -> {sum(B[k]['good'] for k in g)}/{len(g)}"
          f" | blisko drutu {sum(A[k]['good'] for k in w)} -> {sum(B[k]['good'] for k in w)}/{len(w)}")
    if fx: print('   naprawione:', ' '.join(map(str, fx[:40])))
    if br: print('   zepsute:   ', ' '.join(map(str, br[:40])))

line('do strojenia (przed ' + cut + ')', [k for k in common if (A[k].get('app') or '') < cut])
line('sprawdzian (od ' + cut + ')', [k for k in common if (A[k].get('app') or '') >= cut])
