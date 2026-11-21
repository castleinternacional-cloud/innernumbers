"""Procedural particle organs for Inner Numbers. Each organ: N points (surface first, then volume),
surface flag, a colour gradient, a cut-slice colouring (front half removed, slice = plane y=0),
labels for the slice, a pulse function and an optional view rotation."""
import math
import numpy as np
from heart3d import f_heart, surface_points as heart_surface, volume_points as heart_volume

N = 9000
NS = 5000

def _sample_implicit(f, n, box, rng):
    out = []
    lo, hi = np.array(box[0]), np.array(box[1])
    while sum(len(o) for o in out) < n:
        p = rng.uniform(lo, hi, (n * 3, 3)); out.append(p[f(p) < 0])
    return np.concatenate(out)[:n]

def _surface_from_implicit(f, n, rng, rmax=2.0, center=(0, 0, 0)):
    c = np.array(center, float)
    d = rng.normal(size=(n, 3)); d /= np.linalg.norm(d, axis=1, keepdims=True)
    lo = np.zeros(n); hi = np.full(n, rmax)
    for _ in range(30):
        m = (lo + hi) / 2; p = c + d * m[:, None]
        ins = f(p) < 0
        lo = np.where(ins, m, lo); hi = np.where(ins, hi, m)
    return c + d * lo[:, None]

class Organ:
    name = "organ"; pal = ((255, 70, 170), (140, 90, 255), (0, 230, 255)); view_rot = 0.0; view_tilt = 0.2; labels = []
    def __init__(self, rng):
        self.rng = rng; self.surf, self.vol = self.build(rng)
        self.P = np.concatenate([self.surf, self.vol]).astype(np.float32)
        self.is_vol = np.r_[np.zeros(len(self.surf), bool), np.ones(len(self.vol), bool)]
    def pulse(self, t): return 1.0
    def slice_colors(self, P): return np.tile(np.array([230, 80, 110.]), (len(P), 1))

# ------------------------------------------------------------------ heart
class Heart(Organ):
    name = "heart"
    labels = [("LEFT VENTRICLE", (0.3, -0.25), 1), ("RIGHT VENTRICLE", (-0.3, -0.2), -1), ("ATRIA", (0.0, 0.43), 0)]
    def build(self, rng): return heart_surface(NS, rng), heart_volume(N - NS, rng) * 0.97
    def pulse(self, t):
        ph = (t * 70 / 60) % 1.0
        return 1 + 0.06 * math.exp(-ph * 12) + 0.035 * math.exp(-max(0, ph - 0.25) * 12) * (ph > 0.25)
    def slice_colors(self, P):
        def ell(cx, cz, rx, rz): return ((P[:, 0] - cx) / rx) ** 2 + ((P[:, 2] - cz) / rz) ** 2
        e = np.minimum.reduce([ell(0.3, -0.25, 0.26, 0.42), ell(-0.3, -0.2, 0.22, 0.36), ell(0.32, 0.42, 0.22, 0.16), ell(-0.32, 0.44, 0.2, 0.15)])
        c = np.tile(np.array([255, 70, 100.]) * 1.7, (len(P), 1))
        c[(e >= 0.85) & (e < 1.15)] = np.array([255, 220, 235.]) * 2.0
        c[e < 0.85] = np.array([90, 0, 20.]) * 0.6
        return c

# ------------------------------------------------------------------ eye (optical axis = +x in slice view)
class Eye(Organ):
    name = "eye"; pal = ((200, 240, 255), (90, 180, 255), (40, 90, 255)); view_rot = -math.pi / 2
    labels = [("CORNEA", (1.02, 0.0), 1), ("LENS", (0.62, 0.0), 0), ("RETINA", (-0.9, -0.35), -1)]
    def build(self, rng):
        f = lambda p: (p ** 2).sum(1) - 1.0
        s = _surface_from_implicit(f, NS - 600, rng)
        # cornea bulge
        th = rng.uniform(0, 2 * np.pi, 600); r = np.sqrt(rng.uniform(0, 1, 600)) * 0.5
        cx = np.sqrt(np.maximum(0, 1.12 ** 2 - r ** 2)) - 0.1
        corn = np.stack([cx, r * np.cos(th), r * np.sin(th)], 1)
        v = _sample_implicit(f, N - NS, ([-1, -1, -1], [1, 1, 1]), rng) * 0.98
        return np.concatenate([s, corn]), v
    def surface_colors(self, P):
        r = np.sqrt(P[:, 1] ** 2 + P[:, 2] ** 2)
        c = np.tile(np.array([225, 235, 255.]), (len(P), 1))
        front = P[:, 0] > 0.75
        c[front & (r < 0.5)] = np.array([40, 170, 255.]) * 1.3   # iris
        c[front & (r < 0.2)] = np.array([10, 10, 25.])           # pupil
        return c
    def pulse(self, t): return 1.0
    def slice_colors(self, P):
        rad = np.sqrt((P ** 2).sum(1))
        c = np.tile(np.array([120, 190, 255.]) * 0.35, (len(P), 1))       # vitreous
        c[rad > 0.86] = np.array([255, 150, 60.]) * 1.4                     # retina
        c[rad > 0.92] = np.array([160, 30, 40.]) * 1.4                      # choroid
        c[rad > 0.96] = np.array([240, 245, 255.]) * 1.6                    # sclera
        lens = ((P[:, 0] - 0.62) / 0.16) ** 2 + (P[:, 2] / 0.42) ** 2 < 1
        c[lens] = np.array([120, 255, 255.]) * 1.8
        return c

# ------------------------------------------------------------------ lungs
class Lungs(Organ):
    name = "lungs"; pal = ((255, 120, 170), (180, 255, 120), (0, 220, 160))
    labels = [("TRACHEA", (0.0, 1.1), 0), ("BRONCHI", (0.32, 0.5), 1), ("AIR SACS", (-0.65, -0.35), -1)]
    def build(self, rng):
        def lung(p, side):
            x = (p[:, 0] - side * 0.58) / 0.48; y = p[:, 1] / 0.42; z = (p[:, 2] + 0.05) / (0.95 - 0.15 * (p[:, 2] > 0.4))
            med = np.where(side * p[:, 0] < 0.18, 3.0, 0)  # flatten medial side
            return x * x + y * y + z * z - 1 + med * (0.18 - side * p[:, 0]).clip(0)
        f = lambda p: np.minimum(lung(p, 1), lung(p, -1))
        sl = np.concatenate([_surface_from_implicit(lambda p: lung(p, 1), (NS - 900) // 2, rng, center=(0.6, 0, 0)),
                             _surface_from_implicit(lambda p: lung(p, -1), (NS - 900) // 2, rng, center=(-0.6, 0, 0))])
        tree = self._tree(rng, 900)
        v = _sample_implicit(f, N - NS - 1200, ([-1.2, -0.5, -1.1], [1.2, 0.5, 1.0]), rng)
        self.tree_inner = self._tree(rng, 1200, inner=True)
        return np.concatenate([sl, tree]), np.concatenate([v, self.tree_inner])
    def _tree(self, rng, n, inner=False):
        segs = [((0, 0, 1.45), (0, 0, 0.75), 0.06)]
        def branch(p, d, L, depth):
            if depth == 0: return
            q = (p[0] + d[0] * L, p[1], p[2] + d[1] * L); segs.append((p, q, 0.04 * depth / 4));
            for a in (-0.5, 0.5):
                nd = (d[0] * math.cos(a) - d[1] * math.sin(a), d[0] * math.sin(a) + d[1] * math.cos(a))
                branch(q, nd, L * 0.68, depth - 1)
        branch((0, 0, 0.75), (0.75, -0.66), 0.45, 4); branch((0, 0, 0.75), (-0.75, -0.66), 0.45, 4)
        segs = segs[:] if not inner else segs[1:]
        k = rng.integers(0, len(segs), n); u = rng.uniform(0, 1, n)
        a = np.array([segs[i][0] for i in k]); b = np.array([segs[i][1] for i in k]); w = np.array([segs[i][2] for i in k])
        p = a + (b - a) * u[:, None]; p += rng.normal(size=(n, 3)) * w[:, None] * 0.5
        return p
    def pulse(self, t): return 1 + 0.045 * math.sin(2 * math.pi * t / 4.0)
    def slice_colors(self, P):
        c = np.tile(np.array([255, 120, 160.]) * 1.0, (len(P), 1))
        c[len(P) - 1200:] = np.array([235, 255, 240.]) * 2.0   # airway tree
        dots = (np.sin(P[:, 0] * 38) * np.sin(P[:, 2] * 38)) > 0.6
        c[:len(P) - 1200][dots[:len(P) - 1200]] = np.array([255, 190, 210.]) * 1.6
        return c

# ------------------------------------------------------------------ red blood cell (disc facing camera)
class RBC(Organ):
    name = "rbc"; pal = ((255, 120, 120), (230, 30, 60), (140, 0, 60)); view_tilt = 1.0
    labels = [("NO NUCLEUS", (0.0, 0.0), 0), ("HEMOGLOBIN", (0.95, 0.0), 1)]
    def thick(self, rho):
        rho = np.clip(rho, 0, 1)
        return 0.5 * np.sqrt(1 - rho ** 2) * (0.21 + 2.0 * rho ** 2 - 1.12 * rho ** 4)
    def build(self, rng):
        R = 1.15
        rho = np.sqrt(rng.uniform(0, 1, NS)); th = rng.uniform(0, 2 * np.pi, NS); sgn = rng.choice([-1, 1], NS)
        y = sgn * self.thick(rho) * R * 0.95
        s = np.stack([rho * R * np.cos(th), y, rho * R * np.sin(th)], 1)
        nv = N - NS; rho = np.sqrt(rng.uniform(0, 1, nv)); th = rng.uniform(0, 2 * np.pi, nv)
        y = rng.uniform(-1, 1, nv) * self.thick(rho) * R * 0.9
        v = np.stack([rho * R * np.cos(th), y, rho * R * np.sin(th)], 1)
        return s, v
    def pulse(self, t): return 1.0
    def slice_colors(self, P):
        c = np.tile(np.array([255, 50, 70.]) * 1.6, (len(P), 1))
        r = np.sqrt(P[:, 0] ** 2 + P[:, 2] ** 2)
        c[r < 0.35] = np.array([255, 120, 140.]) * 0.9
        return c

# ------------------------------------------------------------------ skin block
class Skin(Organ):
    name = "skin"; pal = ((255, 200, 120), (255, 110, 60), (220, 40, 80)); view_rot = 0.5
    labels = [("EPIDERMIS", (0.9, 0.93), 1), ("DERMIS", (0.9, 0.55), 1), ("FAT", (0.9, -0.05), 1), ("MUSCLE", (0.9, -0.7), 1)]
    def build(self, rng):
        box_lo, box_hi = np.array([-1.0, -0.55, -0.95]), np.array([1.0, 0.55, 1.0])
        top = lambda x, y: 1.0 + 0.03 * np.sin(x * 9) * np.cos(y * 7)
        n = NS - 500; faces = rng.integers(0, 6, n); p = rng.uniform(box_lo, box_hi, (n, 3))
        for ax in range(3):
            p[faces == ax * 2, ax] = box_lo[ax]; p[faces == ax * 2 + 1, ax] = box_hi[ax]
        topm = faces == 5; p[topm, 2] = top(p[topm, 0], p[topm, 1])
        hair = []
        for _ in range(25):
            hx, hy = rng.uniform(-0.9, 0.9), rng.uniform(-0.5, 0.5); L = rng.uniform(0.25, 0.45); ang = rng.uniform(-0.4, 0.4)
            u = rng.uniform(0, 1, 20); hair.append(np.stack([hx + np.sin(ang) * L * u, np.full(20, hy), 1.0 + L * u * np.cos(ang)], 1))
        v = rng.uniform(box_lo, box_hi, (N - NS, 3))
        return np.concatenate([p, np.concatenate(hair)]), v
    def pulse(self, t): return 1.0
    def slice_colors(self, P):
        z = P[:, 2]; c = np.zeros((len(P), 3))
        c[:] = np.array([220, 40, 60.]) * (1.1 + 0.3 * np.sin(z * 60))[:, None]     # muscle striations
        fat = z > -0.45; c[fat] = np.array([255, 210, 90.]) * (1.0 + 0.5 * (np.sin(P[fat, 0] * 30) * np.sin(z[fat] * 30) > 0.3))[:, None]
        der = z > 0.25; c[der] = np.array([255, 120, 150.]) * 1.4
        fol = der & (np.abs(np.sin(P[:, 0] * 6)) > 0.97); c[fol] = np.array([255, 240, 220.]) * 1.8
        epi = z > 0.86; c[epi] = np.array([255, 220, 180.]) * 2.0
        return c

# ------------------------------------------------------------------ long bone
class Bone(Organ):
    name = "bone"; pal = ((255, 245, 225), (200, 220, 255), (120, 160, 255))
    labels = [("COMPACT BONE", (0.27, 0.2), 1), ("SPONGY BONE", (0.0, 0.95), 1), ("MARROW", (0.0, -0.1), -1)]
    def f(self, p):
        shaft = (p[:, 0] ** 2 + p[:, 1] ** 2) / 0.27 ** 2 - 1 + np.where(np.abs(p[:, 2]) > 1.0, 9, 0)
        e1 = ((p[:, 0] - 0.05) ** 2 + p[:, 1] ** 2 + (p[:, 2] - 1.05) ** 2) / 0.45 ** 2 - 1
        e2 = (p[:, 0] ** 2 + p[:, 1] ** 2 + (p[:, 2] + 1.05) ** 2) / 0.42 ** 2 - 1
        return np.minimum.reduce([shaft, e1, e2])
    def build(self, rng):
        s = np.concatenate([_surface_from_implicit(self.f, NS // 3, rng, center=(0, 0, 0)),
                            _surface_from_implicit(self.f, NS // 3, rng, center=(0.05, 0, 1.05)),
                            _surface_from_implicit(self.f, NS - 2 * (NS // 3), rng, center=(0, 0, -1.05))])
        v = _sample_implicit(self.f, N - NS, ([-0.5, -0.5, -1.5], [0.55, 0.5, 1.5]), rng)
        return s, v
    def pulse(self, t): return 1.0
    def slice_colors(self, P):
        r = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2); z = P[:, 2]
        c = np.tile(np.array([255, 245, 225.]) * 1.8, (len(P), 1))       # compact
        ends = np.abs(z) > 0.8
        sp = ends & ((np.sin(P[:, 0] * 45) * np.sin(z * 45)) > 0.2); c[sp] = np.array([255, 150, 120.]) * 1.3
        c[ends & ~sp] = np.array([255, 235, 210.]) * 1.4
        marrow = (~ends) & (r < 0.17); c[marrow] = np.array([255, 40, 60.]) * 1.5
        return c

# ------------------------------------------------------------------ brain (side view, coronal slice)
class Brain(Organ):
    name = "brain"; pal = ((255, 120, 200), (170, 110, 255), (90, 200, 255)); view_rot = math.pi / 2.4
    labels = [("GRAY MATTER", (0.7, 0.55), 1), ("WHITE MATTER", (-0.25, 0.1), -1)]
    def f(self, p):
        x, y, z = p[:, 0] / 0.85, p[:, 1] / 1.15, (p[:, 2] - 0.1) / 0.8
        g = 0.05 * np.sin(p[:, 0] * 11 + np.sin(p[:, 1] * 9) * 2) * np.sin(p[:, 2] * 10 + p[:, 1] * 6)
        groove = 0.08 * np.exp(-(p[:, 0] / 0.05) ** 2) * (p[:, 2] > -0.1)
        cb = ((p[:, 0] / 0.55) ** 2 + ((p[:, 1] - 0.75) / 0.4) ** 2 + ((p[:, 2] + 0.6) / 0.28) ** 2) - 1
        return np.minimum(x * x + y * y + z * z - 1 + g + groove * 6, cb)
    def build(self, rng):
        s = _surface_from_implicit(self.f, NS, rng)
        v = _sample_implicit(self.f, N - NS, ([-0.9, -1.2, -0.9], [0.9, 1.2, 1.0]), rng)
        return s, v
    def pulse(self, t): return 1 + 0.01 * math.sin(t * 2)
    def slice_colors(self, P):
        x, z = P[:, 0], P[:, 2]
        rr = (x / 0.85) ** 2 + ((z - 0.1) / 0.8) ** 2
        c = np.tile(np.array([245, 240, 255.]) * 1.7, (len(P), 1))     # white matter
        gm = rr > 0.62 + 0.08 * np.sin(x * 25) * np.sin(z * 22); c[gm] = np.array([255, 110, 180.]) * 1.5
        vent = ((np.abs(x) - 0.12) / 0.07) ** 2 + ((z - 0.15) / 0.18) ** 2 < 1; c[vent] = np.array([40, 30, 80.])
        mid = np.abs(x) < 0.025; c[mid] = np.array([30, 20, 60.])
        return c

# ------------------------------------------------------------------ bacteria colony (rods + cocci)
class Bacteria(Organ):
    name = "bacteria"; pal = ((120, 255, 170), (40, 220, 200), (60, 140, 255)); view_tilt = 0.3
    def build(self, rng):
        pts_s, pts_v = [], []
        k = 46; ns_each = NS // k; nv_each = (N - NS) // k
        for i in range(k):
            c = rng.normal(0, 0.62, 3); c[1] *= 0.6
            d = rng.normal(size=3); d /= np.linalg.norm(d)
            rod = i % 3 != 0
            L = rng.uniform(0.18, 0.32) if rod else 0.0; r = rng.uniform(0.06, 0.09)
            def sample(n, surf):
                u = rng.uniform(-1, 1, n)[:, None] * L / 2
                q = rng.normal(size=(n, 3)); q /= np.linalg.norm(q, axis=1, keepdims=True)
                rr = r if surf else r * rng.uniform(0, 1, (n, 1)) ** (1 / 3)
                return c + u * d + q * rr
            pts_s.append(sample(ns_each, True)); pts_v.append(sample(nv_each, False))
        s = np.concatenate(pts_s); v = np.concatenate(pts_v)
        s = np.concatenate([s, s[: NS - len(s)]]) if len(s) < NS else s[:NS]
        v = np.concatenate([v, v[: (N - NS) - len(v)]]) if len(v) < N - NS else v[: N - NS]
        return s, v
    def pulse(self, t): return 1.0 + 0.02 * math.sin(t * 2.0)

# ------------------------------------------------------------------ DNA double helix (axis = z)
class DNA(Organ):
    name = "dna"; pal = ((120, 255, 220), (60, 160, 255), (190, 90, 255)); view_tilt = 0.15
    labels = [("BACKBONE", (0.45, 0.55), 1), ("BASE PAIRS", (0.0, -0.35), -1)]
    R0, TURNS, ZH = 0.42, 2.6, 1.45
    def _strand(self, rng, n, phase, jitter=0.03):
        z = rng.uniform(-self.ZH, self.ZH, n); a = z / (2 * self.ZH) * self.TURNS * 2 * np.pi + phase
        p = np.stack([self.R0 * np.cos(a), self.R0 * np.sin(a), z], 1)
        return p + rng.normal(size=(n, 3)) * jitter
    def _rungs(self, rng, n, k=34):
        zr = np.linspace(-self.ZH * 0.97, self.ZH * 0.97, k); i = rng.integers(0, k, n); z = zr[i]
        a = z / (2 * self.ZH) * self.TURNS * 2 * np.pi; u = rng.uniform(-1, 1, n)
        p = np.stack([self.R0 * np.cos(a) * u, self.R0 * np.sin(a) * u, z], 1)
        self._rung_u = u
        return p + rng.normal(size=(n, 3)) * 0.012
    def build(self, rng):
        ns = (NS - 1600) // 2
        s = np.concatenate([self._strand(rng, ns, 0), self._strand(rng, NS - 1600 - ns, np.pi), self._rungs(rng, 1600)])
        nv = N - NS
        v = np.concatenate([self._strand(rng, nv // 3, 0, 0.06), self._strand(rng, nv // 3, np.pi, 0.06), self._rungs(rng, nv - 2 * (nv // 3))])
        return s, v
    def pulse(self, t): return 1.0 + 0.015 * math.sin(t * 2.2)
    def surface_colors(self, P):
        rr = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        c = np.tile(np.array([90, 200, 255.]), (len(P), 1))
        rung = rr < self.R0 * 0.85
        side = (P[:, 0] * np.cos(P[:, 2] * 6) > 0)
        c[rung & side] = np.array([255, 90, 170.]); c[rung & ~side] = np.array([255, 210, 80.])
        return c * 1.2
    def slice_colors(self, P):
        rr = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2)
        c = np.tile(np.array([120, 230, 255.]) * 1.8, (len(P), 1))
        rung = rr < self.R0 * 0.85
        c[rung] = np.where((np.floor(P[rung, 2] * 12) % 2 == 0)[:, None], np.array([255, 90, 170.]) * 1.7, np.array([255, 210, 80.]) * 1.7)
        return c

# ------------------------------------------------------------------ neuron (cell body top, axon down along -z)
class Neuron(Organ):
    name = "neuron"; pal = ((255, 200, 90), (255, 110, 200), (120, 140, 255)); view_tilt = 0.1
    labels = [("CELL BODY", (-0.15, 0.78), -1), ("MYELIN", (0.07, -0.12), 1), ("AXON", (-0.03, -0.55), -1)]
    SOMA = np.array([0.0, 0.0, 0.95])
    def _branches(self, rng, n):
        segs = []
        def br(p, d, L, depth, w):
            q = p + d * L; segs.append((p, q, w))
            if depth == 0: return
            for a in (-0.55, 0.5):
                c, s = math.cos(a), math.sin(a)
                nd = np.array([d[0] * c - d[2] * s, d[1] + rng.normal() * 0.2, d[0] * s + d[2] * c]); nd /= np.linalg.norm(nd)
                br(q, nd, L * 0.7, depth - 1, w * 0.7)
        for ang in np.linspace(-1.2, 1.2, 5):
            d = np.array([math.sin(ang), rng.normal() * 0.3, math.cos(ang) * 0.8 + 0.2]); d /= np.linalg.norm(d)
            br(self.SOMA + d * 0.2, d, 0.32, 3, 0.03)
        # axon terminals
        for ang in (-0.7, -0.25, 0.25, 0.7):
            d = np.array([math.sin(ang), 0, -math.cos(ang)]); br(np.array([0, 0, -1.25]), d, 0.22, 1, 0.02)
        k = rng.integers(0, len(segs), n); u = rng.uniform(0, 1, n)
        a = np.array([segs[i][0] for i in k]); b = np.array([segs[i][1] for i in k]); w = np.array([segs[i][2] for i in k])
        return a + (b - a) * u[:, None] + rng.normal(size=(n, 3)) * w[:, None] * 0.5
    def _axon(self, rng, n, r, z0=0.72, z1=-1.25):
        z = rng.uniform(z1, z0, n); th = rng.uniform(0, 2 * np.pi, n)
        rad = r * (1 + 0.9 * (self._myelin(z)))
        return np.stack([rad * np.cos(th), rad * np.sin(th), z], 1)
    def _myelin(self, z):
        return ((z < 0.55) & (z > -1.15) & (np.mod(z, 0.24) > 0.04)).astype(float)
    def build(self, rng):
        soma = self.SOMA + _surface_from_implicit(lambda p: (p ** 2).sum(1) - 0.23 ** 2, 1200, rng, rmax=0.5)
        s = np.concatenate([soma, self._axon(rng, 1500, 0.05), self._branches(rng, NS - 2700)])
        q = rng.normal(size=(1200, 3)); q /= np.linalg.norm(q, axis=1, keepdims=True)
        sv = self.SOMA + q * 0.22 * rng.uniform(0, 1, (1200, 1)) ** (1 / 3)
        ax = self._axon(rng, N - NS - 1200, 0.045); ax[:, :2] *= rng.uniform(0, 1, (len(ax), 1))
        return s * 0.8, np.concatenate([sv, ax]) * 0.8
    def pulse(self, t): return 1.0 + 0.02 * math.exp(-((t * 1.3) % 1.0) * 8)
    def slice_colors(self, P):
        P = P / 0.8
        c = np.tile(np.array([255, 200, 90.]) * 1.5, (len(P), 1))
        d = np.sqrt(((P - self.SOMA) ** 2).sum(1))
        c[d < 0.09] = np.array([255, 90, 170.]) * 1.8                       # nucleus
        rr = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2); ax = (P[:, 2] < 0.72) & (d > 0.24)
        c[ax] = np.array([0, 220, 255.]) * 1.7
        my = ax & (self._myelin(P[:, 2]) > 0) & (rr > 0.03); c[my] = np.array([245, 245, 255.]) * 1.9
        return c

REGISTRY = {"heart": Heart, "eye": Eye, "lungs": Lungs, "rbc": RBC, "skin": Skin, "bone": Bone, "brain": Brain, "bacteria": Bacteria, "dna": DNA, "neuron": Neuron}
_cache = {}
def get(name, seed=7):
    if name not in _cache: _cache[name] = REGISTRY[name](np.random.default_rng(seed + hash(name) % 97))
    return _cache[name]
