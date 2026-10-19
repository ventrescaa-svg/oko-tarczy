"""Sprawdza nawisy w plikach STL (w orientacji do druku): powierzchnia scian skierowanych w dol
bardziej niz 45 st., ktore nie leza na stole. Male wartosci (mostki nad otworami) sa w porzadku."""
import sys, glob, os
import numpy as np


def read_stl(path):
    d = np.fromfile(path, dtype=np.uint8)
    n = int(np.frombuffer(d[80:84].tobytes(), np.uint32)[0])
    rec = np.frombuffer(d[84:84 + n * 50].tobytes(), dtype=np.dtype([('n', '<f4', 3), ('v', '<f4', (3, 3)), ('a', '<u2')]))
    return rec['v'].astype(float)


def overhang(tri, limit=47.0, bed=0.4):   # 45 st. + 2 st. na schodki z siatki
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    area = np.linalg.norm(n, axis=1) / 2
    nz = n[:, 2] / np.maximum(2 * area, 1e-12)
    zmin = tri[:, :, 2].min(1)
    bad = (nz < -np.cos(np.radians(90 - limit))) & (zmin > bed)
    return float(area[bad].sum()), tri[bad]


if __name__ == '__main__':
    for p in sorted(glob.glob(os.path.join(sys.argv[1], '*.stl'))):
        a, t = overhang(read_stl(p))
        where = ''
        if len(t):
            c = t.mean(1)
            where = 'z %.0f..%.0f' % (c[:, 2].min(), c[:, 2].max())
        print(f'{os.path.basename(p):26s} nawisy {a:7.1f} mm2  {where}')
