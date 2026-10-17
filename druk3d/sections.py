"""2D sections of SDF parts for checking dimensions."""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import sdf as S


def slice_xz(fn, x0, x1, z0, z1, y=0.0, h=0.1):
    xs = np.arange(x0, x1, h, dtype=np.float32); zs = np.arange(z0, z1, h, dtype=np.float32)
    g = S.Grid(None, None, h, [xs, np.array([y], np.float32), zs])
    return xs, zs, fn(g)[:, 0, :]


def slice_xy(fn, x0, x1, y0, y1, z=0.0, h=0.1):
    xs = np.arange(x0, x1, h, dtype=np.float32); ys = np.arange(y0, y1, h, dtype=np.float32)
    g = S.Grid(None, None, h, [xs, ys, np.array([z], np.float32)])
    return xs, ys, fn(g)[:, :, 0]


def show(ax, a, b, f, title, extra=None):
    ax.contourf(a, b, (f.T < 0).astype(float), levels=[0.5, 1.5], colors=['#9aa4b1'])
    ax.contour(a, b, f.T, levels=[0], colors='k', linewidths=0.6)
    ax.set_aspect('equal'); ax.set_title(title, fontsize=9); ax.grid(True, lw=0.3)
    if extra: extra(ax)
