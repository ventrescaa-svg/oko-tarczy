import json, numpy as np, torch, torch.nn as nn, torch.nn.functional as F, math, sys, time, os
torch.manual_seed(int(os.environ.get('SEED', 0))); np.random.seed(int(os.environ.get('SEED', 0)))
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
# Użycie: python3 train.py dane.npz   (ALL=1 EP=20 SAVE=model.pt: na wszystkim; FOLD=0/5 EP=10: sprawdzian po czasie)
DATA = sys.argv[1]
d = np.load(DATA); X, Y = d['X'], d['Y']
meta = json.load(open(DATA.rsplit('.', 1)[0] + '.meta.json'))
N, H, W, _ = X.shape
NTEST = int(os.environ.get('NTEST', 160))
order = np.argsort([m['id'] for m in meta])
test = order[-NTEST:]; train = order[:-NTEST]
if os.environ.get('ALL'): train = order
if os.environ.get('FOLD'):   # time folds: test = fold-th block
    f, K = map(int, os.environ['FOLD'].split('/')); blk = np.array_split(order, K)
    test = blk[f]; train = np.concatenate([b for j, b in enumerate(blk) if j != f])
S2 = 2  # output stride
class Net(nn.Module):
    def __init__(s, c=24):
        super().__init__()
        def blk(i, o, st=1): return nn.Sequential(nn.Conv2d(i, o, 3, st, 1), nn.BatchNorm2d(o), nn.ReLU(), nn.Conv2d(o, o, 3, 1, 1), nn.BatchNorm2d(o), nn.ReLU())
        s.e1 = blk(9, c, 2); s.e2 = blk(c, 2*c, 2); s.e3 = blk(2*c, 4*c, 2); s.e4 = blk(4*c, 4*c, 2)
        s.d3 = blk(8*c, 4*c); s.d2 = blk(6*c, 2*c); s.d1 = blk(3*c, c); s.out = nn.Conv2d(c, 1, 1)
    def forward(s, x):
        e1 = s.e1(x); e2 = s.e2(e1); e3 = s.e3(e2); e4 = s.e4(e3)
        u = lambda a, b: torch.cat([F.interpolate(a, size=b.shape[2:], mode='bilinear', align_corners=False), b], 1)
        d3 = s.d3(u(e4, e3)); d2 = s.d2(u(d3, e2)); d1 = s.d1(u(d2, e1))
        return s.out(d1)[:, 0]
def batch(idx, aug):
    xs, ts, ms = [], [], []
    for i in idx:
        mt = meta[i]; w, h = mt['w'], mt['h']
        a = X[i, :h, :w].astype(np.float32) / 255
        t = Y[i].copy()
        if aug:
            g = np.random.uniform(0.7, 1.3) * np.random.uniform(0.92, 1.08, 3)
            a[..., :3] *= g; a[..., 3:] *= g * np.random.uniform(0.95, 1.05)
            a += np.random.normal(0, np.random.uniform(0, 0.02), a.shape).astype(np.float32)
            a = np.clip(a, 0, 1)
            ox, oy = np.random.randint(0, W - w + 1), np.random.randint(0, H - h + 1)
        else: ox = oy = 0
        c = np.zeros((H, W, 9), np.float32); c[oy:oy+h, ox:ox+w, :6] = a
        c[oy:oy+h, ox:ox+w, 6:] = a[..., 3:] - a[..., :3]
        m = np.zeros((H // S2, W // S2), np.float32); m[oy // S2:(oy + h) // S2, ox // S2:(ox + w) // S2] = 1
        xs.append(c.transpose(2, 0, 1)); ts.append([t[0] + ox, t[1] + oy]); ms.append(m)
    return torch.tensor(np.array(xs)), torch.tensor(np.array(ts, np.float32)), torch.tensor(np.array(ms))
gy, gx = torch.meshgrid(torch.arange(H // S2).float(), torch.arange(W // S2).float(), indexing='ij')
gx = gx * S2 + (S2 - 1) / 2; gy = gy * S2 + (S2 - 1) / 2
def loss_fn(o, t, m, wgt):
    o = o.masked_fill(m == 0, -1e4)
    sig = 3.0
    tg = torch.exp(-((gx[None] - t[:, 0, None, None]) ** 2 + (gy[None] - t[:, 1, None, None]) ** 2) / (2 * sig * sig)) * m
    tg = tg / tg.sum((1, 2), keepdim=True).clamp_min(1e-6)
    lp = F.log_softmax(o.flatten(1), 1).view_as(o)
    return (-(tg * lp).sum((1, 2)) * wgt).mean()
def predict(o, m):
    o = o.masked_fill(m == 0, -1e4); B = o.shape[0]
    P = torch.softmax(o.flatten(1), 1).view_as(o)
    k = o.flatten(1).argmax(1); yi, xi = k // o.shape[2], k % o.shape[2]
    out = []
    for b in range(B):
        y0, y1, x0, x1 = max(0, yi[b]-2), yi[b]+3, max(0, xi[b]-2), xi[b]+3
        p = torch.softmax(o[b, y0:y1, x0:x1].flatten(), 0).view(y1 - y0, x1 - x0)
        c0, c1, r0, r1 = max(0, xi[b]-3), xi[b]+4, max(0, yi[b]-3), yi[b]+4
        out.append([(p * gx[y0:y1, x0:x1]).sum().item(), (p * gy[y0:y1, x0:x1]).sum().item(), P[b, r0:r1, c0:c1].sum().item()])
    return np.array(out)
net = Net(); torch.set_num_threads(4)
EP = int(os.environ.get('EP', 50)); BS = 16
opt = torch.optim.AdamW(net.parameters(), 2e-3, weight_decay=1e-4)
sched = torch.optim.lr_scheduler.OneCycleLR(opt, 2e-3, total_steps=EP * math.ceil(len(train) / BS))
wt = np.array([3.0 if meta[i]['src'] == 'tap' else 1.0 for i in range(N)], np.float32)
t0 = time.time()
for ep in range(EP):
    net.train(); p = np.random.permutation(train); L = 0
    for b in range(0, len(p), BS):
        idx = p[b:b+BS]; x, t, m = batch(idx, True)
        l = loss_fn(net(x), t, m, torch.tensor(wt[idx])); opt.zero_grad(); l.backward(); opt.step(); sched.step(); L += l.item() * len(idx)
    if ep % 10 == 9 or ep == EP - 1: print(f'ep {ep+1} loss {L/len(p):.3f} {time.time()-t0:.0f}s', flush=True)
net.eval(); res = []
if os.environ.get('SAVE'): torch.save(net.state_dict(), os.environ['SAVE'])
with torch.no_grad():
    for b in range(0, len(test), 16):
        idx = test[b:b+16]; x, t, m = batch(idx, False); pr = predict(net(x), m)
        for i, q in zip(idx, pr):
            mt = meta[i]; Hi = np.linalg.inv(np.array(mt['Hc'])); v = Hi @ [q[0], q[1], 1]; lab = score(v[0]/v[2], v[1]/v[2])
            v2 = Hi @ [Y[i][0], Y[i][1], 1]; err = math.hypot(v[0]/v[2] - v2[0]/v2[2], v[1]/v[2] - v2[1]/v2[2])
            res.append(dict(id=mt['id'], src=mt['src'], label=mt['label'], app=mt['app'], model=lab, err=err, conf=q[2]))
json.dump(res, open(os.environ.get('OUT', 'wyniki.json'), 'w'))
n = len(res); mo = sum(r['model'] == r['label'] for r in res); ap = sum(r['app'] == r['label'] for r in res)
tp = [r for r in res if r['src'] == 'tap']
print(f'test {n} (id {min(r["id"] for r in res)}-{max(r["id"] for r in res)}): model {mo}, aplikacja na żywo {ap} | tap {len(tp)}: model {sum(r["model"]==r["label"] for r in tp)}, app {sum(r["app"]==r["label"] for r in tp)}')
e = np.array([r['err'] for r in res]); et = np.array([r['err'] for r in tp])
print(f'błąd mm mediana {np.median(e):.1f}, 90% {np.percentile(e,90):.1f} | tap mediana {np.median(et):.1f}, 90% {np.percentile(et,90):.1f}')

