"""Rozpakowuje eksport "Nauka AI" (ZIP) do katalogu z surowymi obrazami RGBA dla test_rzutow.js.
Użycie: python3 narzedzia/rozpakuj.py eksport.zip [eksport-cz2z3.zip ...] katalog_wyjsciowy
Eksport w częściach (-cz1z3, ...) albo paczki z GitHuba (oko-tarczy-dane/paczki/*.zip): podaj wszystkie.
Ten sam rzut (to samo id) w kilku plikach: zostaje wersja z pliku podanego później (paczki mają czas w nazwie,
więc `paczki/*.zip` jest już po kolei). Rzuty są układane według czasu."""
import json, os, sys, zipfile, io
from PIL import Image
import numpy as np

zps, out = sys.argv[1:-1], sys.argv[-1]
os.makedirs(out, exist_ok=True)
man, samples, cals = None, {}, {}
for zi, zp in enumerate(zps):
    with zipfile.ZipFile(zp) as z:
        m = json.loads(z.read('manifest.json'))
        if man is None: man = {k: v for k, v in m.items() if k not in ('samples', 'cals', 'part')}
        for si, s in enumerate(m['samples']): samples[s.get('id') or f'{zi}-{si}'] = (zi, s)
        # od 2026.10.25d: zdjęcia z kalibracji (cal/*.jpg + homografia H tarcza mm -> px wideo) i dziennik czasów
        for ci, c in enumerate(m.get('cals', [])): cals[c.get('id') or f'{zi}-c{ci}'] = (zi, c)
        if 'dziennik.txt' in z.namelist():   # najnowszy wygrywa
            with open(os.path.join(out, 'dziennik.txt'), 'wb') as f: f.write(z.read('dziennik.txt'))
zf = [zipfile.ZipFile(zp) for zp in zps]
S = sorted(samples.values(), key=lambda t: t[1].get('ts', 0))
for i, (zi, s) in enumerate(S, 1):
    # od 2026.10.26d: cały obraz przetwarzania przed/po i pełna maska (fullRef/fullCur/fullMask)
    for k in ('ref', 'cur', 'hiRef', 'hiCur', 'mask', 'occ', 'fullRef', 'fullCur', 'fullMask'):
        if k not in s['files']: continue
        im = Image.open(io.BytesIO(zf[zi].read(s['files'][k]))).convert('RGBA')   # mask/occ: 0 albo 255
        np.asarray(im, dtype=np.uint8).tofile(os.path.join(out, f'{i:03d}_{k.lower()}.rgba'))
CL = []
for j, (zi, c) in enumerate(sorted(cals.values(), key=lambda t: t[1].get('ts', 0)), 1):
    os.makedirs(os.path.join(out, 'cal'), exist_ok=True)
    name = f"cal/{j:03d}-{c.get('tag', 'cal')}.jpg"
    with open(os.path.join(out, name), 'wb') as f: f.write(zf[zi].read(c['file']))
    CL.append(dict(c, file=name))
man = man or {}
man.update(samples=[s for _, s in S], cals=CL, count=len(S))
with open(os.path.join(out, 'manifest.json'), 'w') as f:
    json.dump(man, f)
print(len(S), 'rzutów,', len(CL), 'zdjęć z kalibracji ->', out)
