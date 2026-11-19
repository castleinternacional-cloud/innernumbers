"""3 YouTube thumbnails (1280x720) for 'Every Number Your Body Hits in One Day'.
Big particle organ + huge yellow number + 2-3 words (never the title).
python3 engine/thumbs_one_day.py out/thumbs_one_day
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
import longform as L
from thumbs_shower import text, base, YEL, WHT

W, H = L.W, L.H

def thumb_a():
    """Heart + 100,000 BEATS TODAY."""
    x, y, c = L.organ_pts("heart", 2.0, 400, W * 0.76, H * 0.50, spin=0)
    im = base([(x, y, c * 1.15, 3)]); d = ImageDraw.Draw(im)
    text(d, (80, 200), "100,000", 300, YEL, stroke=12)
    text(d, (95, 540), "BEATS TODAY", 140, WHT)
    return im

def thumb_b():
    """Blood cells + 330 BILLION NEW CELLS."""
    x, y, c = L.organ_pts("rbc", 2.0, 430, W * 0.5, H * 0.56, spin=0, dim=0.9)
    im = base([(x, y, c * 1.7, 3)]); d = ImageDraw.Draw(im)
    text(d, (W / 2, 280), "330 BILLION", 270, YEL, anchor="mm", stroke=12)
    text(d, (W / 2, 520), "NEW CELLS. TODAY.", 130, WHT, anchor="mm")
    return im

def thumb_c():
    """Spine/bone + -2 CM BY TONIGHT."""
    x, y, c = L.organ_pts("bone", 2.0, 360, W * 0.76, H * 0.50, spin=0)
    im = base([(x, y, c * 1.3, 3)]); d = ImageDraw.Draw(im)
    text(d, (70, 180), "-2 CM", 360, YEL, stroke=12)
    text(d, (90, 590), "BY TONIGHT", 150, WHT)
    return im

def main(out):
    os.makedirs(out, exist_ok=True)
    for name, fn in [("thumb_A_100k_beats", thumb_a), ("thumb_B_330_billion", thumb_b), ("thumb_C_minus_2cm", thumb_c)]:
        im = fn().resize((1280, 720), Image.LANCZOS).filter(ImageFilter.UnsharpMask(1.2, 60, 2))
        p = os.path.join(out, name + ".jpg"); im.save(p, quality=92); print(p, os.path.getsize(p) // 1024, "KB")
        im.resize((320, 180), Image.LANCZOS).save(os.path.join(out, name + "_mobile_preview.png"))

if __name__ == "__main__":
    main(sys.argv[1])
