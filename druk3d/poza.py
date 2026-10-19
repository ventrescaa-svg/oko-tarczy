"""Polozenie telefonu w uchwycie: aparat, kierunek patrzenia i kadr.

Uklad uchwytu (uchwyty.phone_base): os zawiasu wzdluz y w punkcie (EAR_X, 0, EAR_Z), telefon lezy plecami
na plycie (z = 8), aparat w okienku przy stalej szczece (x ok. -41), patrzy w strone -z.
Samsung: aparat w lewym gornym rogu plecow, wiec gora telefonu wypada po stronie -y uchwytu.
Uchwyt jest zalozony obrocony o 180 st. (FLIP), dzieki temu na godzinie 3 telefon stoi
aparatem do gory i ekran nie jest do gory nogami. Zawias ramienia (rama.HINGE_U, rama.HINGE_Z) policzony
funkcja hinge_for() dla aparatu w CAM_TARGET.
"""
import numpy as np
import rama as R
import uchwyty as U

CAM_LOCAL = np.array([(U.WIN_X[0] + U.WIN_X[1]) / 2, 0.0, 7.0])
HINGE_LOCAL = np.array([U.EAR_X, 0.0, U.EAR_Z])
PHONE_BOX = ((-U.PH_X + 6.0, -U.PH_X + 6.0 + 76.0), (-30.0, 130.0), (8.0, 17.0))   # telefon z etui, aparat ok. 30 mm od gory
FLIP = np.diag([-1.0, -1.0, 1.0])
FOV_LONG, FOV_SHORT = 70.0, 43.0      # aparat glowny 1x, wideo 16:9 (dluzszy bok wzdluz ramy); z zapasem
F_PX = 960.0 / np.tan(np.radians(FOV_LONG / 2))   # ogniskowa w px przy wideo 1920x1080
CAM_TARGET = (300.0, 290.0)           # aparat: odleglosc od osi tarczy, wysokosc nad tarcza
AIM_R = 32.0                          # os aparatu trafia w tarcze 32 mm od bulla w strone telefonu


def rz(deg):
    a = np.radians(deg); c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def ry(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def _tilt(cam_rz, aim_r):
    d = np.array([aim_r - cam_rz[0], 0.0, -cam_rz[1]], float)
    return np.arctan2(-d[0], -d[2])          # ry(a) @ (0,0,-1) ma kierunek d


def hinge_for(cam_rz=CAM_TARGET, aim_r=AIM_R):
    """Gdzie musi byc zawias ramienia (u, z wzgledem naroza), zeby aparat byl w cam_rz."""
    M = ry(_tilt(cam_rz, aim_r)) @ FLIP
    h = np.array([cam_rz[0], 0, cam_rz[1]]) - M @ (CAM_LOCAL - HINGE_LOCAL)
    return h[0] - R.RC, h[2]


def pose(k=0, aim_r=AIM_R):
    """(M, t): punkt uchwytu p -> swiat M @ p + t, telefon na narozu k, aparat celuje w aim_r."""
    hinge_c = np.array([R.HINGE_U, 0.0, R.HINGE_Z])
    off = FLIP @ (CAM_LOCAL - HINGE_LOCAL)
    a = 0.0
    for _ in range(50):                       # aparat lezy na okregu wokol zawiasu; dopasuj kat
        cam = ry(a) @ off + hinge_c + np.array([R.RC, 0, 0])
        a = _tilt((cam[0], cam[2]), aim_r)
    Rc = rz(45 * k)
    M = Rc @ ry(a) @ FLIP
    t = Rc @ (hinge_c + np.array([R.RC, 0, 0])) - M @ HINGE_LOCAL
    return M, t


def camera(k=0, aim_r=AIM_R):
    M, t = pose(k, aim_r)
    c = M @ CAM_LOCAL + t
    view = M @ np.array([0, 0, -1.0])
    e_long = M @ np.array([0, 1.0, 0])     # dluzszy bok kadru (wzdluz telefonu)
    e_short = np.cross(view, e_long)
    return c, view, e_long, e_short


def needed_points(k=0):
    """Co musi byc w kadrze: tarcza do r 175 oraz rzutki na podwojnej (r 170) do 40 mm nad tarcza."""
    pts = []
    for r in (0, 60, 110, 175):
        for a in np.linspace(0, 2 * np.pi, 72, endpoint=False):
            pts.append((r * np.cos(a), r * np.sin(a), 0.0))
    for a in np.linspace(0, 2 * np.pi, 72, endpoint=False):
        for z in (15.0, 40.0):
            pts.append((170 * np.cos(a), 170 * np.sin(a), z))
    return np.array(pts) @ rz(45 * k).T


def frame_fit(k=0, aim_r=AIM_R):
    """Zajecie kadru (1.0 = do samej krawedzi): dluzszy bok (min, max), krotszy bok (min, max)."""
    c, v, el, es = camera(k, aim_r)
    P = needed_points(k) - c
    z = P @ v
    TL, TS = np.tan(np.radians(FOV_LONG / 2)), np.tan(np.radians(FOV_SHORT / 2))
    tl, ts = (P @ el) / z / TL, (P @ es) / z / TS
    return (float(tl.min()), float(tl.max())), (float(ts.min()), float(ts.max()))


def px_per_mm(k=0, aim_r=AIM_R):
    """Rozdzielczosc przy bullu w pelnym wideo: w strone telefonu i w poprzek."""
    c, v, el, es = camera(k, aim_r)
    rad = rz(45 * k) @ np.array([1.0, 0, 0]); tan = rz(45 * k) @ np.array([0, 1.0, 0])

    def proj(p):
        q = p - c
        return F_PX * np.array([q @ el, q @ es]) / (q @ v)
    o = proj(np.zeros(3))
    return float(np.linalg.norm(proj(rad) - o)), float(np.linalg.norm(proj(tan) - o))


def phone_corners(k=0):
    M, t = pose(k)
    (x0, x1), (y0, y1), (z0, z1) = PHONE_BOX
    pts = np.array([[x, y, z] for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)])
    return pts @ M.T + t


if __name__ == '__main__':
    print('zawias dla aparatu w', CAM_TARGET, '->', np.round(hinge_for(), 1), ' (w rama.py:', R.HINGE_U, R.HINGE_Z, ')')
    c, v, el, es = camera(0)
    print('aparat', c.round(1), 'odl. do bulla', round(float(np.linalg.norm(c))), 'mm, kat od osi tarczy',
          round(float(np.degrees(np.arccos(c[2] / np.linalg.norm(c)))), 1))
    print('gora telefonu (kierunek +y swiata?)', (pose(0)[0] @ np.array([0, -1.0, 0])).round(2))
    fl, fs = frame_fit(0)
    print('kadr: dluzszy bok %.2f..%.2f, krotszy %.2f..%.2f' % (fl + fs))
    pr, pt = px_per_mm(0)
    print('px/mm przy bullu (pelne wideo): w strone telefonu %.2f, w poprzek %.2f' % (pr, pt))
    W = phone_corners(0)
    print('telefon: r %.0f..%.0f, z %.0f..%.0f' % (np.hypot(W[:, 0], W[:, 1]).min(), np.hypot(W[:, 0], W[:, 1]).max(), W[:, 2].min(), W[:, 2].max()))
