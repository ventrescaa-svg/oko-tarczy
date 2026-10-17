"""Buduje wszystkie czesci do druku: STL w orientacji do druku + sprawdzenie + podglady."""
import os, sys, json, time
import numpy as np
import sdf as S
import ring as Rg
import uchwyty as U

OUT = sys.argv[1] if len(sys.argv) > 1 else 'stl'
H_SMALL = 0.4
H_FINE = {'galka_M5': 0.3}
BED = (265.0, 265.0, 300.0)

PARTS = [  # nazwa, ilosc, budowa
    ('ring_segment_zwykly', 3, lambda: Rg.segment('plain'), 'seg'),
    ('ring_segment_z_dociskiem', 4, lambda: Rg.segment('clamp'), 'seg'),
    ('ring_segment_z_przewodem', 1, lambda: Rg.segment('power'), 'seg'),
    ('zacisk_na_ring', 2, U.ring_clamp, 'small'),
    ('koncowka_rurki', 2, U.tube_end, 'small'),
    ('uchwyt_telefonu', 2, U.phone_base, 'small'),
    ('szczeka_telefonu', 2, U.phone_jaw, 'small'),
    ('galka_M5', 16, U.knob, 'small'),
]


def build(name, how, kind):
    if kind == 'seg':
        g, f = how()
        v, fc = S.mesh(g, f)
        return v, fc, Rg.to_print_segment(v)
    lo, hi, fn = how()
    g, f = S.evaluate(fn, lo, hi, H_FINE.get(name, H_SMALL))
    v, fc = S.mesh(g, f)
    return v, fc, S.to_bed(v @ U.PRINT[name].T)


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    report = []
    meshes = {}
    only = sys.argv[2].split(',') if len(sys.argv) > 2 else None
    for name, qty, how, kind in PARTS:
        if only and name not in only:
            continue
        t = time.time()
        v, fc, vp = build(name, how, kind)
        info = S.check(vp, fc)
        size = np.array(info['size'])
        fits = bool(size[2] <= BED[2] and (np.all(size[:2] <= BED[:2])))
        S.write_stl(os.path.join(OUT, f'{name}.stl'), vp, fc, name)
        meshes[name] = (v, fc)
        info.update(name=name, qty=qty, fits_bed=fits, sec=round(time.time() - t, 1))
        report.append(info)
        print(json.dumps(info, default=float), flush=True)
    json.dump(report, open(os.path.join(OUT, '_report.json'), 'w'), default=float, indent=1)
