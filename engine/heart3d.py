"""Procedural 3D heart: implicit surface, point cloud, ray-marched cutaway. Pure numpy."""
import numpy as np

def f_heart(x, y, z):
    # Taubin heart, z up, y depth
    a = x * x + 2.25 * y * y + z * z - 1
    return a * a * a - x * x * z ** 3 - 0.045 * y * y * z ** 3

def surface_points(n, rng):
    d = rng.normal(size=(n, 3)); d /= np.linalg.norm(d, axis=1, keepdims=True)
    lo = np.zeros(n); hi = np.full(n, 2.0)
    for _ in range(30):
        m = (lo + hi) / 2; p = d * m[:, None]
        inside = f_heart(p[:, 0], p[:, 1], p[:, 2]) < 0
        lo = np.where(inside, m, lo); hi = np.where(inside, hi, m)
    return d * lo[:, None]

def volume_points(n, rng):
    pts = []
    while sum(len(p) for p in pts) < n:
        p = rng.uniform([-1.4, -1, -1.2], [1.4, 1, 1.4], (n, 3))
        pts.append(p[f_heart(*p.T) < 0])
    return np.concatenate(pts)[:n]

def rot(ax, ay):
    ca, sa, cb, sb = np.cos(ax), np.sin(ax), np.cos(ay), np.sin(ay)
    Rz = np.array([[ca, -sa, 0], [sa, ca, 0], [0, 0, 1]])
    Rx = np.array([[1, 0, 0], [0, cb, -sb], [0, sb, cb]])
    return Rx @ Rz

def project(P, W, H, scale, cam=4.0, cx=None, cy=None):
    """P: (N,3) with z up, y depth. returns screen x, y, depth factor."""
    cx = W / 2 if cx is None else cx; cy = H / 2 if cy is None else cy
    depth = cam + P[:, 1]
    s = scale * cam / depth
    return cx + P[:, 0] * s, cy - P[:, 2] * s, s / scale

def raymarch_cut(W, H, R, cut, scale, beat=1.0, cy_off=0.0):
    """Render heart with everything at local x > cut removed (cutaway). Returns RGB float image and mask."""
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    cam = 4.0
    # camera at (0,-cam,0) looking +y; screen plane
    u = (xs - W / 2) / scale; v = -(ys - H / 2) / scale + cy_off
    ro = np.array([0, -cam, 0], np.float32)
    rd = np.stack([u, np.full_like(u, cam), v], -1)
    rd /= np.linalg.norm(rd, axis=-1, keepdims=True)
    Rt = R.T
    o = ro @ Rt.T; d = rd.reshape(-1, 3) @ Rt.T  # rays in object space (object rotated by R)
    o = o / beat; d = d
    N = d.shape[0]
    # bounding sphere r=1.75 around origin
    b_ = (o[None, :] * d).sum(1); c_ = (o * o).sum() - 1.75 ** 2
    disc = b_ * b_ - c_
    t = np.where(disc > 0, -b_ - np.sqrt(np.maximum(disc, 0)), 9).astype(np.float32)
    tmax = np.where(disc > 0, -b_ + np.sqrt(np.maximum(disc, 0)), 0)
    hit = np.zeros(N, bool); face = np.zeros(N, bool)
    def g(p):
        fh = f_heart(p[:, 0], p[:, 1], p[:, 2])
        pl = (cut - p[:, 1]) * 3.0
        return np.maximum(fh, pl), fh, pl
    prev, _, _ = g(o + d * np.minimum(t, 9)[:, None])
    step = 0.035
    alive = disc > 0
    for _ in range(int(3.6 / step)):
        idx = np.where(alive)[0]
        if len(idx) == 0: break
        tn = t[idx] + step
        val, fh, pl = g(o + d[idx] * tn[:, None])
        crossed = (val < 0) & (prev[idx] >= 0)
        # refine
        if crossed.any():
            ci = idx[crossed]; a = t[ci]; b = tn[crossed]
            for _ in range(8):
                m = (a + b) / 2; vm, _, _ = g(o + d[ci] * m[:, None])
                a = np.where(vm >= 0, m, a); b = np.where(vm >= 0, b, m)
            t[ci] = b; hit[ci] = True; alive[ci] = False
            _, fhh, plh = g(o + d[ci] * b[:, None])
            face[ci] = plh > fhh
        nc = ~crossed
        t[idx[nc]] = tn[nc]; prev[idx[nc]] = val[nc]
        alive[idx[nc][tn[nc] > tmax[idx[nc]]]] = False
    P = o + d * t[:, None]
    img = np.zeros((N, 3), np.float32)
    # surface shading
    e = 1e-3
    hs = hit & ~face
    if hs.any():
        p = P[hs]
        gx = f_heart(p[:, 0] + e, p[:, 1], p[:, 2]) - f_heart(p[:, 0] - e, p[:, 1], p[:, 2])
        gy = f_heart(p[:, 0], p[:, 1] + e, p[:, 2]) - f_heart(p[:, 0], p[:, 1] - e, p[:, 2])
        gz = f_heart(p[:, 0], p[:, 1], p[:, 2] + e) - f_heart(p[:, 0], p[:, 1], p[:, 2] - e)
        n = np.stack([gx, gy, gz], 1); n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-9
        L = np.array([-0.5, -0.7, 0.6]) @ Rt.T; L /= np.linalg.norm(L)
        V = -d[hs]
        diff = np.clip(n @ L, 0, 1)
        h = (L + V); h /= np.linalg.norm(h, axis=1, keepdims=True)
        spec = np.clip((n * h).sum(1), 0, 1) ** 40
        rim = (1 - np.clip((n * V).sum(1), 0, 1)) ** 3
        # subtle vessel striping
        vein = 0.5 + 0.5 * np.sin(p[:, 0] * 9 + np.sin(p[:, 2] * 7) * 2)
        base = np.array([150, 18, 30]) * (0.85 + 0.15 * vein[:, None])
        img[hs] = base * (0.18 + 0.9 * diff[:, None]) + spec[:, None] * 255 * 0.8 + rim[:, None] * np.array([255, 90, 120]) * 0.6
    # cut face: layered interior
    if face.any():
        p = P[face]
        fh = f_heart(p[:, 0], p[:, 1], p[:, 2])
        depth = -fh  # 0 at surface, grows inward
        col = np.zeros((len(p), 3))
        # chambers: two ventricles (lower) + two atria (upper)
        def ell(c, r):
            return (((p[:, 0] - c[0]) / r[0]) ** 2 + ((p[:, 2] - c[1]) / r[1]) ** 2)
        lv = ell((0.30, -0.25), (0.26, 0.42)); rv = ell((-0.30, -0.20), (0.22, 0.36))
        la = ell((0.32, 0.42), (0.22, 0.16)); ra = ell((-0.32, 0.44), (0.20, 0.15))
        chamber = np.minimum.reduce([lv, rv, la, ra])
        muscle = np.array([168, 34, 44]); outer = np.array([240, 190, 150]); blood = np.array([70, 0, 10])
        fiber = 0.93 + 0.07 * np.sin(p[:, 0] * 70 + p[:, 2] * 45)
        shade = 0.8 + 0.2 * np.clip(1 - np.abs(p[:, 0]) * 0.5, 0, 1)
        col[:] = muscle * (fiber * shade)[:, None]
        col[depth < 0.006] = outer
        inch = chamber < 1
        col[inch] = blood * (0.6 + 0.4 * chamber[inch, None]) + np.array([40, 0, 5]) * (1 - chamber[inch, None])
        edge = (chamber > 0.9) & (chamber < 1.0)
        col[edge] = np.array([230, 90, 100])
        img[face] = col
    return img.reshape(H, W, 3), hit.reshape(H, W), face.reshape(H, W)
