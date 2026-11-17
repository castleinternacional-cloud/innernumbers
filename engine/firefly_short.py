"""Inner Numbers - Firefly Pointillism short (9:16). One conserved pool of soft light points:
skin block -> cells shed -> scatter -> bacteria colony -> "1,300,000,000" -> back to skin (seamless loop).
Rendering follows the Firefly Pointillism grammar: points on black, depth = blur (5 levels), halo,
1-exp(-x) tone map. Captions are crisp text for sound-off viewers.

python3 engine/firefly_short.py voice.wav timings.json out/firefly_skin.mp4
"""
import os, sys, json, math, subprocess
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
from heart3d import rot
import organs as O
import render as R

W, H, FPS = 1080, 1920, 30
DUR = 10.0
N = 16000
rng = np.random.default_rng(21)
FB, FBo = R.FONT_BLACK, R.FONT_BOLD
YEL = (255, 214, 0)

def ease(x): x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)

# ------------------------------------------------------------------ shapes (each: N x [x, y, blur], N x rgb)
def sample_organ(name, n):
    o = O.get(name); idx = rng.integers(0, len(o.P), n)
    P = o.P[idx] + rng.normal(0, 0.012, (n, 3))
    tt = np.clip((o.P[idx, 2] + 1.2) / 2.6, 0, 1)[:, None]
    p0, p1, p2 = [np.array(c, float) for c in o.pal]
    col = np.where(tt < .5, p0 + (p1 - p0) * tt * 2, p1 + (p2 - p1) * (tt - .5) * 2)
    return P, col, o

SKIN_P, SKIN_C, SKIN_O = sample_organ("skin", N)
SKIN_C = SKIN_C * 0.75 + np.array([255, 190, 120.]) * 0.25          # warm the skin points (firefly: warm)
BAC_P, BAC_C, BAC_O = sample_organ("bacteria", N)
BAC_C = BAC_C * 0.55 + np.array([190, 255, 140.]) * 0.45              # warm-ish green
TOP = SKIN_P[:, 2] > 0.9                                               # surface + hair points: these shed
SHED = TOP & (rng.random(N) < 0.55)
PH = rng.random(N)                                                     # per-point phase (stagger, twinkle)

def project(P, t, scale, cx, cy, yaw0=0.0, tilt=0.25, spin=1.0):
    ang = yaw0 + 2 * math.pi * t / DUR * spin                          # one full turn per loop = seamless
    Q = P @ rot(ang, tilt).T
    s = scale * 4.0 / (4.0 + Q[:, 1])
    x = cx + Q[:, 0] * s; y = cy - Q[:, 2] * s
    blur = np.clip(0.15 + (Q[:, 1] + 1.0) * 0.55, 0, 1.6)              # far side slightly softer
    return x, y, blur

def text_points(txt, n, cy, size):
    im = Image.new("L", (W, 400)); d = ImageDraw.Draw(im)
    f = ImageFont.truetype(FB, size)
    while d.textlength(txt, font=f) > W * 0.92: size -= 6; f = ImageFont.truetype(FB, size)
    d.text((W / 2, 200), txt, font=f, fill=255, anchor="mm")
    a = np.array(im) > 128
    ys, xs = np.nonzero(a)
    k = rng.integers(0, len(xs), n)
    return xs[k] + rng.uniform(-0.6, 0.6, n), ys[k] - 200 + cy + rng.uniform(-0.6, 0.6, n)

NUM_X, NUM_Y = text_points("1,300,000,000", N, H * 0.43, 170)
NUM_C = np.tile(np.array([255, 205, 70.]), (N, 1)) * (0.85 + 0.3 * rng.random((N, 1)))

# scatter cloud (out of focus, drifting): positions on a wide disc
SC_X = W / 2 + rng.normal(0, W * 0.42, N); SC_Y = H * 0.45 + rng.normal(0, H * 0.26, N)

def curl(t, amp):
    return (amp * np.sin(t * 1.3 + PH * 40), amp * np.cos(t * 1.1 + PH * 31))

# ------------------------------------------------------------------ timeline
# 0.0-2.4 skin (cells shed from top from 0.5)   2.4-3.2 burst/scatter   3.2-5.4 bacteria
# 5.4-6.2 regroup      6.2-8.4 number         8.4-10.0 back to skin (== frame 0)
def lerp(a, b, k): return a + (b - a) * k

def stagger(t0, t1, t):
    """per-point eased progress with stagger -> points arrive at different times (flock feel)."""
    span = t1 - t0
    return ease((t - t0 - PH * span * 0.45) / (span * 0.55))

def state(t):
    sx, sy, sb = project(SKIN_P, t, 330, W / 2, H * 0.47)
    # shedding: top points lift off and fall/drift as soft bokeh, then rejoin before 2.4? no - they stay off
    shed_k = ease((t - 1.8 - PH * 0.9) / 0.8) * SHED
    sx = sx + shed_k * (np.sin(PH * 50) * 260 + max(t - 1.8, 0) * 30 * np.cos(PH * 9))
    sy = sy + shed_k * (-120 + max(t - 1.8, 0) * 260 * (0.4 + PH))
    sb = sb + shed_k * 1.6
    skin = (sx, sy, sb, SKIN_C)

    bx, by, bb = project(BAC_P, t, 380, W / 2, H * 0.45, tilt=0.35, spin=-1.0)
    cx, cy = curl(t, 6)
    bac = (bx + cx, by + cy, bb, BAC_C)

    nb = np.full(N, 0.05) + 0.12 * (0.5 + 0.5 * np.sin(t * 6 + PH * 30))   # number twinkles
    num = (NUM_X + np.sin(t * 2 + PH * 20) * 1.5, NUM_Y + np.cos(t * 2 + PH * 17) * 1.5, nb, NUM_C)

    scx, scy = curl(t, 40)
    sc = (SC_X + scx, SC_Y + scy, np.full(N, 1.9), lerp(SKIN_C, BAC_C, 0.5) * 0.32)

    def mix(A, B, k):
        k = np.asarray(k, float)
        out = []
        for a, b in zip(A, B):
            a = np.asarray(a, float); b = np.asarray(b, float)
            out.append(lerp(a, b, k[:, None] if a.ndim == 2 else k))
        # mid-transition points defocus (focus pull = how forms appear)
        out[2] = out[2] + 0.9 * np.sin(np.pi * k)
        return tuple(out)

    if t < 3.0: return skin
    if t < 3.7: return mix(skin, sc, stagger(3.0, 3.7, t))
    if t < 4.6: return mix(sc, bac, stagger(3.7, 4.6, t))
    if t < 5.3: return bac
    if t < 5.9: return mix(bac, sc, stagger(5.3, 5.9, t))
    if t < 6.6: return mix(sc, num, stagger(5.9, 6.6, t))
    if t < 8.1: return num
    # back to skin; frame at t=10 matches frame 0 (spin period = DUR, no shedding yet)
    skin0 = list(project(SKIN_P, t, 330, W / 2, H * 0.47)) + [SKIN_C]
    return mix(num, tuple(skin0), stagger(8.1, 9.85, t))

# ------------------------------------------------------------------ firefly renderer
SIG = [1.0, 2.1, 4.8, 10.5, 23.0]; RES = [1, 1, 2, 4, 8]; GAIN = [1, 1.55, 2.7, 5.2, 10]

def splat_level(x, y, w, col, res):
    ww, hh = W // res, H // res
    X = (x / res).astype(int); Y = (y / res).astype(int)
    m = (X >= 0) & (X < ww) & (Y >= 0) & (Y < hh) & (w > 1e-4)
    if not m.any(): return np.zeros((hh, ww, 3), np.float32)
    idx = Y[m] * ww + X[m]; c = col[m] * w[m, None]
    acc = np.stack([np.bincount(idx, weights=c[:, k], minlength=ww * hh) for k in range(3)], 1)
    return acc.reshape(hh, ww, 3).astype(np.float32)

def blur_img(a, sigma):
    return cv2.GaussianBlur(a, (0, 0), sigmaX=max(sigma, 0.3), borderType=cv2.BORDER_CONSTANT)

def up(a):
    return cv2.resize(a, (W, H), interpolation=cv2.INTER_LINEAR)

NBG = 70
BG_X = rng.uniform(0, W, NBG); BG_Y = rng.uniform(0, H, NBG); BG_PH = rng.random(NBG)

def render(t):
    x, y, b, col = state(t)
    b = np.clip(b, 0, 4)
    col = col / 255.0
    tw = 0.8 + 0.2 * np.sin(t * 3 + PH * 60)                            # breathing
    out = np.zeros((H, W, 3), np.float32)
    lv = np.floor(b).astype(int); fr = b - lv
    for L in range(5):
        w = np.where(lv == L, 1 - fr, 0) + np.where(lv + 1 == L, fr, 0)
        w = w * 0.84 + (np.where(lv + 2 == L, 0.16, 0) if L >= 2 else 0)   # halo: 16 % two levels up
        if L == 4: w = w + np.where(lv >= 4, 1.0, 0)
        res = RES[L]
        acc = splat_level(x, y, w * tw, col, res) * (GAIN[L] / res ** 2) * 1.15
        acc = blur_img(acc, SIG[L] / res)
        if res > 1: acc = up(acc)
        out += acc
    # distant ambient fireflies (very faint, large) - still points, still conserved visually
    bga = 0.5 + 0.5 * np.sin(t * 2 * math.pi / DUR * 3 + BG_PH * 6.28)
    bg = splat_level(BG_X, BG_Y, bga * 0.35, np.tile([1.0, 0.75, 0.45], (NBG, 1)), 8)
    bg = blur_img(bg, 2.5)
    out += up(bg) * 0.9
    img = 1 - np.exp(-out * 2.2)
    img = np.clip(img, 0, 1) ** (1 / 2.2)
    return Image.fromarray((img * 255).astype(np.uint8))

# ------------------------------------------------------------------ captions (sound-off), word by word
def captions(d, t, words):
    cur = [w for w in words if w["t0"] <= t < w["t1"] + 0.15]
    if not cur: return
    # show the current phrase chunk (up to 3 words) with the active word highlighted
    w = cur[-1]; grp = [x for x in words if x["g"] == w["g"]]
    f = ImageFont.truetype(FB, 86)
    txt = [x["w"].upper() for x in grp]
    widths = [d.textlength(s, font=f) for s in txt]; gap = 24
    total = sum(widths) + gap * (len(txt) - 1); xx = W / 2 - total / 2
    y = H * 0.765
    for x, s, wd in zip(grp, txt, widths):
        on = x["t0"] <= t
        if not on: xx += wd + gap; continue
        num = any(ch.isdigit() for ch in s) or s.strip(".,?!") in ("BILLION",)
        fill = YEL if num else (255, 255, 255)
        d.text((xx, y), s, font=f, fill=fill, stroke_width=8, stroke_fill=(0, 0, 0), anchor="lm")
        xx += wd + gap

def main(voice, timings, out):
    words = json.load(open(timings))
    tmp = out + ".silent.mp4"
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    n = int(DUR * FPS)
    for fi in range(n):
        t = fi / FPS
        im = render(t); d = ImageDraw.Draw(im)
        captions(d, t, words)
        d.text((W / 2, 150), "INNER NUMBERS", font=ImageFont.truetype(FBo, 30), fill=(150, 140, 120), anchor="mm")
        ff.stdin.write(im.tobytes())
        if fi % 30 == 0: print("frame", fi, n, flush=True)
    ff.stdin.close(); ff.wait()
    music = out + ".music.wav"
    R.make_music(DUR, os.path.dirname(out) or ".", heartbeat=False, seed=12)
    os.replace(os.path.join(os.path.dirname(out) or ".", "music.wav"), music)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-i", voice, "-i", music,
                    "-filter_complex", "[1:a]aresample=44100,apad[v];[2:a]volume=0.8[m];[v][m]amix=inputs=2:duration=shortest:normalize=0,atrim=0:%.2f,loudnorm=I=-14:TP=-1.5[a]" % DUR,
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-t", str(DUR), "-movflags", "+faststart", out], check=True)
    os.remove(tmp); os.remove(music); print("DONE", out)

if __name__ == "__main__":
    if sys.argv[1] == "--still":
        render(float(sys.argv[2])).save(sys.argv[3])
    else:
        main(sys.argv[1], sys.argv[2], sys.argv[3])
