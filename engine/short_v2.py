"""Inner Numbers v2 - style A (3D particles) + Veritasium-like graphs. Pure code.
python3 engine/short_v2.py episodes_v2/heart.json out/v2_heart
"""
import os, sys, json, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(__file__))
import render as R
from heart3d import rot, project
import organs as O
from styles import splat, glow, bokeh_layer, heartbeat_scale, font, FB, FBo, FM

W, H, FPS = 1080, 1920, 30
rng = np.random.default_rng(7)
N = 9000
CYAN = np.array([0, 230, 255.]); VIOLET = np.array([140, 90, 255.]); PINK = np.array([255, 70, 170.])
RED = np.array([255, 60, 80.]); BLUE = np.array([60, 170, 255.]); WHITE = np.array([235, 240, 255.])

def ease(x): x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)

# ------------------------------------------------------------------ shared geometry
PH = rng.uniform(0, 1, N)
DUST = np.stack([rng.uniform(0, W, N), rng.uniform(0, H, N)], 1)
EP_ORGAN = ["heart"]
SLICE_GAIN = 0.45

def organ_of(sc):
    return O.get(sc["visual"].get("organ", EP_ORGAN[0]))

def organ_screen(o, t, scale=330, cy=H * 0.45, cx=W / 2, rot_amt=1.0):
    Rm = rot(o.view_rot * rot_amt + 0.5 * math.sin(t * 0.9) * rot_amt, o.view_tilt * rot_amt + 0.08 * math.sin(t * 0.7))
    Q = (o.P * o.pulse(t)) @ Rm.T
    x, y, k = project(Q, W, H, scale, cx=cx, cy=cy)
    p0, p1, p2 = [np.array(c, float) for c in o.pal]
    tt = np.clip((o.P[:, 2] + 1.2) / 2.6, 0, 1)[:, None]
    col = np.where(tt < .5, p0 + (p1 - p0) * tt * 2, p1 + (p2 - p1) * (tt - .5) * 2)
    if hasattr(o, "surface_colors"): col[~o.is_vol] = o.surface_colors(o.P[~o.is_vol])
    col = col * (1.25 - ((Q[:, 1] + 1.5) / 3) * 0.8)[:, None]
    return np.stack([x, y], 1), col, Q

def dust(t, amt=1.0):
    p = DUST.copy(); p[:, 1] = (p[:, 1] - t * 20 * (0.3 + PH)) % H; p[:, 0] += np.sin(t * 0.6 + PH * 20) * 10
    return p, np.tile(VIOLET * 0.25 * amt, (N, 1))

def fill_rect_targets(idx, x0, y0, x1, y1):
    n = len(idx)
    return np.stack([rng.uniform(x0, x1, n), rng.uniform(y0, y1, n)], 1)

# ------------------------------------------------------------------ scenes: each returns (targets, colors, overlay_fn)
def sc_heart(sc, t, lt):
    p, c, _ = organ_screen(organ_of(sc), t)
    v = sc["visual"]
    def ov(d):
        if v.get("title"):
            a = ease((lt - 0.2) / 0.4); g = int(255 * a)
            fit_text(d, v["title"], H * 0.16, 170, (g, g, g))
            if v.get("sub"): d.text((W / 2, H * 0.16 + 120), v["sub"], font=font(FBo, 52), fill=(g, int(g * .82), int(g * .88)), anchor="mm")
    return p, c, ov

def fit_text(d, txt, y, size, fill, maxw=W * 0.9):
    while size > 40 and d.textlength(txt, font=font(FB, size)) > maxw: size -= 6
    d.text((W / 2, y), txt, font=font(FB, size), fill=fill, anchor="mm", stroke_width=6, stroke_fill=(0, 0, 0))

def sc_counter(sc, t, lt):
    p, c, _ = organ_screen(organ_of(sc), t, scale=200, cy=H * 0.56)
    v = sc["visual"]; target = v["value"]; dur = sc["_dur"]
    def ov(d):
        x = ease(lt / max(0.5, min(1.6, dur * 0.6))); val = int(round(target * (1 - (1 - x) ** 3)))
        fit_text(d, f"{val:,}" + v.get("suffix", ""), H * 0.27, 190, (255, 255, 255))
        d.text((W / 2, H * 0.27 + 130), v.get("label", ""), font=font(FBo, 54), fill=(255, 210, 225), anchor="mm")
        if v.get("note"): d.text((W / 2, H * 0.27 + 200), v["note"], font=font(FM, 40), fill=(170, 180, 210), anchor="mm")
    return p, c * 0.8, ov

GX0, GX1, GY0, GY1 = 150, W - 110, H * 0.62, H * 0.30   # graph box (y0 bottom)
def sc_linegraph(sc, t, lt):
    v = sc["visual"]; pts = np.array(v["points"], float)  # [[x,y],...] in data units
    xmax, ymax = v["xmax"], v["ymax"]; dur = sc["_dur"]
    prog = ease((lt - 0.4) / max(0.6, dur * 0.75))
    def to_screen(a):
        return np.stack([GX0 + a[:, 0] / xmax * (GX1 - GX0), GY0 - a[:, 1] / ymax * (GY0 - GY1)], 1)
    S = to_screen(pts)
    # interpolate current head
    xs = np.linspace(0, xmax, 300); ys = np.interp(xs, pts[:, 0], pts[:, 1]); C = to_screen(np.stack([xs, ys], 1))
    k = max(2, int(prog * 299) + 1)
    # particles fill area under curve up to progress
    n_area = int(N * 0.55); idx = np.arange(n_area)
    u = rng.uniform(0, 1, n_area) if "_u" not in sc else sc["_u"]; sc["_u"] = u
    vfrac = sc.setdefault("_v", rng.uniform(0, 1, n_area))
    xx = u * (xs[k - 1]); yy = np.interp(xx, pts[:, 0], pts[:, 1]) * vfrac
    A = to_screen(np.stack([xx, yy], 1))
    dp, dc = dust(t, 0.6)
    tg = dp.copy(); col = dc.copy()
    tg[:n_area] = A; col[:n_area] = CYAN * 0.35
    def ov(d):
        a = ease(lt * 2)
        g = int(60 * a)
        for i in range(5):
            gy = GY0 - (GY0 - GY1) * i / 4
            d.line([(GX0, gy), (GX1, gy)], fill=(g, g + 10, g + 30), width=1)
            d.text((GX0 - 18, gy), v["ylabels"][i], font=font(FM, 34), fill=(150, 160, 190), anchor="rm")
        for i, lab in enumerate(v["xlabels"]):
            gx = GX0 + (GX1 - GX0) * i / (len(v["xlabels"]) - 1)
            d.text((gx, GY0 + 40), lab, font=font(FM, 34), fill=(150, 160, 190), anchor="mm")
        d.line([(GX0, GY0), (GX1, GY0)], fill=(200, 205, 225), width=3)
        d.line([(GX0, GY0), (GX0, GY1 - 30)], fill=(200, 205, 225), width=3)
        for (x0, x1, lab) in v.get("bands", []):
            sx0 = GX0 + x0 / xmax * (GX1 - GX0); sx1 = GX0 + x1 / xmax * (GX1 - GX0)
            d.rectangle([sx0, GY1 - 30, sx1, GY0], outline=None, fill=None)
            d.text(((sx0 + sx1) / 2, GY1 - 10), lab, font=font(FBo, 36), fill=(140, 150, 255), anchor="mm")
            d.line([(sx1, GY1), (sx1, GY0)], fill=(90, 90, 160), width=2)
        d.line([tuple(p) for p in C[:k]], fill=(0, 230, 255), width=7, joint="curve")
        hx, hy = C[k - 1]; val = ys[k - 1]
        d.ellipse([hx - 14, hy - 14, hx + 14, hy + 14], fill=(255, 255, 255))
        d.text((hx - 20, hy - 50), f"{int(val):,}", font=font(FB, 64), fill=(255, 255, 255), anchor="rm", stroke_width=5, stroke_fill=(0, 0, 0))
        d.text((W / 2, H * 0.21), v["title"], font=font(FB, 70), fill=(255, 255, 255), anchor="mm")
    return tg, col, ov

def sc_bars(sc, t, lt, state):
    v = sc["visual"]; items = v["items"]; show = v["show"]   # how many bars visible in this scene
    n = len(items); vmax = max(i[1] for i in items)
    bw = 200; gap = (W - 2 * 120 - n * bw) / (n - 1); base = H * 0.64; top = H * 0.26
    dp, dc = dust(t, 0.5); tg = dp.copy(); col = dc.copy()
    per = int(N * 0.6 / n)
    rects = []
    for i, (name, val, sub) in enumerate(items):
        x0 = 120 + i * (bw + gap); grow = 1.0 if i < show - 1 else ease(lt / 0.9)
        if i >= show: grow = 0
        h = (base - top) * val / vmax * grow
        rects.append((x0, base - h, x0 + bw, base, grow, name, val, sub))
        if grow > 0:
            sl = slice(i * per, (i + 1) * per)
            hh = max(h, 6)
            uv = sc.setdefault(f"_uv{i}", rng.uniform(0, 1, (per, 2)))
            tg[sl] = np.stack([x0 + 4 + uv[:, 0] * (bw - 8), base - uv[:, 1] * hh], 1)
            col[sl] = [PINK, VIOLET, CYAN][i % 3] * 0.9
    def ov(d):
        d.text((W / 2, H * 0.19), v["title"], font=font(FB, 70), fill=(255, 255, 255), anchor="mm")
        d.line([(80, base + 3), (W - 80, base + 3)], fill=(200, 205, 225), width=3)
        for (x0, y0, x1, y1, grow, name, val, sub) in rects:
            if grow <= 0: continue
            cx = (x0 + x1) / 2
            vv = val * grow; txt = f"{vv:.1f}" if (val < 10 and val != int(val)) else f"{int(round(vv)):,}"
            d.text((cx, min(y0, base - 6) - 50), txt + v.get("unit", ""), font=font(FB, 70), fill=(255, 255, 255), anchor="mm", stroke_width=5, stroke_fill=(0, 0, 0))
            d.text((cx, base + 55), name, font=font(FBo, 42), fill=(230, 235, 255), anchor="mm")
            d.text((cx, base + 105), sub, font=font(FM, 32), fill=(150, 160, 190), anchor="mm")
    return tg, col, ov

def sc_cutaway(sc, t, lt):
    o = organ_of(sc); P0 = o.P; IV = o.is_vol
    turn = ease(lt / 0.6); sep = ease((lt - 0.5) / 1.0)
    Rm = rot((o.view_rot + 0.3 * math.sin(t * 0.6)) * (1 - turn), o.view_tilt * (1 - turn))
    P = P0 * o.pulse(t)
    front = (~IV) & (P[:, 1] < 0)
    Pm = P.copy()
    Pm[front, 1] -= 2.4 * sep; Pm[front, 0] += np.sign(P[front, 0] + 1e-6) * 1.2 * sep
    flat = IV | ((~IV) & ~front)
    Pm[flat, 1] = P[flat, 1] * (1 - sep)
    Q = Pm @ Rm.T
    x, y, k = project(Q, W, H, 330, cy=H * 0.47)
    p0, p1, p2 = [np.array(c, float) for c in o.pal]
    col = np.tile(p1 * 0.7, (N, 1))
    col[flat] = col[flat] * (1 - sep) + o.slice_colors(P0[flat]) * sep * SLICE_GAIN
    col[front] *= np.clip(1 - sep * 1.6, 0, 1)
    tg = np.stack([x, y], 1)
    v = sc["visual"]
    def ov(d):
        a = ease((lt - 1.4) / 0.5)
        if a <= 0: return
        g = int(255 * a)
        if v.get("value"):
            fit_text(d, v["value"], H * 0.15, 150, (g, g, g))
            d.text((W / 2, H * 0.15 + 110), v.get("label", ""), font=font(FBo, 52), fill=(g, int(g * .8), int(g * .85)), anchor="mm")
        for i, (name, (px, pz), side) in enumerate(v.get("labels_override", None) or o.labels):
            aa = np.clip(a * 2 - i * 0.3, 0, 1); gg = int(255 * aa)
            if gg <= 0: continue
            sx, sy = W / 2 + px * 330, H * 0.47 - pz * 330
            if side: ex, ey = sx + side * 120, sy + 230
            else: ex, ey = sx, sy - 200
            ex = min(max(ex, 230), W - 230)
            d.ellipse([sx - 8, sy - 8, sx + 8, sy + 8], outline=(gg, gg, gg), width=4)
            d.line([(sx, sy), (ex, ey)], fill=(gg, gg, gg), width=3)
            d.text((ex, ey + (30 if side else -30)), name, font=font(FBo, 38), fill=(gg, gg, gg), anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0))
    return tg, col, ov

def tub_icon(d, x, y, w, h, fill, colr):
    # bathtub: rounded body + rim + legs
    d.rounded_rectangle([x, y + h * 0.25, x + w, y + h * 0.85], radius=int(h * 0.25), outline=colr, width=4)
    d.line([(x - 6, y + h * 0.25), (x + w + 6, y + h * 0.25)], fill=colr, width=5)
    d.line([(x + w * 0.15, y + h * 0.85), (x + w * 0.12, y + h)], fill=colr, width=4)
    d.line([(x + w * 0.85, y + h * 0.85), (x + w * 0.88, y + h)], fill=colr, width=4)
    d.line([(x + w * 0.82, y + h * 0.25), (x + w * 0.82, y), (x + w * 0.95, y)], fill=colr, width=4)
    if fill > 0:
        fy = y + h * 0.85 - 6 - (h * 0.6 - 6) * fill
        if fy < y + h * 0.85 - 5: d.rounded_rectangle([x + 5, fy, x + w - 5, y + h * 0.85 - 5], radius=int(min(h * 0.18, max(1, (y + h * 0.85 - 5 - fy) / 2))), fill=(40, 150, 255))

def sc_tubs(sc, t, lt):
    v = sc["visual"]; total = v["count"]; dur = sc["_dur"]
    cols, rows = 6, 8; tw, th = 120, 80; gx = (W - cols * tw) / (cols + 1); y0 = H * 0.22
    prog = ease((lt - 0.3) / max(0.6, dur * 0.8)) * total
    dp, dc = dust(t, 0.5)
    def ov(d):
        d.text((W / 2, H * 0.15), v["title"], font=font(FB, 64), fill=(255, 255, 255), anchor="mm")
        for i in range(total):
            r, c = divmod(i, cols)
            x = gx + c * (tw + gx); y = y0 + r * (th + 22)
            f = float(np.clip(prog - i, 0, 1))
            tub_icon(d, x, y, tw, th, f, (220, 230, 255) if f > 0 else (90, 100, 130))
        d.text((W / 2, y0 + rows * (th + 22) + 50), f"{int(min(prog, total))} bathtubs", font=font(FB, 80), fill=(255, 255, 255), anchor="mm", stroke_width=5, stroke_fill=(0, 0, 0))
    return dp, dc, ov

def sc_end(sc, t, lt):
    p, c, _ = organ_screen(organ_of(sc), t, scale=230, cy=H * 0.40)
    def ov(d):
        d.text((W / 2, H * 0.60), "INNER NUMBERS", font=font(FB, 96), fill=(240, 245, 255), anchor="mm")
        d.text((W / 2, H * 0.60 + 85), "your body, counted", font=font(FM, 48), fill=(0, 230, 255), anchor="mm")
    return p, c, ov

SCENES = {"heart3d": sc_heart, "counter": sc_counter, "linegraph": sc_linegraph, "bars": sc_bars,
          "cutaway": sc_cutaway, "tubs": sc_tubs, "end": sc_end}

# ------------------------------------------------------------------ optional camera moves (opt-in per scene)
# scene["visual"]["camera"]: "pull_back" | "push_in" | "crane_up"
CAM_C = np.array([W / 2, H * 0.47])
def apply_camera(sc, tg, lt):
    cam = sc["visual"].get("camera")
    if not cam: return tg
    e = ease(lt / max(0.6, min(1.8, sc["_dur"] * 0.7)))
    if cam == "pull_back": return CAM_C + (tg - CAM_C) * (2.8 * (1 - e) + e)
    if cam == "push_in": return CAM_C + (tg - CAM_C) * (1 + 0.35 * e)
    if cam == "crane_up": return tg + np.array([0, H * 0.6 * (1 - e)])
    return tg

def captions(d, t, wt):
    i = next((k for k, w in enumerate(wt) if w[0] <= t < w[1]), None)
    if i is None: return
    # group words into chunks of <=3 that don't cross sentence/scene ends
    grp_start = wt[i][3]; grp = [w for w in wt if w[3] == grp_start]
    words = [g[2].upper() for g in grp]; size = 88
    while True:
        f = font(FB, size); widths = [d.textlength(x + " ", font=f) for x in words]
        if sum(widths) <= W * 0.9 or size < 50: break
        size -= 4
    x = W / 2 - sum(widths) / 2; y = H * 0.80
    for g, wd, ww in zip(grp, words, widths):
        active = g is wt[i]
        d.text((x, y), wd, font=f, fill=(255, 220, 60) if active else (255, 255, 255), anchor="lm", stroke_width=9, stroke_fill=(0, 0, 0))
        x += ww

CAP_STYLE = ["a"]
FSB = "/usr/share/fonts/opentype/inter/InterDisplay-SemiBold.otf"
NUMWORDS = set("one two three four five six seven eight nine ten eleven twelve fifteen seventeen twenty thirty forty fifty sixty seventy eighty ninety hundred thousand million billion trillion half percent".split())

def chunks_v2(scenes):
    """sentence chunks (<=7 words) with per-word timing: list of (t0, t1, [(w, a, b)])"""
    out = []
    for sc in scenes:
        words = sc["say"].split(); L = [len(w) + 2 for w in words]; tot = sum(L); t = sc["_t0"]; cur = []
        for w, l in zip(words, L):
            dd = (sc["_t1"] - sc["_t0"]) * l / tot; cur.append((w, t, t + dd)); t += dd
            if len(cur) >= 7 or (w[-1] in ".?!" and len(cur) >= 3):
                out.append(cur); cur = []
        if cur: out.append(cur)
    return [(c[0][1], c[-1][2] + 0.15, c) for c in out]

def wrap(d, words, f, maxw):
    lines = [[]]
    for w in words:
        test = " ".join([x[0] for x in lines[-1]] + [w[0]])
        if lines[-1] and d.textlength(test, font=f) > maxw: lines.append([])
        lines[-1].append(w)
    return lines

def captions_v2(d, im, t, ch):
    st = CAP_STYLE[0]
    c = next((c for c in ch if c[0] <= t < c[1]), None)
    if c is None: return
    words = c[2]
    if st == "d1":
        f = font(FSB, 58); lines = wrap(d, words, f, 820); y0 = H * 0.79 - (len(lines) - 1) * 36
        ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        od.rounded_rectangle([90, y0 - 60, W - 90, y0 + (len(lines) - 1) * 72 + 60], radius=30, fill=(0, 0, 0, 150))
        im.paste(Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB"))
        d2 = ImageDraw.Draw(im)
        for i, ln in enumerate(lines):
            d2.text((W / 2, y0 + i * 72), " ".join(x[0] for x in ln), font=f, fill=(255, 255, 255), anchor="mm")
    elif st == "d2":
        f = font(FSB, 62); lines = wrap(d, words, f, 900); y0 = H * 0.79 - (len(lines) - 1) * 38
        for i, ln in enumerate(lines):
            tw = d.textlength(" ".join(x[0] for x in ln), font=f); x = W / 2 - tw / 2
            for (w, a, b) in ln:
                col = (255, 255, 255) if a <= t else (150, 150, 170)
                d.text((x, y0 + i * 76), w, font=f, fill=col, anchor="lm", stroke_width=3, stroke_fill=(10, 5, 20))
                x += d.textlength(w + " ", font=f)
    elif st == "d3":
        f = font(FSB, 56); lines = wrap(d, words, f, 840); y0 = H * 0.77
        hgt = len(lines) * 70
        d.rectangle([92, y0 - 38, 100, y0 - 38 + hgt], fill=(0, 230, 255))
        for i, ln in enumerate(lines):
            x = 128
            for (w, a, b) in ln:
                if a > t: break
                d.text((x, y0 + i * 70), w, font=f, fill=(255, 255, 255), anchor="lm", stroke_width=2, stroke_fill=(10, 5, 20))
                x += d.textlength(w + " ", font=f)
    elif st == "d4y":
        f = font(FBo, 64); lines = wrap(d, words, f, 900); y0 = H * 0.79 - (len(lines) - 1) * 40
        for i, ln in enumerate(lines):
            tw = d.textlength(" ".join(x[0] for x in ln), font=f); x = W / 2 - tw / 2
            for (w, a, b) in ln:
                k = float(np.clip((t - a) / 0.18, 0, 1))
                ww = w.strip(".,?!").lower(); key = ww in NUMWORDS or (ww.rstrip("s") in NUMWORDS and ww != "ones") or ww in ("tens", "dozens") or any(ch.isdigit() for ch in w)
                base = (255, 214, 60) if key else (255, 255, 255)
                col = tuple(int(v * k + 20 * (1 - k)) for v in base)
                if k > 0: d.text((x, y0 + i * 80 + (1 - k) * 14), w, font=f, fill=col, anchor="lm", stroke_width=3, stroke_fill=(10, 5, 20))
                x += d.textlength(w + " ", font=f)
    elif st == "d4":
        f = font(FSB, 62); lines = wrap(d, words, f, 900); y0 = H * 0.79 - (len(lines) - 1) * 38
        for i, ln in enumerate(lines):
            tw = d.textlength(" ".join(x[0] for x in ln), font=f); x = W / 2 - tw / 2
            for (w, a, b) in ln:
                k = float(np.clip((t - a) / 0.18, 0, 1))
                key = w.strip(".,?!").lower() in NUMWORDS
                base = (0, 230, 255) if key else (255, 255, 255)
                col = tuple(int(v * k + 20 * (1 - k)) for v in base)
                if k > 0: d.text((x, y0 + i * 76 + (1 - k) * 14), w, font=f, fill=col, anchor="lm", stroke_width=3, stroke_fill=(10, 5, 20))
                x += d.textlength(w + " ", font=f)

def word_timing(scenes):
    out = []; gid = 0
    for sc in scenes:
        words = sc["say"].split(); L = [len(w) + 2 for w in words]; tot = sum(L); t = sc["_t0"]
        cnt = 0
        for w, l in zip(words, L):
            dd = (sc["_t1"] - sc["_t0"]) * l / tot
            out.append((t, t + dd, w, gid)); t += dd; cnt += 1
            if cnt >= 3 or w[-1] in ".,?!": gid += 1; cnt = 0
        gid += 1
    return out

def main(ep_path, outdir):
    ep = json.load(open(ep_path)); os.makedirs(outdir, exist_ok=True)
    EP_ORGAN[0] = ep.get("organ", "heart")
    timings, dur = R.make_voice(ep, outdir)
    R.make_music(dur + 0.8, outdir, heartbeat=ep.get("heartbeat", EP_ORGAN[0] == "heart"), seed=ep.get("seed", 3))
    scenes = ep["scenes"]
    for sc, (a, b) in zip(scenes, timings):
        sc["_t0"], sc["_t1"] = a, b; sc["_dur"] = b - a + R.GAP
    wt = word_timing(scenes); ch = chunks_v2(scenes)
    CAP_STYLE[0] = ep.get("captions", "a")
    pos = DUST.copy().astype(np.float32); vel = np.zeros_like(pos)
    total = int((dur + 0.6) * FPS)
    tmp = os.path.join(outdir, "silent.mp4")
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    yy = np.linspace(0, 1, H)[:, None, None]
    bg0 = (np.array([16, 8, 36]) * (1 - yy) + np.array([4, 4, 12]) * yy) * np.ones((1, W, 1))
    colcur = np.tile(VIOLET * 0.3, (N, 1))
    for fi in range(total):
        t = fi / FPS
        si = next((k for k, s in enumerate(scenes) if s["_t0"] <= t < s["_t0"] + s["_dur"]), len(scenes) - 1)
        sc = scenes[si]; lt = t - sc["_t0"]
        fn = SCENES[sc["visual"]["type"]]
        tg, col, ov = fn(sc, t, lt, None) if fn is sc_bars else fn(sc, t, lt)
        tg = apply_camera(sc, tg, lt)
        act = np.clip(lt * 2.5 - PH * 0.7, 0, 1)[:, None]
        vel = vel * 0.72 + (tg - pos) * 0.16 * act
        pos = pos + vel
        colcur = colcur + (col - colcur) * 0.12
        layer = splat(np.zeros((H, W, 3), np.float32), pos[:, 0], pos[:, 1], colcur * 1.5, 2)
        img = bg0 + bokeh_layer(t, (90, 40, 160)) * 0.7 + layer + glow(layer, 18, gain=2.0)
        im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
        if ov: ov(d)
        if CAP_STYLE[0] == "a": captions(d, t, wt)
        else: captions_v2(d, im, t, ch); d = ImageDraw.Draw(im)
        d.text((W / 2, H - 110), "INNER NUMBERS", font=font(FBo, 32), fill=(170, 175, 200), anchor="mm")
        ff.stdin.write(im.tobytes())
        if fi % 150 == 0: print("frame", fi, total, flush=True)
    ff.stdin.close(); ff.wait()
    final = os.path.join(outdir, f"{ep['id']}.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-i", os.path.join(outdir, "voice.wav"), "-i", os.path.join(outdir, "music.wav"),
                    "-filter_complex", "[1:a]aresample=44100[v];[v][2:a]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5[a]",
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", final], check=True)
    os.remove(tmp); print("DONE", final, round(dur, 1))

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
