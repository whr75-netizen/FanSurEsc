"""Geometric image-generation guides; these flat diagrams are NOT game art."""
from pathlib import Path
import math
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'Tools/Building35/Guides'
OUT.mkdir(parents=True, exist_ok=True)
R = np.array([1, 0, -1]) / math.sqrt(2)
U = np.array([.5/math.sqrt(2), math.sqrt(.75), .5/math.sqrt(2)])
D = np.cross(R, U)

def draw(name, faces):
    points = np.array([p for face, color in faces for p in face])
    projected = np.column_stack((points @ R, -points @ U))
    lo, hi = projected.min(0), projected.max(0)
    scale = 850 / max(hi-lo)
    center = (lo+hi)/2
    im = Image.new('RGBA', (1024, 1024), (0,0,0,0))
    pen = ImageDraw.Draw(im)
    for face, color in sorted(faces, key=lambda a: float(np.mean(a[0],axis=0) @ D), reverse=True):
        q = np.array(face)
        xy = (np.column_stack((q @ R, -q @ U))-center)*scale+512
        pen.polygon([tuple(v) for v in xy], fill=color, outline=(35,43,44,255), width=3)
    im.save(OUT / (name+'.png'))

def box(w,d,h):
    a,b,c,e=(-w/2,0,-d/2),(w/2,0,-d/2),(w/2,h,-d/2),(-w/2,h,-d/2)
    return [([a,b,c,e],(119,91,61,255)),
            ([(-w/2,0,d/2),a,e,(-w/2,h,d/2)],(97,72,48,255)),
            ([e,c,(w/2,h,d/2),(-w/2,h,d/2)],(171,132,82,255))]

def cylinder(r,h):
    rings = [[(r*math.cos(i*math.tau/40), y, r*math.sin(i*math.tau/40)) for i in range(40)] for y in (0,h)]
    faces=[]
    for i in range(40):
        j=(i+1)%40
        v=np.array(rings[0][i]); shade=112 if v @ R > 0 else 99
        faces.append(([rings[0][i],rings[0][j],rings[1][j],rings[1][i]],(shade,81,52,255)))
    faces.append((rings[1],(170,130,82,255)))
    return faces

draw('crate',box(.5,.4,.35))
draw('barrel',cylinder(.23,.65))
draw('counter',box(2.4,.8,1.0))
draw('fridge',box(.65,1.55,1.9))
draw('utility',box(1.3,.55,.9))
draw('cleaning',box(.6,.6,1.65))
draw('register',box(.55,.4,.42))
# The plant guide includes a translucent geometric canopy envelope, not invented leaf art.
plant=cylinder(.16,.30)
plant += [([(x,y,z) for x,y,z in face],(79,100,62,100)) for face,color in box(.6,.6,1.0)]
draw('plant',plant)
print(OUT)
