"""3 YouTube thumbnails (1280x720) for the 'stop showering' long-form episode.
python3 engine/thumbs_shower.py out/thumbs
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
import longform as L

W, H = L.W, L.H
YEL = (255, 214, 0); WHT = (255, 255, 255); RED = (255, 70, 80)

def text(d, xy, s, size, fill, anchor="la", stroke=10, fnt=None):
    d.text(xy, s, font=L.font(fnt or L.FB, size), fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=(0, 0, 0))

def base(parts, t=2.0, vignette=True):
    parts = [(x, y, c * 1.35, max(sz, 3)) for x, y, c, sz in parts]   # thumbnails: denser, brighter particles
    im = L.compose(t, parts)
    if vignette:
        yy, xx = np.mgrid[0:H, 0:W]
        v = 1 - 0.55 * (((xx - W / 2) / (W / 1.3)) ** 2 + ((yy - H / 2) / (H / 1.3)) ** 2)
        im = Image.fromarray((np.array(im, np.float32) * np.clip(v, 0.3, 1)[..., None]).astype(np.uint8))
    return im

def thumb_a():
    """DAY 30 + dirty skin block + bacteria swarm."""
    sx, sy, sc = L.organ_pts("skin", 2.0, 520, W * 0.68, H * 0.58, yaw=0.3, spin=0)
    bx, by, bc = L.organ_pts("bacteria", 2.0, 620, W * 0.68, H * 0.48, spin=0)
    im = base([(sx, sy, sc * 0.75, 3), (bx, by, bc * np.array([0.6, 1.2, 0.5]), 4)])
    d = ImageDraw.Draw(im)
    text(d, (90, 150), "DAY 30", 300, YEL)
    text(d, (100, 470), "NO SHOWER", 150, WHT)
    return im

def thumb_b():
    """Big number: 1,300,000,000 skin cells."""
    sx, sy, sc = L.organ_pts("skin", 2.0, 470, W * 0.5, H * 0.72, spin=0, dim=0.8)
    im = base([(sx, sy, sc, 3)])
    d = ImageDraw.Draw(im)
    text(d, (W / 2, 250), "1,300,000,000", 220, YEL, anchor="mm", stroke=12)
    text(d, (W / 2, 450), "SKIN CELLS. GONE.", 120, WHT, anchor="mm")
    return im

def thumb_c():
    """Split DAY 1 (clean) vs DAY 30 (bacteria everywhere)."""
    lx, ly, lc = L.organ_pts("skin", 2.0, 330, W * 0.25, H * 0.60, spin=0)
    rx, ry, rc = L.organ_pts("skin", 2.0, 330, W * 0.75, H * 0.60, spin=0, dim=0.5)
    bx, by, bc = L.organ_pts("bacteria", 2.0, 430, W * 0.75, H * 0.55, spin=0)
    im = base([(lx, ly, lc, 3), (rx, ry, rc, 3), (bx, by, bc * np.array([0.6, 1.2, 0.5]), 4)], vignette=False)
    d = ImageDraw.Draw(im)
    d.rectangle([W / 2 - 6, 0, W / 2 + 6, H], fill=(0, 0, 0))
    text(d, (W * 0.25, 120), "DAY 1", 190, WHT, anchor="mm")
    text(d, (W * 0.75, 120), "DAY 30", 190, YEL, anchor="mm")
    text(d, (W * 0.75, H - 110), "WHAT LIVES ON YOU", 70, RED, anchor="mm", stroke=8)
    return im

def main(out):
    os.makedirs(out, exist_ok=True)
    for name, fn in [("thumb_A_day30", thumb_a), ("thumb_B_number", thumb_b), ("thumb_C_split", thumb_c)]:
        im = fn().resize((1280, 720), Image.LANCZOS).filter(ImageFilter.UnsharpMask(1.2, 60, 2))
        p = os.path.join(out, name + ".jpg"); im.save(p, quality=92); print(p, os.path.getsize(p) // 1024, "KB")

if __name__ == "__main__":
    main(sys.argv[1])
