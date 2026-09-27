"""Template-owned furniture dimensions plus explicitly flat decorative sprite layers."""
import json, math
from pathlib import Path
import numpy as np
from PIL import Image
from project_faces import project,R

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/artifacts/building35'
data=json.loads((OUT/'native/furniture-corners.json').read_text(encoding='utf-8-sig'))

def box_vertices(w,d,h):
    return {'top_back':[w/2,h,d/2],'top_left':[-w/2,h,d/2],'top_right':[w/2,h,-d/2],
            'top_near':[-w/2,h,-d/2],'bottom_left':[-w/2,0,d/2],
            'bottom_right':[w/2,0,-d/2],'bottom_near':[-w/2,0,-d/2]}

def furniture(source_id,output_id,w,d,h,reflect=False):
    a=next(x for x in data['assets'] if x['id']==source_id);v=box_vertices(w,d,h)
    if reflect:
        # Symmetric end-panel reuse is explicit; it is not recovery of an unseen opposite side.
        v['top_left'],v['top_right']=v['top_right'],v['top_left']
        v['bottom_left'],v['bottom_right']=v['bottom_right'],v['bottom_left']
    spec={'id':output_id,'source':a['native_path'],'ppu':127,'preserve_outline':True,
          'ground_from_source_outline':True,
          'faces':[{'id':key,'source_xy':[a['corners'][k] for k in names],'xyz':[v[k] for k in names]}
                   for key,names in data['face_shared_vertices'].items()],
          'limitations':['Painted fixed-view planes; source corner annotation uncertainty 1-2 texels.',
                         'Symmetric side-panel appearance reused for the required visible end.' if reflect else 'Source visible face correspondence retained.']}
    project(spec,OUT/'projected-new'/output_id)

furniture('counter','empty_counter',2.4,.8,1)
furniture('counter','island_body_template',1.6,1.2,.65)
furniture('fridge','fridge',1.55,.65,1.9,True)
furniture('utility','utility_bench',1.3,.55,.9)
furniture('cleaning','cleaning_cabinet',.6,.6,1.65)

props=json.loads((OUT/'prop-landmarks.json').read_text(encoding='utf-8-sig'))
crate=next(a for a in props['assets'] if a['id']=='crate');v=box_vertices(.5,.4,.35)
v['top_front']=v['top_near'];v['bottom_front']=v['bottom_near']
project({'id':'crate','source':crate['native_path'],'ppu':127,'preserve_outline':True,'ground_from_source_outline':True,
         'faces':[{'id':key,'source_xy':[crate['points'][k] for k in names],'xyz':[v[k] for k in names]} for key,names in crate['faces'].items()],
         'limitations':['Source sample relocation follows the physical crate template; output is not claimed lossless.']},OUT/'projected-new/crate')

def flat_prop(source_id,output_id,height):
    path=f'docs/artifacts/building35/native/{source_id}/native.png'
    a=np.array(Image.open(ROOT/path)); y,x=np.where(a[...,3]>=128)
    left,top,right,bottom=int(x.min())-.5,int(y.min())-.5,int(x.max())+.5,int(y.max())+.5
    width=(right-left)/(bottom-top)*height*math.sqrt(.75)
    # Vertical camera-facing 2D plane: output image sampling remains isotropic in screen coordinates.
    origin=R*(-width/2); along=R*width
    xyz=[origin+np.array([0,height,0]),origin+along+np.array([0,height,0]),origin+along,origin]
    project({'id':output_id,'source':path,'ppu':127,'preserve_outline':False,
             'faces':[{'id':'upright_2d_sprite','source_xy':[[left,top],[right,top],[right,bottom],[left,bottom]],'xyz':[p.tolist() for p in xyz]}],
             'limitations':['Explicit upright 2D sprite with a shared foot anchor, not reconstructed 3D planes.',
                            'Generated guide establishes the painted view. Organic/detail shapes retain their source aspect; no mathematical internal-angle guarantee.',
                            'Height is the declared 2D presentation extent. Collider footprint is a conservative role-plan proxy.']},OUT/'projected-new'/output_id)

flat_prop('plant','plant',1.0)
flat_prop('barrel','barrel',.65)
flat_prop('register','register',.42)
flat_prop('produce','appletray',.25)

assets=[]
for folder in [OUT/'projected-grounded',OUT/'projected-new']:
    for receipt in sorted(folder.glob('*/receipt.json')):
        r=json.loads(receipt.read_text())
        assets.append({'id':r['id'],'folder':receipt.parent.relative_to(ROOT).as_posix(),'receipt':receipt.relative_to(ROOT).as_posix()})
(OUT/'production-manifest.json').write_text(json.dumps({'assets':assets},indent=2),encoding='utf8')
