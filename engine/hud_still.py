"""Hologram HUD look test for Inner Numbers: the heart as a light wireframe, scan plane, target lock,
leader to a data card, chip rail, HUD subtitle. One still, 1080x1920.
python3 engine/hud_still.py out/hud_heart.png
"""
import os, sys, math
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(__file__))
from heart3d import f_heart, rot

W, H = 1080, 1920
FD = os.path.join(os.path.dirname(__file__), "..", "brand", "fonts")
def F(name, s): return ImageFont.truetype(os.path.join(FD, name), s)
LIGHT, MED, SEMI, MONO = "Rajdhani-Light.ttf", "Rajdhani-Medium.ttf", "Rajdhani-SemiBold.ttf", "ShareTechMono-Regular.ttf"
HUE = np.array([90, 225, 255.]) / 255           # ice cyan
ACC = (255, 184, 64)                              # warm accent: locked values only
HUEc = tuple(int(c * 255) for c in HUE)

def radius(d):
    lo = np.zeros(len(d)); hi = np.full(len(d), 2.0)
    for _ in range(28):
        m = (lo + hi) / 2; p = d * m[:, None]
        ins = f_heart(p[:, 0], p[:, 1], p[:, 2]) < 0
        lo = np.where(ins, m, lo); hi = np.where(ins, hi, m)
    return lo

def sph(el, az):
    return np.stack([np.cos(el) * np.cos(az), np.cos(el) * np.sin(az), np.sin(el)], -1)

def wire():
    lines = []
    for el in np.linspace(-1.35, 1.35, 22):                       # latitude rings
        az = np.linspace(0, 2 * np.pi, 160); d = sph(np.full_like(az, el), az)
        lines.append(d * radius(d)[:, None])
    for az0 in np.linspace(0, 2 * np.pi, 28, endpoint=False):     # meridians
        el = np.linspace(-1.5, 1.5, 120); d = sph(el, np.full_like(el, az0))
        lines.append(d * radius(d)[:, None])
    return lines

def project(P, Rm, scale, cx, cy, cam=4.2):
    Q = P @ Rm.T; s = scale * cam / (cam + Q[:, 1])
    return np.stack([cx + Q[:, 0] * s, cy - Q[:, 2] * s], 1), Q[:, 1], Q[:, 2]

def main(out):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    bg = np.zeros((H, W, 3), np.float32)
    lift = np.exp(-(((xx - W / 2) / 520) ** 2 + ((yy - H * 0.47) / 700) ** 2))
    bg += lift[..., None] * HUE * 0.10 + np.array([0.01, 0.02, 0.03])
    # dot grid
    g = np.zeros((H, W), np.float32); g[::36, ::36] = 1
    bg += cv2.GaussianBlur(g, (0, 0), 0.8)[..., None] * HUE * 0.9 * (0.3 + 0.7 * lift[..., None])

    line = np.zeros((H, W, 3), np.float32); hot = np.zeros((H, W, 3), np.float32)
    Rm = rot(0.55, 0.32); cx, cy, sc = W / 2, H * 0.40, 285
    scan_z = 0.15                                                       # scan plane height (model units)
    for P in wire():
        xy, depth, z = project(P, Rm, sc, cx, cy)
        fog = np.clip(1.15 - (depth + 1.2) / 2.4 * 0.85, 0.25, 1.0)
        for i in range(len(xy) - 1):
            a = float(fog[i]) * (1.0 if z[i] < scan_z + 0.02 else 0.18)  # above the scan: barely built
            c = tuple(float(v) * a for v in HUE)
            cv2.line(line, tuple(xy[i].astype(int)), tuple(xy[i + 1].astype(int)), c, 2, cv2.LINE_AA)
    # scan plane: bright ellipse at scan_z
    az = np.linspace(0, 2 * np.pi, 240); ring = np.stack([1.22 * np.cos(az), 1.22 * np.sin(az), np.full_like(az, scan_z)], 1)
    rxy, _, _ = project(ring, Rm, sc, cx, cy)
    cv2.polylines(hot, [rxy.astype(np.int32)], True, (0.95, 1.0, 1.0), 3, cv2.LINE_AA)
    # projector pad
    for r, w_, a in [(1.45, 2, 0.6), (1.2, 1, 0.35), (1.7, 1, 0.25)]:
        pad = np.stack([r * np.cos(az), r * np.sin(az), np.full_like(az, -1.55)], 1)
        pxy, _, _ = project(pad, Rm, sc, cx, cy)
        cv2.polylines(line, [pxy.astype(np.int32)], True, tuple(float(v) * a for v in HUE), w_, cv2.LINE_AA)
    for k in range(72):
        t = 2 * np.pi * k / 72; p = np.array([[1.45 * np.cos(t), 1.45 * np.sin(t), -1.55], [1.55 * np.cos(t), 1.55 * np.sin(t), -1.55]])
        q, _, _ = project(p, Rm, sc, cx, cy)
        cv2.line(line, tuple(q[0].astype(int)), tuple(q[1].astype(int)), tuple(float(v) * 0.45 for v in HUE), 1, cv2.LINE_AA)

    glow = cv2.GaussianBlur(line, (0, 0), 6) * 1.6 + cv2.GaussianBlur(line, (0, 0), 22) * 1.2 + cv2.GaussianBlur(hot, (0, 0), 10) * 2
    img = bg + line * 1.3 + hot + glow
    vig = 1 - 0.55 * (((xx - W / 2) / W) ** 2 + ((yy - H / 2) / (H * 0.8)) ** 2) * 2.2
    img = img * np.clip(vig, 0.25, 1)[..., None]
    im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)); d = ImageDraw.Draw(im)

    # HUD frame: corner brackets + micro data
    def bracket(x, y, sx, sy, L=60): d.line([(x, y), (x + sx * L, y)], fill=HUEc, width=2); d.line([(x, y), (x, y + sy * L)], fill=HUEc, width=2)
    for x, y, sx, sy in [(40, 60, 1, 1), (W - 40, 60, -1, 1), (40, H - 60, 1, -1), (W - 40, H - 60, -1, -1)]: bracket(x, y, sx, sy)
    d.text((70, 80), "INNER NUMBERS  //  BODY SCAN", font=F(MONO, 30), fill=HUEc)
    d.text((W - 70, 80), "HEART  ·  LIVE", font=F(MONO, 30), fill=HUEc, anchor="ra")
    d.text((70, H - 110), "SCAN 41%   ·   Z +0.15", font=F(MONO, 28), fill=HUEc)
    d.text((W - 70, H - 110), "32.0°  ·  4.2 M", font=F(MONO, 28), fill=HUEc, anchor="ra")
    for i in range(30):                                           # side rulers
        y = 260 + i * 44; L = 18 if i % 5 else 34
        d.line([(40, y), (40 + L, y)], fill=tuple(int(c * 0.6) for c in HUEc), width=1)
        d.line([(W - 40, y), (W - 40 - L, y)], fill=tuple(int(c * 0.6) for c in HUEc), width=1)

    # title as a value
    d.text((80, 150), "HEART", font=F(LIGHT, 170), fill=(225, 240, 245))
    d.line([(84, 345), (520, 345)], fill=HUEc, width=2)
    d.text((86, 362), "01  ·  CARDIAC PUMP", font=F(MONO, 32), fill=HUEc)

    # target lock on left ventricle + leader to card
    lv, _, _ = project(np.array([[0.35, -0.2, -0.35]]), Rm, sc, cx, cy); tx, ty = lv[0]
    s = 58
    for (ax, ay, sx, sy) in [(tx - s, ty - s, 1, 1), (tx + s, ty - s, -1, 1), (tx - s, ty + s, 1, -1), (tx + s, ty + s, -1, -1)]:
        d.line([(ax, ay), (ax + sx * 20, ay)], fill=(240, 255, 255), width=3); d.line([(ax, ay), (ax, ay + sy * 20)], fill=(240, 255, 255), width=3)
    d.ellipse([tx - 10, ty - 10, tx + 10, ty + 10], outline=(240, 255, 255), width=3)
    d.rectangle([tx + s + 6, ty - s - 4, tx + s + 56, ty - s + 38], fill=(5, 12, 16), outline=HUEc)
    d.text((tx + s + 31, ty - s + 17), "01", font=F(SEMI, 32), fill=(235, 245, 250), anchor="mm")
    c0 = (480, 1190, W - 70, 1430)
    d.line([(tx + 8, ty + 10), (tx + 60, c0[1] - 40), (c0[0] + 40, c0[1] - 40), (c0[0] + 40, c0[1])], fill=HUEc, width=2)
    d.rectangle(c0, fill=(4, 10, 14), outline=tuple(int(c * 0.7) for c in HUEc))
    d.text((c0[0] + 24, c0[1] + 22), "01   LEFT VENTRICLE", font=F(SEMI, 36), fill=HUEc)
    d.text((c0[0] + 24, c0[1] + 78), "70", font=F(LIGHT, 130), fill=ACC)
    d.text((c0[0] + 175, c0[1] + 150), "mL / beat", font=F(MED, 40), fill=ACC)
    d.text((c0[0] + 24, c0[1] + 200), "the strongest chamber", font=F(MED, 34), fill=(200, 215, 222))

    # chip rail (locked values dock here)
    for i, (lab, val, unit) in enumerate([("RATE", "70", "bpm"), ("PER DAY", "100,000", "beats")]):
        y0 = 1190 + i * 125
        d.rectangle([70, y0, 440, y0 + 112], fill=(4, 10, 14), outline=tuple(int(c * 0.7) for c in HUEc))
        d.text((92, y0 + 14), lab, font=F(SEMI, 30), fill=HUEc)
        d.text((92, y0 + 44), val, font=F(LIGHT, 72), fill=ACC)
        d.text((92 + d.textlength(val, font=F(LIGHT, 72)) + 10, y0 + 80), unit, font=F(MED, 32), fill=ACC)

    # HUD subtitle with voiceprint bars
    sub = "EVERY BEAT PUSHES 70 mL OF BLOOD"
    f = F(MED, 50); tw = d.textlength(sub, font=f); sx0 = W / 2 - tw / 2 - 40; sy0 = H - 330
    d.rectangle([sx0, sy0, W - sx0, sy0 + 110], fill=(4, 10, 14), outline=tuple(int(c * 0.6) for c in HUEc))
    d.text((W / 2, sy0 + 42), sub, font=f, fill=(235, 245, 250), anchor="mm")
    rng = np.random.default_rng(3)
    for i in range(40):
        h = rng.uniform(4, 22); x = W / 2 - 200 + i * 10
        d.line([(x, sy0 + 92 - h / 2), (x, sy0 + 92 + h / 2)], fill=HUEc, width=3)
    im.save(out); print(out)

if __name__ == "__main__":
    main(sys.argv[1])
