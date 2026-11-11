"""WITHDRAWN hypothesis: material provenance does not locate native geometry.
Use verify_native_proof.py and actual PIGMENT bindings instead. No runtime
change was made from the failed UV-barycentric assumption below.
"""
from pathlib import Path
import hashlib,io,json,struct,sys
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;R=H.parents[2]
sys.path.insert(0,str(R/'resume-20261111'))
from replay_phase25 import FaceWithOneOriginalAlpha,NativeAlpha,geometry,read
def source_kind():
 f=io.BytesIO((R/'bounded-form115/runtime24/GEOMETRY_BINDINGS24.bin').read_bytes())
 def string():
  n=shift=0
  while True:
   x=f.read(1)[0];n|=(x&127)<<shift
   if x<128:break
   shift+=7
  return f.read(n).decode()
 def integer():return struct.unpack('<i',f.read(4))[0]
 assert string()=='geometry-bindings24/v1';topology=string();texture=string();n=integer()
 for _ in range(n):integer();count=integer();f.read(count*4)
 count=integer();a=np.frombuffer(f.read(count*32),dtype=np.dtype([('uv','<f4',(4,)),('source','<i4',(4,))]));kind=np.unique(a['source'][:,1:],axis=0)
 assert len(kind)==1 and not f.read();part,submesh,renderer=map(int,kind[0]);return part,submesh,renderer
def main():
 part,submesh,renderer=source_kind()
 src=next(v for v in read(R/'aperture-runtime111/inputs/ALPHA111.json')['images']if v['renderer']==1 and v['submesh']==3)
 p=R/'aperture-runtime111/inputs'/src['file'];assert hashlib.sha256(p.read_bytes()).hexdigest()==src['sha256'];im=Image.open(p);image=np.asarray(im.convert('RGBA'))[:,:,3].astype(float)/255;im.close()
 base=read(R/'argon23-runtime113/SOURCE113.json')['ownSkinMask'];rows=[]
 for result,folder in [('GPU_GATE26.json','phase-run'),('GPU_MOTION26.json','motion-run')]:
  d=read(H/result);st=read(next((H/'gate-alpha'/folder).glob('STATE113-*-finished.json')));pack={v['sourceId']:Path(v['output'])for v in st['sequencePackets']}
  for row in d['sourceCertificateRows']:
   if 'columnWitness'not in row:continue
   p=pack[row['sourceId']];m=read(p/'RAW_MANIFEST.json');c=geometry(p,m);raw=(p/'SOURCE-columns26.f32').read_bytes();col=np.frombuffer(raw,dtype='<f4',offset=8).reshape(-1,3,4)[row['columnWitness']]
   primitive=int(round(float(col[1,2])));ti=int(c['partMap'][part,primitive-1]);assert list(c['sources'][ti,:3])==[renderer,submesh,primitive]
   vi=c['triangles'][ti,:3];uv=c['uv'][vi];point=col[1,:2];ab=np.linalg.solve(np.stack([uv[1]-uv[0],uv[2]-uv[0]],axis=1),point-uv[0]);bary=np.r_[1-ab.sum(),ab];assert bary.min()>=-1e-7
   world=bary@c['world4'][vi];view=c['view']@world;clip=c['projection']@view;xy=np.array([(clip[0]/clip[3]*.5+.5)*480,(.5-clip[1]/clip[3]*.5)*272]);z=-view[2]
   mi=np.unique(c['triangles'][(c['sources'][:,0]==1)&(c['sources'][:,1]==3),3]);a=NativeAlpha.__new__(NativeAlpha);a.ctx=c;a.images={int(mi[0]):image};a.sources={int(mi[0]):src};face=FaceWithOneOriginalAlpha(c,np.zeros(len(base),np.uint32),a)
   proof=face.query([xy],[z],row['owner'],limit=m['runtime24']['socketDiameters'][row['owner']-1])[0]
   det=np.linalg.det(np.stack([c['physicalXY'][vi[1]]-c['physicalXY'][vi[0]],c['physicalXY'][vi[2]]-c['physicalXY'][vi[0]]],axis=1));cull=int(c['materials'][c['triangles'][ti,3],1,2]);back=(cull==2 and det<0)or(cull==1 and det>0)
   trans=[0.,0.]if back else proof['faceInterval'];registered=np.array(m['forward102']['headHair25']['origin'])+col[0,:2]
   rows.append({'sourceId':row['sourceId'],'canonical':row['canonical'],'owner':row['owner'],'sourceKind':[part,submesh,renderer],'sourcePrimitive':primitive,'UV':point.tolist(),'barycentric':bary.tolist(),'nativeSourceXY':xy.tolist(),'nativeSourceDepth':float(z),'registeredColumnXY':registered.tolist(),'registeredMinusNativePx':(registered-xy).tolist(),'strictOriginalFaceVisibility':trans,'sourceBackface':bool(back),'originalHits':proof['hits']})
 out={'rows':rows,'CPUOnly':True,'noOwnSkinExemptionInOriginalRay':True,'sourceKindFromActualBinding':[part,submesh,renderer],
  'correctsEarlierAudit':'Earlier temporary audit incorrectly assumed part3/submesh6 from final role6. Binding actually uses part0/submesh3. No runtime change was based on that assumption.'}
 target=H/'CURVE_NATIVE_SOURCE_AUDIT26.json'
 if target.exists()and not(H/'CURVE_NATIVE_SOURCE_AUDIT26_WRONG_PART.json').exists():(H/'CURVE_NATIVE_SOURCE_AUDIT26_WRONG_PART.json').write_bytes(target.read_bytes())
 target.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps({'sourceKind':out['sourceKindFromActualBinding'],'rows':[{'sourceId':v['sourceId'],'errorPx':v['registeredMinusNativePx'],'nativeVisible':v['strictOriginalFaceVisibility']}for v in rows]}))
if __name__=='__main__':raise RuntimeError('Withdrawn material-to-geometry inference; use verify_native_proof.py')
