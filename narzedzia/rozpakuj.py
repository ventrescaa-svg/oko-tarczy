"""Rozpakowuje eksport "Nauka AI" (ZIP) do katalogu z surowymi obrazami RGBA dla test_rzutow.js.
Użycie: python3 narzedzia/rozpakuj.py eksport.zip katalog_wyjsciowy"""
import json, os, sys, zipfile, io
from PIL import Image
import numpy as np

zp, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
with zipfile.ZipFile(zp) as z:
    man = json.loads(z.read('manifest.json'))
    for i, s in enumerate(man['samples'], 1):
        for k in ('ref', 'cur', 'hiRef', 'hiCur'):
            if k not in s['files']: continue
            im = Image.open(io.BytesIO(z.read(s['files'][k]))).convert('RGBA')
            np.asarray(im, dtype=np.uint8).tofile(os.path.join(out, f'{i:03d}_{k.lower()}.rgba'))
    with open(os.path.join(out, 'manifest.json'), 'w') as f:
        json.dump(man, f)
print(len(man['samples']), 'rzutów ->', out)
