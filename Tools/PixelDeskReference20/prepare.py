"""Fixed-reference measurement, constrained fit, and reusable wood material."""
import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'LocalOnly/DeskReference20'
SOURCE = Path('C:/Users/JG/.codex/generated_images/01a08c0e-bbf2-7d10-b1e8-607c2c27f6d3/exec-4cbe1c16-82f7-44be-8f3a-cdcf8378f8cd.png')
OUT.mkdir(parents=True, exist_ok=True)
shutil.copy2(SOURCE, OUT / 'reference.png')

# Explicit manual landmark observations, not per-part geometry corrections.
names = ['top_FL','top_FR','top_BR','top_BL', 'foot_FL','foot_FR','foot_BR','foot_BL',
         'slab_bottom_FL','slab_bottom_FR','slab_bottom_BR']
observed = np.array([(156,225),(1048,487),(1380,311),(480,56),
                     (214,732),(1044,977),(1330,811),(489,594),
                     (156,254),(1048,516),(1380,342)], float)
H = .74
L = .075

def model_points(v):
    w,d,_,_,_,_,_,t,inset = v
    corners = [(-1,-1),(1,-1),(1,1),(-1,1)]
    top = [(sx*w/2,sy*d/2,H) for sx,sy in corners]
    # The same visible (+X,-Y) corner of every identical foot.
    feet = [(sx*(w/2-inset-L/2)+L/2,sy*(d/2-inset-L/2)-L/2,0) for sx,sy in corners]
    bottom = [(x,y,H-t) for x,y,_ in top[:3]]
    return np.array(top+feet+bottom)

def project(points, v):
    _,_,p,phi,theta,ox,oy,_,_ = v
    r = np.array([np.cos(phi),np.sin(phi),0])
    u = np.array([-np.sin(phi)*np.sin(theta),np.cos(phi)*np.sin(theta),np.cos(theta)])
    return np.column_stack((ox*1000+p*1000*points@r,oy*1000-p*1000*points@u))

v = np.array([1.5,.77,.74,.64,.40,.77,.89,.04,.028])
lower = np.array([.8,.35,.4,.25,.20,.1,.3,.025,0])
upper = np.array([2.0,1.1,1.3,1.1,.80,1.4,1.4,.07,.10])
lam = 1e-3
iterations = 0
for iterations in range(100):
    residual = (project(model_points(v),v)-observed).ravel()
    cols = []
    for k in range(len(v)):
        dv = np.zeros_like(v); dv[k] = 1e-5
        cols.append(((project(model_points(v+dv),v+dv)-observed).ravel()-residual)/1e-5)
    jac = np.column_stack(cols)
    delta = np.linalg.lstsq(np.vstack((jac,np.sqrt(lam)*np.eye(len(v)))),
                            np.r_[-residual,np.zeros(len(v))],rcond=None)[0]
    candidate = np.clip(v+delta,lower,upper)
    if np.sum((project(model_points(candidate),candidate)-observed)**2) < residual@residual:
        v = candidate; lam = max(lam/3,1e-7)
        if np.linalg.norm(delta)<1e-8: break
    else:
        lam *= 10
        if lam > 1e12: break

w,d,p,phi,theta,ox,oy,t,inset = v
predicted = project(model_points(v),v)
im = Image.open(OUT/'reference.png').convert('RGBA')

# Affine rectification of the measured top surface into a reusable material.
# Whole-object pixels, legs/drawers/outline/screen coordinates are not sampled.
fl,fr,br,bl = observed[:4]
count_u,count_v = 256,128
uu,vv = np.meshgrid((np.arange(count_u)+.5)/count_u,(np.arange(count_v)+.5)/count_v)
uu = .025+.95*uu; vv = .045+.91*vv
coords = fl[None,None,:]+uu[...,None]*(fr-fl)+vv[...,None]*(bl-fl)
rgb = np.asarray(im)[np.rint(coords[...,1]).astype(int),np.rint(coords[...,0]).astype(int),:3]
Image.fromarray(rgb.astype('uint8')).save(OUT/'wood_material.png')

def sample_median(rect):
    x0,y0,x1,y1 = rect
    a = np.asarray(im)[y0:y1,x0:x1,:3]
    return np.median(a.reshape(-1,3),axis=0)

base = np.median(rgb.reshape(-1,3),axis=0)
# Fixed material samples avoiding handles and outline, documented for repeatability.
front = sample_median((300,325,355,375))
side = sample_median((1130,490,1210,515))
spec = {
 'reference_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
 'size':[1536,1024], 'coarse_size':[192,128],
 'height':H,'width':float(w),'depth':float(d),'top_thickness':float(t),
 'leg_width':L,'common_leg_inset':float(inset),
 'pixels_per_meter':float(p*1000),'azimuth':float(phi),'elevation':float(theta),
 'origin_px':[float(ox*1000),float(oy*1000)],
 'measurement_note':'Manual approximate landmarks; fit uses one common camera and equal legs, no per-leg correction.',
 'fit_iterations':iterations+1,
 'landmarks':[{'name':name,'observed':o.tolist(),'predicted':q.tolist(),'error_px':float(np.linalg.norm(q-o))}
              for name,o,q in zip(names,observed,predicted)],
 'landmark_rmse_px':float(np.sqrt(np.mean((predicted-observed)**2))),
 'material_top_median_rgb':base.tolist(),
 'face_srgb_factors':{'top':[1,1,1],'front':np.clip(front/base,.4,1.15).tolist(),
                      'side':np.clip(side/base,.4,1.15).tolist(),'bottom':[.48,.36,.28]},
 'source_material_sample_rects':{'front':[300,325,355,375],'side':[1130,490,1210,515]},
 'comparison_thresholds':{'alpha':128,'rgb_per_channel':8,'foreground_fraction':.99,'iou':.99},
 'lighting':'No lights; unlit emission; role colors measured from reference; Standard color transform.',
 'outline':'Local face boundary of constant world thickness, occluded by true mesh depth; no image overlay.'
}
(OUT/'spec.json').write_text(json.dumps(spec,indent=2),encoding='utf-8')
for role,factors in {**spec['face_srgb_factors'],'handle':[.45,.36,.29]}.items():
    tinted=np.clip(np.rint(rgb.astype(float)*np.array(factors)),0,255).astype('uint8')
    Image.fromarray(tinted).save(OUT/f'wood_{role}.png')
shutil.copy2(Path(__file__).with_name('prompt.txt'),OUT/'prompt.txt')
print(json.dumps({'width':w,'depth':d,'landmark_rmse_px':spec['landmark_rmse_px'],
                  'azimuth_deg':float(np.degrees(phi)),'elevation_deg':float(np.degrees(theta)),
                  'face_factors':spec['face_srgb_factors']}))
