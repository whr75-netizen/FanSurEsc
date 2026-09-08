"""Optional, color-agnostic local color-line coherence after palette transfer.

Not semantic matting: illumination/conflicting layers can make the fit ambiguous.
Only source-neighbour-supported low-residual fits may select a reference ramp.
No hue name, object coordinate, source RGB constant, or new mixed RGB is used.
"""
from itertools import combinations
import numpy as np
from .palette import rgb_to_oklab


def color_line_weight(p,a,b,max_residual=.16):
    """Fit p's Oklab chromaticity to b+t(a-b); return t or uncertainty None.

    L is checked separately, permitting modest illumination differences rather
    than claiming that this is a unique physical alpha-matte reconstruction.
    """
    vector = a[1:]-b[1:]
    denominator = float(np.dot(vector,vector))
    if denominator < .0004:
        return None
    weight = float(np.dot(p[1:]-b[1:],vector)/denominator)
    if not .15 <= weight <= .85:
        return None
    residual = float(np.linalg.norm(p[1:]-(b[1:]+weight*vector))/np.sqrt(denominator))
    if residual > max_residual or not min(a[0],b[0])-.06 <= p[0] <= max(a[0],b[0])+.06:
        return None
    return weight,residual


def apply_color_coherence(source,restyled,mappings,radius=2):
    """Select only existing reference colors; preserve size and alpha exactly."""
    if source.shape != restyled.shape or source.dtype != np.uint8 or restyled.dtype != np.uint8:
        raise ValueError('Source/restyled must have identical uint8 RGB/RGBA shapes.')
    if source.ndim != 3 or source.shape[2] not in (3,4):
        raise ValueError('Expected RGB/RGBA.')
    if source.shape[0]*source.shape[1] > 262144:
        raise ValueError('Optional coherence pass currently supports at most262144 native pixels. Disable this pass for larger outputs; no hidden resize/fallback.')
    if isinstance(radius,bool) or not isinstance(radius,int) or not 1<=radius<=3:
        raise ValueError('Radius must be1..3 native pixels.')
    colors,inverse = np.unique(source[...,:3].reshape(-1,3),axis=0,return_inverse=True)
    src_lab = rgb_to_oklab(colors/255)
    model = {tuple(item['source_rgb']):item for item in mappings}
    ramps = []
    target_lab = []
    for c in colors:
        item = model.get(tuple(int(v) for v in c))
        if item is None or not item.get('target_ramp'):
            # Fully transparent source RGB can be deliberately absent from model.
            ramps.append(np.array([c],dtype=np.uint8));target_lab.append(src_lab[len(ramps)-1])
            continue
        ramp = np.array(item['target_ramp'],dtype=np.uint8)
        order = np.argsort(rgb_to_oklab(ramp/255)[:,0])
        ramps.append(ramp[order])
        target_lab.append(rgb_to_oklab(np.array(item['target_rgb'])/255))
    target_lab = np.array(target_lab)
    src_chroma = np.linalg.norm(src_lab[:,1:],axis=1)
    ref_chroma = np.linalg.norm(target_lab[:,1:],axis=1)
    labels = inverse.reshape(source.shape[:2])
    visible = source[...,3]>0 if source.shape[2]==4 else np.ones(labels.shape,dtype=bool)
    output = restyled.copy()
    cache = {}
    changed = 0
    rejected = 0
    h,w = labels.shape
    for y in range(h):
        for x in range(w):
            if not visible[y,x]:
                continue
            p = int(labels[y,x])
            y0,y1=max(0,y-radius),min(h,y+radius+1)
            x0,x1=max(0,x-radius),min(w,x+radius+1)
            near,counts = np.unique(labels[y0:y1,x0:x1][visible[y0:y1,x0:x1]],return_counts=True)
            anchors = near[(counts>=2)&(near!=p)]
            best = None
            for first,second in combinations(anchors,2):
                # Accent is relative chroma evidence, not a particular named hue.
                a,b = (int(first),int(second)) if ref_chroma[first]>ref_chroma[second] else (int(second),int(first))
                key = p,a,b
                if key not in cache:
                    fit = None
                    if ref_chroma[a]>max(.04,ref_chroma[b]*1.35) and src_chroma[a]>src_chroma[b]*1.08:
                        fit = color_line_weight(src_lab[p],src_lab[a],src_lab[b])
                    cache[key] = fit
                fit = cache[key]
                if fit is None:
                    continue
                weight,residual = fit
                if np.array_equal(ramps[p],ramps[a]):
                    continue
                # Require target ramp separation as evidence, otherwise retain the
                # original class rather than moving every boundary toward a neighbour.
                if np.linalg.norm(target_lab[a,1:]-target_lab[b,1:])<.04:
                    continue
                score = residual+.10*abs(.5-weight)
                if best is None or score<best[0]:
                    best=(score,a,weight)
            if best is None:
                rejected+=1
                continue
            _,a,weight=best
            # Quantize membership to this reference ramp: no pixel RGB blending.
            index=int(np.clip(np.rint((1-weight)*(len(ramps[a])-1)),0,len(ramps[a])-1))
            color=ramps[a][index]
            if not np.array_equal(color,output[y,x,:3]):
                output[y,x,:3]=color
                changed+=1
    return output,{'method':'neighbour-supported Oklab color-line fit + discrete reference-ramp selection',
                   'object_or_hue_specific_rules':False,'source_coordinates_used':False,
                   'radius_native_pixels':radius,'changed_pixels':changed,'retained_without_fit':rejected,
                   'physical_alpha_reconstruction_claimed':False,
                   'limitation':'A good 2-color chromaticity fit is not proof of a material or a foreground layer.'}
