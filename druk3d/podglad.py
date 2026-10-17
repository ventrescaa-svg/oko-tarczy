"""Podglady: zlozenie (pierscien + tarcza + 2 uchwyty z telefonami) i czesci w orientacji do druku."""
import sys, os
import numpy as np
import sdf as S
import ring as Rg
import uchwyty as U
import render as Rd

OUT = sys.argv[1] if len(sys.argv) > 1 else 'podglad'
os.makedirs(OUT, exist_ok=True)
HC = 1.0


def coarse(lohifn, h):
    lo, hi, fn = lohifn
    g, f = S.evaluate(fn, lo, hi, h)
    return S.mesh(g, f)


def rz(deg):
    a = np.radians(deg); c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def cyl_mesh(c0, c1, r, n=32):
    c0, c1 = np.array(c0, float), np.array(c1, float)
    ax = c1 - c0; L = np.linalg.norm(ax); ax /= L
    t = np.cross(ax, [1, 0, 0] if abs(ax[0]) < 0.9 else [0, 1, 0]); t /= np.linalg.norm(t)
    b = np.cross(ax, t)
    ang = np.linspace(0, 2 * np.pi, n, endpoint=False)
    ring = np.cos(ang)[:, None] * t + np.sin(ang)[:, None] * b
    v = np.concatenate([c0 + r * ring, c1 + r * ring, [c0, c1]])
    f = []
    for i in range(n):
        j = (i + 1) % n
        f += [[i, j, n + j], [i, n + j, n + i], [2 * n, j, i], [2 * n + 1, n + i, n + j]]
    return v, np.array(f)


def box_mesh(lo, hi):
    lo, hi = np.array(lo, float), np.array(hi, float)
    v = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
    f = np.array([[0, 2, 3], [0, 3, 1], [4, 5, 7], [4, 7, 6], [0, 1, 5], [0, 5, 4], [2, 6, 7], [2, 7, 3], [0, 4, 6], [0, 6, 2], [1, 3, 7], [1, 7, 5]])
    return v, f


if __name__ == '__main__':
    segs = {k: S.mesh(*Rg.segment(k)) for k in []}
    old = Rg.H_SEG; Rg.H_SEG = 1.2
    segs = {k: S.mesh(*Rg.segment(k)) for k in ('plain', 'clamp', 'power')}
    Rg.H_SEG = old
    clamp = coarse(U.ring_clamp(), HC); tend = coarse(U.tube_end(), HC); base = coarse(U.phone_base(), HC); jaw = coarse(U.phone_jaw(), HC)
    grey, dark, wood, blue = (0.9, 0.9, 0.92), (0.35, 0.37, 0.4), (0.78, 0.62, 0.42), (0.25, 0.35, 0.6)
    parts = []
    # tarcza
    bv, bf = cyl_mesh((0, 0, -38), (0, 0, 0), Rg.BOARD_R, 96)
    parts.append((bv, bf, (0.15, 0.15, 0.15)))
    # pierscien: dociski na 45, 135, 225, 315 st., przewod na dole (270)
    order = {0: 'plain', 45: 'clamp', 90: 'plain', 135: 'clamp', 180: 'plain', 225: 'clamp', 270: 'power', 315: 'clamp'}
    for ang, k in order.items():
        v, f = segs[k]
        parts.append((v @ rz(ang).T, f, grey))
    # uchwyty telefonow: 3 i 12 godzina
    sock_r = Rg.R_OUT + 25
    tube_top = 290.0
    for ang in (0, 90):
        R = rz(ang)
        parts.append((clamp[0] @ R.T, clamp[1], dark))
        tv, tf = cyl_mesh((sock_r, 0, -8), (sock_r, 0, tube_top), 10.0)
        parts.append((tv @ R.T, tf, wood))
        ev = tend[0] + np.array([sock_r, 0, tube_top - 28])
        parts.append((ev @ R.T, tend[1], dark))
        hinge = np.array([sock_r, 0, tube_top - 28 + 41])
        d = -hinge / np.linalg.norm(hinge)
        sa, ca = -d[0], -d[2]
        al = np.arctan2(sa, ca)
        Ry = np.array([[np.cos(al), 0, np.sin(al)], [0, 1, 0], [-np.sin(al), 0, np.cos(al)]])
        def place(v):
            return ((v - np.array([0, 0, -9])) @ Ry.T + hinge) @ R.T
        parts.append((place(base[0]), base[1], dark))
        parts.append((place(jaw[0] + np.array([21, 0, 0])), jaw[1], dark))
        pv, pf = box_mesh((-56, -70, 8), (21, 92, 17))
        parts.append((place(pv), pf, blue))
    Rd.render(parts, os.path.join(OUT, 'zlozenie.png'), elev=22, azim=-35, size=(10, 9), title='Pierscien LED + 2 telefony (3 i 12 godz.)')
    Rd.render(parts, os.path.join(OUT, 'zlozenie_przod.png'), elev=88, azim=-90, size=(9, 9), title='Widok od strony gracza')
    # czesci w orientacji do druku
    for name, m in [('uchwyt_telefonu', base), ('zacisk_na_ring', clamp), ('koncowka_rurki', tend), ('szczeka_telefonu', jaw)]:
        v = S.to_bed(m[0] @ U.PRINT[name].T)
        Rd.render([(v, m[1], (0.8, 0.8, 0.85))], os.path.join(OUT, f'druk_{name}.png'), elev=25, azim=-50, size=(5, 5), title=name + ' (jak na stole)')
    v = Rg.to_print_segment(segs['clamp'][0])
    Rd.render([(v, segs['clamp'][1], (0.8, 0.8, 0.85))], os.path.join(OUT, 'druk_segment.png'), elev=35, azim=-60, size=(6, 6), title='segment (przodem do stolu)')
