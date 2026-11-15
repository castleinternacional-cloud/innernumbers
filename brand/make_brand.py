import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
rng=np.random.default_rng(7)
BG=(6,10,24)
def heart_points(n):
    pts=[]
    while len(pts)<n:
        x,y=rng.uniform(-1.3,1.3),rng.uniform(-1.3,1.3)
        if (x*x+y*y-1)**3 - x*x*y**3 <= 0: pts.append((x,-y))
    return np.array(pts)
def color(t):  # cyan -> violet -> pink
    a=np.array([0,229,255]);b=np.array([124,92,255]);c=np.array([255,64,160])
    return tuple((a+(b-a)*t*2).astype(int)) if t<.5 else tuple((b+(c-b)*(t-.5)*2).astype(int))
def particles(img,pts,cx,cy,scale,rmin,rmax):
    glow=Image.new("RGB",img.size,(0,0,0));d=ImageDraw.Draw(glow);d2=ImageDraw.Draw(img)
    for x,y in pts:
        px,py=cx+x*scale,cy+y*scale; t=(y+1.2)/2.4; t=min(max(t,0),1)
        r=rng.uniform(rmin,rmax); col=color(t)
        d.ellipse([px-r*3,py-r*3,px+r*3,py+r*3],fill=col)
        d2.ellipse([px-r,py-r,px+r,py+r],fill=col)
    glow=glow.filter(ImageFilter.GaussianBlur(rmax*4))
    return Image.blend(img,Image.fromarray(np.clip(np.array(img,int)+np.array(glow,int)*0.6,0,255).astype('uint8')),1)
# Profile 800x800
S=800; img=Image.new("RGB",(S,S),BG)
img=particles(img,heart_points(900),S/2,S/2+20,235,3,7)
# stray particles flying in
d=ImageDraw.Draw(img)
for _ in range(120):
    x,y=rng.uniform(0,S),rng.uniform(0,S); r=rng.uniform(1,2.5)
    d.ellipse([x-r,y-r,x+r,y+r],fill=(90,140,220))
img.save("brand/profile_800.png")
# Banner 2560x1440, safe zone 1546x423 centered
W,H=2560,1440; b=Image.new("RGB",(W,H),BG)
bg=rng.uniform([0,0],[W,H],(2500,2));
d=ImageDraw.Draw(b)
for x,y in bg:
    r=rng.uniform(1,3); t=x/W; c=color(t); c=tuple(int(v*0.55) for v in c)
    d.ellipse([x-r,y-r,x+r,y+r],fill=c)
b=b.filter(ImageFilter.GaussianBlur(1.2))
b=particles(b,heart_points(500),W/2-580,H/2,135,2,5)
d=ImageDraw.Draw(b)
f1=ImageFont.truetype("/usr/share/fonts/opentype/inter/InterDisplay-Black.otf" if __import__('os').path.exists("/usr/share/fonts/opentype/inter/InterDisplay-Black.otf") else "/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf",132)
f2=ImageFont.truetype("/usr/share/fonts/opentype/inter/InterDisplay-Medium.otf",56)
d.text((W/2-370,H/2-40),"INNER NUMBERS",font=f1,fill=(240,245,255),anchor="lm")
d.text((W/2-366,H/2+75),"Your body, counted.  New Short every day.",font=f2,fill=(0,229,255),anchor="lm")
b.save("brand/banner_2560x1440.png")
print("ok")
