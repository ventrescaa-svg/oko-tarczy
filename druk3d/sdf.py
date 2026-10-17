"""Minimal signed-distance modelling: primitives, booleans, marching cubes, binary STL.
All sizes in mm. Negative = inside. Only numpy + scikit-image are needed."""
import numpy as np
from skimage.measure import marching_cubes


class Grid:
    def __init__(self, lo, hi, h, _xs=None):
        self.h = h
        if _xs is None:
            self.lo = np.array(lo, float) - 2 * h
            n = np.ceil((np.array(hi, float) + 2 * h - self.lo) / h).astype(int) + 1
            _xs = [self.lo[i] + h * np.arange(n[i], dtype=np.float32) for i in range(3)]
        else:
            self.lo = np.array([_xs[0][0], _xs[1][0], _xs[2][0]], float)
        self.xs = _xs
        self.n = np.array([len(a) for a in _xs])
        self.X = _xs[0][:, None, None]
        self.Y = _xs[1][None, :, None]
        self.Z = _xs[2][None, None, :]

    def slab(self, i0, i1):
        return Grid(None, None, self.h, [self.xs[0][i0:i1], self.xs[1], self.xs[2]])


def evaluate(fn, lo, hi, h, slab=600_000):
    """Evaluate fn(grid) -> field slab by slab (keeps arrays small; much faster here)."""
    g = Grid(lo, hi, h)
    out = np.empty(tuple(g.n), dtype=np.float32)
    step = max(1, int(slab // (g.n[1] * g.n[2])))
    for i0 in range(0, g.n[0], step):
        i1 = min(g.n[0], i0 + step)
        out[i0:i1] = fn(g.slab(i0, i1))
    return g, out


def union(*a):
    out = a[0]
    for b in a[1:]:
        out = np.minimum(out, b)
    return out


def inter(*a):
    out = a[0]
    for b in a[1:]:
        out = np.maximum(out, b)
    return out


def diff(a, *b):
    out = a
    for c in b:
        out = np.maximum(out, -c)
    return out


def _frame(g, origin, u, v, w):
    o = np.array(origin, np.float32); u = np.array(u, np.float32); v = np.array(v, np.float32); w = np.array(w, np.float32)
    dx, dy, dz = g.X - o[0], g.Y - o[1], g.Z - o[2]
    a = dx * u[0] + dy * u[1] + dz * u[2]
    b = dx * v[0] + dy * v[1] + dz * v[2]
    c = dx * w[0] + dy * w[1] + dz * w[2]
    return a, b, c


def _box_local(a, b, c, ra, rb, rc):
    qa = np.maximum(ra[0] - a, a - ra[1])
    qb = np.maximum(rb[0] - b, b - rb[1])
    qc = np.maximum(rc[0] - c, c - rc[1])
    outside = np.sqrt(np.maximum(qa, 0) ** 2 + np.maximum(qb, 0) ** 2 + np.maximum(qc, 0) ** 2)
    inside = np.minimum(np.maximum(np.maximum(qa, qb), qc), 0)
    return (outside + inside).astype(np.float32)


def box(g, ra, rb, rc, origin=(0, 0, 0), u=(1, 0, 0), v=(0, 1, 0), w=(0, 0, 1)):
    """Box given by ranges along the frame axes u, v, w (orthonormal) from origin."""
    a, b, c = _frame(g, origin, u, v, w)
    return _box_local(a, b, c, ra, rb, rc)


def cyl(g, origin, axis, radius, t0, t1, rad_dir=None):
    """Finite cylinder along unit axis from origin, axial range [t0, t1]."""
    ax = np.array(axis, float); ax /= np.linalg.norm(ax); ax = ax.astype(np.float32)
    o = np.array(origin, np.float32)
    dx, dy, dz = g.X - o[0], g.Y - o[1], g.Z - o[2]
    t = dx * ax[0] + dy * ax[1] + dz * ax[2]
    px, py, pz = dx - t * ax[0], dy - t * ax[1], dz - t * ax[2]
    r = np.sqrt(px * px + py * py + pz * pz)
    qr = r - radius
    qt = np.maximum(t0 - t, t - t1)
    outside = np.sqrt(np.maximum(qr, 0) ** 2 + np.maximum(qt, 0) ** 2)
    inside = np.minimum(np.maximum(qr, qt), 0)
    return (outside + inside).astype(np.float32)


def teardrop(g, origin, axis, up, radius, t0, t1):
    """Horizontal hole that prints without support: cylinder + 45-degree roof towards `up`."""
    c = cyl(g, origin, axis, radius, t0, t1)
    ax = np.array(axis, float); ax /= np.linalg.norm(ax)
    upv = np.array(up, float); upv -= ax * (upv @ ax); upv /= np.linalg.norm(upv)
    side = np.cross(ax, upv)
    a, b, cc = _frame(g, origin, ax, side, upv)
    # square rotated 45 degrees, corner at radius*sqrt2 above the axis, only the upper half
    d1 = (np.abs(b) + cc) / np.sqrt(2) - radius
    roof = np.maximum(np.maximum(d1, -cc), np.maximum(t0 - a, a - t1))
    return np.minimum(c, roof.astype(np.float32))


def hexprism(g, origin, axis, flat_dir, af, t0, t1):
    """Hexagonal prism (nut trap): across-flats `af`, flats facing +-flat_dir."""
    ax = np.array(axis, float); ax /= np.linalg.norm(ax)
    fd = np.array(flat_dir, float); fd -= ax * (fd @ ax); fd /= np.linalg.norm(fd)
    o3 = np.cross(ax, fd)
    a, b, c = _frame(g, origin, ax, fd, o3)
    k = af / 2
    d = np.abs(b) - k
    for ang in (60, 120):
        cs, sn = np.cos(np.radians(ang)), np.sin(np.radians(ang))
        d = np.maximum(d, np.abs(b * cs + c * sn) - k)
    d = np.maximum(d, np.maximum(t0 - a, a - t1))
    return d.astype(np.float32)


def polygon_sdf2(px, py, poly):
    """Signed distance of points to a closed 2D polygon (list of (x,y)), negative inside."""
    poly = np.asarray(poly, float)
    d2 = np.full(px.shape, np.inf, dtype=np.float32)
    inside = np.zeros(px.shape, dtype=bool)
    n = len(poly)
    for i in range(n):
        ax_, ay_ = np.float32(poly[i][0]), np.float32(poly[i][1]); bx_, by_ = np.float32(poly[(i + 1) % n][0]), np.float32(poly[(i + 1) % n][1])
        ex, ey = bx_ - ax_, by_ - ay_
        wx, wy = px - ax_, py - ay_
        t = np.clip((wx * ex + wy * ey) / (ex * ex + ey * ey), 0, 1)
        dx, dy = wx - ex * t, wy - ey * t
        d2 = np.minimum(d2, dx * dx + dy * dy)
        cond = ((ay_ <= py) & (py < by_)) | ((by_ <= py) & (py < ay_))
        xint = ax_ + (py - ay_) * ex / (ey if ey != 0 else 1e-12)
        inside ^= cond & (px < xint)
    d = np.sqrt(d2)
    return np.where(inside, -d, d).astype(np.float32)


def revolve(g, profile_rz, th0, th1):
    """Polygon in (r, z) revolved around the z axis between angles th0..th1 (degrees, < 180 span)."""
    R = np.sqrt(g.X ** 2 + g.Y ** 2)
    R, Z = np.broadcast_arrays(R, g.Z)
    d = polygon_sdf2(R, Z, profile_rz)
    a0, a1 = np.radians(th0), np.radians(th1)
    d0 = g.X * np.sin(a0) - g.Y * np.cos(a0)
    d1 = -g.X * np.sin(a1) + g.Y * np.cos(a1)
    wedge = np.maximum(d0, d1)
    return np.maximum(d, wedge).astype(np.float32)


def extrude(g, poly_xy, z0, z1, origin=(0, 0, 0), u=(1, 0, 0), v=(0, 1, 0), w=(0, 0, 1)):
    """2D polygon in the (u, v) plane extruded along w between z0..z1."""
    a, b, c = _frame(g, origin, u, v, w)
    a, b, c = np.broadcast_arrays(a, b, c)
    d = polygon_sdf2(a, b, poly_xy)
    return np.maximum(d, np.maximum(z0 - c, c - z1)).astype(np.float32)


def frame_at(phi_deg):
    """Joint frame at angle phi: radial u, tangential t (towards +angle), z."""
    p = np.radians(phi_deg)
    u = (np.cos(p), np.sin(p), 0.0)
    t = (-np.sin(p), np.cos(p), 0.0)
    return u, t, (0.0, 0.0, 1.0)


def mesh(g, field):
    f = np.pad(field, 1, constant_values=1.0)
    verts, faces, _, _ = marching_cubes(f, level=0.0, spacing=(g.h, g.h, g.h))
    verts = verts + g.lo - g.h
    # orient faces outwards (positive volume)
    v0, v1, v2 = verts[faces[:, 0]], verts[faces[:, 1]], verts[faces[:, 2]]
    vol = np.einsum('ij,ij->i', v0, np.cross(v1, v2)).sum() / 6
    if vol < 0:
        faces = faces[:, ::-1]
    return verts.astype(np.float64), faces.astype(np.int64)


def transform(verts, R=np.eye(3), t=(0, 0, 0)):
    return verts @ np.asarray(R, float).T + np.asarray(t, float)


def to_bed(verts):
    """Move so the part sits on z=0, centred in x/y."""
    lo, hi = verts.min(0), verts.max(0)
    return verts - np.array([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]])


def write_stl(path, verts, faces, name='part'):
    v0, v1, v2 = verts[faces[:, 0]], verts[faces[:, 1]], verts[faces[:, 2]]
    nrm = np.cross(v1 - v0, v2 - v0)
    ln = np.linalg.norm(nrm, axis=1, keepdims=True); ln[ln == 0] = 1
    nrm /= ln
    rec = np.zeros(len(faces), dtype=[('n', '<f4', 3), ('a', '<f4', 3), ('b', '<f4', 3), ('c', '<f4', 3), ('x', '<u2')])
    rec['n'], rec['a'], rec['b'], rec['c'] = nrm, v0, v1, v2
    with open(path, 'wb') as f:
        f.write(name.encode()[:80].ljust(80, b' '))
        f.write(np.uint32(len(faces)).tobytes())
        f.write(rec.tobytes())


def check(verts, faces):
    """Watertight check (every edge shared by exactly two faces with opposite direction) and stats."""
    e = np.concatenate([faces[:, [0, 1]], faces[:, [1, 2]], faces[:, [2, 0]]])
    key = e[:, 0] * (len(verts) + 1) + e[:, 1]
    rkey = e[:, 1] * (len(verts) + 1) + e[:, 0]
    s = np.sort(key)
    dup = np.any(s[1:] == s[:-1])
    closed = np.isin(key, rkey).all()
    v0, v1, v2 = verts[faces[:, 0]], verts[faces[:, 1]], verts[faces[:, 2]]
    vol = np.einsum('ij,ij->i', v0, np.cross(v1, v2)).sum() / 6
    return {'tris': len(faces), 'closed': bool(closed and not dup), 'vol_cm3': vol / 1000,
            'size': (verts.max(0) - verts.min(0)).round(1).tolist()}
