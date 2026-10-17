"""Oko Tarczy - pierscien LED wokol tarczy + uchwyty na 2 telefony (druk 3D, Zortrax M300 Plus).

Uklad wspolrzednych: srodek tarczy = (0,0,0), os z wychodzi z tarczy w strone gracza,
z = 0 to przednia powierzchnia tarczy. Wymiary w mm.
Uruchom: python3 druk3d/ring.py [katalog_wyjsciowy]
"""
import os
import sys
import numpy as np
import sdf as S

# ---------------- parametry ----------------
BOARD_R = 225.5          # Winmau Blade 6: srednica 451 mm
R_IN = 231.0             # wewnetrzna sciana pierscienia (luz 5.5 mm do boku tarczy)
R_OUT = 258.0            # zewnetrzna sciana
R_LIP = 220.0            # wewnetrzna krawedz daszka (zaslania tasme od przodu)
Z_BACK = -12.0           # tyl pierscienia (za przednia powierzchnia tarczy)
Z_FRONT = 19.0           # przod pierscienia
Z_LIP = 15.0             # spod daszka
STRIP_Z = (3.0, 13.6)    # rowek na tasme COB 10 mm (10.6 mm szerokosci)
STRIP_DEPTH = 0.8
SEG = 45.0               # 8 segmentow po 45 stopni
TONGUE_R = (238.0, 251.0)
TONGUE_Z = (-7.0, Z_FRONT)
TONGUE_L = 16.0
FIT = 0.25               # luz na strone w polaczeniach
JOINT_SCREWS = (5.5, 12.0)   # odleglosc wkretow od styku (wzdluz obwodu)
JOINT_SCREW_Z = 2.0
CLAMP_Z = -6.0           # wysokosc srub dociskowych M5 (na boku tarczy)
M5_HOLE = 5.5
M5_NUT_AF = 8.4
H_SEG = 0.45             # rozdzielczosc siatki (mm)

PROFILE = [  # (r, z), przekroj pierscienia
    (R_IN, Z_BACK), (R_OUT - 1.5, Z_BACK), (R_OUT, Z_BACK + 1.5), (R_OUT, Z_FRONT - 1.5),
    (R_OUT - 1.5, Z_FRONT), (R_LIP + 1.0, Z_FRONT), (R_LIP, Z_FRONT - 1.0), (R_LIP, Z_LIP),
    (R_IN, Z_LIP), (R_IN, STRIP_Z[1]), (R_IN + STRIP_DEPTH, STRIP_Z[1]),
    (R_IN + STRIP_DEPTH, STRIP_Z[0]), (R_IN, STRIP_Z[0]),
]


def segment(kind='plain'):
    """kind: 'plain', 'clamp' (docisk do tarczy + nozka), 'power' (otwor na przewod)."""
    th0, th1 = -SEG / 2, SEG / 2
    a1 = np.radians(th1)
    lo = (R_LIP * np.cos(a1) - 10, -R_OUT * np.sin(a1) - 3, Z_BACK - 1)
    hi = (R_OUT + 6, R_OUT * np.sin(a1) + TONGUE_L + 4, Z_FRONT + 1)
    return S.evaluate(lambda g: _segment_field(g, kind), lo, hi, H_SEG)


def _segment_field(g, kind):
    th0, th1 = -SEG / 2, SEG / 2
    body = S.revolve(g, PROFILE, th0, th1)
    # wypust na koncu th1
    u1, t1, z = S.frame_at(th1)
    tongue = S.box(g, TONGUE_R, (-1.0, TONGUE_L), TONGUE_Z, u=u1, v=t1, w=z)
    # lekkie fazowanie konca wypustu (latwiej wcisnac)
    tip = S.box(g, (TONGUE_R[0] + 1.2, TONGUE_R[1] - 1.2), (TONGUE_L - 1.2, TONGUE_L + 5), (TONGUE_Z[0] + 1.2, TONGUE_Z[1] + 5), u=u1, v=t1, w=z)
    tongue = S.diff(tongue, S.diff(S.box(g, (TONGUE_R[0] - 1, TONGUE_R[1] + 1), (TONGUE_L - 1.2, TONGUE_L + 1), (TONGUE_Z[0] - 1, TONGUE_Z[1] + 1), u=u1, v=t1, w=z), tip))
    body = S.union(body, tongue)
    for d in JOINT_SCREWS:   # otwory pilotowe na wkrety 3.5 mm w wypuscie
        o = np.array(u1) * 0 + np.array(t1) * d + np.array(z) * JOINT_SCREW_Z
        body = S.diff(body, S.cyl(g, o, u1, 1.4, TONGUE_R[0] - 3, R_OUT + 3))
    # gniazdo na poczatku th0
    u0, t0, _ = S.frame_at(th0)
    pocket = S.box(g, (TONGUE_R[0] - FIT, TONGUE_R[1] + FIT), (-2.0, TONGUE_L + 0.5), (TONGUE_Z[0] - FIT, Z_FRONT + 2), u=u0, v=t0, w=z)
    body = S.diff(body, pocket)
    for d in JOINT_SCREWS:   # otwory przelotowe 3.8 mm + gniazdo lba wkretu
        o = np.array(t0) * d + np.array(z) * JOINT_SCREW_Z
        body = S.diff(body, S.cyl(g, o, u0, 1.9, R_IN - 2, R_OUT + 3))
        body = S.diff(body, S.cyl(g, o, u0, 3.8, R_OUT - 1.0, R_OUT + 3))
    um, tm, _ = S.frame_at(0.0)
    if kind == 'clamp':
        # sruba dociskowa M5 promieniowo do boku tarczy + gniazdo nakretki wsuwane od tylu
        o = np.array(z) * CLAMP_Z
        body = S.diff(body, S.teardrop(g, o, um, (0, 0, -1), M5_HOLE / 2, BOARD_R - 2, R_OUT + 3))
        nut_c = 244.0
        body = S.diff(body, S.hexprism(g, o + np.array(um) * nut_c, um, tm, M5_NUT_AF, -2.3, 2.3))
        body = S.diff(body, S.box(g, (nut_c - 2.3, nut_c + 2.3), (-M5_NUT_AF / 2, M5_NUT_AF / 2), (Z_BACK - 2, CLAMP_Z), u=um, v=tm, w=z))
        # nozka: opiera sie o przod tarczy i ustala glebokosc
        body = S.union(body, S.box(g, (R_LIP + 0.5, BOARD_R - 1.0), (-4.0, 4.0), (0.0, Z_LIP + 0.5), u=um, v=tm, w=z))
    if kind == 'power':
        o = np.array(z) * ((STRIP_Z[0] + STRIP_Z[1]) / 2)
        body = S.diff(body, S.teardrop(g, o, um, (0, 0, -1), 3.5, R_IN - 2, R_OUT + 3))
    return body


def to_print_segment(verts):
    """Druk przodem do stolu: z_druk = Z_FRONT - z; obrot, zeby lezal ukosnie na stole."""
    v = verts.copy()
    v[:, 2] = Z_FRONT - v[:, 2]
    v[:, 1] = -v[:, 1]       # odbicie lustrzane przez flip z musi zostac skompensowane
    v = S.to_bed(v)
    ang = np.radians(-45)
    R = np.array([[np.cos(ang), -np.sin(ang), 0], [np.sin(ang), np.cos(ang), 0], [0, 0, 1]])
    return S.to_bed(v @ R.T)


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'stl'
    os.makedirs(out, exist_ok=True)
    for kind in ['plain', 'clamp', 'power']:
        g, f = segment(kind)
        v, fc = S.mesh(g, f)
        print(kind, S.check(v, fc))
