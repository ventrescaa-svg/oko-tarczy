"""Kontrola zlozenia: kolizje miedzy czesciami, kadr aparatow, zaslanianie tarczy i tory rzutek.

Telefony na narozach 0 (godz. 3) i 6 (godz. 6). Uruchom: python3 sprawdz.py
"""
import itertools
import types
import numpy as np
import sdf as S
import rama as R
import uchwyty as U
import poza as P

PHONES = (0, 6)


def rz(deg):
    a = np.radians(deg); c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def placed(fn, Rm, t):
    """fn(siatka lokalna) -> sdf; zwraca funkcje punktow swiata (N,3). Rm: kolumny = osie lokalne w swiecie."""
    Rm = np.asarray(Rm, float); t = np.asarray(t, float)

    def f(Q):
        L = (Q - t) @ Rm
        g = types.SimpleNamespace(X=L[:, 0].astype(np.float32), Y=L[:, 1].astype(np.float32), Z=L[:, 2].astype(np.float32), h=0.5)
        return np.asarray(fn(g), float)
    return f


def phone_fn(g):
    (x0, x1), (y0, y1), (z0, z1) = P.PHONE_BOX
    return S.box(g, (x0, x1), (y0, y1), (z0 + 0.3, z1))


def assembly(phones=PHONES):
    parts = {}
    ap = R.RC * np.cos(R.A22)
    for k in range(8):
        phi = 45 * k
        kind = 'noga' if k % 2 else 'telefon'
        c = R.RC * np.array([np.cos(np.radians(phi)), np.sin(np.radians(phi)), 0])
        parts[f'naroze{k}'] = placed(R.corner(kind)[2], rz(phi), c)
        mid = np.radians(phi + 22.5)
        xa = np.array([-np.sin(mid), np.cos(mid), 0]); ya = np.array([np.cos(mid), np.sin(mid), 0])
        parts[f'belka{k}'] = placed(R.bar()[2], np.stack([xa, ya, [0, 0, 1]], 1), ap * np.array([np.cos(mid), np.sin(mid), 0]))
        if kind == 'noga':
            parts[f'noga{k}'] = placed(R.leg()[2], np.eye(3), c)
            parts[f'plytka{k}'] = placed(R.wall_plate()[2], np.eye(3), c)
    for k in phones:
        c = R.RC * np.array([np.cos(np.radians(45 * k)), np.sin(np.radians(45 * k)), 0])
        parts[f'ramie{k}'] = placed(R.phone_arm()[2], rz(45 * k), c)
        M, t = P.pose(k)
        parts[f'uchwyt{k}'] = placed(U.phone_base()[2], M, t)
        parts[f'szczeka{k}'] = placed(U.phone_jaw()[2], M, t + M @ np.array([P.PHONE_BOX[0][1], 0, 0]))
        parts[f'telefon{k}'] = placed(phone_fn, M, t)
    return parts


def collisions(parts, n=3_000_000, seed=1):
    rng = np.random.default_rng(seed)
    box = np.array([[-430, 430], [-430, 430], [-50, 360]])
    pts = rng.uniform(box[:, 0], box[:, 1], size=(n, 3)).astype(np.float32)
    inside = {k: f(pts) < -0.15 for k, f in parts.items()}
    bad = []
    for a, b in itertools.combinations(parts, 2):
        m = int((inside[a] & inside[b]).sum())
        if m:
            bad.append((a, b, m))
    return bad


def hinge_clearance(k, aims=(-60, -30, 0, 32, 60, 90, 120)):
    """Szczelina miedzy ramieniem a uchwytem/telefonem przy roznym pochyleniu telefonu (> 0 = nie dotyka).
    Zwraca liste (kat pochylenia wzgledem ustawienia docelowego, szczelina/2 w mm)."""
    rng = np.random.default_rng(2)
    c = R.RC * np.array([np.cos(np.radians(45 * k)), np.sin(np.radians(45 * k)), 0])
    arm = placed(R.phone_arm()[2], rz(45 * k), c)
    M0, _ = P.pose(k)
    out = []
    for ar in aims:
        M, t = P.pose(k, ar)
        ear = M @ np.array([U.EAR_X, U.EAR_Y[0], U.EAR_Z]) + t
        Q = ear + rng.uniform(-60, 60, size=(600_000, 3))
        a = arm(Q)
        others = [placed(U.phone_base()[2], M, t), placed(phone_fn, M, t),
                  placed(U.phone_jaw()[2], M, t + M @ np.array([P.PHONE_BOX[0][1], 0, 0]))]
        gap = min(float(np.maximum(a, f(Q)).min()) for f in others)
        tilt = np.degrees(np.arccos(np.clip((M @ [0, 0, 1.0]) @ (M0 @ [0, 0, 1.0]), -1, 1)))
        out.append((round(float(np.sign(ar - P.AIM_R) * tilt), 1), round(gap, 2)))
    return out


def occlusion(parts, k):
    c, v, el, es = P.camera(k)
    own = {f'telefon{k}', f'uchwyt{k}', f'szczeka{k}'}
    others = [f for name, f in parts.items() if name not in own]
    base_own = parts[f'uchwyt{k}']
    pts = P.needed_points(k)
    s = np.linspace(0.0, 1.0, 400)[1:-2]
    blocked = []
    for p in pts:
        Q = c + s[:, None] * (p - c)
        far = s * np.linalg.norm(p - c) > 4.0          # pierwsze 4 mm to okienko w uchwycie
        hit = np.min([f(Q) for f in others], axis=0) < 0
        hit |= (base_own(Q) < 0) & far
        if hit.any():
            blocked.append(p)
    return len(blocked), len(pts)


def dart_paths(parts):
    """Tory rzutek: proste od punktu wbicia w strone gracza, opadanie 0..18 st., z boku +-6 st.
    Liczy, ile torow przecina uchwyty i telefony."""
    names = [n for n in parts if n.startswith(('ramie', 'uchwyt', 'szczeka', 'telefon'))]
    hits = {n: 0 for n in names}
    total = 0
    zs = np.linspace(5, 420, 140)
    for r in np.linspace(0, 200, 11):
        for a in np.linspace(0, 2 * np.pi, 36, endpoint=False):
            p0 = np.array([r * np.cos(a), r * np.sin(a), 0])
            for dn in np.radians([0, 6, 12, 18]):          # rzutka opada: wczesniej byla wyzej (+y)
                for lat in np.radians([-6, 0, 6]):
                    d = np.array([np.tan(lat), np.tan(dn), 1.0])
                    Q = p0 + zs[:, None] * d
                    total += 1
                    for n in names:
                        if (parts[n](Q) < 0).any():
                            hits[n] += 1
    return hits, total


if __name__ == '__main__':
    parts = assembly()
    bad = collisions(parts)
    print('kolizje (liczba punktow wspolnych):', bad if bad else 'brak')
    for k in PHONES:
        print(f'--- telefon na narozu {k} (godz. {[3, 1.5, 12, 10.5, 9, 7.5, 6, 4.5][k]})')
        print('  szczelina ramie/uchwyt przy pochyleniu (st., mm):', hinge_clearance(k))
        c, v, el, es = P.camera(k)
        print('  aparat', c.round(1), 'odl. do bulla %.0f mm' % np.linalg.norm(c))
        fl, fs = P.frame_fit(k)
        print('  kadr: dluzszy bok %.2f..%.2f, krotszy %.2f..%.2f (1.0 = krawedz kadru)' % (fl + fs))
        pr, pt = P.px_per_mm(k)
        print('  px/mm przy bullu: %.2f w strone telefonu, %.2f w poprzek' % (pr, pt))
        nb, nt = occlusion(parts, k)
        print(f'  promienie do tarczy i rzutek zasloniete: {nb}/{nt}')
    hits, total = dart_paths(parts)
    print('tory rzutek (z %d) trafiajace w:' % total, {k: v for k, v in hits.items() if v} or 'nic')
