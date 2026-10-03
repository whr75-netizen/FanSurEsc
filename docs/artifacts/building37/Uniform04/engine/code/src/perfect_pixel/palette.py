"""Opt-in, deterministic palette abstraction on a locked Perfect Pixel grid.

This is an experimental heuristic, not a reproduction of Gerstner et al., nor a
semantic redraw model. Existing get_perfect_pixel() remains unchanged.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from decimal import Decimal, InvalidOperation, ROUND_FLOOR
from numbers import Real
import hashlib
import numpy as np
from . import perfect_pixel_noCV2 as original


@dataclass(frozen=True)
class PaletteOptions:
    color_families: int = 6
    tones_per_family: int = 3
    flatten_strength: float = .75
    feature_strength: float = 1.5
    refine_intensity: float = .2
    # Hex reference color and relative importance (.25 demotes, 4 promotes).
    color_priorities: tuple = ()
    merge_hue_degrees: float = 20
    palette_method: str = 'color_ranges'
    range_hue_width: float = 15

    def validate(self):
        if self.palette_method not in ('color_ranges','legacy'):
            raise ValueError('palette_method must be color_ranges or legacy.')
        if isinstance(self.range_hue_width,bool) or not isinstance(self.range_hue_width,Real) or not np.isfinite(self.range_hue_width) or not 5 <= self.range_hue_width <= 60:
            raise ValueError('range_hue_width must be finite in [5,60].')
        for name, low, high in [('color_families', 2, 12), ('tones_per_family', 1, 4)]:
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, np.integer)) or not low <= value <= high:
                raise ValueError('%s must be an integer in [%s, %s]' % (name, low, high))
        for name, high in [('flatten_strength', 1), ('feature_strength', 3), ('refine_intensity', .45), ('merge_hue_degrees',45)]:
            raw = getattr(self, name)
            if isinstance(raw, bool) or not isinstance(raw, Real):
                raise ValueError('%s must be a number, not a string or boolean.' % name)
            value = float(raw)
            if not np.isfinite(value) or not 0 <= value <= high:
                raise ValueError('%s must be finite and in [0, %s]' % (name, high))
        for color, weight in self.color_priorities:
            parse_hex(color)
            if not np.isfinite(float(weight)) or not .25 <= float(weight) <= 4:
                raise ValueError('Color priority must be in [.25, 4].')


@dataclass
class PixelResult:
    image: np.ndarray
    palette: np.ndarray
    metadata: dict


def parse_hex(value):
    value = str(value).strip().lstrip('#')
    if len(value) != 6:
        raise ValueError('Priority color must be #RRGGBB.')
    try:
        return np.array([int(value[i:i+2], 16) for i in (0, 2, 4)], dtype=np.uint8)
    except ValueError as exc:
        raise ValueError('Priority color must be #RRGGBB.') from exc


def _image(image):
    a = np.asarray(image)
    if a.dtype != np.uint8 or a.ndim != 3 or a.shape[2] not in (3, 4) or min(a.shape[:2]) < 1:
        raise ValueError('Expected nonempty uint8 RGB or RGBA, shape H,W,3/4.')
    if a.shape[0] * a.shape[1] > 16_000_000:
        raise ValueError('Input exceeds the explicit 16 megapixel processing limit; no hidden resize is performed.')
    return a


def scaled_grid(base_grid, scale='1.0'):
    """Always derive from the immutable base, never from the previous output.

    Decimal avoids floor(70 * binary-float .9) accidentally becoming 62.
    """
    if len(base_grid) != 2:
        raise ValueError('base_grid must contain width and height.')
    base = []
    for x in base_grid:
        if isinstance(x, bool) or not isinstance(x, (int, np.integer)) or not 1 <= int(x) <= 4096:
            raise ValueError('Base dimensions must be integers in [1,4096].')
        base.append(int(x))
    try:
        factor = Decimal(str(scale))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError('Invalid resolution scale.') from exc
    if not factor.is_finite() or not Decimal('.1') <= factor <= Decimal('4'):
        raise ValueError('Resolution scale must be finite and in [.1,4].')
    target = tuple(max(1, int((Decimal(x)*factor).to_integral_value(rounding=ROUND_FLOOR))) for x in base)
    if max(target) > 4096 or target[0]*target[1] > 4_194_304:
        raise ValueError('Target exceeds 4096 per axis or 4 megapixels.')
    return target


def detect_base_grid(image):
    a = _image(image)
    # Correct RGB backend, shared original detector. A photo has no true hidden grid.
    rgb = a[..., :3].copy()
    if a.shape[2] == 4:
        rgb[a[..., 3] < 128] = 0
    w, h, _ = original.get_perfect_pixel(rgb, sample_method='center', fix_square=False)
    if w is None or h is None or w < 1 or h < 1:
        raise ValueError('No usable grid was detected. Set a manual base width/height; photographs have no intrinsic pixel grid.')
    return int(w), int(h)


def rgb_to_oklab(rgb):
    """Ottosson's published sRGB/D65 matrices; input float sRGB [0,1]."""
    rgb = np.asarray(rgb, dtype=np.float32)
    lin = np.where(rgb <= .04045, rgb/12.92, ((rgb+.055)/1.055)**2.4)
    lms = lin @ np.array([[.4122214708,.5363325363,.0514459929],
                         [.2119034982,.6806995451,.1073969566],
                         [.0883024619,.2817188376,.6299787005]], dtype=np.float32).T
    return np.cbrt(lms) @ np.array([[.2104542553,.7936177850,-.0040720468],
                                  [1.9779984951,-2.4285922050,.4505937099],
                                  [.0259040371,.7827717662,-.8086757660]], dtype=np.float32).T


def oklab_to_rgb(lab):
    lab = np.asarray(lab, dtype=np.float32)
    lms = (lab @ np.array([[1,.3963377774,.2158037573],
                          [1,-.1055613458,-.0638541728],
                          [1,-.0894841775,-1.2914855480]], dtype=np.float32).T)**3
    lin = lms @ np.array([[4.0767416621,-3.3077115913,.2309699292],
                         [-1.2684380046,2.6097574011,-.3413193965],
                         [-.0041960863,-.7034186147,1.7076147010]], dtype=np.float32).T
    lin = np.clip(lin, 0, 1)
    return np.clip(np.where(lin <= .0031308, 12.92*lin, 1.055*lin**(1/2.4)-.055), 0, 1)


def _box_mean(values, radius, valid):
    h, w = valid.shape
    radius = max(1, int(radius))
    def box(a):
        p = np.pad(a, ((radius,radius),(radius,radius)), mode='edge')
        sat = np.pad(p, ((1,0),(1,0))).cumsum(0, dtype=np.float64).cumsum(1)
        k=radius*2+1
        return sat[k:k+h,k:k+w]-sat[:h,k:k+w]-sat[k:k+h,:w]+sat[:h,:w]
    return (box(values*valid)/np.maximum(box(valid), 1e-8)).astype(np.float32)


def _feature_map(lab, valid, cell_size):
    radius = max(1, min(10, int(round(cell_size*.55))))
    mean = _box_mean(lab[...,0], radius, valid)
    contrast = np.abs(lab[...,0]-mean)
    # Both small bright and dark marks. Bounded, non-semantic importance.
    return (np.clip(contrast/.13, 0, 1)*valid).astype(np.float32)


def _flatten(lab, valid, importance, strength, cell_size):
    if strength <= 0:
        return lab.copy()
    h,w = valid.shape
    radius = max(1, min(5, int(round(cell_size*.4))))
    spatial_sigma = max(1, radius*.8)
    range_sigma = .035 + .085*strength
    pad = np.pad(lab, ((radius,radius),(radius,radius),(0,0)), mode='edge')
    vp = np.pad(valid, ((radius,radius),(radius,radius)), mode='edge')
    out = np.zeros_like(lab)
    norm = np.zeros((h,w), dtype=np.float32)
    for dy in range(-radius,radius+1):
        for dx in range(-radius,radius+1):
            shifted = pad[radius+dy:radius+dy+h,radius+dx:radius+dx+w]
            delta = np.sum((lab-shifted)**2,axis=2)
            weight = np.exp(-delta/(2*range_sigma**2)-(dx*dx+dy*dy)/(2*spatial_sigma**2))
            weight *= vp[radius+dy:radius+dy+h,radius+dx:radius+dx+w]
            out += shifted*weight[...,None]
            norm += weight
    out /= np.maximum(norm[...,None],1e-8)
    mix = strength*(1-.8*importance)
    return lab*(1-mix[...,None])+out*mix[...,None]


def _priority(lab, priorities):
    out = np.ones(lab.shape[:-1], dtype=np.float32)
    for color, factor in priorities:
        ref = rgb_to_oklab(parse_hex(color).astype(np.float32)/255)
        affinity = np.exp(-np.sum((lab-ref)**2,axis=-1)/(2*.075**2))
        out *= 1+(float(factor)-1)*affinity
    return np.clip(out, .25, 4)


def _nearest(data, centers):
    result=np.empty(len(data),dtype=np.int32)
    for start in range(0,len(data),32768):
        block=data[start:start+32768]
        result[start:start+len(block)]=np.argmin(np.sum((block[:,None,:]-centers[None,:,:])**2,axis=2),axis=1)
    return result


def _kmeans(data, weights, count):
    count=min(count,len(data))
    centers=[data[int(np.argmax(weights))].copy()]
    distance=np.sum((data-centers[0])**2,axis=1)
    for _ in range(1,count):
        index=int(np.argmax(distance*np.sqrt(weights)))
        if distance[index] < 1e-10: break
        centers.append(data[index].copy())
        distance=np.minimum(distance,np.sum((data-centers[-1])**2,axis=1))
    centers=np.array(centers,dtype=np.float32)
    for _ in range(14):
        labels=_nearest(data,centers)
        updated=centers.copy()
        for k in range(len(centers)):
            mask=labels==k
            if np.any(mask): updated[k]=np.average(data[mask],weights=weights[mask],axis=0)
        if np.max(np.abs(updated-centers))<1e-5:
            centers=updated;break
        centers=updated
    return centers,_nearest(data,centers)


def _palette(lab, valid, importance, options):
    visible = valid > 0
    colors=lab[visible]
    priority=_priority(colors,options.color_priorities)
    weights=1+options.feature_strength*importance[visible]
    weights*=priority
    # Color-bin histogram keeps fitting bounded while retaining rare accent colors.
    srgb=np.rint(oklab_to_rgb(colors)*255).astype(np.uint8)
    bins=(srgb//8).astype(np.int32)
    keys=bins[:,0]*1024+bins[:,1]*32+bins[:,2]
    _,inverse=np.unique(keys,return_inverse=True)
    count=np.bincount(inverse)
    mass=np.bincount(inverse,weights=weights)
    means=np.column_stack([np.bincount(inverse,weights=colors[:,c]*weights)/mass for c in range(3)]).astype(np.float32)
    # Temper large areas' votes without giving a one-pixel outlier unlimited power.
    fit_weights=mass/np.maximum(count,1)**.3
    chroma=np.linalg.norm(means[:,1:],axis=1)
    neutral=chroma<.028
    groups=[]
    if np.any(neutral): groups.append(np.flatnonzero(neutral))
    remaining=np.flatnonzero(~neutral)
    if len(remaining):
        family_features=means[remaining]*np.array([.18,1,1],dtype=np.float32)
        _,labels=_kmeans(family_features,fit_weights[remaining],options.color_families-len(groups))
        groups.extend(remaining[labels==k] for k in range(labels.max()+1) if np.any(labels==k))
    # Shadows of the same warm hue previously used several independent ramps.
    # Merge close hue families before imposing the tone limit. Neutral colors stay separate.
    if options.merge_hue_degrees>0:
        protected=1 if np.any(neutral) else 0
        merged=groups[:protected]
        angle_sets=[]
        for group in groups[protected:]:
            ab=np.average(means[group,1:],axis=0,weights=mass[group])
            angle=float(np.arctan2(ab[1],ab[0]))
            destination=None
            for i,angles in enumerate(angle_sets):
                distances=[abs(np.arctan2(np.sin(angle-a),np.cos(angle-a))) for a in angles]
                if max(distances)<=np.deg2rad(options.merge_hue_degrees):destination=i;break
            if destination is None:
                angle_sets.append([angle]);merged.append(group)
            else:
                angle_sets[destination].append(angle)
                merged[protected+destination]=np.concatenate([merged[protected+destination],group])
        groups=merged
    palette=[]; families=[]
    histogram_family=np.zeros(len(means),dtype=np.int32)
    for group in groups:
        histogram_family[group]=len(families)
        centers,_=_kmeans(means[group],fit_weights[group],options.tones_per_family)
        centers=centers[np.argsort(centers[:,0])]
        # Fit distances may use averages, but OUTPUT colors are actual source pixels.
        members=np.flatnonzero(np.isin(inverse,group))
        source_labels=_nearest(colors[members],centers)
        entries=[]
        for k,center in enumerate(centers):
            candidates=members[source_labels==k]
            if not len(candidates):candidates=members
            unique_rgb,counts=np.unique(srgb[candidates],return_counts=True,axis=0)
            frequent=int(np.argmax(counts))
            if counts[frequent]>=max(16,len(candidates)*.1):
                # Keep a genuinely flat background/base color exactly, not averaged with highlights.
                entry=unique_rgb[frequent]
            else:
                distance=np.sum((colors[candidates]-center)**2,axis=1)
                entry=srgb[candidates[int(np.argmin(distance))]]
            entries.append(entry)
        family=[]
        for c in entries:
            value=tuple(int(x) for x in c)
            if value not in palette: palette.append(value)
            idx=palette.index(value)
            if idx not in family:family.append(idx)
        families.append(family)
    palette=np.array(palette,dtype=np.uint8)
    family_map=np.zeros(valid.shape,dtype=np.int32)
    family_map[visible]=histogram_family[inverse]
    return palette,families,family_map


def _grid_edges(image, grid, intensity):
    h,w=image.shape[:2]
    gray=original.rgb_to_gray(image[...,:3])
    gx,gy=original.sobel_xy(gray)
    def edges(length,count,gradient):
        result=np.linspace(0,length,count+1,dtype=np.float64)
        if count>=length or intensity<=0:return result
        cell=length/count
        # Preserve count, both endpoints, and monotonicity; unlike accumulated snapping.
        for i in range(1,count):
            lo=max(1,int(np.ceil(result[i]-cell*intensity)))
            hi=min(length-1,int(np.floor(result[i]+cell*intensity)))
            if hi>=lo:
                values=gradient[lo:hi+1]
                if float(values.max())>1e-8:result[i]=lo+int(np.argmax(values))
        return result
    return edges(w,grid[0],np.abs(gx).sum(0)),edges(h,grid[1],np.abs(gy).sum(1))


def _vote(lab, palette, importance, valid, edges, options, families, family_map, preselected_labels=None):
    h,w=valid.shape
    if preselected_labels is None:
        labels=np.zeros((h,w),dtype=np.int32)
        palette_lab=rgb_to_oklab(palette.astype(np.float32)/255)
        for k,indices in enumerate(families):
            region=family_map==k
            labels[region]=np.asarray(indices)[_nearest(lab[region],palette_lab[indices])]
    else:
        labels=preselected_labels
    weight=(1+options.feature_strength*importance)*_priority(lab,options.color_priorities)
    ex,ey=edges
    out=np.zeros((len(ey)-1,len(ex)-1,4),dtype=np.uint8)
    for j in range(len(ey)-1):
        y0=max(0,min(h-1,int(np.floor(ey[j]))));y1=max(y0+1,min(h,int(np.ceil(ey[j+1]))))
        for i in range(len(ex)-1):
            x0=max(0,min(w-1,int(np.floor(ex[i]))));x1=max(x0+1,min(w,int(np.ceil(ex[i+1]))))
            # Pixel area overlap avoids double-counting a partial boundary pixel.
            yy=np.arange(y0,y1);xx=np.arange(x0,x1)
            overlap_y=np.maximum(0,np.minimum(yy+1,ey[j+1])-np.maximum(yy,ey[j]))
            overlap_x=np.maximum(0,np.minimum(xx+1,ex[i+1])-np.maximum(xx,ex[i]))
            spatial=overlap_y[:,None]*overlap_x[None,:]
            dx=(xx+.5-(ex[i]+ex[i+1])*.5)/max(ex[i+1]-ex[i],1e-6)
            dy=(yy+.5-(ey[j]+ey[j+1])*.5)/max(ey[j+1]-ey[j],1e-6)
            spatial*=.4+.6*np.exp(-2*(dy[:,None]**2+dx[None,:]**2))
            foreground=valid[y0:y1,x0:x1]
            ballot=weight[y0:y1,x0:x1]*spatial
            # Color preference must never expand/shrink the alpha silhouette.
            fg=float(np.sum(spatial*foreground));bg=float(np.sum(spatial*(1-foreground)))
            if fg<=0 or bg>fg:continue
            votes=np.bincount(labels[y0:y1,x0:x1].ravel(),weights=(ballot*foreground).ravel(),minlength=len(palette))
            out[j,i,:3]=palette[int(np.argmax(votes))]
            out[j,i,3]=255
    return out


def get_palette_pixel(image, base_grid=None, resolution_scale='1.0', options=None, mode='palette'):
    """Process ORIGINAL input each call; output pixels are discrete palette entries.

    mode='original' is a center-sample comparison on the SAME locked grid, not
    a claim to be bit-identical to upstream's wandering grid/fix_square output.
    """
    image=_image(image)
    options=options or PaletteOptions()
    options.validate()
    if mode not in ('palette','original'):raise ValueError('mode must be palette or original.')
    if base_grid is None:base_grid=detect_base_grid(image)
    grid=scaled_grid(base_grid,resolution_scale)
    base=tuple(int(x) for x in base_grid)
    rgb=image[...,:3].copy()
    alpha=image[...,3] if image.shape[2]==4 else np.full(image.shape[:2],255,dtype=np.uint8)
    valid=(alpha>=128).astype(np.float32)
    rgb[valid==0]=0
    edges=_grid_edges(rgb,grid,options.refine_intensity)
    palette=np.empty((0,3),dtype=np.uint8);families=[];range_details=None
    if mode=='original':
        ex,ey=edges
        xs=np.minimum(image.shape[1]-1,((ex[:-1]+ex[1:])*.5).astype(int))
        ys=np.minimum(image.shape[0]-1,((ey[:-1]+ey[1:])*.5).astype(int))
        output=image[ys[:,None],xs[None,:]].copy()
    elif not np.any(valid):
        output=np.zeros((grid[1],grid[0],image.shape[2]),dtype=np.uint8)
    else:
        lab=rgb_to_oklab(rgb.astype(np.float32)/255)
        # A density slider must not also silently change the palette/flattening.
        cell_size=min(image.shape[1]/base[0],image.shape[0]/base[1])
        importance=_feature_map(lab,valid,cell_size)
        if options.palette_method == 'color_ranges':
            from .color_ranges import build_color_ranges,clean_tone_labels
            palette,families,family_map,tone_labels,range_details=build_color_ranges(rgb,lab,valid,options)
            tone_labels=clean_tone_labels(tone_labels,family_map,importance,options.flatten_strength)
            rgba=_vote(lab,palette,importance,valid,edges,options,families,family_map,tone_labels)
        else:
            flattened=_flatten(lab,valid,importance,options.flatten_strength,cell_size)
            palette,families,family_map=_palette(lab,valid,importance,options)
            rgba=_vote(flattened,palette,importance,valid,edges,options,families,family_map)
        output=rgba if image.shape[2]==4 else rgba[...,:3]
    metadata={'algorithm':'perfect-pixel-palette-lab/0.3','mode':mode,
              'source_sha256_pixels':hashlib.sha256(image.tobytes()).hexdigest(),
              'source_shape':list(image.shape),'base_grid':list(base),'resolution_scale':str(resolution_scale),
              'target_grid':list(grid),'options':asdict(options),
              'palette':palette.tolist(),'family_palette_indices':families,
              'max_colors':(len(families) if options.palette_method=='color_ranges' else options.color_families)*options.tones_per_family,
              'color_range_details':range_details,
              'alpha_policy':'binary coverage vote at128 in palette mode; no transparent RGB contamination',
              'semantic_segmentation':False,'design_approval':'pending_user_review',
              'palette_color_policy':'actual input RGB representatives; no average-color output',
              'notes':['Automatic color families are not semantic skin/hair/material masks.',
                       'Small high-contrast features are weighted, not guaranteed semantic eye/nose preservation.',
                       'No dithering, generative redraw, or output RGB mixing.',
                       'Resolution ratio changes sampling density, not preview/export zoom.',
                       'Increasing resolution cannot reconstruct absent detail.']}
    return PixelResult(output,palette,metadata)
