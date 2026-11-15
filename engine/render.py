"""Inner Numbers - video engine.
Usage: python3 engine/render.py episodes/ep001.json out/ep001 [--format short|long]
Builds voice (Kokoro, local), particle + cross-section animation, captions, music, and muxes an MP4.
"""
import json, math, os, subprocess, sys, argparse
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_BLACK = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
FONT_BOLD = "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf"
FONT_MED = "/usr/share/fonts/opentype/inter/InterDisplay-Medium.otf"
FPS = 30
SR = 24000
GAP = 0.28  # silence between scenes (s)

PALETTES = {
    "aurora": [(0, 229, 255), (124, 92, 255), (255, 64, 160)],
    "ember": [(255, 196, 0), (255, 98, 40), (220, 20, 80)],
    "lime": [(180, 255, 60), (0, 220, 160), (0, 150, 255)],
    "ice": [(220, 245, 255), (90, 180, 255), (40, 80, 255)],
    "blood": [(255, 120, 120), (230, 30, 60), (140, 0, 60)],
}

# ---------------------------------------------------------------- voice
def make_voice(ep, outdir):
    import soundfile as sf
    from kokoro_onnx import Kokoro
    k = Kokoro(os.path.join(ROOT, "models/kokoro-v1.0.onnx"), os.path.join(ROOT, "models/voices-v1.0.bin"))
    voice = ep.get("voice", "am_michael"); speed = ep.get("speed", 1.05)
    chunks, timings, t = [], [], 0.0
    gap = np.zeros(int(SR * GAP), dtype=np.float32)
    for sc in ep["scenes"]:
        s, sr = k.create(sc["say"], voice=voice, speed=speed, lang="en-us")
        s = s.astype(np.float32)
        # trim leading/trailing near-silence
        idx = np.where(np.abs(s) > 0.01)[0]
        if len(idx): s = s[max(0, idx[0] - 600): idx[-1] + 2400]
        d = len(s) / SR
        timings.append((t, t + d)); chunks += [s, gap]; t += d + GAP
    audio = np.concatenate(chunks)
    audio = audio / max(1e-6, np.abs(audio).max()) * 0.92
    sf.write(os.path.join(outdir, "voice.wav"), audio, SR)
    return timings, len(audio) / SR

def make_music(duration, outdir, heartbeat=False, seed=1):
    import soundfile as sf
    rng = np.random.default_rng(seed)
    sr = 44100; n = int(sr * duration); t = np.arange(n) / sr
    root = rng.choice([110.0, 123.47, 98.0, 130.81])
    chord = [1, 1.5, 2, 2.5198] if rng.random() < .5 else [1, 1.4983, 2, 2.3784]
    pad = np.zeros(n)
    for i, r in enumerate(chord):
        f = root * r
        lfo = 0.6 + 0.4 * np.sin(2 * np.pi * (0.05 + 0.03 * i) * t + i)
        pad += lfo * (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * f * 2.003 * t))
    pad /= np.abs(pad).max()
    fade = np.minimum(1, np.minimum(t / 2.0, (duration - t) / 2.0))
    out = pad * fade * 0.10
    if heartbeat:  # soft lub-dub at 70 bpm
        beat = 60 / 70
        for start in np.arange(0.4, duration - 0.5, beat):
            for off, amp in ((0, 1.0), (0.22, 0.7)):
                i0 = int((start + off) * sr); L = int(0.12 * sr)
                if i0 + L >= n: continue
                tt = np.arange(L) / sr
                out[i0:i0 + L] += amp * 0.22 * np.sin(2 * np.pi * 55 * tt) * np.exp(-tt * 30)
    sf.write(os.path.join(outdir, "music.wav"), np.stack([out, out], 1).astype(np.float32), sr)

# ---------------------------------------------------------------- targets
def text_mask(W, H, text, cx, cy, maxw, size):
    size = int(size)
    while True:
        f = ImageFont.truetype(FONT_BLACK, size)
        bb = f.getbbox(text)
        if bb[2] - bb[0] <= maxw or size < 40: break
        size = int(size * 0.92)
    m = Image.new("L", (W, H), 0); d = ImageDraw.Draw(m)
    d.text((cx, cy), text, font=f, fill=255, anchor="mm")
    m.font = f
    return m

def heart_mask(W, H, cx, cy, s):
    ys, xs = np.mgrid[0:H, 0:W]
    x = (xs - cx) / s; y = -(ys - cy) / s
    return Image.fromarray((((x * x + y * y - 1) ** 3 - x * x * y ** 3) <= 0).astype(np.uint8) * 255)

def sample(mask, n, rng, edge=False):
    a = np.array(mask)
    if edge:
        e = np.array(mask.filter(ImageFilter.FIND_EDGES))
        a = e
    ys, xs = np.where(a > 128)
    if len(xs) == 0: return None
    i = rng.integers(0, len(xs), n)
    return np.stack([xs[i] + rng.uniform(-.5, .5, n), ys[i] + rng.uniform(-.5, .5, n)], 1).astype(np.float32)

# ---------------------------------------------------------------- scenes
class Scene:
    def __init__(self, spec, t0, t1, W, H, N, rng):
        self.s, self.t0, self.t1, self.W, self.H, self.N, self.rng = spec, t0, t1, W, H, N, rng
        v = spec["visual"]; self.kind = v["type"]; self.v = v
        cx, cy = W / 2, H * (0.40 if H > W else 0.45)
        self.cx, self.cy = cx, cy
        unit = min(W, H)
        if self.kind == "number":
            m = text_mask(W, H, v["value"], cx, cy, W * 0.86, unit * 0.30)
            self.target = sample(m, N, rng); self.numfont = ImageFont.truetype(FONT_BLACK, max(40, int(m.font.size * 0.96)))
        elif self.kind == "heart":
            self.target = sample(heart_mask(W, H, cx, cy + unit * 0.02, unit * 0.30), N, rng)
        elif self.kind in ("layers", "flow", "end"):
            self.target = None
        self.layer_r = unit * 0.36

    def targets(self, t, base):
        k = self.kind; N = self.N
        if self.target is not None:
            if k == "heart":
                ph = ((t - self.t0) * 70 / 60) % 1.0
                beat = np.exp(-ph * 14) + 0.6 * np.exp(-max(0, ph - 0.22) * 14) * (ph > 0.22)
                c = np.array([self.cx, self.cy]); return c + (self.target - c) * (1 + 0.07 * beat)
            return self.target
        if k == "layers":
            L = self.v["layers"]; n = len(L)
            prog = np.clip((t - self.t0) / max(0.1, (self.t1 - self.t0) * 0.85), 0, 1)
            zoom = 1 + 0.35 * prog
            ring = (np.arange(N) % n)
            ang = base[:, 0] * 2 * np.pi + (t - self.t0) * 0.15 * (1 + ring * 0.2)
            r = self.layer_r * zoom * (1 - ring / n) * (0.995 + 0.01 * base[:, 1])
            return np.stack([self.cx + r * np.cos(ang), self.cy + r * np.sin(ang)], 1)
        if k == "flow":
            u = (base[:, 0] + (t - self.t0) * 0.18) % 1.0
            y = self.H * (1.05 - 1.1 * u)
            x = self.cx + np.sin(u * 2 * np.pi * 1.5 + 0.8) * self.W * 0.18
            off = (base[:, 1] - .5) * self.W * 0.16
            return np.stack([x + off, y], 1)
        if k == "end":
            if not hasattr(self, "_h"):
                self._h = sample(heart_mask(self.W, self.H, self.cx, self.cy - min(self.W, self.H) * 0.05, min(self.W, self.H) * 0.20), N, self.rng)
            return self._h
        return None

# ---------------------------------------------------------------- captions
def caption_chunks(scenes):
    out = []
    for sc in scenes:
        words = sc.s["say"].split(); t0, t1 = sc.t0, sc.t1
        groups, cur = [], []
        for w in words:
            cur.append(w)
            if len(cur) >= 3 or w[-1] in ".,?!": groups.append(cur); cur = []
        if cur: groups.append(cur)
        total = sum(len(" ".join(g)) + 4 for g in groups); t = t0
        for g in groups:
            d = (t1 - t0) * (len(" ".join(g)) + 4) / total
            out.append((t, t + d, " ".join(g))); t += d
    return out

def splat(idx, col, n):
    return np.stack([np.bincount(idx, weights=col[:, c], minlength=n) for c in range(3)], 1).astype(np.float32)

# ---------------------------------------------------------------- render
def render(ep, outdir, fmt):
    os.makedirs(outdir, exist_ok=True)
    W, H = (1080, 1920) if fmt == "short" else (1920, 1080)
    rng = np.random.default_rng(ep.get("seed", 1))
    pal = [np.array(c, np.float32) for c in PALETTES[ep.get("palette", "aurora")]]
    timings, dur = make_voice(ep, outdir)
    make_music(dur + 0.6, outdir, heartbeat=ep.get("heartbeat", False), seed=ep.get("seed", 1))
    N = 5000 if fmt == "short" else 5500
    scenes = [Scene(sc, a, b + GAP, W, H, N, rng) for sc, (a, b) in zip(ep["scenes"], timings)]
    caps = caption_chunks(scenes)

    # background
    yy = np.linspace(0, 1, H)[:, None, None]
    bg = (np.array([6, 10, 24]) * (1 - yy) + np.array([14, 8, 34]) * yy) * np.ones((1, W, 1))
    vign = (1 - 0.55 * (((np.linspace(-1, 1, W)[None, :]) ** 2 + (np.linspace(-1, 1, H)[:, None]) ** 2) / 2))[..., None]
    bg = (bg * vign).astype(np.float32)

    pos = np.stack([rng.uniform(0, W, N), rng.uniform(0, H, N)], 1).astype(np.float32)
    vel = np.zeros_like(pos)
    base = rng.uniform(0, 1, (N, 2)).astype(np.float32)
    size = rng.choice([1, 1, 1, 2], N)
    stars = np.stack([rng.uniform(0, W, 400), rng.uniform(0, H, 400)], 1)

    fcap = ImageFont.truetype(FONT_BLACK, 78 if fmt == "short" else 64)
    flab = ImageFont.truetype(FONT_BOLD, 54 if fmt == "short" else 48)
    fsmall = ImageFont.truetype(FONT_MED, 40 if fmt == "short" else 34)
    total_frames = int((dur + 0.5) * FPS)
    tmpvid = os.path.join(outdir, "silent.mp4")
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                           "-pix_fmt", "yuv420p", tmpvid], stdin=subprocess.PIPE)
    hw, hh = W // 2, H // 2
    for fi in range(total_frames):
        t = fi / FPS
        sc = next((s for s in scenes if s.t0 <= t < s.t1), scenes[-1])
        tg = sc.targets(t, base)
        # spring physics toward target, staggered by base[:,0]
        local = t - sc.t0
        act = np.clip((local * 2.2 - base[:, 0] * 0.6), 0, 1)[:, None]
        if tg is not None:
            force = (tg - pos) * 0.10 * act
            vel = vel * 0.78 + force
        noise = (np.stack([np.sin(t * 1.3 + base[:, 1] * 40), np.cos(t * 1.1 + base[:, 0] * 40)], 1)) * 0.6
        pos = pos + vel + noise
        # colours by vertical position
        ty = np.clip(0.55 * pos[:, 1] / H + 0.45 * base[:, 1], 0, 1)[:, None]
        col = np.where(ty < .5, pal[0] + (pal[1] - pal[0]) * ty * 2, pal[1] + (pal[2] - pal[1]) * (ty - .5) * 2)
        # glow buffer at half res
        xi = np.clip((pos[:, 0] / 2).astype(int), 0, hw - 1); yi = np.clip((pos[:, 1] / 2).astype(int), 0, hh - 1)
        g = splat(yi * hw + xi, col * 0.9, hh * hw).reshape(hh, hw, 3)
        gimg = Image.fromarray(np.clip(g, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(6))
        glow = np.array(gimg.resize((W, H), Image.BILINEAR), np.float32) * 3.0
        frame = bg + glow
        # sharp particles
        X = np.clip(pos[:, 0].astype(int), 1, W - 3); Y = np.clip(pos[:, 1].astype(int), 1, H - 3)
        big = size == 2
        idx = np.concatenate([(Y + dy) * W + X + dx for dy in (0, 1) for dx in (0, 1)] + [Y[big] * W + X[big] - 1, Y[big] * W + X[big] + 2])
        cc = np.concatenate([col * 1.5] * 4 + [col[big] * .6] * 2)
        frame = frame + splat(idx, cc, H * W).reshape(H, W, 3)
        tw = (0.5 + 0.5 * np.sin(t * 2 + np.arange(400)))
        frame[stars[:, 1].astype(int), stars[:, 0].astype(int)] += (60 * tw)[:, None]
        img = Image.fromarray(np.clip(frame, 0, 255).astype(np.uint8))
        d = ImageDraw.Draw(img)
        a = min(1, local * 3)
        # scene overlays
        if sc.kind == "number":
            ca = np.clip((local - 0.7) * 2.5, 0, 1)
            if ca > 0:
                m = sc.mask_img if hasattr(sc, "mask_img") else None
                fnum = sc.numfont
                d.text((sc.cx, sc.cy), sc.v["value"], font=fnum, fill=(int(255*ca), int(255*ca), int(255*ca)), anchor="mm", stroke_width=5, stroke_fill=(0,0,0))
        if sc.kind == "number" and sc.v.get("label"):
            d.text((sc.cx, sc.cy + min(W, H) * 0.22), sc.v["label"], font=flab, fill=(int(230 * a), int(235 * a), int(255 * a)), anchor="mm")
        if sc.kind == "layers":
            L = sc.v["layers"]; n = len(L)
            prog = np.clip(local / max(0.1, (sc.t1 - sc.t0) * 0.85), 0, 1); zoom = 1 + 0.35 * prog
            shown = int(prog * n * 1.05) + 1
            for i, name in enumerate(L[:shown]):
                r = sc.layer_r * zoom * (1 - i / n)
                c = tuple(int(v) for v in (pal[0] + (pal[2] - pal[0]) * (i / max(1, n - 1))))
                d.ellipse([sc.cx - r, sc.cy - r, sc.cx + r, sc.cy + r], outline=c, width=3)
            cur = min(shown, n) - 1
            ctext = f"LAYER {cur+1}: {L[cur].upper()}"
            ly = sc.cy - sc.layer_r * 1.75 if H > W else H * 0.08
            d.text((W / 2, ly), ctext, font=flab, fill=(255, 255, 255), anchor="mm", stroke_width=5, stroke_fill=(0, 0, 0))
            # scanning cut line
            sy = sc.cy - sc.layer_r * zoom + 2 * sc.layer_r * zoom * ((local * 0.5) % 1)
            d.line([(sc.cx - sc.layer_r * zoom * 1.1, sy), (sc.cx + sc.layer_r * zoom * 1.1, sy)], fill=(255, 255, 255), width=2)
        if sc.kind == "flow" and sc.v.get("value"):
            fbig = ImageFont.truetype(FONT_BLACK, int(min(W, H) * 0.17))
            d.text((sc.cx, sc.cy), sc.v["value"], font=fbig, fill=(255, 255, 255), anchor="mm", stroke_width=6, stroke_fill=(10, 10, 30))
            if sc.v.get("label"):
                d.text((sc.cx, sc.cy + min(W, H) * 0.14), sc.v["label"], font=flab, fill=(230, 235, 255), anchor="mm", stroke_width=4, stroke_fill=(10, 10, 30))
        if sc.kind == "end":
            d.text((sc.cx, sc.cy + min(W, H) * 0.25), "INNER NUMBERS", font=ImageFont.truetype(FONT_BLACK, 84), fill=(240, 245, 255), anchor="mm")
            d.text((sc.cx, sc.cy + min(W, H) * 0.25 + 80), "your body, counted", font=fsmall, fill=tuple(int(v) for v in pal[0]), anchor="mm")
        # captions
        cap = next((c for c in caps if c[0] <= t < c[1]), None)
        if cap:
            cy_ = H * 0.74 if H > W else H * 0.88
            txt = cap[2].upper()
            d.text((W / 2, cy_), txt, font=fcap, fill=(255, 255, 255), anchor="mm", stroke_width=8, stroke_fill=(0, 0, 0))
        ff.stdin.write(img.tobytes())
        if fi % 150 == 0: print(f"frame {fi}/{total_frames}", flush=True)
    ff.stdin.close(); ff.wait()
    final = os.path.join(outdir, f"{ep['id']}_{fmt}.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmpvid, "-i", os.path.join(outdir, "voice.wav"),
                    "-i", os.path.join(outdir, "music.wav"), "-filter_complex",
                    "[1:a]aresample=44100,volume=1.0[v];[2:a]volume=1.0[m];[v][m]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5[a]",
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", final], check=True)
    os.remove(tmpvid)
    print("DONE", final, round(dur, 1), "s")
    return final

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("episode"); ap.add_argument("outdir"); ap.add_argument("--format", default="short")
    a = ap.parse_args()
    render(json.load(open(a.episode)), a.outdir, a.format)
