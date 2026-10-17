"""Uchwyt telefonu na pierscien: zacisk na pierscien z gniazdem rurki 20 mm, koncowka rurki z zawiasem
typu GoPro, uchwyt telefonu z przesuwna szczeka, galki do srub M5.
Kazda funkcja zwraca (lo, hi, fn) w ukladzie lokalnym czesci; orientacja do druku w PRINT."""
import numpy as np
import sdf as S
import ring as Rg

M5 = 2.75          # promien otworu M5
NUT_AF = 8.4
NUT_T = 4.4
TUBE_R = 10.2      # rurka/kolek 20 mm
GP_R = 7.5         # promien palcow zawiasu GoPro
GP_HOLE = 2.65
# palce 3-zebne (y) i 2-zebne (y)
GP3 = [(-7.6, -4.6), (-1.5, 1.5), (4.6, 7.6)]
GP2 = [(-4.45, -1.65), (1.65, 4.45)]


def _gp_fingers(g, fingers, base_z, hinge_dz, sign, widen=False):
    """Palce zawiasu w plaszczyznach y=const; os zawiasu wzdluz y w odleglosci hinge_dz od podstawy
    (sign=+1: w gore osi z, -1: w dol). widen=True dodaje skos 45 st. po stronie -x (druk bez podpor)."""
    hz = base_z + sign * hinge_dz
    out = None
    for y0, y1 in fingers:
        a, b = (base_z, hz) if sign > 0 else (hz, base_z)
        f = S.box(g, (-GP_R, GP_R), (y0, y1), (a - 0.01, b + 0.01))
        f = S.union(f, S.cyl(g, (0, 0, hz), (0, 1, 0), GP_R, y0, y1))
        if widen:
            # trojkat od podstawy do zawiasu po stronie -x
            poly = [(-GP_R, hz), (-GP_R - abs(hinge_dz), base_z), (-GP_R, base_z)]
            f = S.union(f, _tri_xz(g, poly, y0, y1))
        f = S.diff(f, S.cyl(g, (0, 0, hz), (0, 1, 0), GP_HOLE, y0 - 1, y1 + 1))
        out = f if out is None else S.union(out, f)
    return out


def _tri_xz(g, poly, y0, y1):
    # wielokat w plaszczyznie (x, z), wyciagniety wzdluz y
    X, Z = np.broadcast_arrays(g.X + 0 * g.Z, g.Z + 0 * g.X)
    X = np.broadcast_to(X, np.broadcast_shapes(X.shape, g.Y.shape))
    Z = np.broadcast_to(Z, X.shape)
    d = S.polygon_sdf2(X, Z, poly)
    Y = np.broadcast_to(g.Y, X.shape)
    return np.maximum(d, np.maximum(y0 - Y, Y - y1)).astype(np.float32)


# ---------- zacisk na pierscien + gniazdo rurki ----------
# uklad: x = promien pierscienia, y = styczna, z = os tarczy (jak w ring.py dla kata 0)
def ring_clamp():
    RO, ZF, ZB = Rg.R_OUT, Rg.Z_FRONT, Rg.Z_BACK
    W = 18.0
    sock_r = RO + 7 + 18      # os rurki
    lo = (236 - 2, -W - 2, ZB - 10)
    hi = (sock_r + 20, W + 2, 47)

    def fn(g):
        jaw_f = S.box(g, (238.0, RO + 7), (-W, W), (ZF + 0.3, ZF + 6.3))
        bridge = S.box(g, (RO + 0.4, RO + 7), (-W, W), (ZB - 8, ZF + 6.3))
        jaw_b = S.box(g, (240.0, RO + 7), (-W, W), (ZB - 8, ZB - 0.4))
        sock = S.box(g, (RO + 6, sock_r + 18), (-W, W), (-6.0, 46.0))
        body = S.union(jaw_f, bridge, jaw_b, sock)
        # sruba dociskowa M5 od tylu w osi z, nakretka w tylnej szczece (wsuwana od srodka)
        sx = 249.0
        body = S.diff(body, S.teardrop(g, (sx, 0, 0), (0, 0, 1), (0, 1, 0), M5, ZB - 12, ZB + 1))
        zc = ZB - 4.2
        body = S.diff(body, S.hexprism(g, (sx, 0, zc), (0, 0, 1), (0, 1, 0), NUT_AF, -NUT_T / 2, NUT_T / 2))
        body = S.diff(body, S.box(g, (230.0, sx), (-NUT_AF / 2, NUT_AF / 2), (zc - NUT_T / 2, zc + NUT_T / 2)))
        # gniazdo rurki (przelotowe, lezka do druku)
        body = S.diff(body, S.teardrop(g, (sock_r, 0, 0), (0, 0, 1), (0, 1, 0), TUBE_R, -10, 50))
        # sruba ustalajaca rurke wzdluz y, nakretka wsuwana od przodu (z)
        zs = 20.0
        body = S.diff(body, S.cyl(g, (sock_r, 0, zs), (0, 1, 0), M5, 0, W + 2))
        yc = TUBE_R + 4.0
        body = S.diff(body, S.hexprism(g, (sock_r, yc, zs), (0, 1, 0), (1, 0, 0), NUT_AF, -NUT_T / 2, NUT_T / 2))
        body = S.diff(body, S.box(g, (sock_r - NUT_AF / 2, sock_r + NUT_AF / 2), (yc - NUT_T / 2, yc + NUT_T / 2), (zs, 50)))
        return body
    return lo, hi, fn


# ---------- koncowka rurki z zawiasem (2 palce) ----------
def tube_end():
    B = 18.0
    L = 32.0
    lo = (-B - 2, -B - 2, -2)
    hi = (B + 2, B + 2, L + 9 + GP_R + 2)

    def fn(g):
        body = S.box(g, (-B, B), (-B, B), (0.0, L))
        body = S.diff(body, S.cyl(g, (0, 0, -1), (0, 0, 1), TUBE_R, 0, 28.0))
        # sruba ustalajaca wzdluz x, nakretka wsuwana od gory (szczelina w z)
        zs = 13.0
        body = S.diff(body, S.cyl(g, (0, 0, zs), (1, 0, 0), M5, 0, B + 2))
        xc = TUBE_R + 4.0
        body = S.diff(body, S.hexprism(g, (xc, 0, zs), (1, 0, 0), (0, 1, 0), NUT_AF, -NUT_T / 2, NUT_T / 2))
        body = S.diff(body, S.box(g, (xc - NUT_T / 2, xc + NUT_T / 2), (-NUT_AF / 2, NUT_AF / 2), (zs, L + 1)))
        body = S.union(body, _gp_fingers(g, GP2, L - 0.01, 9.0, +1))
        return body
    return lo, hi, fn


# ---------- uchwyt telefonu (podstawa) ----------
PH_X = 62.0        # pol dlugosci podstawy (w poprzek telefonu)
PH_Y = 23.0        # pol szerokosci (wzdluz telefonu)


def phone_base():
    YW = PH_Y + 3.0           # plyta szersza o boczne prowadnice
    lo = (-PH_X - 2, -YW - 2, -9 - GP_R - 2)
    hi = (PH_X + 2, YW + 2, 26)

    def fn(g):
        body = S.box(g, (-PH_X, PH_X), (-YW, YW), (0.0, 8.0))
        body = S.union(body, S.box(g, (-PH_X, -PH_X + 6), (-YW, YW), (0.0, 24.0)))          # stala szczeka
        body = S.union(body, S.box(g, (-PH_X + 5.9, -PH_X + 10), (-YW, YW), (21.0, 24.0)))   # wywiniecie
        body = S.union(body, S.box(g, (PH_X - 8, PH_X), (-YW, YW), (0.0, 24.0)))           # blok sruby
        # kanal na stope przesuwnej szczeki (na cala jej szerokosc), boczne listwy prowadza
        body = S.diff(body, S.box(g, (-PH_X + 6, PH_X - 8), (-PH_Y - 0.3, PH_Y + 0.3), (5.0, 9.0)))
        # sruba M5 wzdluz x w bloku, nakretka wsuwana od gory
        zs = 14.0
        body = S.diff(body, S.cyl(g, (0, 0, zs), (1, 0, 0), M5, PH_X - 10, PH_X + 2))
        xc = PH_X - 4.0
        body = S.diff(body, S.hexprism(g, (xc, 0, zs), (1, 0, 0), (0, 1, 0), NUT_AF, -NUT_T / 2, NUT_T / 2))
        body = S.diff(body, S.box(g, (xc - NUT_T / 2, xc + NUT_T / 2), (-NUT_AF / 2, NUT_AF / 2), (zs, 26)))
        body = S.union(body, _gp_fingers(g, GP3, 0.01, 9.0, -1, widen=True))
        return body
    return lo, hi, fn


# ---------- przesuwna szczeka ----------
def phone_jaw():
    lo = (-6, -PH_Y - 2, 3)
    hi = (24, PH_Y + 2, 26)

    def fn(g):
        foot = S.box(g, (0.0, 22.0), (-PH_Y, PH_Y), (5.2, 8.0))
        wall = S.box(g, (0.0, 6.0), (-PH_Y, PH_Y), (7.9, 24.0))
        lip = _tri_xz(g, [(0.1, 17.0), (0.1, 24.0), (-4.0, 24.0), (-4.0, 21.0)], -PH_Y, PH_Y)
        return S.union(foot, wall, lip)
    return lo, hi, fn


# ---------- galka do sruby/nakretki M5 ----------
def knob():
    R = 11.0
    lo = (-R - 2, -R - 2, -1)
    hi = (R + 2, R + 2, 12)

    def fn(g):
        body = S.cyl(g, (0, 0, 0), (0, 0, 1), R, 0.0, 11.0)
        for k in range(8):
            a = np.radians(k * 45)
            body = S.diff(body, S.cyl(g, (R * 1.08 * np.cos(a), R * 1.08 * np.sin(a), 0), (0, 0, 1), 2.4, -1, 12))
        body = S.diff(body, S.hexprism(g, (0, 0, 0), (0, 0, 1), (1, 0, 0), 8.25, -1, 4.2))
        body = S.diff(body, S.cyl(g, (0, 0, 0), (0, 0, 1), M5, -1, 12))
        return body
    return lo, hi, fn


def rot(axis, deg):
    a = np.radians(deg); c, s = np.cos(a), np.sin(a)
    if axis == 'x':
        return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
    if axis == 'y':
        return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


# obrot do druku (z lokalnego ukladu): os pionowa druku
PRINT = {
    'zacisk_na_ring': rot('x', 90),         # styczna (y) pionowo
    'koncowka_rurki': np.eye(3),            # rurka pionowo, palce do gory
    'uchwyt_telefonu': rot('y', -90),       # os x pionowo, stala szczeka na stole
    'szczeka_telefonu': np.eye(3),          # stopa na stole, daszek ze skosem 45 st.
    'galka_M5': np.eye(3),
}
