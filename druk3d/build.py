"""Buduje wszystkie czesci do druku: STL w orientacji do druku + sprawdzenie szczelnosci i stolu."""
import os, sys, json, time
import numpy as np
import sdf as S
import rama as R
import uchwyty as U

OUT = sys.argv[1] if len(sys.argv) > 1 else 'stl'
BED = (265.0, 265.0, 300.0)
FLIP = U.rot('x', 180)          # przodem do stolu

PARTS = [  # nazwa, ilosc, budowa, obrot do druku, rozdzielczosc
    ('belka', 8, R.bar, FLIP, 0.45),
    ('naroznik_telefon', 4, lambda: R.corner('telefon'), FLIP, 0.45),
    ('naroznik_noga', 4, lambda: R.corner('noga'), FLIP, 0.45),
    ('noga', 4, R.leg, np.eye(3), 0.45),
    ('plytka_scienna', 4, R.wall_plate, np.eye(3), 0.4),
    ('ramie_telefonu', 2, R.phone_arm, np.eye(3), 0.35),
    ('uchwyt_telefonu', 2, U.phone_base, U.PRINT['uchwyt_telefonu'], 0.4),
    ('szczeka_telefonu', 2, U.phone_jaw, U.PRINT['szczeka_telefonu'], 0.4),
    ('galka_M5', 4, U.knob, np.eye(3), 0.3),
]


def build(how, h):
    lo, hi, fn = how()
    g, f = S.evaluate(fn, lo, hi, h)
    return S.mesh(g, f)


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    only = sys.argv[2].split(',') if len(sys.argv) > 2 else None
    report = []
    for name, qty, how, rot, h in PARTS:
        if only and name not in only:
            continue
        t = time.time()
        v, fc = build(how, h)
        vp = S.to_bed(v @ np.asarray(rot).T)
        info = S.check(vp, fc)
        size = np.array(info['size'])
        # obrot o 45 st. na stole, jesli trzeba
        fits = bool(size[2] <= BED[2] and np.all(size[:2] <= BED[:2]))
        if not fits and size[2] <= BED[2]:
            vp = S.to_bed(vp @ U.rot('z', 45).T); info = S.check(vp, fc); size = np.array(info['size'])
            fits = bool(np.all(size[:2] <= BED[:2]))
        S.write_stl(os.path.join(OUT, f'{name}.stl'), vp, fc, name)
        info.update(name=name, qty=qty, fits_bed=fits, sec=round(time.time() - t, 1))
        report.append(info)
        print(f"{name:20s} x{qty:<2d} closed={info['closed']} fits={fits} size={info['size']} vol={info['vol_cm3']:.1f}cm3 tris={info['tris']} {info['sec']}s", flush=True)
    json.dump(report, open(os.path.join(OUT, '_report.json'), 'w'), default=float, indent=1)
