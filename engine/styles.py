"""Three 7-second style test clips, pure code. python3 engine/styles.py out/styles"""
import os, sys, subprocess, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
sys.path.insert(0, os.path.dirname(__file__))
from heart3d import f_heart, surface_points, volume_points, rot, project, raymarch_cut
import render as R

W, H, FPS = 1080, 1920, 30
DUR = 7.0
LINE = "Your heart will beat about one hundred thousand times today."
FB = R.FONT_BLACK; FBo = R.FONT_BOLD; FM = R.FONT_MED
rng = np.random.default_rng(3)

def font(p, s): return ImageFont.truetype(p, int(s))

def voice(out):
    import soundfile as sf
    from kokoro_onnx import Kokoro
    k = Kokoro(os.path.join(R.ROOT, "models/kokoro-v1.0.onnx"), os.path.join(R.ROOT, "models/voices-v1.0.bin"))
    s, sr = k.create(LINE, voice="am_michael", speed=1.0, lang="en-us")
    pad = np.zeros(int(sr * 0.6), np.float32)
    a = np.concatenate([pad, s.astype(np.float32)])
    sf.write(os.path.join(out, "voice.wav"), a / np.abs(a).max() * 0.9, sr)
    return 0.6, 0.6 + len(s) / sr

def words_timing(t0, t1):
    w = LINE.split(); L = [len(x) + 2 for x in w]; tot = sum(L); out = []; t = t0
    for x, l in zip(w, L):
        d = (t1 - t0) * l / tot; out.append((t, t + d, x)); t += d
    return out

def draw_caption(d, t, wt, y):
    # show 3-word window, active word highlighted
    i = next((k for k, (a, b, _) in enumerate(wt) if a <= t < b), None)
    if i is None: return
    s = (i // 3) * 3; grp = wt[s:s + 3]
    words = [g[2].upper() for g in grp]; size = 92
    while True:
        f = font(FB, size); widths = [d.textlength(x + " ", font=f) for x in words]
        if sum(widths) <= W * 0.9 or size < 50: break
        size -= 4
    x = W / 2 - sum(widths) / 2
    for k, (wd, ww) in enumerate(zip(words, widths)):
        active = (s + k) == i
        col = (255, 220, 60) if active else (255, 255, 255)
        d.text((x, y), wd, font=f, fill=col, anchor="lm", stroke_width=9, stroke_fill=(0, 0, 0))
        x += ww

def counter_value(t, t0=1.0, t1=4.2, target=100000):
    p = np.clip((t - t0) / (t1 - t0), 0, 1); p = 1 - (1 - p) ** 3
    return int(target * p)

def bg_space(t, tint=(10, 14, 34)):
    yy = np.linspace(0, 1, H)[:, None, None]
    base = np.array(tint) * (1 - yy) + np.array([4, 4, 12]) * yy
    return np.broadcast_to(base, (H, W, 3)).astype(np.float32).copy()

BOKEH = np.stack([rng.uniform(0, W, 60), rng.uniform(0, H, 60), rng.uniform(6, 26, 60), rng.uniform(0, 6.28, 60)], 1)
def bokeh_layer(t, col):
    im = Image.new("RGB", (W // 4, H // 4)); d = ImageDraw.Draw(im)
    for x, y, r, ph in BOKEH:
        yy = (y - t * 25 * (r / 20)) % H
        a = 0.35 + 0.25 * math.sin(t * 1.5 + ph)
        c = tuple(int(v * a) for v in col)
        d.ellipse([(x - r) / 4, (yy - r) / 4, (x + r) / 4, (yy + r) / 4], fill=c)
    im = im.filter(ImageFilter.GaussianBlur(2)).resize((W, H), Image.BILINEAR)
    return np.array(im, np.float32)

def glow(arr, radius, half=4, gain=1.0):
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).resize((W // half, H // half), Image.BILINEAR)
    im = im.filter(ImageFilter.GaussianBlur(radius / half))
    return np.array(im.resize((W, H), Image.BILINEAR), np.float32) * gain

def splat(img, x, y, col, size=1):
    X = np.clip(x.astype(int), 1, W - 3); Y = np.clip(y.astype(int), 1, H - 3)
    idx = []; cc = []
    for dy in range(size):
        for dx in range(size):
            idx.append((Y + dy) * W + X + dx); cc.append(col)
    idx = np.concatenate(idx); cc = np.concatenate(cc)
    acc = np.stack([np.bincount(idx, weights=cc[:, c], minlength=W * H) for c in range(3)], 1).reshape(H, W, 3)
    return img + acc.astype(np.float32)

def heartbeat_scale(t, bpm=70):
    ph = (t * bpm / 60) % 1.0
    return 1 + 0.06 * math.exp(-ph * 12) + 0.035 * math.exp(-max(0, ph - 0.25) * 12) * (ph > 0.25)

def number_targets(text, n, cy, size):
    m = Image.new("L", (W, H)); d = ImageDraw.Draw(m)
    d.text((W / 2, cy), text, font=font(FB, size), fill=255, anchor="mm")
    ys, xs = np.where(np.array(m) > 128); i = rng.integers(0, len(xs), n)
    return xs[i].astype(np.float32), ys[i].astype(np.float32)

def hud_text(d, t):
    v = counter_value(t)
    d.text((W / 2, 250), f"{v:,}", font=font(FB, 170), fill=(255, 255, 255), anchor="mm", stroke_width=6, stroke_fill=(0, 0, 0))
    d.text((W / 2, 370), "HEARTBEATS TODAY", font=font(FBo, 52), fill=(255, 210, 220), anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0))

# ------------------------------------------------------------------ style A: 3D particles
def style_particles(t, wt, state):
    if "pts" not in state:
        P = np.concatenate([surface_points(9000, rng), volume_points(3000, rng) * 0.9])
        state["pts"] = P; state["ph"] = rng.uniform(0, 1, len(P))
        tx, ty = number_targets("100,000", len(P), H * 0.42, 250)
        state["tx"], state["ty"] = tx, ty
    P = state["pts"]
    img = bg_space(t, (16, 8, 36)) + bokeh_layer(t, (90, 40, 160))
    s = heartbeat_scale(t)
    Rm = rot(0.55 * math.sin(t * 0.9), 0.2 + 0.08 * math.sin(t * 0.7))
    Q = (P * s) @ Rm.T
    x, y, k = project(Q, W, H, 330, cy=H * 0.45)
    # morph into number between 4.4s and 5.4s, back to heart at the end
    m = np.clip((t - 4.4) / 0.9, 0, 1); m = m * m * (3 - 2 * m)
    m *= 1 - np.clip((t - 6.3) / 0.6, 0, 1)
    delay = state["ph"] * 0.5
    mm = np.clip(m * 1.5 - delay, 0, 1)
    x = x * (1 - mm) + state["tx"] * mm; y = y * (1 - mm) + state["ty"] * mm
    depth = (Q[:, 1] + 1.5) / 3  # 0 front .. 1 back
    c1 = np.array([0, 230, 255]); c2 = np.array([140, 90, 255]); c3 = np.array([255, 70, 170])
    tt = np.clip((P[:, 2] + 1.2) / 2.6, 0, 1)[:, None]
    col = np.where(tt < .5, c3 + (c2 - c3) * tt * 2, c2 + (c1 - c2) * (tt - .5) * 2)
    bright = (1.25 - depth * 0.8)[:, None]
    tw = 0.7 + 0.3 * np.sin(t * 6 + state["ph"] * 30)[:, None]
    layer = np.zeros((H, W, 3), np.float32)
    layer = splat(layer, x, y, col * bright * tw * 1.6, 2)
    img = img + layer + glow(layer, 18, gain=2.2)
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    if t < 4.3: hud_text(d, t)
    ca = float(np.clip((t - 5.0) / 0.4, 0, 1) * (1 - np.clip((t - 6.2) / 0.3, 0, 1)))
    if ca > 0:
        v = int(255 * ca)
        d.text((W / 2, H * 0.42), "100,000", font=font(FB, 240), fill=(v, v, v), anchor="mm", stroke_width=6, stroke_fill=(0, 0, 0))
        d.text((W / 2, H * 0.42 + 190), "BEATS EVERY DAY", font=font(FBo, 56), fill=(v, int(v * .85), int(v * .9)), anchor="mm")
    draw_caption(d, t, wt, H * 0.78)
    return im

# ------------------------------------------------------------------ style B: 3D cutaway
LABELS = [("Left ventricle", (0.30, -0.25), (1.0, 0.0)), ("Right ventricle", (-0.30, -0.2), (-1.0, 0.0)),
          ("Left atrium", (0.32, 0.42), (1.0, 0.6)), ("Right atrium", (-0.32, 0.44), (-1.0, 0.6))]
def style_cutaway(t, wt, state, fi):
    if fi % 2 == 0 or "last" not in state:
        rw, rh = 360, 640
        cut = -2.0 + 2.15 * np.clip((t - 2.2) / 1.6, 0, 1) ** 1.5
        ang = 0.35 * math.sin(t * 0.5) if t < 2.2 else 0.35 * math.sin(2.2 * 0.5) * (1 - np.clip((t - 2.2) / 1.6, 0, 1))
        img, hit, face = raymarch_cut(rw, rh, rot(ang, 0.12), cut, 112 * heartbeat_scale(t) ** 0.5)
        a = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).resize((W, H), Image.LANCZOS)
        mk = Image.fromarray((hit * 255).astype(np.uint8)).resize((W, H), Image.BILINEAR)
        state["last"] = (np.array(a, np.float32), np.array(mk, np.float32)[..., None] / 255, cut)
    obj, mk, cut = state["last"]
    yy = np.linspace(0, 1, H)[:, None, None]; xx = np.linspace(-1, 1, W)[None, :, None]
    bg = (np.array([40, 10, 18]) * (1 - (xx ** 2 + (yy - 0.45) ** 2 * 2))).clip(0) + 6
    bg = np.broadcast_to(bg, (H, W, 3)).astype(np.float32) + bokeh_layer(t, (120, 30, 40)) * 0.6
    halo = glow(obj * mk, 60, gain=0.9) * np.array([1.0, 0.35, 0.4])
    img = bg * (1 - mk) + obj * mk + halo
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    if t < 3.4: hud_text(d, t)
    # labels after the cut opens
    la = np.clip((t - 4.0) / 0.4, 0, 1)
    if la > 0:
        scale = 112 * 3; cx, cy = W / 2, H / 2
        for i, (name, (px, pz), (dx, dz)) in enumerate(LABELS):
            a2 = np.clip(la * 2 - i * 0.25, 0, 1)
            if a2 <= 0: continue
            sx, sy = cx + px * scale / 1.0 * (4 / 4.0) * 0.98, cy - pz * scale * 0.98
            ex = sx + dx * 150; ey = sy - dz * 110 - 30
            colr = (int(255 * a2), int(255 * a2), int(255 * a2))
            d.ellipse([sx - 9, sy - 9, sx + 9, sy + 9], outline=colr, width=4)
            d.line([(sx, sy), (ex, ey)], fill=colr, width=4)
            d.text((ex + (12 if dx > 0 else -12), ey), name, font=font(FBo, 46), fill=colr, anchor="lm" if dx > 0 else "rm", stroke_width=4, stroke_fill=(0, 0, 0))
        d.text((W / 2, 300), "4 CHAMBERS", font=font(FB, 110), fill=(255, 255, 255), anchor="mm", stroke_width=6, stroke_fill=(0, 0, 0))
    draw_caption(d, t, wt, H * 0.80)
    return im

# ------------------------------------------------------------------ style C: hologram scanner
def heart_grid():
    lines = []
    for z in np.linspace(-1.05, 1.25, 16):  # horizontal contours
        th = np.linspace(0, 2 * np.pi, 140)
        d = np.stack([np.cos(th), np.sin(th) / 1.5, np.full_like(th, 0)], 1)
        pts = []
        for dd in d:
            lo, hi = 0, 2
            for _ in range(25):
                m = (lo + hi) / 2
                if f_heart(dd[0] * m, dd[1] * m, z) < 0: lo = m
                else: hi = m
            pts.append((dd[0] * lo, dd[1] * lo, z) if lo > 0.01 else None)
        lines.append(pts)
    for phi in np.linspace(0, 2 * np.pi, 18, endpoint=False):  # vertical meridians
        th = np.linspace(-1.5, 1.5, 120)
        dirs = np.stack([np.cos(th) * np.cos(phi), np.cos(th) * np.sin(phi), np.sin(th)], 1)
        lo = np.zeros(len(dirs)); hi = np.full(len(dirs), 2.0)
        for _ in range(25):
            m = (lo + hi) / 2; p = dirs * m[:, None]
            ins = f_heart(p[:, 0], p[:, 1], p[:, 2]) < 0
            lo = np.where(ins, m, lo); hi = np.where(ins, hi, m)
        lines.append([tuple(p) for p in dirs * lo[:, None]])
    return lines

def style_scanner(t, wt, state):
    if "grid" not in state: state["grid"] = heart_grid()
    img = np.zeros((H, W, 3), np.float32) + np.array([2, 10, 16])
    lay = Image.new("RGB", (W, H)); d = ImageDraw.Draw(lay)
    # background grid
    for gx in range(0, W, 60): d.line([(gx, 0), (gx, H)], fill=(0, 30, 40), width=1)
    for gy in range(0, H, 60): d.line([(0, gy), (W, gy)], fill=(0, 30, 40), width=1)
    s = heartbeat_scale(t) * 330; Rm = rot(0.6 * math.sin(t * 0.8), 0.18)
    scan_z = 1.3 - ((t * 0.45) % 1.0) * 2.6
    for line in state["grid"]:
        P = np.array([p if p is not None else (np.nan,) * 3 for p in line], float)
        Q = P @ Rm.T
        x, y, k = project(Q, W, H, s, cy=H * 0.47)
        near = np.abs(P[:, 2] - scan_z) < 0.07
        for i in range(len(P) - 1):
            if np.isnan(x[i]) or np.isnan(x[i + 1]): continue
            front = Q[i, 1] < 0
            c = (255, 255, 255) if near[i] else ((0, 220, 255) if front else (0, 90, 120))
            d.line([(x[i], y[i]), (x[i + 1], y[i + 1])], fill=c, width=3 if near[i] else 2)
    # scan plane
    sy = H * 0.47 - scan_z * s
    d.line([(80, sy), (W - 80, sy)], fill=(120, 255, 255), width=3)
    arr = np.array(lay, np.float32)
    img = img + arr + glow(arr, 22, gain=1.6)
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
    # HUD brackets
    for (x0, y0, sx, sy2) in [(70, 520, 1, 1), (W - 70, 520, -1, 1), (70, 1380, 1, -1), (W - 70, 1380, -1, -1)]:
        d.line([(x0, y0), (x0 + 90 * sx, y0)], fill=(0, 220, 255), width=5); d.line([(x0, y0), (x0, y0 + 90 * sy2)], fill=(0, 220, 255), width=5)
    blink = int(t * 2) % 2 == 0
    d.text((90, 470), "● SCANNING: HEART" if blink else "  SCANNING: HEART", font=font(FBo, 40), fill=(0, 230, 255), anchor="lm")
    d.text((W - 90, 470), f"BPM 70", font=font(FBo, 40), fill=(255, 90, 120), anchor="rm")
    hud_text(d, t)
    # ECG line
    xs = np.arange(80, W - 80, 4); base = 1500
    def ecg(u):
        ph = u % 1.0
        return (-140 * math.exp(-((ph - 0.3) / 0.012) ** 2) + 40 * math.exp(-((ph - 0.33) / 0.015) ** 2)
                - 18 * math.exp(-((ph - 0.12) / 0.03) ** 2) - 30 * math.exp(-((ph - 0.55) / 0.05) ** 2))
    pts = [(x, base + ecg((x - 80) / 420 - t * 70 / 60)) for x in xs]
    d.line(pts, fill=(80, 255, 140), width=4)
    draw_caption(d, t, wt, H * 0.70)
    return im

def make(name, fn, out, v0, v1):
    wt = words_timing(v0, v1); state = {}
    path = os.path.join(out, f"silent_{name}.mp4")
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", path], stdin=subprocess.PIPE)
    for fi in range(int(DUR * FPS)):
        t = fi / FPS
        im = fn(t, wt, state, fi) if fn is style_cutaway else fn(t, wt, state)
        # watermark
        dd = ImageDraw.Draw(im); dd.text((W / 2, H - 120), "INNER NUMBERS", font=font(FBo, 34), fill=(200, 200, 220), anchor="mm")
        ff.stdin.write(im.tobytes())
    ff.stdin.close(); ff.wait()
    final = os.path.join(out, f"estilo_{name}.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", path, "-i", os.path.join(out, "voice.wav"), "-i", os.path.join(out, "music.wav"),
                    "-filter_complex", "[1:a]aresample=44100[v];[v][2:a]amix=inputs=2:duration=longest:normalize=0,loudnorm=I=-14:TP=-1.5[a]",
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-t", str(DUR), final], check=True)
    os.remove(path); print("DONE", final, flush=True)

if __name__ == "__main__":
    out = sys.argv[1]; which = sys.argv[2:] or ["A", "B", "C"]
    os.makedirs(out, exist_ok=True)
    v0, v1 = voice(out); R.make_music(DUR + 0.5, out, heartbeat=True, seed=5)
    if "A" in which: make("A_particulas3D", style_particles, out, v0, v1)
    if "C" in which: make("C_escaner", style_scanner, out, v0, v1)
    if "B" in which: make("B_corte3D", style_cutaway, out, v0, v1)
