"""Inner Numbers long-form v2 (16:9) - builds on longform.py with more visual variety:
24h dial chapter cards, live tickers, bar comparisons, side-by-side organs, Earth-wrap, nerve pulse,
per-scene camera zoom, chapter progress bar, "since you pressed play" HUD, d4y captions (numbers in yellow).

  PYTHONHASHSEED=0 python3 engine/longday.py voice  episodes_long/one_day.json out/one_day
  PYTHONHASHSEED=0 python3 engine/longday.py render episodes_long/one_day.json out/one_day 0 2   (part 0 of 2)
  PYTHONHASHSEED=0 python3 engine/longday.py mux    episodes_long/one_day.json out/one_day 2
  python3 engine/longday.py frame episodes_long/one_day.json out/one_day 12.5 out/f.png   (one still)
PYTHONHASHSEED=0 keeps organ shapes identical across parallel parts.
"""
import os, sys, json, math, subprocess
import numpy as np
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.dirname(__file__))
import longform as L
import render as R
from heart3d import rot

W, H, FPS = L.W, L.H, L.FPS
font, ease, fade_col = L.font, L.ease, L.fade_col
FB, FBo, FM, SERIF_IT = L.FB, L.FBo, L.FM, L.SERIF_IT
YELLOW, WHITE, SOFT = L.YELLOW, L.WHITE, L.SOFT

def base(t, organ, scale, cx, cy, dim=1.0, extra=()):
    x, y, c = L.organ_pts(organ, t, scale, cx, cy, dim=dim)
    dx, dy, dc = L.dust(t)
    return L.compose(t, [(dx, dy, dc, 1), (x, y, c, 2)] + list(extra))

def fmt_num(v, dec=0):
    return f"{v:,.{dec}f}"

# ------------------------------------------------------------------ new scene types
def sc_dial(sc, t, lt):
    """Chapter card: 24h dial with sweeping arc, organ in the middle, chapter label on the left."""
    v = sc["visual"]; h1 = v["hour"]; h0 = v.get("from", max(0, h1 - 4))
    k = ease(lt / 1.6); h = h0 + (h1 - h0) * k
    cx, cy, R0 = W * 0.70, H * 0.47, 280
    im = base(t, v["organ"], 150, cx, cy)
    d = ImageDraw.Draw(im); a = ease(lt / 0.4)
    for i in range(24):
        ang = -math.pi / 2 + i / 24 * 2 * math.pi
        r1 = R0 - (26 if i % 6 == 0 else 12)
        d.line([(cx + R0 * math.cos(ang), cy + R0 * math.sin(ang)), (cx + r1 * math.cos(ang), cy + r1 * math.sin(ang))],
               fill=fade_col(SOFT, a), width=4 if i % 6 == 0 else 2)
    for i, lab in [(0, "00"), (6, "06"), (12, "12"), (18, "18")]:
        ang = -math.pi / 2 + i / 24 * 2 * math.pi
        d.text((cx + (R0 + 42) * math.cos(ang), cy + (R0 + 42) * math.sin(ang)), lab, font=font(FBo, 30), fill=fade_col(SOFT, a), anchor="mm")
    if h > 0.01:
        d.arc([cx - R0 - 14, cy - R0 - 14, cx + R0 + 14, cy + R0 + 14], -90, -90 + 360 * h / 24, fill=fade_col(YELLOW, a), width=10)
        ang = -math.pi / 2 + h / 24 * 2 * math.pi
        ex, ey = cx + (R0 + 14) * math.cos(ang), cy + (R0 + 14) * math.sin(ang)
        d.ellipse([ex - 14, ey - 14, ex + 14, ey + 14], fill=YELLOW)
    d.text((124, 300), v.get("kicker", ""), font=font(FBo, 38), fill=fade_col(YELLOW, a))
    d.text((110, 345), f"{int(h) % 24:02d}:{int((h % 1) * 60):02d}" if h1 < 24 or k < 1 else "24:00", font=font(FB, 210), fill=fade_col(WHITE, a))
    b = ease((lt - 0.8) / 0.5)
    d.text((126, 590), v.get("name", ""), font=font(SERIF_IT, 64), fill=fade_col((235, 228, 240), b))
    return im

def sc_ticker(sc, t, lt):
    """A live counter running at a real rate (per second)."""
    v = sc["visual"]
    im = base(t, v.get("organ", "rbc"), 300, W * 0.5, H * 0.56, dim=0.5)
    d = ImageDraw.Draw(im); a = ease(lt / 0.4)
    val = v["rate"] * t if v.get("global") else v.get("start", 0) + v["rate"] * lt
    if "cap" in v: val = min(val, v["cap"])
    d.text((W / 2, H * 0.40), fmt_num(val), font=font(FB, 190), fill=fade_col(YELLOW, a), anchor="mm", stroke_width=6, stroke_fill=(0, 0, 0))
    d.text((W / 2, H * 0.40 + 150), v.get("label", ""), font=font(SERIF_IT, 66), fill=fade_col(WHITE, a), anchor="mm")
    if v.get("note"): d.text((W / 2, H * 0.40 + 230), v["note"], font=font(FM, 36), fill=fade_col(SOFT, ease((lt - 1.0) / 0.5)), anchor="mm")
    return im

def sc_bars(sc, t, lt):
    """Horizontal bar comparison, bars grow one by one (linear scale on purpose)."""
    v = sc["visual"]
    im = base(t, v.get("organ", "rbc"), 170, W * 0.88, H * 0.80, dim=0.4)
    d = ImageDraw.Draw(im); a0 = ease(lt / 0.4)
    d.text((124, 120), v["title"], font=font(FB, 64), fill=fade_col(WHITE, a0))
    if v.get("sub"): d.text((128, 200), v["sub"], font=font(SERIF_IT, 44), fill=fade_col((225, 220, 240), a0))
    bars = v["bars"]; vmax = max(b[1] for b in bars)
    step = max(0.9, sc["_dur"] * 0.7 / len(bars)); x0, x1 = 560, 1700
    for i, (lab, val, txt) in enumerate(bars):
        k = ease((lt - 0.4 - i * step) / 0.9)
        y = 330 + i * 150
        d.text((x0 - 30, y + 30), lab, font=font(FBo, 40), fill=fade_col(WHITE, max(a0 * 0.4, min(1, k * 3))), anchor="rm")
        if k <= 0: continue
        wbar = max(6, (x1 - x0) * val / vmax * k)
        col = YELLOW if i == v.get("hi", -1) else (120, 170, 255)
        d.rounded_rectangle([x0, y, x0 + wbar, y + 62], radius=10, fill=col)
        if val / vmax < 0.75: d.text((x0 + wbar + 20, y + 31), txt, font=font(FB, 44), fill=YELLOW, anchor="lm")
        else: d.text((x0 + wbar - 20, y + 31), txt, font=font(FB, 44), fill=(15, 15, 25), anchor="rm")
    return im

def sc_duo(sc, t, lt):
    """Two organs side by side, a number under each."""
    v = sc["visual"]
    xl, yl, cl = L.organ_pts(v["left"]["organ"], t, v["left"].get("scale", 230), W * 0.28, H * 0.42, yaw=0.0)
    xr, yr, cr = L.organ_pts(v["right"]["organ"], t, v["right"].get("scale", 230), W * 0.72, H * 0.42, yaw=1.2)
    dx, dy, dc = L.dust(t)
    im = L.compose(t, [(dx, dy, dc, 1), (xl, yl, cl, 2), (xr, yr, cr, 2)]); d = ImageDraw.Draw(im)
    if v.get("title"): d.text((W / 2, 110), v["title"], font=font(FBo, 40), fill=fade_col(YELLOW, ease(lt / 0.4)), anchor="mm")
    for i, (side, cx) in enumerate([("left", W * 0.28), ("right", W * 0.72)]):
        a = ease((lt - 0.4 - i * 1.4) / 0.5)
        if a <= 0: continue
        d.text((cx, H * 0.76), v[side]["num"], font=font(FB, 130), fill=fade_col(YELLOW if i == 1 else WHITE, a), anchor="mm", stroke_width=4, stroke_fill=(0, 0, 0))
        d.text((cx, H * 0.76 + 95), v[side]["label"], font=font(SERIF_IT, 50), fill=fade_col((230, 225, 240), a), anchor="mm")
    return im

_rng = np.random.default_rng(3)
_EP = _rng.normal(size=(7000, 3)); _EP /= np.linalg.norm(_EP, axis=1, keepdims=True)
def sc_earth(sc, t, lt):
    """Particle Earth with a yellow line wrapping around it; mile counter."""
    v = sc["visual"]; k = ease((lt - 0.3) / max(1.0, sc["_dur"] * 0.8))
    cx, cy, Re = W * 0.66, H * 0.53, 300
    Rm = rot(t * 0.25, 0.35)
    Q = _EP @ Rm.T
    x = cx + Q[:, 0] * Re; y = cy - Q[:, 2] * Re
    front = (Q[:, 1] < 0.2)
    col = np.where(front[:, None], np.array([60, 140, 255.]), np.array([20, 50, 110.])) * (0.6 + 0.4 * np.abs(Q[:, 2:3]))
    dx, dy, dc = L.dust(t)
    im = L.compose(t, [(dx, dy, dc, 1), (x, y, col, 2)]); d = ImageDraw.Draw(im)
    laps = v["laps"] * k
    if laps > 0.005:
        th = np.linspace(0, laps * 2 * math.pi, max(2, int(laps * 260)))
        tilt = 0.10 + 0.22 * th / (2 * math.pi)  # each lap tilts a bit, so laps don't overlap
        P = np.stack([np.cos(th), np.sin(th) * np.cos(tilt), np.sin(th) * np.sin(tilt) * 3.0 - 0.3 + 0.25 * th / (2 * math.pi)], 1) * 1.06
        P = P / np.linalg.norm(P, axis=1, keepdims=True) * 1.06
        Q2 = P @ rot(0.0, 0.35).T
        pts = list(zip(cx + Q2[:, 0] * Re, cy - Q2[:, 2] * Re)); dep = Q2[:, 1]
        for (p0, p1, z) in zip(pts[:-1], pts[1:], dep[1:]):
            d.line([p0, p1], fill=YELLOW if z < 0.15 else (120, 100, 20), width=6 if z < 0.15 else 3)
        d.ellipse([pts[-1][0] - 11, pts[-1][1] - 11, pts[-1][0] + 11, pts[-1][1] + 11], fill=YELLOW)
    a = ease(lt / 0.4)
    d.text((124, 250), v.get("kicker", "YOUR BLOOD VESSELS"), font=font(FBo, 38), fill=fade_col(YELLOW, a))
    d.text((110, 300), fmt_num(v["miles"] * k), font=font(FB, 170), fill=fade_col(WHITE, a))
    d.text((126, 490), "miles, end to end", font=font(SERIF_IT, 60), fill=fade_col((235, 228, 240), a))
    b = ease((lt - 1.5) / 0.5)
    d.text((126, 600), f"{laps:.1f}x", font=font(FB, 110), fill=fade_col(YELLOW, b))
    d.text((128, 730), "around the Earth", font=font(SERIF_IT, 52), fill=fade_col((230, 225, 240), b))
    if v.get("note"): d.text((128, 820), v["note"], font=font(FM, 32), fill=fade_col(SOFT, b))
    return im

def sc_pulse(sc, t, lt):
    """A nerve: a wavy line of particles with a bright signal racing along it."""
    v = sc["visual"]
    xs = np.linspace(100, W - 100, 900)
    ys = H * 0.62 + 70 * np.sin(xs / 150 + 0.6) + 25 * np.sin(xs / 47)
    col = np.tile(np.array([110, 80, 230.]), (len(xs), 1)) * 0.8
    ph = (lt * 0.9) % 1.0; px = 100 + (W - 200) * ph
    g = np.exp(-((xs - px) / 60) ** 2)[:, None]
    col = col + g * np.array([255, 230, 120.]) * 2.5
    bx, by, bc = L.organ_pts(v.get("organ", "brain"), t, 150, 300, H * 0.28, dim=0.8)
    dx, dy, dc = L.dust(t)
    im = L.compose(t, [(dx, dy, dc, 1), (bx, by, bc, 2), (xs, ys, col, 4)]); d = ImageDraw.Draw(im)
    a = ease(lt / 0.4)
    d.text((W * 0.58, 190), v["num"], font=font(FB, 190), fill=fade_col(YELLOW, a), anchor="mm", stroke_width=5, stroke_fill=(0, 0, 0))
    d.text((W * 0.58, 320), v["label"], font=font(SERIF_IT, 62), fill=fade_col(WHITE, a), anchor="mm")
    if v.get("note"): d.text((W * 0.58, 400), v["note"], font=font(FM, 36), fill=fade_col(SOFT, ease((lt - 1) / .5)), anchor="mm")
    return im

SCENES = dict(L.SCENES)
SCENES.update({"dial": sc_dial, "ticker": sc_ticker, "bars": sc_bars, "duo": sc_duo, "earth": sc_earth, "pulse": sc_pulse})

# ------------------------------------------------------------------ overlays
NUMWORDS = set("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty thirty forty fifty sixty seventy eighty ninety hundred thousand million billion trillion half percent point".split())
def is_num(w):
    s = w.strip(".,?!;:'\"").lower()
    return any(ch.isdigit() for ch in s) or s in NUMWORDS or s.split("-")[0] in NUMWORDS

def subtitle(d, sc, lt):
    words = sc["say"].split(); dur = sc["_t1"] - sc["_t0"]
    if lt > dur + 0.2: return
    chunks, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) >= 7 or (w.endswith((".", "?", "!", ",")) and len(cur) >= 3): chunks.append(cur); cur = []
    if cur: chunks.append(cur)
    tot = sum(len(" ".join(c)) for c in chunks); acc = 0
    for ch in chunks:
        share = len(" ".join(ch)) / tot * dur
        if lt < acc + share or ch is chunks[-1]:
            f = font(FB, 50); sp = d.textlength(" ", font=f)
            ws = [w.upper() for w in ch]; tw = sum(d.textlength(w, font=f) for w in ws) + sp * (len(ws) - 1)
            x = W / 2 - tw / 2; y = H - 118
            for w, raw in zip(ws, ch):
                d.text((x, y), w, font=f, fill=YELLOW if is_num(raw) else WHITE, anchor="lm", stroke_width=5, stroke_fill=(0, 0, 0))
                x += d.textlength(w, font=f) + sp
            return
        acc += share

def overlays(d, ep, scenes, si, t):
    d.text((W - 60, 50), "INNER NUMBERS", font=font(FBo, 26), fill=(150, 155, 185), anchor="rm")
    hud0 = ep.get("hud_from_scene", 3)
    if si >= hud0 and scenes[si]["visual"]["type"] not in ("ticker",):
        d.text((60, 40), "NEW CELLS SINCE YOU PRESSED PLAY", font=font(FBo, 22), fill=(170, 175, 205))
        d.text((60, 66), fmt_num(ep.get("hud_rate", 3_800_000) * t), font=font(FB, 40), fill=YELLOW)
    # chapter progress bar
    chs = [k for k, s in enumerate(scenes) if s.get("chapter")]
    if chs and si >= chs[0]:
        n = len(chs); bw = 90; gap = 10; x0 = W / 2 - (n * bw + (n - 1) * gap) / 2
        cur = max(i for i, k in enumerate(chs) if k <= si)
        for i in range(n):
            col = YELLOW if i == cur else ((200, 200, 220) if i < cur else (70, 70, 95))
            d.rounded_rectangle([x0 + i * (bw + gap), 40, x0 + i * (bw + gap) + bw, 48], radius=4, fill=col)

def camera(im, sc, lt):
    cam = sc["visual"].get("camera")
    if not cam: return im
    k = ease(lt / max(1.0, sc["_dur"]))
    z = {"push_in": 1.0 + 0.14 * k, "pull_back": 1.16 - 0.16 * k}.get(cam, 1.0)
    if z <= 1.001: return im
    w, h = W / z, H / z
    return im.crop((int((W - w) / 2), int((H - h) / 2), int((W + w) / 2), int((H + h) / 2))).resize((W, H))

def frame_at(ep, scenes, t):
    si = next((k for k, s in enumerate(scenes) if s["_t0"] <= t < s["_t0"] + s["_dur"]), len(scenes) - 1)
    sc = scenes[si]; lt = t - sc["_t0"]
    im = camera(SCENES[sc["visual"]["type"]](sc, t, lt), sc, lt)
    if lt < 0.22 and si > 0:
        im = Image.blend(Image.new("RGB", (W, H)), im, 0.4 + 0.6 * lt / 0.22)
    d = ImageDraw.Draw(im)
    subtitle(d, sc, lt); overlays(d, ep, scenes, si, t)
    return im

# ------------------------------------------------------------------ pipeline
def load(ep_path, outdir):
    ep = json.load(open(ep_path)); tm = json.load(open(os.path.join(outdir, "timings.json")))
    scenes = ep["scenes"]
    for sc, (a, b) in zip(scenes, tm["timings"]):
        sc["_t0"], sc["_t1"] = a, b; sc["_dur"] = b - a + R.GAP
    return ep, scenes, tm["dur"]

def cmd_voice(ep_path, outdir):
    ep = json.load(open(ep_path)); os.makedirs(outdir, exist_ok=True)
    timings, dur = R.make_voice(ep, outdir)
    R.make_music(dur + 1.0, outdir, heartbeat=False, seed=ep.get("seed", 5))
    json.dump({"timings": timings, "dur": dur}, open(os.path.join(outdir, "timings.json"), "w"))
    chap = [(timings[k][0], s["chapter"]) for k, s in enumerate(ep["scenes"]) if s.get("chapter")]
    with open(os.path.join(outdir, "chapters.txt"), "w") as f:
        for t0, name in [(0, ep.get("intro_chapter", "Intro"))] + chap:
            f.write(f"{int(t0 // 60)}:{int(t0 % 60):02d} {name}\n")
    print("voice", round(dur, 1), "s"); print(open(os.path.join(outdir, "chapters.txt")).read())

def cmd_render(ep_path, outdir, part, nparts):
    ep, scenes, dur = load(ep_path, outdir)
    total = int((dur + 0.8) * FPS); a = total * part // nparts; b = total * (part + 1) // nparts
    tmp = os.path.join(outdir, f"part{part}.mp4")
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", tmp], stdin=subprocess.PIPE)
    for fi in range(a, b):
        ff.stdin.write(frame_at(ep, scenes, fi / FPS).tobytes())
        if fi % 600 == 0: print("part", part, "frame", fi, b, flush=True)
    ff.stdin.close(); ff.wait(); print("PART DONE", part)

def cmd_mux(ep_path, outdir, nparts):
    ep = json.load(open(ep_path))
    lst = os.path.join(outdir, "parts.txt")
    open(lst, "w").write("".join(f"file 'part{i}.mp4'\n" for i in range(nparts)))
    final = os.path.join(outdir, f"{ep['id']}.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-i", os.path.join(outdir, "voice.wav"), "-i", os.path.join(outdir, "music.wav"),
                    "-filter_complex", "[1:a]aresample=44100[v];[v][2:a]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5[a]",
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", final], check=True)
    print("DONE", final)

if __name__ == "__main__":
    c = sys.argv[1]
    if c == "voice": cmd_voice(sys.argv[2], sys.argv[3])
    elif c == "render": cmd_render(sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]))
    elif c == "mux": cmd_mux(sys.argv[2], sys.argv[3], int(sys.argv[4]))
    elif c == "frame":
        ep, scenes, dur = load(sys.argv[2], sys.argv[3]); frame_at(ep, scenes, float(sys.argv[4])).save(sys.argv[5])
