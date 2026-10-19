"""Oko Tarczy - osmiokatna rama LED na nozkach, odsunieta od tarczy, z uchwytami telefonow na narozach.

Uklad: srodek tarczy (0,0,0), z = 0 przod tarczy, os z w strone gracza. Plyta OSB przy z = -44.
Naroza osmiokata na katach 0, 45, ..., 315 st. (0 = godzina 3). Nozki w narozach 45/135/225/315,
telefony w narozach 0 (godz. 3) i 90 (godz. 12). Tasma LED na tylnej sciance belek, swieci w tarcze.
Wymiary w mm.
"""
import numpy as np
import sdf as S
from uchwyty import M5, NUT_AF, NUT_T, EAR_Y

# ---------------- parametry ----------------
RC = 350.0            # promien do srodka naroza
Z_OSB = -44.0         # plyta OSB (przod tarczy = 0)
Z_FRONT = 190.0       # przod belek
BAR_W = 32.0          # szerokosc belki (w plaszczyznie ramy)
BAR_D = 24.0          # grubosc belki (wzdluz osi tarczy)
Z_BACK = Z_FRONT - BAR_D
WALL = 4.0            # scianki narozy
SOCK = 22.0           # od srodka naroza do dna gniazda belki
SOCK_L = 25.0         # glebokosc gniazda
FIT = 0.3             # luz na strone
STRIP_W = 10.6        # rowek na tasme COB 10 mm
STRIP_D = 1.2
CH = 8.0              # fazy 45 st. na tylnych krawedziach belki: gniazdo w narozu ma krotszy mostek przy druku
H = 0.45              # rozdzielczosc siatki

A22 = np.radians(22.5)
LS = 2 * RC * np.sin(A22)                 # dlugosc boku (srodek-srodek naroza)
BAR_L = LS - 2 * SOCK - 2 * 0.5           # belka z luzem 0.5 na koncach
SCREW_S = SOCK + 0.5 + 12.5               # wkret laczacy belke (odleglosc od srodka naroza)
CZ = (Z_BACK - WALL, Z_FRONT + WALL)      # zakres z naroza

# gniazdo nogi (kwadrat 24) i nozka
LEG = 24.0
Z_PLATE_FRONT = Z_OSB + 10.0              # przod plytki sciennej
LEG_SOCK_DEPTH = 24.0

# polozenie zawiasu telefonu wzgledem naroza (u = na zewnatrz, z)
HINGE_U, HINGE_Z = -58.8, 280.5      # z poza.hinge_for(): aparat ok. (r 300, z 290), telefon aparatem do gory
PHONE_BOLT_U, PHONE_BOLT_T = -10.0, 16.0


def _dirs():
    dp = np.array([-np.sin(A22), np.cos(A22), 0.0])   # w ukladzie naroza (u, t, z)
    dm = np.array([-np.sin(A22), -np.cos(A22), 0.0])
    npl = np.array([np.cos(A22), np.sin(A22), 0.0])
    nmi = np.array([np.cos(A22), -np.sin(A22), 0.0])
    return (dp, npl), (dm, nmi)


# ---------------- belka ----------------
def bar():
    """Uklad: x wzdluz belki, y na zewnatrz ramy, z jak w tarczy."""
    L2 = BAR_L / 2
    lo, hi = (-L2 - 1, -BAR_W / 2 - 1, Z_BACK - 1), (L2 + 1, BAR_W / 2 + 1, Z_FRONT + 1)

    def fn(g):
        b = S.box(g, (-L2, L2), (-BAR_W / 2, BAR_W / 2), (Z_BACK, Z_FRONT))
        # lekkie fazki na przednich krawedziach
        for sy in (-1, 1):
            b = S.diff(b, S.box(g, (-L2 - 1, L2 + 1), (-1.2, 1.2), (-1.2, 1.2),
                                origin=(0, sy * BAR_W / 2, Z_FRONT), u=(1, 0, 0), v=(0, np.sqrt(.5), np.sqrt(.5)), w=(0, -np.sqrt(.5), np.sqrt(.5))))
        # fazy na tylnych krawedziach (pasuja do daszka gniazda w narozu)
        for sy in (-1, 1):
            b = S.diff(b, S.extrude(g, [(sy * BAR_W / 2, Z_BACK + CH), (sy * (BAR_W / 2 - CH), Z_BACK), (sy * (BAR_W / 2 + 1), Z_BACK - 1)],
                                    -L2 - 1, L2 + 1, u=(0, 1, 0), v=(0, 0, 1), w=(1, 0, 0)))
        # rowek na tasme LED na tylnej sciance (od strony tarczy)
        b = S.diff(b, S.box(g, (-L2 - 1, L2 + 1), (-STRIP_W / 2, STRIP_W / 2), (Z_BACK - 1, Z_BACK + STRIP_D)))
        # otwory pilotowe pod wkrety 3,5 mm (od zewnetrznej strony, przy obu koncach)
        for sx in (-1, 1):
            x = sx * (L2 - 12.5)
            b = S.diff(b, S.cyl(g, (x, 0, (Z_BACK + Z_FRONT) / 2), (0, 1, 0), 1.4, 3.0, BAR_W / 2 + 1))
        return b
    return lo, hi, fn


# ---------------- naroze ----------------
def corner(kind):
    """kind: 'telefon' (gniazda nakretek pod uchwyt telefonu) albo 'noga' (gniazdo nogi).
    Uklad naroza: x = u (od srodka tarczy na zewnatrz), y = t (stycznie), z jak w tarczy; srodek naroza w (0,0)."""
    (dp, npl), (dm, nmi) = _dirs()
    ext = SOCK + SOCK_L
    lo = (-50, -ext - 5, CZ[0] - 1)
    hi = (30, ext + 5, CZ[1] + 1)
    zc = (Z_BACK + Z_FRONT) / 2

    def fn(g):
        z = (0, 0, 1)
        body = S.cyl(g, (0, 0, 0), (0, 0, 1), 24.0, CZ[0], CZ[1])
        for d, n in ((dp, npl), (dm, nmi)):
            body = S.union(body, S.box(g, (0.0, ext), (-BAR_W / 2 - WALL, BAR_W / 2 + WALL), CZ, u=d, v=n, w=z))
        for d, n in ((dp, npl), (dm, nmi)):
            a, zb0, zf0 = BAR_W / 2 + FIT, Z_BACK - FIT, Z_FRONT + FIT
            prof = [(-a, zf0), (a, zf0), (a, zb0 + CH), (a - CH, zb0), (-a + CH, zb0), (-a, zb0 + CH)]
            body = S.diff(body, S.extrude(g, prof, SOCK, ext + 2, u=n, v=z, w=d))
            # otwor na wkret laczacy belke (od zewnatrz)
            o = d * SCREW_S + np.array([0, 0, zc])
            body = S.diff(body, S.cyl(g, o, n, 1.95, BAR_W / 2 - 2, BAR_W / 2 + WALL + 2))
            body = S.diff(body, S.cyl(g, o, n, 3.9, BAR_W / 2 + WALL - 1.0, BAR_W / 2 + WALL + 3))
            # rowek na przewody na tylnej sciance (po zewnetrznej stronie)
            body = S.diff(body, S.box(g, (-14.0, ext + 2), (14.0, 18.5), (CZ[0] - 1, CZ[0] + 2.0), u=d, v=n, w=z))
        if kind == 'telefon':
            for st in (-1, 1):
                o = (PHONE_BOLT_U, st * PHONE_BOLT_T, 0)
                body = S.diff(body, S.cyl(g, o, (0, 0, 1), M5, CZ[0] - 1, CZ[1] + 1))
                body = S.diff(body, S.hexprism(g, (PHONE_BOLT_U, st * PHONE_BOLT_T, CZ[0]), (0, 0, 1), (1, 0, 0), NUT_AF, -1, NUT_T + 0.2))
        else:
            # gniazdo nogi ustawione wzdluz osi swiata (naroze lezy pod katem 45 st.)
            c, s = np.cos(np.radians(-45)), np.sin(np.radians(-45))
            ux, uy = (c, s, 0), (-s, c, 0)
            body = S.diff(body, S.box(g, (-LEG / 2 - FIT, LEG / 2 + FIT), (-LEG / 2 - FIT, LEG / 2 + FIT), (CZ[0] - 1, CZ[0] + LEG_SOCK_DEPTH), u=ux, v=uy, w=z))
            # wkret mocujacy noge (wzdluz osi x swiata, od zewnatrz)
            zz = CZ[0] + LEG_SOCK_DEPTH - 12.0
            body = S.diff(body, S.cyl(g, (0, 0, zz), ux, 1.95, LEG / 2 - 2, 30))
            body = S.diff(body, S.cyl(g, (0, 0, zz), ux, 3.9, 22.0, 30))
        return body
    return lo, hi, fn


# ---------------- noga ----------------
LEG_TOP = CZ[0] + LEG_SOCK_DEPTH          # koniec nogi w gniezdzie naroza
FOOT_T = 8.0
DT_W0, DT_W1, DT_D, DT_L = 19.4, 25.4, 5.7, 60.0   # jaskolczy ogon: szer. przy stopie, na koncu, glebokosc, dlugosc


def leg():
    """Uklad swiata (x, y), z wzdluz nogi. Stopa z jaskolczym ogonem wsuwana pionowo (y) w plytke."""
    zf = Z_PLATE_FRONT
    lo = (-20, -DT_L / 2 - 2, zf - DT_D - 1)
    hi = (20, DT_L / 2 + 2, LEG_TOP + 1)

    def fn(g):
        post = S.box(g, (-LEG / 2, LEG / 2), (-LEG / 2, LEG / 2), (zf - 0.01, LEG_TOP))
        tail = S.extrude(g, [(-DT_W0 / 2, zf), (DT_W0 / 2, zf), (DT_W1 / 2, zf - DT_D), (-DT_W1 / 2, zf - DT_D)],
                         -DT_L / 2, DT_L / 2, u=(1, 0, 0), v=(0, 0, 1), w=(0, 1, 0))
        body = S.union(post, tail)
        # zebra z ogona do slupka (wzdluz y), szerokosc jak gora ogona - drukuje sie bez podpor
        for sy in (-1, 1):
            rib = S.extrude(g, [(sy * LEG / 2, zf - 0.01), (sy * DT_L / 2, zf - 0.01), (sy * LEG / 2, zf + (DT_L / 2 - LEG / 2))],
                            -DT_W0 / 2, DT_W0 / 2, u=(0, 1, 0), v=(0, 0, 1), w=(1, 0, 0))
            body = S.union(body, rib)
        # otwory pilotowe pod wkret z naroza (na wszystkich 4 scianach)
        zz = LEG_TOP - 12.0
        for ax in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0)):
            body = S.diff(body, S.cyl(g, (0, 0, zz), ax, 1.4, LEG / 2 - 10, LEG / 2 + 1))
        # rowek na przewod zasilania wzdluz nogi
        body = S.diff(body, S.box(g, (LEG / 2 - 3.5, LEG / 2 + 1), (-2.5, 2.5), (zf + 2, LEG_TOP + 1)))
        return body
    return lo, hi, fn


# ---------------- plytka scienna ----------------
PL_W, PL_H = 60.0, 90.0


def wall_plate():
    z0, z1 = Z_OSB, Z_PLATE_FRONT
    lo = (-PL_W / 2 - 1, -PL_H / 2 - 1, z0 - 1)
    hi = (PL_W / 2 + 1, PL_H / 2 + 1, z1 + 1)

    def fn(g):
        p = S.box(g, (-PL_W / 2, PL_W / 2), (-PL_H / 2, PL_H / 2), (z0, z1))
        y_stop = -PL_H / 2 + 12.0
        a0, a1 = DT_W0 / 2 + FIT, DT_W1 / 2 + FIT
        ch = S.extrude(g, [(-a0, z1 + 0.01), (a0, z1 + 0.01), (a1, z1 - DT_D - FIT), (-a1, z1 - DT_D - FIT)],
                       y_stop, PL_H / 2 + 2, u=(1, 0, 0), v=(0, 0, 1), w=(0, 1, 0))
        # rozszerzenie u gory, latwiej trafic stopa
        p = S.diff(p, ch)
        p = S.diff(p, S.extrude(g, [(-a1 - 3, z1 + 0.01), (a1 + 3, z1 + 0.01), (a1, z1 - DT_D - FIT), (-a1, z1 - DT_D - FIT)],
                                PL_H / 2 - 8, PL_H / 2 + 2, u=(1, 0, 0), v=(0, 0, 1), w=(0, 1, 0)))
        for sx in (-1, 1):
            for sy in (-1, 1):
                o = (sx * 22.0, sy * 33.0, 0)
                p = S.diff(p, S.cyl(g, o, (0, 0, 1), 2.25, z0 - 1, z1 + 1))
                # lby wkretow stozkowych 4 mm
                p = S.diff(p, _cone(g, o, z1))
        return p
    return lo, hi, fn


def _cone(g, o, z1):
    # stozek pod leb wkretu: promien 4.2 przy powierzchni, 2.25 na glebokosci 2
    dx, dy = g.X - o[0], g.Y - o[1]
    r = np.sqrt(dx * dx + dy * dy)
    zz = g.Z - z1
    rad = 2.25 + (4.2 - 2.25) * (zz + 2.0) / 2.0
    d = np.maximum(r - rad, np.maximum(-2.0 - zz, zz - 1.0))
    return d.astype(np.float32)


# ---------------- ramie telefonu (na narozu 'telefon') ----------------
ARM_T = (-EAR_Y[0] + 0.2, -EAR_Y[0] + 14.2)   # ramie obok gory telefonu, poza kadrem aparatu
BOSS_R = 9.0


def phone_arm():
    """Uklad naroza (u, t, z). Podstawa na przodzie naroza (2 sruby M5), ramie skosem do ucha zawiasu.
    Ramie lezy w pasie t = ARM_T, obok gory telefonu, wiec nie wchodzi w kadr. Os zawiasu wzdluz t."""
    zb = CZ[1]
    hu, hz = HINGE_U, HINGE_Z
    t0, t1 = ARM_T
    root = np.array([PHONE_BOLT_U, zb + 2.0])       # koniec ramienia schowany w podstawie (bez nawisu)
    hinge = np.array([hu, hz])
    v = root - hinge; v /= np.linalg.norm(v)
    nrm = np.array([-v[1], v[0]])
    lo = (hu - BOSS_R - 2, -PHONE_BOLT_T - 10, zb - 1)
    hi = (PHONE_BOLT_U + 16, t1 + 2, hz + BOSS_R + 2)

    def fn(g):
        base = S.box(g, (PHONE_BOLT_U - 14, PHONE_BOLT_U + 14), (-PHONE_BOLT_T - 8, t1), (zb, zb + 7.0))
        poly = [tuple(root + nrm * 9), tuple(root - nrm * 9), tuple(hinge - nrm * 9), tuple(hinge + nrm * 9)]
        arm = S.extrude(g, poly, t0, t1, u=(1, 0, 0), v=(0, 0, 1), w=(0, 1, 0))
        arm = S.inter(arm, S.box(g, (-200, 200), (-200, 200), (zb, 400)))
        boss = S.cyl(g, (hu, 0, hz), (0, 1, 0), BOSS_R, t0, t1)
        body = S.union(base, arm, boss)
        body = S.diff(body, S.teardrop(g, (hu, 0, hz), (0, 1, 0), (0, 0, 1), M5, t0 - 1, t1 + 1))
        for st in (-1, 1):
            o = (PHONE_BOLT_U, st * PHONE_BOLT_T, 0)
            body = S.diff(body, S.cyl(g, o, (0, 0, 1), M5, zb - 1, zb + 8))
        return body
    return lo, hi, fn
