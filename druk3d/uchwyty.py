"""Uchwyt telefonu z przesuwna szczeka i uchem zawiasu (sruba M5 z galka), galki do srub M5.
Kazda funkcja zwraca (lo, hi, fn) w ukladzie lokalnym czesci; orientacja do druku w PRINT."""
import numpy as np
import sdf as S

M5 = 2.75          # promien otworu M5
NUT_AF = 8.4
NUT_T = 4.4


def _tri_xz(g, poly, y0, y1):
    # wielokat w plaszczyznie (x, z), wyciagniety wzdluz y
    X, Z = np.broadcast_arrays(g.X + 0 * g.Z, g.Z + 0 * g.X)
    X = np.broadcast_to(X, np.broadcast_shapes(X.shape, g.Y.shape))
    Z = np.broadcast_to(Z, X.shape)
    d = S.polygon_sdf2(X, Z, poly)
    Y = np.broadcast_to(g.Y, X.shape)
    return np.maximum(d, np.maximum(y0 - Y, Y - y1)).astype(np.float32)


# ---------- uchwyt telefonu (podstawa) ----------
PH_X = 62.0        # pol dlugosci podstawy (w poprzek telefonu)
PH_Y = 23.0        # pol szerokosci (wzdluz telefonu)
WIN_X = (-PH_X + 6.0, -PH_X + 36.0)   # okienko na aparat przy stalej szczece
WIN_Y = 17.0
# ucho zawiasu na koncu plyty od strony gory telefonu; os wzdluz y tuz za aparatem
EAR_X, EAR_Z, EAR_R = (WIN_X[0] + WIN_X[1]) / 2, -6.0, 9.0
EAR_Y = (-PH_Y - 3.0 - 7.0, -PH_Y - 3.0)


def phone_base():
    YW = PH_Y + 3.0           # plyta szersza o boczne prowadnice
    lo = (-PH_X - 2, EAR_Y[0] - 2, EAR_Z - EAR_R - 2)
    hi = (PH_X + 2, YW + 2, 26)

    def fn(g):
        body = S.box(g, (-PH_X, PH_X), (-YW, YW), (0.0, 8.0))
        body = S.union(body, S.box(g, (-PH_X, -PH_X + 6), (-YW, YW), (0.0, 24.0)))          # stala szczeka
        body = S.union(body, S.box(g, (-PH_X + 5.9, -PH_X + 10), (-YW, YW), (21.0, 24.0)))   # wywiniecie
        body = S.union(body, S.box(g, (PH_X - 8, PH_X), (-YW, YW), (0.0, 24.0)))           # blok sruby
        # skos 45 st. pod blokiem sruby (blok jest u gory przy druku, bez tego wisialby w powietrzu)
        body = S.union(body, _tri_xz(g, [(PH_X - 8, 8.0), (PH_X - 8, 24.0), (PH_X - 24, 8.0)], -YW, YW))
        # ucho zawiasu: od stolu (stala szczeka) do osi, u gory zaokraglone
        ear = S.box(g, (-PH_X, EAR_X), EAR_Y, (EAR_Z - EAR_R, 8.0))
        ear = S.union(ear, S.cyl(g, (EAR_X, 0, EAR_Z), (0, 1, 0), EAR_R, EAR_Y[0], EAR_Y[1]))
        body = S.union(body, ear)
        # kanal na stope przesuwnej szczeki (na cala jej szerokosc), boczne listwy prowadza
        body = S.diff(body, S.box(g, (-PH_X + 6, PH_X - 8), (-PH_Y - 0.3, PH_Y + 0.3), (5.0, 9.0)))
        body = S.diff(body, _tri_xz(g, [(PH_X - 8.01, 5.0), (PH_X - 8.01, 9.0), (PH_X - 4.0, 9.0)], -PH_Y - 0.3, PH_Y + 0.3))
        # sruba M5 wzdluz x w bloku, nakretka wsuwana od gory
        zs = 14.0
        body = S.diff(body, S.cyl(g, (0, 0, zs), (1, 0, 0), M5, PH_X - 26, PH_X + 2))
        xc = PH_X - 4.0
        body = S.diff(body, S.hexprism(g, (xc, 0, zs), (1, 0, 0), (0, 1, 0), NUT_AF, -NUT_T / 2, NUT_T / 2))
        body = S.diff(body, S.box(g, (xc - NUT_T / 2, xc + NUT_T / 2), (-NUT_AF / 2, NUT_AF / 2), (zs, 26)))
        # okienko na aparat telefonu (telefon aparatem do stalej szczeki)
        # okienko z daszkiem pod katem 45 st. (gora okienka przy druku)
        win = [(-WIN_Y, WIN_X[0]), (WIN_Y, WIN_X[0]), (WIN_Y, WIN_X[1]), (0.0, WIN_X[1] + WIN_Y), (-WIN_Y, WIN_X[1])]
        body = S.diff(body, S.extrude(g, win, -1.0, 10.0, u=(0, 1, 0), v=(1, 0, 0), w=(0, 0, 1)))
        # otwor zawiasu i gniazdo nakretki od wewnetrznej strony ucha (pod plyta)
        body = S.diff(body, S.teardrop(g, (EAR_X, 0, EAR_Z), (0, 1, 0), (1, 0, 0), M5, EAR_Y[0] - 1, EAR_Y[1] + 1))
        body = S.diff(body, S.hexprism(g, (EAR_X, 0, EAR_Z), (0, 1, 0), (0, 0, 1), NUT_AF, EAR_Y[1] - NUT_T - 0.2, EAR_Y[1] + 1))
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
    'uchwyt_telefonu': rot('y', -90),       # os x pionowo, stala szczeka na stole
    'szczeka_telefonu': np.eye(3),          # stopa na stole, daszek ze skosem 45 st.
    'galka_M5': np.eye(3),
}
