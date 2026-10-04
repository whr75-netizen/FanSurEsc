"""N16 semantic solids -> intrinsic material labels -> native caches.

Production never resizes a beauty image. See PerfectPixelUniform/BUILDING16.md.
Each phase is a WorkLoop command; Unity observation is a separate integration gate.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT/'Tools/PerfectPixelUniform'))
from native14_materials import Appearance, _palette

def read(p): return json.loads(Path(p).read_text(encoding='utf-8'))
def write(p, v):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(v, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def inputs():
    contract = read(ROOT/'Tools/Building37/input-contract.json')
    placement = read(ROOT/'docs/artifacts/building38/placement-baseline.json')
    return contract, placement

def geometry(out):
    from geometry16 import build_asset, build_box
    contract, placement = inputs(); catalog=[]
    for asset in contract['assets']:
        data=build_asset(asset, ppu=31.75)
        save_geometry(out, asset['id'], data, catalog)
    for row in placement['rows']:
        if 'Structure - closed volumes/' not in row['path'] and 'Cutaway bases/' not in row['path']: continue
        name=row['path'].split('/')[-2]
        if name == 'Floor': continue  # approved floor geometry, UV and source remain intact
        dimensions=np.asarray(row['colliderSize'], dtype=float)
        ident='structure_'+''.join(c if c.isalnum() else '_' for c in name)
        data=build_box(ident, [-dimensions/2, dimensions/2], ppu=31.75, material=2)
        save_geometry(out, ident, data, catalog, row['path'])
    write(out/'geometry-catalog.json', catalog)

def save_geometry(out, ident, data, catalog, path=None):
    folder=out/ident; folder.mkdir(parents=True, exist_ok=True)
    arrays={k:v for k,v in data.items() if isinstance(v,np.ndarray)}
    np.savez_compressed(folder/'geometry.npz', **arrays)
    meta={k:v for k,v in data.items() if not isinstance(v,np.ndarray)}
    # Geometry metadata may contain NumPy scalar values: serialize explicitly.
    meta=json.loads(json.dumps(meta, default=lambda x: x.tolist() if hasattr(x,'tolist') else str(x)))
    write(folder/'geometry.json', meta)
    vertices=data['mesh_vertices'].tolist(); triangles=data['mesh_triangles'].reshape(-1).tolist()
    write(folder/'mesh.json', {'vertices':vertices,'triangles':triangles})
    h,w=data['mask'].shape
    catalog.append({'id':ident,'width':w,'height':h,'origin':list(map(int,data['origin'])),
                    'ppu':31.75,'structurePath':path or '', 'bounds':np.asarray(data['bounds']).tolist(),
                    'metadata':meta})

def load(out, item):
    with np.load(out/item['id']/'geometry.npz') as z: return {k:z[k] for k in z.files}

def materials(out):
    reference=ROOT/'docs/artifacts/building37/NativeObject14/appearance-reference.png'
    settings=read(ROOT/'Tools/PerfectPixelUniform/native15_recipe.json')
    appearance=Appearance(reference, settings['materials'])
    palettes=np.zeros((10,4,3),np.uint8)
    for row,name in enumerate(['wood','navy','brass']):
        colors=appearance.palettes[name]
        indices=np.floor(np.linspace(0,len(colors)-1,4)+.5).astype(int)
        palettes[row]=colors[indices]
    sheet=ROOT/'Tools/Building37/Source/sheet.png'
    rgba=np.asarray(Image.open(sheet).convert('RGBA')); rgb=rgba[...,:3].astype(float)
    visible=(rgba[...,3]>127)&(rgb.max(-1)>20)
    r,g,b=np.moveaxis(rgb,-1,0); hi=rgb.max(-1); lo=rgb.min(-1)
    yy,xx=np.indices(visible.shape)
    paper_area=(yy>=818)&(xx>=294)&(xx<631)
    apple_area=(yy>=425)&(yy<818)&(xx>=1133)&(xx<1267)
    selectors=[visible&paper_area&(hi-lo<48)&(hi>120), visible&(g>r*1.08)&(g>b*1.08),
        visible&apple_area&(r>g*1.5)&(r>b*1.5)&(r>70),
        visible&(b>r*1.05)&(g>r*.9),
        visible&(r>g*1.15)&(g>b*1.1),visible&(hi-lo<40)&(hi>55)&(hi<170),
        visible&(r>g*1.05)&(g>b*1.05)&(hi>95)]
    provenance=[]
    for index, selection in enumerate(selectors,3):
        colors,_,report=_palette(rgba[...,:3][selection],4)
        palettes[index]=colors; provenance.append({'material':index+1,**report})
    Image.fromarray(palettes,'RGB').save(out/'palette.png')
    write(out/'palette-provenance.json',{'wood_reference':appearance.report(),
        'source_sheet_sha256':sha(sheet),'role_palettes':provenance,
        'pure_albedo_recovery_claimed':False,'spatial_lighting_rgb_copied':False})
    for item in read(out/'geometry-catalog.json'):
        data=load(out,item); mask=data['mask']; ids=data['material'].astype(np.uint8).copy()
        semantic_details(item,data,ids)
        position=data['position']; normal=data['normal']; rank=np.full(mask.shape,2,np.uint8)
        wood=mask&(ids==1)
        if wood.any():
            p=position[wood]; n=normal[wood]
            u=np.mod(np.where(abs(n[:,0])>.7,p[:,2],p[:,0])+1.04,2.08)/2.08
            v=np.mod(np.where(abs(n[:,1])>.7,p[:,2],p[:,1]),.7)/.7
            samples=appearance.sample('wood',u,v)
            rank[wood]=np.argmin(np.sum((samples[:,None,:].astype(float)-palettes[0][None,:,:])**2,axis=-1),axis=1)
        packed=np.stack([ids,rank,data['edge'].astype(np.uint8),mask.astype(np.uint8)*255],-1)
        packed[~mask]=0
        Image.fromarray(packed,'RGBA').save(out/item['id']/'material.png')
    write(out/'material-receipt.json',{'material_labels':10,'observed_rgb_only':True,
        'beauty_resized':False,'source_sha256':sha(sheet),'reference_sha256':sha(reference)})

def semantic_details(item,data,ids):
    """Source-declared flush inlays/clock hands/paper ink, inside geometry only.

    Surface-space intervals and pixel-width strokes do not expand the silhouette.
    These are material design features, not automatic reconstruction from RGB.
    """
    ident=item['id'];mask=data['mask'];p=data['position'];n=data['normal'];x,y,z=np.moveaxis(p,-1,0)
    if ident in ['empty_counter','island_body_template','utility_bench','cleaning_cabinet']:
        contract,_=inputs();definition=next(a for a in contract['assets'] if a['id']==ident)
        width,height,depth=definition['size_xyz_m'];facing=definition['facing']
        coordinate=z if facing=='-X' else x;span=depth if facing=='-X' else width
        front=(n[...,0]<-.9) if facing=='-X' else ((n[...,2]>.9) if facing=='+Z' else (n[...,2]<-.9))
        count=3 if ident=='empty_counter' else (2 if ident=='island_body_template' else 1)
        pitch=span/count;phase=np.mod(coordinate+span/2,pitch)
        line=.55/31.75;inset=max(.06,1.5/31.75)
        bottom=.13;top=height-.16
        panel=((abs(phase-inset)<line)|(abs(phase-(pitch-inset))<line))&(y>bottom)&(y<top)
        panel|=((abs(y-bottom)<line)|(abs(y-top)<line))&(phase>inset)&(phase<pitch-inset)
        ids[mask&front&panel&(ids==2)]=3
    if ident=='detail_clock':
        # Flat face has a real circular geometry; ink is contained in that face.
        width,height,_=next(a['size_xyz_m'] for a in inputs()[0]['assets'] if a['id']==ident)
        dx=x;dy=y-height/2;radius=min(width,height)/2
        hands=((abs(dx)<.5/31.75)&(dy>-.04)&(dy<radius*.63))
        hands|=((abs(dy+dx*.5)<.6/31.75)&(dx>0)&(dx<radius*.53))
        angle=np.arctan2(dy,dx);ring=(np.hypot(dx,dy)>radius*.72)&(np.hypot(dx,dy)<radius*.86)
        ticks=ring&(abs(np.sin(angle*6))<.28)
        ids[mask&(ids==4)&(hands|ticks)]=2
    if ident=='detail_poster':
        height=.48;stem=mask&(ids==4)&(abs(z)<.45/31.75)&(y>.07)&(y<height-.07)
        leaves=np.zeros(mask.shape,bool)
        for center,side in [(.15,1),(.23,-1),(.31,1),(.38,-1)]:
            leaves|=((z-side*.045)/.045)**2+((y-center)/.025)**2<1
        ids[stem|(mask&(ids==4)&leaves)]=5
    if ident=='detail_ledger':
        ids[mask&(abs(n[...,1])>.9)&(abs(x)>.017)]=4

def export(out):
    palette=np.asarray(Image.open(out/'palette.png').convert('RGB'))
    catalog=read(out/'geometry-catalog.json'); entries=[]; pictures=[]
    light=np.array([-.2,.84,-.5]);light/=np.linalg.norm(light)
    for item in catalog:
        ident=item['id']; data=load(out,item); mask=data['mask']
        for name in ['position','normal']:
            values=np.concatenate([data[name].astype(np.float32),mask[...,None].astype(np.float32)],-1)
            values[~mask]=0; values.astype('<f4').tofile(out/ident/(name+'.f32'))
        material=np.asarray(Image.open(out/ident/'material.png'))
        lambert=np.maximum(np.sum(data['normal']*light,axis=-1),0)
        band=np.minimum((np.clip(.2+.8*lambert,0,.999)*4).astype(int),3)
        wood=material[...,0]==1
        index=np.where(wood,np.clip(material[...,1].astype(int)+band-2,0,3),band)
        color=palette[np.maximum(material[...,0].astype(int)-1,0),index].copy()
        edge=material[...,2];color[(edge==1)|(edge==2)]=[6,9,13]
        crease=edge==3
        color[crease]=palette[np.maximum(material[...,0][crease].astype(int)-1,0),np.maximum(index[crease]-1,0)]
        rgba=np.concatenate([color,mask[...,None].astype(np.uint8)*255],-1);rgba[~mask]=0
        Image.fromarray(rgba,'RGBA').save(out/ident/'preview.png')
        entries.append({**{k:v for k,v in item.items() if k!='metadata'},'bindingPath':item['structurePath'],
            **{name+'File':ident+'/'+name+suffix for name,suffix in
               [('position','.f32'),('normal','.f32'),('material','.png'),('preview','.png'),('mesh','.json')]}})
        if not item['structurePath']: pictures.append((ident,rgba))
    # Atlas is packing only, source native pixels are pasted without resampling.
    cellw=max(p.shape[1] for _,p in pictures)+12;cellh=max(p.shape[0] for _,p in pictures)+18
    atlas=Image.new('RGBA',(cellw*6,cellh*3),(19,20,27,255))
    from PIL import ImageDraw
    draw=ImageDraw.Draw(atlas)
    for i,(name,p) in enumerate(pictures):
        x=(i%6)*cellw+6;y=(i//6)*cellh+6
        atlas.alpha_composite(Image.fromarray(p,'RGBA'),(x,y));draw.text((x,y+cellh-16),name,fill='white')
    atlas.save(out/'object-sheet-native.png')
    atlas.resize((atlas.width*4,atlas.height*4),Image.Resampling.NEAREST).save(out/'object-sheet-preview-x4.png')
    write(out/'manifest.json',{'schema':'N16.metric.native.cache.v1','paletteFile':'palette.png','assets':entries,
        'physical_pixels_per_metre':31.75,'lighting_preview_only':True,'runtime_lighting_baked':False})

def validate(out):
    from geometry16 import R,U
    checks=[]
    for item in read(out/'geometry-catalog.json'):
        d=load(out,item);m=d['mask'];n=d['normal'][m];p=d['position'][m]
        h,w=m.shape; yy,xx=np.indices((h,w))
        projected=np.stack([p@R,-p@U],-1)*31.75
        expected=np.stack([xx[m]+.5+item['origin'][0],yy[m]+.5+item['origin'][1]],-1)
        roundtrip=float(np.max(abs(projected-expected)))
        normal_error=float(np.max(abs(np.linalg.norm(n,axis=-1)-1)))
        png=np.asarray(Image.open(out/item['id']/'material.png'))
        minimum=np.asarray(item['bounds'][0]);maximum=np.asarray(item['bounds'][1])
        inside=bool(np.all(p>=minimum-1e-5)&np.all(p<=maximum+1e-5))
        ok=bool(roundtrip<1e-4 and normal_error<1e-5 and inside and
                np.array_equal(png[...,3]>0,m) and np.all(png[...,0][m]>=1) and np.all(png[...,0][m]<=10))
        checks.append({'asset':item['id'],'success':ok,'roundtrip_pixel_error':roundtrip,
            'unit_normal_error':normal_error,'inside_declared_bounds':inside,
            'native_size':[w,h],'covered_pixels':int(m.sum()),
            'parts_visible':int(len(np.unique(d['part'][m]))),'edge_pixels':int(np.count_nonzero(d['edge']))})
    objects=sum(not i['structurePath'] for i in read(out/'geometry-catalog.json'))
    result={'success':all(x['success'] for x in checks) and objects==18,'object_types':objects,
        'asset_checks':checks,'production_resize_count':0,'artistic_perfection_claimed':False,
        'unity_integration_observed':False}
    write(out/'cpu-validation.json',result)
    if not result['success']: raise ValueError('Native geometry/material contract failed; see cpu-validation.json')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['geometry','materials','export','validate'])
    parser.add_argument('--output',required=True);args=parser.parse_args()
    out=Path(args.output).resolve()
    if not out.is_relative_to(ROOT): raise ValueError('Output must stay inside workspace')
    out.mkdir(parents=True,exist_ok=True);globals()[args.phase](out)
    print(json.dumps({'phase':args.phase,'output':str(out)}))
