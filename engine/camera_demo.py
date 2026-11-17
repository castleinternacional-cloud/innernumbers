"""Demo: camera moves (split NO CAMERA / REC CAMERA, pull back, dolly zoom, crane up) + viewfinder HUD.
python3 engine/camera_demo.py out/camera_demo.mp4
"""
import os, sys, math, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(__file__))
from heart3d import rot
import organs as O
from styles import splat, glow, bokeh_layer, font, FB, FBo, FM

W, H, FPS = 1080, 1920, 30
SERIF_IT = "/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyrepagella-italic.otf"
if not os.path.exists(SERIF_IT): SERIF_IT = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-BoldItalic.ttf"
YELLOW = (255, 214, 0); RED = (255, 60, 70)
rng = np.random.default_rng(3)
ND = 3500
DUST = np.stack([rng.uniform(-W, W, ND), rng.uniform(-H, H, ND), rng.uniform(0.3, 1.0, ND)], 1)  # x,y around centre, depth
HEART = O.get("heart")
SEG = [("split", 0.0, 2.8), ("pull", 2.8, 4.8), ("dolly", 4.8, 6.8), ("crane", 6.8, 9.0)]
TOTAL = 9.0

def ease(x): x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)

def organ(t, scale, cx, cy, cam=4.0, yaw=0.0, tilt=0.0, spin=1.0):
    o = HEART
    Rm = rot(o.view_rot + yaw + 0.5 * math.sin(t * 0.9) * spin, o.view_tilt + tilt)
    Q = (o.P * o.pulse(t)) @ Rm.T
    s = scale * cam / (cam + Q[:, 1])
    x = cx + Q[:, 0] * s; y = cy - Q[:, 2] * s
    p0, p1, p2 = [np.array(c, float) for c in o.pal]
    tt = np.clip((o.P[:, 2] + 1.2) / 2.6, 0, 1)[:, None]
    col = np.where(tt < .5, p0 + (p1 - p0) * tt * 2, p1 + (p2 - p1) * (tt - .5) * 2)
    if hasattr(o, "surface_colors"): col[~o.is_vol] = o.surface_colors(o.P[~o.is_vol])
    col = col * (1.25 - ((Q[:, 1] + 1.5) / 3) * 0.8)[:, None]
    return x, y, col

def dust(t, zoom, cx, cy, dy=0.0):
    z = DUST[:, 2]
    x = cx + DUST[:, 0] * (1 + (zoom - 1) * z)
    y = cy + ((DUST[:, 1] - t * 30 * z + H) % (2 * H) - H) * (1 + (zoom - 1) * z) + dy * z
    return x, y, np.tile(np.array([140, 90, 255.]) * 0.35, (ND, 1)) * z[:, None]

yy = np.linspace(0, 1, H)[:, None, None]
BG = (np.array([16, 8, 36]) * (1 - yy) + np.array([4, 4, 12]) * yy) * np.ones((1, W, 1))

def render_layer(parts, t):
    layer = np.zeros((H, W, 3), np.float32)
    for x, y, c, sz in parts:
        m = (x > 1) & (x < W - 3) & (y > 1) & (y < H - 3)
        if m.any(): layer = splat(layer, x[m], y[m], c[m] * 1.5, sz)
    return BG + bokeh_layer(t, (90, 40, 160)) * 0.6 + layer + glow(layer, 18, gain=2.0)

def corners(d, x0, y0, x1, y1, L=60, w=5, col=(235, 235, 245)):
    for (x, y, sx, sy) in [(x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)]:
        d.line([(x, y), (x + sx * L, y)], fill=col, width=w); d.line([(x, y), (x, y + sy * L)], fill=col, width=w)

def pill(d, x, y, txt, dot=None, t=0):
    f = font(FBo, 30); tw = d.textlength(txt, font=f); pad = 18; extra = 34 if dot else 0
    d.rounded_rectangle([x, y, x + tw + 2 * pad + extra, y + 54], radius=27, fill=(10, 10, 20))
    if dot and int(t * 2) % 2 == 0: d.ellipse([x + pad, y + 17, x + pad + 20, y + 37], fill=dot)
    d.text((x + pad + extra, y + 27), txt, font=f, fill=(240, 240, 250), anchor="lm")

def timecode(t):
    f = int(t * 24) % 24; s = int(t)
    return f"00:00:{s:02d}:{f:02d}"

def hud(d, t, box, rec=True):
    x0, y0, x1, y1 = box
    corners(d, x0 + 30, y0 + 30, x1 - 30, y1 - 30)
    if rec:
        if int(t * 2) % 2 == 0: d.ellipse([x1 - 150, y1 - 92, x1 - 128, y1 - 70], fill=RED)
        d.text((x1 - 118, y1 - 81), "REC", font=font(FBo, 30), fill=(240, 240, 250), anchor="lm")
        d.text((x0 + 70, y1 - 81), timecode(t), font=font(FM, 28), fill=(210, 210, 225), anchor="lm")

def title(d, a, idx, big, sub):
    g = int(255 * a)
    d.text((80, 230), f"{idx} / 03", font=font(FBo, 34), fill=(g, int(g * .84), 0))
    yb = 280
    for line in big.split("\n"):
        d.text((76, yb), line, font=font(FB, 128), fill=(g, g, g), stroke_width=4, stroke_fill=(0, 0, 0)); yb += 125
    d.text((84, yb + 20), sub, font=font(SERIF_IT, 56), fill=(g, int(g * .9), int(g * .95)))

def frame(t):
    seg = next(s for s in SEG if s[1] <= t < s[2]) if t < TOTAL else SEG[-1]
    name, a, b = seg; u = (t - a) / (b - a); e = ease(u)
    fade = ease((t - a) / 0.35)
    if name == "split":
        half = H // 2
        # top: flat, no camera (no spin, fixed framing)
        top = render_layer([(*organ(t, 230, W / 2, half * 0.55, spin=0.0), 2)], t)
        # bottom: slow push-in + orbit
        bx, by, bc = organ(t, 230 + 120 * e, W / 2, half + half * 0.55, yaw=1.2 * e, tilt=-0.25 * e)
        dx, dy, dc = dust(t, 1 + 0.5 * e, W / 2, half + half * 0.5)
        bot = render_layer([(dx, dy, dc, 1), (bx, by, bc, 2)], t)
        img = np.concatenate([top[:half], bot[half:]], 0)
        im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
        d.line([(0, half), (W, half)], fill=(0, 0, 0), width=8)
        pill(d, 60, 150, "NO CAMERA")
        pill(d, 60, half + 40, "REC  ·  CAMERA", dot=RED, t=t)
        hud(d, t, (0, half, W, H))
        g = int(255 * ease((t - 0.3) / 0.4))
        d.text((W / 2, half - 90), "same heart.", font=font(SERIF_IT, 84), fill=(g, g, g), anchor="mm")
        g2 = int(255 * ease((t - 1.3) / 0.4))
        d.text((W / 2, H - 230), "now with a camera.", font=font(SERIF_IT, 84), fill=(g2, g2, g2), anchor="mm")
        return im
    if name == "pull":
        sc = 950 * (1 - e) + 330 * e
        x, y, c = organ(t, sc, W / 2, H * 0.55)
        dx, dy, dc = dust(t, 2.6 * (1 - e) + 1.0 * e, W / 2, H * 0.55)
        im = Image.fromarray(np.clip(render_layer([(dx, dy, dc, 1), (x, y, c, 2)], t), 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
        title(d, fade, "01", "PULL\nBACK", "the whole heart, at once")
    elif name == "dolly":
        cam = 1.15 * (1 - e) + 9.0 * e          # camera moves away...
        sc = 360                               # ...while the lens zooms in: heart keeps its size, depth warps
        x, y, c = organ(t, sc, W / 2, H * 0.56, cam=cam, yaw=0.5, tilt=0.35, spin=0.3)
        dx, dy, dc = dust(t, 0.6 + 2.8 * e, W / 2, H * 0.56)
        im = Image.fromarray(np.clip(render_layer([(dx, dy, dc * 1.8, 2), (x, y, c, 2)], t), 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
        title(d, fade, "02", "DOLLY\nZOOM", "the heart never moves")
    else:
        cy = H * 1.15 * (1 - e) + H * 0.47 * e
        x, y, c = organ(t, 360, W / 2, cy, tilt=0.6 * (1 - e))
        dx, dy, dc = dust(t, 1.2, W / 2, H * 0.5, dy=(H * 0.6) * (1 - e))
        im = Image.fromarray(np.clip(render_layer([(dx, dy, dc, 1), (x, y, c, 2)], t), 0, 255).astype(np.uint8)); d = ImageDraw.Draw(im)
        title(d, fade, "03", "CRANE\nUP", "from below, to the top")
        n = int(100000 * ease((t - a - 0.6) / 1.2))
        if t - a > 0.6:
            d.text((W / 2, H * 0.82), f"{n:,}", font=font(FB, 150), fill=YELLOW, anchor="mm", stroke_width=6, stroke_fill=(0, 0, 0))
            d.text((W / 2, H * 0.82 + 110), "beats every day", font=font(SERIF_IT, 60), fill=(235, 235, 245), anchor="mm")
    hud(d, t, (0, 0, W, H))
    d.text((W / 2, H - 40), "INNER NUMBERS", font=font(FBo, 28), fill=(170, 175, 200), anchor="mm")
    return im

def main(out):
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    n = int(TOTAL * FPS)
    for fi in range(n):
        ff.stdin.write(frame(fi / FPS).tobytes())
        if fi % 60 == 0: print("frame", fi, n, flush=True)
    ff.stdin.close(); ff.wait(); print("DONE", out)

if __name__ == "__main__":
    if len(sys.argv) > 2:  # preview stills: camera_demo.py out.png t
        frame(float(sys.argv[2])).save(sys.argv[1])
    else:
        main(sys.argv[1])
