"""Podglady: zlozenie (plyta OSB, tarcza, rama na nozkach, 2 telefony) i czesci w orientacji do druku.
Uruchom: python3 podglad.py [katalog]"""
import sys, os
import numpy as np
import sdf as S
import rama as R
import uchwyty as U
import poza as P
import render as Rd

OUT = sys.argv[1] if len(sys.argv) > 1 else 'podglad'
os.makedirs(OUT, exist_ok=True)
PHONES = (0, 6)


def coarse(lohifn, h):
    lo, hi, fn = lohifn
    g, f = S.evaluate(fn, lo, hi, h)
    return S.mesh(g, f)


def rz(deg):
    a = np.radians(deg); c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def box_mesh(lo, hi):
    lo, hi = np.array(lo, float), np.array(hi, float)
    v = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
    f = np.array([[0, 2, 3], [0, 3, 1], [4, 5, 7], [4, 7, 6], [0, 1, 5], [0, 5, 4], [2, 6, 7], [2, 7, 3], [0, 4, 6], [0, 6, 2], [1, 3, 7], [1, 7, 5]])
    return v, f


def cyl_mesh(z0, z1, r, n=96):
    ang = np.linspace(0, 2 * np.pi, n, endpoint=False)
    ring = np.stack([r * np.cos(ang), r * np.sin(ang), np.zeros(n)], 1)
    v = np.concatenate([ring + [0, 0, z0], ring + [0, 0, z1], [[0, 0, z0], [0, 0, z1]]])
    f = []
    for i in range(n):
        j = (i + 1) % n
        f += [[i, j, n + j], [i, n + j, n + i], [2 * n, j, i], [2 * n + 1, n + i, n + j]]
    return v, np.array(f)


def subdiv(m, n):
    """Dzieli kazdy trojkat na 4, n razy (duze sciany psuja kolejnosc rysowania w matplotlib)."""
    tri = m[0][m[1]]
    for _ in range(n):
        a, b, c = tri[:, 0], tri[:, 1], tri[:, 2]
        ab, bc, ca = (a + b) / 2, (b + c) / 2, (c + a) / 2
        tri = np.concatenate([np.stack(x, 1) for x in ((a, ab, ca), (ab, b, bc), (ca, bc, c), (ab, bc, ca))])
    return tri.reshape(-1, 3), np.arange(len(tri) * 3).reshape(-1, 3)


def mv(m, M=np.eye(3), t=(0, 0, 0)):
    return (m[0] @ np.asarray(M).T + np.asarray(t), m[1])


def phone_mount_meshes(k=0):
    """Zblizenie: naroze z ramieniem, uchwytem i telefonem (bez reszty ramy)."""
    hp = 0.7
    grey, dark, blue = (0.92, 0.92, 0.94), (0.33, 0.35, 0.38), (0.25, 0.38, 0.70)
    c = R.RC * np.array([np.cos(np.radians(45 * k)), np.sin(np.radians(45 * k)), 0])
    parts = [(*mv(coarse(R.corner('telefon'), 1.0), rz(45 * k), c), grey),
             (*mv(coarse(R.phone_arm(), hp), rz(45 * k), c), dark)]
    kn = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], float)
    parts.append((*mv(coarse(U.knob(), hp), rz(45 * k) @ kn, c + rz(45 * k) @ np.array([R.HINGE_U, R.ARM_T[1], R.HINGE_Z])), dark))
    M, t = P.pose(k)
    parts.append((*mv(coarse(U.phone_base(), hp), M, t), dark))
    parts.append((*mv(coarse(U.phone_jaw(), hp), M, t + M @ np.array([P.PHONE_BOX[0][1], 0, 0])), dark))
    (x0, x1), (y0, y1), (z0, z1) = P.PHONE_BOX
    parts.append((*mv(subdiv(box_mesh((x0, y0, z0), (x1, y1, z1)), 3), M, t), (0.25, 0.38, 0.70, )))
    W = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]], float)
    return [(v @ W.T, f, col) for v, f, col in parts]


def assembly_meshes():
    hf, hp = 1.6, 0.9
    bar = coarse(R.bar(), hf)
    cor = {k: coarse(R.corner(k), hf) for k in ('telefon', 'noga')}
    leg, plate = coarse(R.leg(), hf), coarse(R.wall_plate(), hf)
    arm, base, jaw, knob = coarse(R.phone_arm(), hp), coarse(U.phone_base(), hp), coarse(U.phone_jaw(), hp), coarse(U.knob(), hp)
    grey, dark, wood, blue, black = (0.92, 0.92, 0.94), (0.33, 0.35, 0.38), (0.80, 0.66, 0.45), (0.25, 0.38, 0.70), (0.13, 0.13, 0.13)
    parts = []
    parts.append((*subdiv(box_mesh((-400, -450, R.Z_OSB - 18), (400, 450, R.Z_OSB)), 5), wood))
    parts.append((*subdiv(cyl_mesh(-38, -0.2, 225.5), 3), black))
    parts.append((*subdiv(cyl_mesh(-0.2, 0.3, 170.0), 3), (0.32, 0.30, 0.26)))
    parts.append((*subdiv(cyl_mesh(0.3, 0.6, 16.0), 1), (0.55, 0.12, 0.10)))
    ap = R.RC * np.cos(R.A22)
    for k in range(8):
        phi = 45 * k
        c = R.RC * np.array([np.cos(np.radians(phi)), np.sin(np.radians(phi)), 0])
        kind = 'noga' if k % 2 else 'telefon'
        parts.append((*mv(cor[kind], rz(phi), c), grey))
        mid = np.radians(phi + 22.5)
        xa = np.array([-np.sin(mid), np.cos(mid), 0]); ya = np.array([np.cos(mid), np.sin(mid), 0])
        parts.append((*mv(bar, np.stack([xa, ya, [0, 0, 1]], 1), ap * np.array([np.cos(mid), np.sin(mid), 0])), grey))
        if kind == 'noga':
            parts.append((*mv(leg, np.eye(3), c), grey))
            parts.append((*mv(plate, np.eye(3), c), dark))
    for k in PHONES:
        c = R.RC * np.array([np.cos(np.radians(45 * k)), np.sin(np.radians(45 * k)), 0])
        parts.append((*mv(arm, rz(45 * k), c), dark))
        kn = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]], float)      # os galki wzdluz t
        parts.append((*mv(knob, rz(45 * k) @ kn, c + rz(45 * k) @ np.array([R.HINGE_U, R.ARM_T[1], R.HINGE_Z])), dark))
        M, t = P.pose(k)
        parts.append((*mv(base, M, t), dark))
        parts.append((*mv(jaw, M, t + M @ np.array([P.PHONE_BOX[0][1], 0, 0])), dark))
        (x0, x1), (y0, y1), (z0, z1) = P.PHONE_BOX
        parts.append((*mv(subdiv(box_mesh((x0, y0, z0), (x1, y1, z1)), 3), M, t), blue))
    # obrot do podgladu: tarcza na scianie (os z swiata poziomo w strone widza, godz. 12 do gory)
    W = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]], float)
    return [(v @ W.T, f, c) for v, f, c in parts]


if __name__ == '__main__':
    parts = assembly_meshes()
    Rd.render(parts, os.path.join(OUT, 'zlozenie.png'), elev=18, azim=-58, size=(10, 9), dpi=120, lim=400,
              title='Rama LED na nozkach + telefony na godz. 3 i 6')
    Rd.render(parts, os.path.join(OUT, 'zlozenie_przod.png'), elev=0, azim=-90, size=(9, 9), dpi=120, lim=420,
              title='Widok od strony gracza')
    Rd.render(parts, os.path.join(OUT, 'zlozenie_bok.png'), elev=0, azim=0, size=(10, 9), dpi=120, lim=330,
              title='Widok z prawej: rama ok. 19 cm przed tarcza, telefon ok. 29 cm')
    Rd.render(phone_mount_meshes(0), os.path.join(OUT, 'uchwyt_telefonu.png'), elev=25, azim=-40, size=(8, 8), dpi=110,
              title='Telefon na godz. 3: ramie, zawias z galka, uchwyt')
    # czesci w orientacji do druku
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import build as B
    tiles = []
    for name, qty, how, rot, h in B.PARTS:
        m = coarse(how(), max(h, 0.8))
        v = S.to_bed(m[0] @ np.asarray(rot).T)
        p = os.path.join(OUT, f'_druk_{name}.png')
        Rd.render([(v, m[1], (0.82, 0.82, 0.86))], p, elev=28, azim=-55, size=(4.2, 4.2), dpi=100, title=f'{name} x{qty}')
        tiles.append(p)
    fig, axs = plt.subplots(3, 3, figsize=(12.6, 12.6))
    for ax, p in zip(axs.ravel(), tiles):
        ax.imshow(plt.imread(p)); ax.set_axis_off()
    for ax in axs.ravel()[len(tiles):]:
        ax.set_axis_off()
    fig.suptitle('Czesci tak, jak leza na stole drukarki (bez podpor)', fontsize=14)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, 'druk_wszystkie.png'), dpi=80)
    for p in tiles:
        os.remove(p)
