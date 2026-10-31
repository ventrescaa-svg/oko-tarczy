import json, numpy as np, sys, math
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from klasowka import w_klasowce
# Użycie: python3 prep.py katalog_z_rozpakuj dane.npz   (zapisuje też meta.json obok)
D, OUTF = sys.argv[1], sys.argv[2]
m = json.load(open(D + '/manifest.json')); S = m['samples']
W, H = 384, 256
SECT = [20,1,18,4,13,6,10,15,2,17,3,19,7,16,8,11,14,9,12,5]
def score(x, y):
    r = math.hypot(x, y)
    if r <= 6.35: return 'BULL'
    if r <= 15.9: return '25'
    if r > 170: return '0'
    k = ((90 - math.degrees(math.atan2(y, x)) + 9) % 360 + 360) % 360
    n = SECT[int(k // 18) % 20]
    if r >= 160: return 'D%d' % n
    if 97 <= r <= 107: return 'T%d' % n
    return str(n)
def mul(a, b): return (np.array(a).reshape(3,3) @ np.array(b).reshape(3,3))
X, Y, meta = [], [], []
for k, s in enumerate(S):
    i = k + 1; src = s['label']['source']
    if src not in ('tap', 'confirmed', 'auto'): continue
    c = s['crop']; w, h = c['w'], c['h']
    if w > W or h > H: continue
    rd = lambda t: np.fromfile(f'{D}/{i:03d}_{t}.rgba', np.uint8).reshape(h, w, 4)[..., :3]
    ref, cur = rd('ref'), rd('cur')
    if np.array_equal(ref, cur): continue
    tip = s['label'].get('tip') or (s.get('det') or {}).get('tip')   # ostateczne miejsce grota (po stuknięciu, po modelu)
    if not tip: continue
    Hc = mul([1,0,-c['x0'],0,1,-c['y0'],0,0,1], s['proc']['Hp'])   # board mm -> crop px
    a = np.zeros((H, W, 6), np.uint8); a[:h, :w, :3] = ref; a[:h, :w, 3:] = cur
    X.append(a); Y.append(tip)
    app = (s.get('det') or {}).get('label')
    meta.append(dict(id=i, sid=s.get('id'), src=src, label=s['label']['label'], app=app, w=w, h=h, Hc=Hc.tolist(), ts=s['ts'], ver=s.get('app'),
                     hold=w_klasowce(s), ai=(s.get('ai') or {}).get('label')))
# check scorer: crop->board with inverse
bad = 0
for mt, t in zip(meta, Y):
    Hi = np.linalg.inv(np.array(mt['Hc'])); p = Hi @ [t[0], t[1], 1]; lab = score(p[0]/p[2], p[1]/p[2])
    if mt['src'] != 'tap' and lab != mt['label']: bad += 1
print(len(X), 'próbek, w klasówce', sum(m['hold'] for m in meta), '; niezgodne etykiety auto/confirmed vs mój scorer:', bad)
np.savez_compressed(OUTF, X=np.array(X), Y=np.array(Y, np.float32))
json.dump(meta, open(OUTF.rsplit('.', 1)[0] + '.meta.json', 'w'))
