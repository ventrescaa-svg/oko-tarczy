"""Rozpakowuje eksport "Nauka AI" (ZIP) do katalogu z surowymi obrazami RGBA dla test_rzutow.js.
Użycie: python3 narzedzia/rozpakuj.py eksport.zip [eksport-cz2z3.zip ...] katalog_wyjsciowy
Eksport w częściach (-cz1z3, -cz2z3, ...): podaj wszystkie części, próbki są łączone po kolei."""
import json, os, sys, zipfile, io
from PIL import Image
import numpy as np

zps, out = sys.argv[1:-1], sys.argv[-1]
os.makedirs(out, exist_ok=True)
man, i = None, 0
for zp in zps:
    with zipfile.ZipFile(zp) as z:
        m = json.loads(z.read('manifest.json'))
        if man is None: man = m
        else: man['samples'] += m['samples']
        for s in m['samples']:
            i += 1
            for k in ('ref', 'cur', 'hiRef', 'hiCur', 'mask', 'occ'):
                if k not in s['files']: continue
                im = Image.open(io.BytesIO(z.read(s['files'][k]))).convert('RGBA')   # mask/occ: 0 albo 255
                np.asarray(im, dtype=np.uint8).tofile(os.path.join(out, f'{i:03d}_{k.lower()}.rgba'))
man['count'] = len(man['samples'])
man.pop('part', None)
with open(os.path.join(out, 'manifest.json'), 'w') as f:
    json.dump(man, f)
print(len(man['samples']), 'rzutów ->', out)
