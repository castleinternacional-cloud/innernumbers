"""Inner Numbers long-form (16:9) - particle organs + bold/serif-italic typography + chapter clock + graphs.
python3 engine/longform.py episodes_long/no_sleep_sample.json out/long_sample
"""
import os, sys, json, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
import render as R
from heart3d import rot
import organs as O

W, H, FPS = 1920, 1080, 30
FB, FBo, FM = R.FONT_BLACK, R.FONT_BOLD, R.FONT_MED
SERIF_IT = "/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyrepagella-italic.otf"
if not os.path.exists(SERIF_IT): SERIF_IT = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-BoldItalic.ttf"
YELLOW = (255, 214, 0); WHITE = (240, 240, 250); SOFT = (175, 180, 210)
_fc = {}
def font(p, s):
    k = (p, int(s))
    if k not in _fc: _fc[k] = ImageFont.truetype(p, int(s))
    return _fc[k]

def ease(x): x = float(np.clip(x, 0, 1)); return x * x * (3 - 2 * x)

rng = np.random.default_rng(11)
ND = 4000
DUST = np.stack([rng.uniform(-W, W, ND), rng.uniform(-H, H, ND), rng.uniform(0.3, 1.0, ND)], 1)
BOKEH = np.stack([rng.uniform(0, W, 50), rng.uniform(0, H, 50), rng.uniform(8, 30, 50), rng.uniform(0, 6.28, 50)], 1)
yy = np.linspace(0, 1, H)[:, None, None]
BG = (np.array([16, 8, 36]) * (1 - yy) + np.array([4, 4, 12]) * yy) * np.ones((1, W, 1))

def splat(img, x, y, col, size=2):
    m = (x > 1) & (x < W - 3) & (y > 1) & (y < H - 3)
    X = x[m].astype(int); Y = y[m].astype(int); col = col[m]
    idx, cc = [], []
    for dy in range(size):
        for dx in range(size):
            idx.append((Y + dy) * W + X + dx); cc.append(col)
    if not idx or not len(X): return img
    idx = np.concatenate(idx); cc = np.concatenate(cc)
    acc = np.stack([np.bincount(idx, weights=cc[:, c], minlength=W * H) for c in range(3)], 1).reshape(H, W, 3)
    return img + acc.astype(np.float32)

def glow(arr, radius=18, half=4, gain=2.0):
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).resize((W // half, H // half), Image.BILINEAR)
    im = im.filter(ImageFilter.GaussianBlur(radius / half))
    return np.array(im.resize((W, H), Image.BILINEAR), np.float32) * gain

def bokeh(t, col=(90, 40, 160)):
    im = Image.new("RGB", (W // 4, H // 4)); d = ImageDraw.Draw(im)
    for x, y, r, ph in BOKEH:
        y2 = (y - t * 20 * (r / 20)) % H; a = 0.35 + 0.25 * math.sin(t * 1.5 + ph)
        c = tuple(int(v * a) for v in col)
        d.ellipse([(x - r) / 4, (y2 - r) / 4, (x + r) / 4, (y2 + r) / 4], fill=c)
    im = im.filter(ImageFilter.GaussianBlur(2)).resize((W, H), Image.BILINEAR)
    return np.array(im, np.float32)

def organ_pts(name, t, scale, cx, cy, yaw=0.0, tilt=0.0, spin=1.0, dim=1.0):
    o = O.get(name)
    Rm = rot(o.view_rot + yaw + 0.5 * math.sin(t * 0.5) * spin, o.view_tilt + tilt)
    Q = (o.P * o.pulse(t)) @ Rm.T
    s = scale * 4.0 / (4.0 + Q[:, 1])
    x = cx + Q[:, 0] * s; y = cy - Q[:, 2] * s
    p0, p1, p2 = [np.array(c, float) for c in o.pal]
    tt = np.clip((o.P[:, 2] + 1.2) / 2.6, 0, 1)[:, None]
    col = np.where(tt < .5, p0 + (p1 - p0) * tt * 2, p1 + (p2 - p1) * (tt - .5) * 2)
    if hasattr(o, "surface_colors"): col[~o.is_vol] = o.surface_colors(o.P[~o.is_vol])
    col = col * (1.25 - ((Q[:, 1] + 1.5) / 3) * 0.8)[:, None] * dim
    return x, y, col

def dust(t, zoom=1.0, cx=W / 2, cy=H / 2, dy=0.0):
    z = DUST[:, 2]
    x = cx + DUST[:, 0] * (1 + (zoom - 1) * z)
    y = cy + ((DUST[:, 1] - t * 25 * z + H) % (2 * H) - H) * (1 + (zoom - 1) * z) + dy * z
    return x, y, np.tile(np.array([140, 90, 255.]) * 0.35, (ND, 1)) * z[:, None]

def compose(t, parts):
    layer = np.zeros((H, W, 3), np.float32)
    for x, y, c, sz in parts: layer = splat(layer, x, y, c * 1.5, sz)
    img = BG + bokeh(t) * 0.6 + layer + glow(layer)
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))

def fade_col(c, a): return tuple(int(v * a) for v in c)

def heading(d, a, kicker, big, sub, x=120, y=150, size=120):
    if a <= 0: return
    if kicker: d.text((x + 4, y), kicker, font=font(FBo, 34), fill=fade_col(YELLOW, a))
    yb = y + 50
    for line in big.split("\n"):
        d.text((x, yb), line, font=font(FB, size), fill=fade_col(WHITE, a)); yb += int(size * 0.98)
    if sub: d.text((x + 6, yb + 18), sub, font=font(SERIF_IT, 56), fill=fade_col((235, 228, 240), a))

# ------------------------------------------------------------------ scenes: (sc, t, lt) -> PIL image
def sc_cold(sc, t, lt):
    v = sc["visual"]; e = ease(lt / max(1.0, sc["_dur"] * 0.9))
    org = v.get("organ", "brain")
    x, y, c = organ_pts(org, t, 1400 * (1 - e) + 330 * e, W * 0.5, H * 0.52)
    dx, dy, dc = dust(t, 2.4 * (1 - e) + 1.0 * e)
    im = compose(t, [(dx, dy, dc, 1), (x, y, c, 2)])
    return im

def sc_title(sc, t, lt):
    v = sc["visual"]
    x, y, c = organ_pts(v.get("organ", "brain"), t, 260, W * 0.79, H * 0.52)
    dx, dy, dc = dust(t)
    im = compose(t, [(dx, dy, dc, 1), (x, y, c, 2)]); d = ImageDraw.Draw(im)
    heading(d, ease((lt - 0.2) / 0.5), v.get("kicker"), v["title"], v.get("sub"), y=260, size=100)
    return im

def clock_txt(h): return f"{int(h):02d}:00"

def sc_clock(sc, t, lt):
    """Chapter: big hour counter on the left, organ dimming on the right, a fact card."""
    v = sc["visual"]; h0, h1 = v.get("from", 0), v["hour"]
    k = ease(lt / 1.4); h = h0 + (h1 - h0) * k
    dim = max(0.35, 1.0 - v.get("dim_rate", 0.0) * h)
    cam = v.get("camera")
    cy = H * 0.52
    if cam == "crane_up": cy = H * 1.2 * (1 - ease(lt / 1.6)) + H * 0.52 * ease(lt / 1.6)
    x, y, c = organ_pts(v.get("organ", "brain"), t, 300, W * 0.72, cy, spin=1.0 + h / 24, dim=dim)
    # flicker = microsleeps after hour 24
    if v.get("flicker") and (int(t * 7) % 9 == 0): c = c * 0.25
    dx, dy, dc = dust(t, 1.0, dy=0)
    im = compose(t, [(dx, dy, dc, 1), (x, y, c, 2)]); d = ImageDraw.Draw(im)
    a = ease(lt / 0.4)
    d.text((124, 150), v.get("label", "HOURS AWAKE"), font=font(FBo, 34), fill=fade_col(YELLOW, a))
    d.text((110, 190), f"DAY {int(round(h))}" if v.get("fmt") == "day" else clock_txt(h), font=font(FB, 230), fill=fade_col(WHITE, a))
    if v.get("fact"):
        b = ease((lt - 1.3) / 0.5)
        d.text((124, 470), v["fact"], font=font(FB, 64), fill=fade_col(YELLOW, b))
        if v.get("note"): d.text((128, 555), v["note"], font=font(SERIF_IT, 50), fill=fade_col((230, 225, 240), b))
    return im

GX0, GX1, GY0, GY1 = 160, 1180, 880, 330
def sc_graph(sc, t, lt):
    v = sc["visual"]
    x, y, c = organ_pts(v.get("organ", "brain"), t, 220, W * 0.82, H * 0.55, dim=0.6)
    dx, dy, dc = dust(t)
    im = compose(t, [(dx, dy, dc, 1), (x, y, c, 2)]); d = ImageDraw.Draw(im)
    a = ease(lt / 0.4)
    d.text((GX0, 160), v["title"], font=font(FB, 64), fill=fade_col(WHITE, a))
    if v.get("sub"): d.text((GX0 + 4, 240), v["sub"], font=font(SERIF_IT, 46), fill=fade_col((225, 220, 240), a))
    xmax, ymax = v["xmax"], v["ymax"]
    def P(px, py): return GX0 + (GX1 - GX0) * px / xmax, GY0 - (GY0 - GY1) * py / ymax
    d.line([(GX0, GY0), (GX1, GY0)], fill=fade_col(SOFT, a), width=3)
    d.line([(GX0, GY0), (GX0, GY1 - 20)], fill=fade_col(SOFT, a), width=3)
    for lx, lab in v.get("xlabels", []):
        px, _ = P(lx, 0); d.text((px, GY0 + 34), lab, font=font(FM, 32), fill=fade_col(SOFT, a), anchor="mm")
    for ly, lab in v.get("ylabels", []):
        _, py = P(0, ly); d.text((GX0 - 20, py), lab, font=font(FM, 30), fill=fade_col(SOFT, a), anchor="rm")
    for ly, lab in v.get("hlines", []):
        _, py = P(0, ly)
        for xx in range(GX0, GX1, 28): d.line([(xx, py), (xx + 14, py)], fill=fade_col((255, 90, 100), a), width=3)
        d.text((GX0 + 20, py - 26), lab, font=font(FBo, 30), fill=fade_col((255, 120, 130), a), anchor="lm")
    pts = v["points"]; k = ease((lt - 0.4) / max(1.0, sc["_dur"] * 0.7))
    xe = pts[0][0] + (pts[-1][0] - pts[0][0]) * k
    poly = []
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        for s in np.linspace(0, 1, 30):
            px = x0 + (x1 - x0) * s
            if px > xe: break
            poly.append(P(px, y0 + (y1 - y0) * s))
    if len(poly) > 1:
        d.line(poly, fill=YELLOW, width=8, joint="curve")
        ex, ey = poly[-1]; d.ellipse([ex - 12, ey - 12, ex + 12, ey + 12], fill=YELLOW)
        for (mx, my, lab) in v.get("marks", []):
            if xe >= mx:
                px, py = P(mx, my)
                d.ellipse([px - 9, py - 9, px + 9, py + 9], outline=WHITE, width=4)
                d.text((px - 14, py - 34), lab, font=font(FBo, 36), fill=WHITE, anchor="rb")
    return im

def sc_record(sc, t, lt):
    v = sc["visual"]; e = ease(lt / max(1.0, sc["_dur"] * 0.8))
    x, y, c = organ_pts(v.get("organ", "brain"), t, 420 * (1 - e) + 230 * e, W * 0.5, H * 0.55, dim=0.55)
    dx, dy, dc = dust(t, 1.0 + 0.6 * e)
    im = compose(t, [(dx, dy, dc, 1), (x, y, c, 2)]); d = ImageDraw.Draw(im)
    n = int(v["value"] * (1 - (1 - e) ** 3))
    a = ease(lt / 0.4)
    d.text((W / 2, H * 0.42), f"{n:,}", font=font(FB, 220 if n >= 1e8 else 260), fill=fade_col(YELLOW, a), anchor="mm", stroke_width=6, stroke_fill=(0, 0, 0))
    d.text((W / 2, H * 0.42 + 175), v.get("label", ""), font=font(SERIF_IT, 70), fill=fade_col(WHITE, a), anchor="mm")
    if v.get("note"): d.text((W / 2, H * 0.42 + 255), v["note"], font=font(FM, 38), fill=fade_col(SOFT, ease((lt - 1.2) / 0.5)), anchor="mm")
    return im

def sc_stats(sc, t, lt):
    """Up to 3 rows: big yellow number + serif label, revealed one by one."""
    v = sc["visual"]
    x, y, c = organ_pts(v.get("organ", "skin"), t, 260, W * 0.78, H * 0.52, dim=0.7)
    dx, dy, dc = dust(t)
    im = compose(t, [(dx, dy, dc, 1), (x, y, c, 2)]); d = ImageDraw.Draw(im)
    a0 = ease(lt / 0.4)
    if v.get("title"): d.text((124, 130), v["title"], font=font(FBo, 38), fill=fade_col(YELLOW, a0))
    rows = v["rows"]; step = max(1.0, sc["_dur"] * 0.8 / len(rows))
    for i, (num, lab) in enumerate(rows):
        a = ease((lt - 0.3 - i * step) / 0.5)
        if a <= 0: continue
        yb = 200 + i * 262
        d.text((118, yb), num, font=font(FB, 140), fill=fade_col(WHITE, a))
        d.text((126, yb + 150), lab, font=font(SERIF_IT, 48), fill=fade_col((230, 225, 240), a))
    return im

SCENES = {"cold": sc_cold, "title": sc_title, "clock": sc_clock, "graph": sc_graph, "record": sc_record, "stats": sc_stats}

# ------------------------------------------------------------------ subtitles (sentence by sentence, bottom)
def subtitle(d, sc, lt):
    txt = sc["say"]; words = txt.split(); dur = sc["_t1"] - sc["_t0"]
    if lt > dur + 0.2: return
    # chunk into ~8-word lines, timed by word share
    chunks, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) >= 8 or w.endswith((".", "?", "!", ",")) and len(cur) >= 4: chunks.append(cur); cur = []
    if cur: chunks.append(cur)
    tot = sum(len(" ".join(c)) for c in chunks); acc = 0
    for ch in chunks:
        s = " ".join(ch); share = len(s) / tot * dur
        if lt < acc + share or ch is chunks[-1]:
            f = font(FBo, 42); tw = d.textlength(s, font=f)
            d.rounded_rectangle([W / 2 - tw / 2 - 22, H - 132, W / 2 + tw / 2 + 22, H - 70], radius=14, fill=(8, 8, 16))
            d.text((W / 2, H - 101), s, font=f, fill=WHITE, anchor="mm"); return
        acc += share

def main(ep_path, outdir):
    ep = json.load(open(ep_path)); os.makedirs(outdir, exist_ok=True)
    timings, dur = R.make_voice(ep, outdir)
    R.make_music(dur + 1.0, outdir, heartbeat=False, seed=ep.get("seed", 5))
    scenes = ep["scenes"]
    for sc, (a, b) in zip(scenes, timings):
        sc["_t0"], sc["_t1"] = a, b; sc["_dur"] = b - a + R.GAP
    total = int((dur + 0.8) * FPS)
    tmp = os.path.join(outdir, "silent.mp4")
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for fi in range(total):
        t = fi / FPS
        si = next((k for k, s in enumerate(scenes) if s["_t0"] <= t < s["_t0"] + s["_dur"]), len(scenes) - 1)
        sc = scenes[si]; lt = t - sc["_t0"]
        im = SCENES[sc["visual"]["type"]](sc, t, lt)
        # short crossfade from black at each scene start
        if lt < 0.25 and si > 0:
            im = Image.blend(Image.new("RGB", (W, H)), im, 0.35 + 0.65 * lt / 0.25)
        d = ImageDraw.Draw(im)
        if ep.get("subtitles", True): subtitle(d, sc, lt)
        d.text((W - 60, 50), "INNER NUMBERS", font=font(FBo, 26), fill=(150, 155, 185), anchor="rm")
        ff.stdin.write(im.tobytes())
        if fi % 300 == 0: print("frame", fi, total, flush=True)
    ff.stdin.close(); ff.wait()
    final = os.path.join(outdir, f"{ep['id']}.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-i", os.path.join(outdir, "voice.wav"), "-i", os.path.join(outdir, "music.wav"),
                    "-filter_complex", "[1:a]aresample=44100[v];[v][2:a]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5[a]",
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", final], check=True)
    os.remove(tmp); print("DONE", final, round(dur, 1))

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
