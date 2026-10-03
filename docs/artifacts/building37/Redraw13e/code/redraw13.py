"""One cabinet: source geometry -> constrained grid -> detail -> integer raster."""
from pathlib import Path
import argparse
import hashlib
import json
import time
import numpy as np
from PIL import Image, ImageDraw
from redraw_geometry13 import geometry, inside, cv2, structural_lines
from redraw_detail13 import face_samples, _lab, _quantize

ROOT = Path(__file__).resolve().parents[2]
SOURCE_SHA = 'e4eb81a6bb53708a807e7eb182bfaa10bc39e37a5ed337c7913384323172d1ae'
ROI = [16, 22, 340, 314]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def grid(g):
    yy, xx = np.indices(tuple(g['size'][::-1]))
    return np.array(g['origin']) + g['pitch'] * np.stack((xx + .5, yy + .5), -1)


def nearest_role(rgb, centers, allowed):
    # Exact source RGB from the nearest pixel of the intended material. Filling
    # an excluded line halo cannot blend in colors from the neighboring brass.
    if not np.any(allowed):
        raise ValueError('MATERIAL_EMPTY_ROLE')
    _, labels = cv2.distanceTransformWithLabels((~allowed).astype(np.uint8), cv2.DIST_L2, 5,
                                                labelType=cv2.DIST_LABEL_PIXEL)
    coords = np.argwhere(allowed)
    ys = np.clip(np.floor(centers[..., 1]).astype(int), 0, rgb.shape[0] - 1)
    xs = np.clip(np.floor(centers[..., 0]).astype(int), 0, rgb.shape[1] - 1)
    lookup = coords[labels[ys, xs] - 1]
    return rgb[lookup[..., 0], lookup[..., 1]], lookup[..., ::-1]


def actual_palette(rgb, count=4):
    lab = _lab(rgb.astype(float))
    ids, _ = _quantize(lab[:, 0], count)
    palette = []
    for i in range(count):
        members = np.flatnonzero(ids == i)
        if not len(members):
            members = np.arange(len(rgb))
        mean = lab[members].mean(0)
        palette.append(rgb[members[np.argmin(np.sum((lab[members] - mean) ** 2, -1))]])
    return np.array(palette, np.uint8), ids


def snapped(p, g):
    return tuple(np.floor((np.array(p) - g['origin']) / g['pitch']).astype(int))


def dark_geometry(rgb,paint,wood,g):
    light=cv2.GaussianBlur(cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY).astype(float),(0,0),.8)
    valley=np.zeros(light.shape,bool)
    for direction in g['families']:
        normal=np.array([-direction[1],direction[0]])
        dx,dy=np.rint(normal*4).astype(int)
        below=np.roll(light,(dy,dx),(0,1));above=np.roll(light,(-dy,-dx),(0,1))
        valley |= (np.minimum(below,above)-light)>3.5
    valley &= paint & ~wood
    lines,_=structural_lines(valley,np.array(g['top']))
    sy,sx=np.indices(paint.shape);centers=np.stack((sx+.5,sy+.5),-1)
    halo=np.zeros(paint.shape,bool)
    for entry in lines:
        if entry['kind']!='trim_line':continue
        a,b=np.array(entry['a']),np.array(entry['b']);d=b-a;length=np.linalg.norm(d);d/=length
        n=np.array([-d[1],d[0]]);t=(centers-a)@d
        halo|=(t>=-1)&(t<=length+1)&(abs((centers-a)@n)<=entry['width']/2+1)
    return lines,halo,{'source_candidate_pixels':int(valley.sum()),'excluded_source_halo_pixels':int((halo&paint).sum())}


def geometry_stage(source, output):
    if output.exists() or digest(source) != SOURCE_SHA:
        raise ValueError('INPUT_REQUIRES_UNCHANGED_SHEET_AND_FRESH_OUTPUT')
    output.mkdir(parents=True)
    rgba = np.array(Image.open(source).convert('RGBA'))[ROI[1]:ROI[3], ROI[0]:ROI[2]]
    g, masks = geometry(rgba)
    g.update(source_sha256=SOURCE_SHA, source_size=[1489, 1056], source_roi=ROI,
             source_coordinates='ROI local corners; add ROI origin for original coordinates',
             mechanism='feature-constrained geometry/detail redraw; no original-grid recovery')
    np.savez_compressed(output/'geometry.npz', rgba=rgba, body=masks[0], wood=masks[1],
                        metal=masks[2], detail_labels=masks[3])
    Image.fromarray(rgba).save(output/'source-cabinet.png')
    write(output/'geometry.json', g)
    # Source-space evidence: long fitted lines, protected feature boxes and cap.
    preview = Image.fromarray(rgba); draw = ImageDraw.Draw(preview)
    draw.line([tuple(p) for p in g['top'] + [g['top'][0]]], fill=(245,80,220,255), width=1)
    for entry in g['lines']:
        draw.line((tuple(entry['a']), tuple(entry['b'])), fill=(80,240,220,255), width=1)
    for f in g['features']:
        draw.rectangle(f['bbox'], outline=(255,255,255,255), width=1)
    preview.save(output/'geometry-overlay.png')
    return {'stage':'geometry', 'pitch_source_px':g['pitch'], 'native_size':g['size'],
            'feature_count':len(g['features']), 'line_count':len(g['lines'])}


def detail_stage(output):
    g = read(output/'geometry.json'); data = np.load(output/'geometry.npz')
    rgba = data['rgba']; rgb = rgba[..., :3]; centers = grid(g)
    outer = inside(centers, g['silhouette'])
    top = inside(centers, g['top']) & outer
    corner = np.array(g['top'])[np.argmax(np.array(g['top'])[:, 1])]
    side = outer & ~top & (centers[..., 0] < corner[0])
    front = outer & ~top & ~side
    sy, sx = np.indices(rgba.shape[:2]); source_centers = np.stack((sx+.5, sy+.5), -1)
    paint = (rgb[..., 2] > rgb[..., 0]) & (rgb[..., 1] > rgb[..., 0]) & data['body']
    dark_lines,halo,dark_analysis=dark_geometry(rgb,paint,data['wood'],g)
    clean_paint=paint & ~halo
    # Keep source position/color lineage separate from output palette IDs.
    colors = np.zeros((*outer.shape, 3), np.uint8)
    roles = np.zeros(outer.shape, np.uint8); tones = np.zeros(outer.shape, np.uint8)
    residual = np.zeros(outer.shape, np.float32); confidence = np.zeros(outer.shape, np.float32)
    metadata = {}; palettes = {}; source_xy = np.zeros((*outer.shape, 2), np.int16)
    for name, rid, selected, allowed, role in (
        ('wood_top', 1, top, data['wood'] & (rgb[...,0] > rgb[...,1]*1.1) & (rgba[...,3]>160), 'wood'),
        ('paint_side', 2, side, clean_paint & (source_centers[...,0] < corner[0]), 'paint'),
        ('paint_front', 3, front, clean_paint & (source_centers[...,0] >= corner[0]), 'paint')):
        sampled, lineage = nearest_role(rgb, centers, allowed)
        xy = centers[selected]
        # A shared invertible planar basis avoids per-door or per-feature warp.
        if role == 'wood':
            directions = np.array(g['families'])[:2].T
            uv = (xy - corner) @ np.linalg.inv(directions).T
        else:
            d = np.array(g['families'])[1 if name=='paint_side' else 0]
            uv = xy @ np.linalg.inv(np.column_stack((d,[0.,1.]))).T
        result = face_samples(sampled[selected].astype(float), uv, role, 4)
        palette, ids = result['palette'], result['tone_ids']
        colors[selected] = palette[ids]; roles[selected]=rid; tones[selected]=ids
        residual[selected] = result['detail_luma']; confidence[selected] = result['grain_confidence']
        source_xy[selected] = lineage[selected]
        metadata[name] = result['analysis']; palettes[name] = palette.tolist()
    source_metal = data['metal']
    metal_rgb = rgb[source_metal]
    metal_palette, _ = actual_palette(metal_rgb, 4)
    # Mask coverage is sampled from the original small decorations. Long narrow
    # strokes are replaced in raster; no palette operation may erase handles.
    yi = np.clip(np.floor(centers[...,1]).astype(int),0,rgb.shape[0]-1)
    xi = np.clip(np.floor(centers[...,0]).astype(int),0,rgb.shape[1]-1)
    detail_labels=data['detail_labels'][yi,xi]
    protected=np.isin(detail_labels,[f['mask_label'] for f in g['features']])
    # Isolated warm specks and the old anti-aliased stroke halo are not copied
    # back. Only fitted wide bands and protected source details own metal cells.
    metal_mask = protected & outer & ~top
    nearest_metal = rgb[yi,xi]
    metal_ids = np.argmin(np.sum((_lab(nearest_metal.reshape(-1,3).astype(float))[:,None,:]
                                 - _lab(metal_palette.astype(float))[None,:,:])**2,-1),-1).reshape(outer.shape)
    colors[metal_mask] = metal_palette[metal_ids[metal_mask]]
    roles[metal_mask]=4; tones[metal_mask]=metal_ids[metal_mask]
    source_xy[metal_mask]=np.stack((xi,yi),-1)[metal_mask]
    palettes['metal']=metal_palette.tolist()
    for entry in g['lines']:
        if entry['kind']!='metal_band':continue
        a,b=np.array(entry['a']),np.array(entry['b']);d=b-a;length=np.linalg.norm(d);d/=length
        n=np.array([-d[1],d[0]]);t=(centers-a)@d;across=(centers-a)@n
        strip=(t>=0)&(t<=length)&(np.abs(across)<=entry['width']/2)&outer&~top
        if not np.any(strip):continue
        # Median source tone across each cross-section bin removes accidental
        # along-strip noise while retaining the observed metal reflectance band.
        source_t=(source_centers-a)@d;source_n=(source_centers-a)@n
        support=source_metal&(source_t>=0)&(source_t<=length)&(np.abs(source_n)<=entry['width']/2+1)
        bins=np.linspace(-entry['width']/2,entry['width']/2,4)
        table=[]
        luma=_lab(metal_palette.astype(float))[:,0]
        for lo,hi in zip(bins,bins[1:]):
            samples=rgb[support&(source_n>=lo)&(source_n<=hi)]
            value=float(np.median(_lab(samples.astype(float))[:,0])) if len(samples) else float(np.median(luma))
            table.append(int(np.argmin(abs(luma-value))))
        band=np.clip(np.searchsorted(bins,across,side='right')-1,0,2)
        ids=np.array(table,np.uint8)[band]
        colors[strip]=metal_palette[ids[strip]];roles[strip]=4;tones[strip]=ids[strip]
        # Retain the observed widening/end ornament, not an invented fitting.
        end=((source_t>=-6)&(source_t<=min(10,length/3)))|((source_t>=length-min(10,length/3))&(source_t<=length+6))
        end &= source_metal & (abs(source_n)<=entry['width']*.9+1)
        native_end=end[yi,xi]&outer&~top
        colors[native_end]=metal_palette[metal_ids[native_end]]
        roles[native_end]=4;tones[native_end]=metal_ids[native_end]
    # Actual source dark paint representative, not invented outline black.
    paint_rgb=rgb[paint]; luma=_lab(paint_rgb.astype(float))[:,0]
    ink_rgb=paint_rgb[np.argmin(np.abs(luma-np.percentile(luma,4)))].tolist()
    palettes['ink']=[ink_rgb]
    metadata['dark_structure']={'detected_lines':dark_lines,**dark_analysis}
    metadata['palettes']=palettes
    np.savez_compressed(output/'detail.npz', colors=colors, roles=roles, tones=tones,
                        detail=residual, confidence=confidence, coverage=outer, top=top,
                        source_xy=source_xy, protected=protected, source_halo=halo,
                        sampled_detail_labels=detail_labels)
    write(output/'detail.json',metadata)
    return {'stage':'detail','role_palettes':palettes,'wood_grain_candidates':metadata['wood_top']['directional_detail']['grain_candidates']}


def raster_stage(output):
    g=read(output/'geometry.json'); details=read(output/'detail.json'); data=np.load(output/'detail.npz')
    coverage=data['coverage']; rgb=data['colors'].copy(); roles=data['roles'].copy()
    ink=tuple(details['palettes']['ink'][0]); metal=details['palettes']['metal']
    size=tuple(g['size']); ink_mask=Image.new('L',size,0); draw=ImageDraw.Draw(ink_mask)
    for entry in details['dark_structure']['detected_lines']:
        if entry['kind']=='trim_line':
            draw.line((snapped(entry['a'],g),snapped(entry['b'],g)),fill=255,width=1)
    # Outer profile has a single owned 1px boundary. Interior source grain is
    # untouched by this operation, and invisible pixels never become ink.
    boundary=np.zeros(coverage.shape,np.uint8)
    contours=cv2.findContours(coverage.astype(np.uint8),cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_NONE)[0]
    cv2.drawContours(boundary,contours,-1,1,1,cv2.LINE_8)
    boundary=boundary.astype(bool)
    drawn=np.array(ink_mask)>0; drawn &= coverage & ~data['top']
    rgb[drawn|boundary]=ink;roles[drawn|boundary]=5
    trim_mask=Image.new('L',size,0); draw=ImageDraw.Draw(trim_mask)
    for entry in g['lines']:
        if entry['kind']=='trim_line':
            draw.line((snapped(entry['a'],g),snapped(entry['b'],g)),fill=255,width=1)
    trim=(np.array(trim_mask)>0)&coverage&~data['top']&~boundary
    rgb[trim]=metal[1];roles[trim]=4
    # The cap's four edges use the same shared continuous vertices. Rim tone is
    # taken from the actual warm palette; it is not an AA gradient halo.
    rim=Image.new('L',size,0);draw=ImageDraw.Draw(rim)
    p=[snapped(v,g) for v in g['top']]
    draw.line(p+[p[0]],fill=255,width=1)
    rim=(np.array(rim)>0)&coverage&~boundary
    rgb[rim]=details['palettes']['wood_top'][3];roles[rim]=1
    # Handles are foreground decorations attached to door faces. A fitted
    # background seam cannot overwrite their observed cells.
    protected=data['protected']&coverage&~data['top']&~boundary
    rgb[protected]=data['colors'][protected];roles[protected]=4
    rgba=np.zeros((*coverage.shape,4),np.uint8);rgba[...,:3]=rgb;rgba[...,3]=coverage.astype(np.uint8)*255
    rgba[~coverage]=0
    Image.fromarray(rgba).save(output/'native.png')
    Image.fromarray(rgba).resize((size[0]*4,size[1]*4),Image.Resampling.NEAREST).save(output/'preview-x4.png')
    Image.fromarray(rgba).resize((size[0]*8,size[1]*8),Image.Resampling.NEAREST).save(output/'preview-x8.png')
    final_ink=roles==5
    final_trim=trim&(roles==4)&~protected
    Image.fromarray((final_ink*255).astype(np.uint8)).save(output/'structure-mask.png')
    np.savez_compressed(output/'raster.npz', roles=roles, trim=final_trim, ink=final_ink,
                        vector_ink=final_ink&drawn&~boundary, rgba=rgba)
    # Native source-density view uses pixel replication for display only. Source
    # is never resampled into the final PNG. Clearly separated panes/labels.
    source=Image.open(output/'source-cabinet.png').convert('RGBA')
    native=Image.fromarray(rgba)
    factor=4
    shown=native.resize((native.width*factor,native.height*factor),Image.Resampling.NEAREST)
    height=max(source.height,shown.height)+32
    comparison=Image.new('RGBA',(source.width+shown.width+32,height),(24,29,39,255))
    comparison.alpha_composite(source,(8,28));comparison.alpha_composite(shown,(source.width+24,28))
    text=ImageDraw.Draw(comparison);text.text((8,8),'SOURCE 1x',fill='white');text.text((source.width+24,8),'NATIVE 4x / nearest',fill='white')
    comparison.save(output/'comparison.png')
    return {'stage':'raster','native_size':list(size),'visible_colors':int(np.unique(rgba[coverage,:3],axis=0).shape[0]),
            'partial_alpha':int(np.count_nonzero((rgba[...,3]>0)&(rgba[...,3]<255)))}


def validate_stage(source,output):
    g=read(output/'geometry.json');details=read(output/'detail.json'); data=np.load(output/'detail.npz'); raster=np.load(output/'raster.npz')
    rgba=np.array(Image.open(output/'native.png').convert('RGBA'));coverage=rgba[...,3]>0
    source_rgb=np.array(Image.open(source).convert('RGBA'))[ROI[1]:ROI[3],ROI[0]:ROI[2],:3]
    actual={tuple(v) for v in source_rgb.reshape(-1,3)}
    palette={tuple(v) for rows in details['palettes'].values() for v in rows}
    checks=[]
    def add(name,ok,observation):checks.append({'id':name,'passed':bool(ok),'observed':observation})
    add('source_sha',digest(source)==SOURCE_SHA,digest(source))
    add('native_geometry_size',list(Image.open(output/'native.png').size)==g['size'],g['size'])
    add('binary_coverage',np.isin(rgba[...,3],[0,255]).all(),np.unique(rgba[...,3]).tolist())
    add('transparent_rgb_zero',(rgba[~coverage]==0).all(),int((rgba[~coverage]!=0).sum()))
    add('actual_source_palette',palette<=actual,sorted(palette))
    add('finite_role_palette',{tuple(v) for v in rgba[coverage,:3]}<=palette,len(np.unique(rgba[coverage,:3],axis=0)))
    add('final_ink_owner_matches_pixels',np.array_equal(raster['ink'],raster['roles']==5)
        and np.all(rgba[raster['ink'],:3]==details['palettes']['ink'][0]),int(raster['ink'].sum()))
    add('uniform_pitch',g['pitch']>0 and not g['observed_grid_recovered'],{'pitch':g['pitch'],'grid_recovery':False})
    labels=data['sampled_detail_labels'];feature_results=[]
    for feature in g['features']:
        selected=(labels==feature['mask_label'])&coverage
        metal_visible=selected&(raster['roles']==4)
        count=int(metal_visible.sum())
        colors=int(np.unique(rgba[metal_visible,:3],axis=0).shape[0]) if count else 0
        feature_results.append({'id':feature['id'],'metal_cells':count,'colors':colors})
    add('protected_features_survive',all(v['metal_cells']>=12 and v['colors']>=3 for v in feature_results),feature_results)
    source_data=np.load(output/'geometry.npz');gaps=[];feature_geometry=[]
    centers=grid(g)
    for feature in g['features']:
        src=np.argwhere(source_data['detail_labels']==feature['mask_label'])[:,::-1]+.5
        selected=(labels==feature['mask_label'])&coverage
        dst=centers[selected]
        error=float(np.linalg.norm(src.mean(0)-dst.mean(0)))
        feature_geometry.append({'id':feature['id'],'centroid_error_source_px':error})
    add('detail_positions_preserved',all(v['centroid_error_source_px']<=g['pitch'] for v in feature_geometry),feature_geometry)
    ids=[f['mask_label'] for f in g['features']]
    for i,a in enumerate(ids):
        ca=np.argwhere((labels==a)&coverage)
        sa=np.argwhere(source_data['detail_labels']==a)
        for b in ids[i+1:]:
            cb=np.argwhere((labels==b)&coverage)
            sb=np.argwhere(source_data['detail_labels']==b)
            distance=int(np.abs(ca[:,None]-cb[None,:]).max(-1).min())
            source_distance=int(np.abs(sa[:,None]-sb[None,:]).max(-1).min())
            # These are source material-support clusters, not individual knobs.
            # Some already touch trim/each other in the source. Preserve that
            # relation; don't invent a new 1px gap or call it a source error.
            separated=source_distance>=2*g['pitch']
            gaps.append({'labels':[a,b],'source_chebyshev_gap_px':source_distance,
                         'chebyshev_gap_cells':distance,'source_resolvable_separation':bool(separated)})
    add('source_detail_support_relations',all(not v['source_resolvable_separation'] or v['chebyshev_gap_cells']>=2 for v in gaps),gaps)
    xy=data['source_xy'];face=np.isin(data['roles'],[2,3])
    forbidden=data['source_halo'][xy[...,1],xy[...,0]]
    add('source_line_halo_not_resampled',not np.any(forbidden&face),int(np.count_nonzero(forbidden&face)))
    line_positions=[]
    for kind,entries,owned in [('ink',details['dark_structure']['detected_lines'],raster['vector_ink']),('trim',g['lines'],raster['trim'])]:
        points=centers[owned]
        distances=np.full(len(points),np.inf)
        for entry in entries:
            if entry['kind']!='trim_line':continue
            a,b=np.array(entry['a']),np.array(entry['b']);delta=b-a
            t=np.clip((points-a)@delta/(delta@delta),0,1)
            distance=np.linalg.norm(points-(a+t[:,None]*delta),axis=1)/g['pitch']
            distances=np.minimum(distances,distance)
        # All owned final vector pixels participate. There is no pre-filter on
        # distance that would make the bound tautologically pass.
        line_positions.append({'kind':kind,'visible_cells':len(points),
                               'max_center_distance_native_px':float(distances.max()) if len(points) else None})
    add('actual_line_positions',all(v['visible_cells']>=10 and v['max_center_distance_native_px']<=1.1 for v in line_positions),line_positions)
    # Each submitted thin vector stroke must be a single Bresenham path before
    # foreground occlusion/joins. This inspects actual fitted segments, not just
    # an unrelated illustrative fixture.
    strokes=[]
    for kind,entries in [('ink',details['dark_structure']['detected_lines']),('trim',g['lines'])]:
        for j,entry in enumerate(entries):
            if entry['kind']!='trim_line':continue
            plane=Image.new('L',tuple(g['size']),0);draw=ImageDraw.Draw(plane)
            a,b=snapped(entry['a'],g),snapped(entry['b'],g)
            draw.line((a,b),fill=255,width=1)
            yy,xx=np.nonzero(np.array(plane));major=xx if abs(b[0]-a[0])>=abs(b[1]-a[1]) else yy
            strokes.append({'kind':kind,'line':j,'cells':len(major),'major_positions':len(np.unique(major))})
    add('actual_vector_strokes_single_pixel',all(v['cells']==v['major_positions'] for v in strokes),strokes)
    band_observations=[]
    for j,entry in enumerate(g['lines']):
        if entry['family']!=2 or entry['width']<6:continue
        a,b=np.array(entry['a']),np.array(entry['b']);direction=b-a;length=np.linalg.norm(direction);direction/=length
        normal=np.array([-direction[1],direction[0]]);t=(centers-a)@direction
        selected=(t>length*.35)&(t<length*.65)&(abs((centers-a)@normal)<=entry['width']/2)&(raster['roles']==4)
        band_observations.append({'line':j,'middle_colors':int(np.unique(rgba[selected,:3],axis=0).shape[0])})
    add('actual_metal_is_not_flat_color',bool(band_observations) and all(v['middle_colors']>=2 for v in band_observations),band_observations)
    wood=data['top']&(raster['roles']==1)&~raster['ink']
    distinct=int(np.unique(rgba[wood,:3],axis=0).shape[0])
    grain=int(np.count_nonzero(np.abs(data['detail'][wood])>.4))
    add('wood_has_tones_and_source_detail',distinct>=3 and grain>=30,{'colors':distinct,'source_detail_cells':grain})
    # Non-axis line fixture: no AA, one minor-axis value per major-axis position.
    fixture=np.zeros((24,40),np.uint8);cv2.line(fixture,(2,19),(35,3),255,1,cv2.LINE_8)
    yy,xx=np.nonzero(fixture)
    add('line8_single_stroke_fixture',np.unique(xx).size==len(xx) and np.isin(fixture,[0,255]).all(),{'cells':len(xx),'columns':np.unique(xx).size})
    # Different source direction families must not be replaced by symmetric +/- .5.
    slopes=[v[1]/v[0] for v in g['families'][:2]]
    add('observed_asymmetric_projection',abs(abs(slopes[0])-abs(slopes[1]))>.005,slopes)
    preview=np.array(Image.open(output/'preview-x8.png'))
    add('preview_is_exact_integer_replication',np.array_equal(preview,np.repeat(np.repeat(rgba,8,axis=0),8,axis=1)),list(preview.shape))
    result={'passed':all(v['passed'] for v in checks),'checks':checks,'art_approved':False,
            'scope':'Source-derived closed-cabinet reconstruction, not universal normalization or AI-art-free proof',
            'unverified':['reference-game style equivalence','physical albedo/Unity relighting','other objects/sheets',
                          'global stroke unions are 1px everywhere including intersections','semantic correctness of every detected detail']}
    write(output/'validation.json',result)
    if not result['passed']:
        raise ValueError('FINAL_CONTRACT_FAILED:'+','.join(v['id'] for v in checks if not v['passed']))
    return {'stage':'validate','passed':True,'check_count':len(checks),'art_approved':False}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=['geometry','detail','raster','validate'])
    parser.add_argument('--source',required=True);parser.add_argument('--output',required=True)
    args=parser.parse_args();source=Path(args.source).resolve();output=Path(args.output).resolve()
    if not output.is_relative_to(ROOT):raise ValueError('OUTPUT_OUTSIDE_WORKSPACE')
    started=time.perf_counter()
    if args.stage=='geometry':result=geometry_stage(source,output)
    elif args.stage=='detail':result=detail_stage(output)
    elif args.stage=='raster':result=raster_stage(output)
    else:result=validate_stage(source,output)
    result['elapsed_seconds']=time.perf_counter()-started
    write(output/(args.stage+'-receipt.json'),result)
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':
    main()
