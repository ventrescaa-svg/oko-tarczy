"""Quick shaded previews of meshes with matplotlib (for checking, not for printing)."""
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


def render(parts, path, elev=25, azim=-60, size=(9, 7), title=None, lim=None, dpi=110):
    """parts: list of (verts, faces, rgb)."""
    fig = plt.figure(figsize=size)
    ax = fig.add_subplot(111, projection='3d')
    ax.set_proj_type('ortho')
    light = np.array([-0.4, -0.6, 0.8]); light /= np.linalg.norm(light)
    allv = []
    for v, f, col in parts:
        tri = v[f]
        n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)
        shade = 0.35 + 0.65 * np.clip(n @ light, 0, 1)
        fc = np.clip(np.array(col)[None, :] * shade[:, None], 0, 1)
        pc = Poly3DCollection(tri, facecolors=fc, edgecolors='none', linewidths=0)
        ax.add_collection3d(pc)
        allv.append(v)
    allv = np.concatenate(allv)
    lo, hi = allv.min(0), allv.max(0)
    c = (lo + hi) / 2
    r = (hi - lo).max() / 2 if lim is None else lim
    ax.set_xlim(c[0] - r, c[0] + r); ax.set_ylim(c[1] - r, c[1] + r); ax.set_zlim(c[2] - r, c[2] + r)
    ax.set_box_aspect((1, 1, 1))
    ax.view_init(elev=elev, azim=azim)
    ax.set_axis_off()
    if title:
        ax.set_title(title, fontsize=11)
    fig.tight_layout()
    fig.savefig(path, dpi=dpi)
    plt.close(fig)
