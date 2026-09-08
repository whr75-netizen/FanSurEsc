"""Bounded hue ranges -> source-only tone ramps, without semantic/position masks.

Histogram smoothing below changes bin statistics only, never image RGB/HSV.
This is a deterministic experimental heuristic; hue boundaries are not materials.
"""
import numpy as np
from .regions import rgb_to_hsv


def _distance_angle(a,b):
    return np.abs((a-b+180) % 360-180)


def _range_map(rgb, valid, requested_width):
    hsv = rgb_to_hsv(rgb)
    visible = valid > 0
    # Only nearly channel-equal/near-black colors are neutral. Pale warm colors
    # must not be discarded solely for low perceptual chroma, as in the old engine.
    spread = np.ptp(rgb.astype(np.int16),axis=2)
    neutral = (spread <= 6) | (hsv[...,2] < .035)
    reliable = visible & ~neutral & (hsv[...,1] >= .14) & (hsv[...,2] >= .15)
    bins = max(6,int(round(360/float(requested_width))))
    width = 360/bins
    if np.any(reliable):
        h = hsv[...,0][reliable]
        hist = np.bincount(np.minimum(359,np.floor(h).astype(int)),minlength=360).astype(float)
        # Center a range on a prominent color, preventing that color from landing
        # exactly on a conventional fixed boundary. Rare ranges are NOT pruned.
        smooth = sum(np.roll(hist,i)*np.exp(-i*i/4.5) for i in range(-5,6))
        peak = float(np.argmax(smooth))+.5
        phase = (peak-width*.5) % width
    else:
        phase = 0.0
    raw = np.minimum(bins-1,np.floor(((hsv[...,0]-phase)%360)/width)).astype(np.int16)
    raw[neutral] = bins
    raw[~visible] = -1
    present = np.unique(raw[visible])
    labels = np.full(raw.shape,-1,dtype=np.int16)
    groups = []
    for i,value in enumerate(present):
        labels[raw==value] = i
        groups.append({'kind':'neutral' if value==bins else 'hue',
                       'hue_start_degrees':None if value==bins else float((phase+value*width)%360),
                       'hue_end_degrees':None if value==bins else float((phase+(value+1)*width)%360),
                       'width_degrees':None if value==bins else width})
    return labels,hsv,groups


def _pick_source_color(rgb, hsv, lightness):
    """Choose an actual color, not an RGB mean. Rare ranges get their own call."""
    colors,inverse,count = np.unique(rgb,return_inverse=True,return_counts=True,axis=0)
    frequent = int(np.argmax(count))
    if count[frequent] >= max(8,len(rgb)*.12):
        return colors[frequent]
    # Choosing from a given hue interval prevents cross-hue medoids. Saturation
    # has its own target so low-saturation pixels cannot win only by lightness.
    target_l = float(np.median(lightness))
    target_s = float(np.quantile(hsv[:,1],.60))
    center_h = float(hsv[len(hsv)//2,0])
    unwrapped_h = center_h+(hsv[:,0]-center_h+180)%360-180
    target_h = float(np.median(unwrapped_h))%360
    score = ((lightness-target_l)/.06)**2 + ((hsv[:,1]-target_s)/.10)**2 + (_distance_angle(hsv[:,0],target_h)/6)**2
    return rgb[int(np.argmin(score))]


def build_color_ranges(rgb, lab, valid, options):
    family_map,hsv,range_info = _range_map(rgb,valid,options.range_hue_width)
    palette = []
    families = []
    tone_labels = np.zeros(valid.shape,dtype=np.int32)
    for i,entry in enumerate(range_info):
        selected = family_map==i
        colors = rgb[selected]
        values = lab[...,0][selected]
        color_hsv = hsv[selected]
        # Scalar LIGHTNESS grouping, restricted to this color range. No global
        # palette competition and no hue/saturation averaging across the image.
        count = min(options.tones_per_family,len(np.unique(values)))
        centers = np.unique(np.quantile(values,np.linspace(.05,.95,count)))
        for _ in range(12):
            assignment = np.argmin(np.abs(values[:,None]-centers),axis=1)
            updated = np.array([np.median(values[assignment==k]) if np.any(assignment==k) else centers[k] for k in range(len(centers))])
            if np.max(np.abs(updated-centers)) < 1e-6:
                break
            centers = updated
        assignment = np.argmin(np.abs(values[:,None]-centers),axis=1)
        global_indices = []
        selected_labels = np.empty(len(colors),dtype=np.int32)
        for k in range(len(centers)):
            members = assignment==k
            if not np.any(members):
                continue
            color = _pick_source_color(colors[members],color_hsv[members],values[members])
            value = tuple(int(c) for c in color)
            if value not in palette:
                palette.append(value)
            palette_index = palette.index(value)
            if palette_index not in global_indices:
                global_indices.append(palette_index)
            selected_labels[members] = palette_index
        tone_labels[selected] = selected_labels
        families.append(global_indices)
        entry['palette_indices'] = global_indices
        entry['source_pixel_count'] = int(selected.sum())
    details = {'mode':'bounded_hue_ranges', 'ranges':range_info,
               'range_count':len(range_info),'requested_hue_width':options.range_hue_width,
               'range_pruning':False,'part_seeds_or_coordinates':False,
               'range_definition':'Circular hue intervals; near-channel-equal/near-black colors separate. No semantic labels.',
               'tone_selection':'Within-range scalar lightness grouping, actual RGB representative constrained by hue and saturation.',
               'cleanup':'One simultaneous label pass; only same-range low-contrast outliers with >=6 matching neighbours.'}
    return np.array(palette,dtype=np.uint8),families,family_map,tone_labels,details


def clean_tone_labels(labels, family_map, importance, strength):
    """No RGB averaging or cross-range changes. Conservative single-pass cleanup."""
    if strength <= 0:
        return labels.copy()
    h,w = labels.shape
    padded = np.pad(labels,1,mode='edge')
    fp = np.pad(family_map,1,mode='constant',constant_values=-2)
    output = labels.copy()
    for start in range(0,h,128):
        end = min(h,start+128)
        region = family_map[start:end]
        neighbours = []
        eligible = []
        for dy,dx in ((-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)):
            neighbours.append(padded[1+start+dy:1+end+dy,1+dx:1+dx+w])
            eligible.append(fp[1+start+dy:1+end+dy,1+dx:1+dx+w]==region)
        neighbours = np.stack(neighbours)
        eligible = np.stack(eligible)
        proposed = labels[start:end].copy()
        count = np.zeros(region.shape,dtype=np.uint8)
        for candidate in neighbours:
            votes = np.sum((neighbours==candidate)&eligible,axis=0,dtype=np.uint8)
            better = votes>count
            proposed[better] = candidate[better]
            count[better] = votes[better]
        protected = importance[start:end] >= (.08+.18*strength)
        change = (count>=6)&~protected&(region>=0)
        output[start:end] = np.where(change,proposed,labels[start:end])
    return output
