from pathlib import Path
import json,struct,subprocess,os,numpy as np
from PIL import Image
from actor_visibility96 import ActorQuery
from review_packed93 import ribbon
from native_width86 import green_repeat_bilinear
H=Path(__file__).resolve().parent;G=H/'face97'

def main():
 root=H/'face96/geometry64';report=json.loads((root/'capture/COMPLETE.json').read_text());frames=[f for f in report['stream77']['frames']if'actorSource96'in f];(G/'fixture').mkdir(parents=True,exist_ok=True);query=ActorQuery(root,frames[0]);materials=query.spec['materials'];keys={(m['renderer'],m['submesh']):i for i,m in enumerate(materials)}
 with(G/'fixture/materials97.bin').open('wb')as b:
  b.write(struct.pack('<ii',9701,len(materials)))
  for m in materials:
   unknown=query.spec['alphaTestGlobal']or query.spec['alphaBlendGlobal']or any(v!=0 for v in m['scroll']);b.write(struct.pack('<4i6di',int(m['cull']),int(m['alphaTest']),int(m['alphaBlend']),int(unknown),m['color'][3],m['cutoff'],*m['scale'],*m['offset'],m['texture']))
  b.write(struct.pack('<i',len(query.tex)))
  for t in query.tex:
   assert t['mipCount']==1;data=query.alpha[t['index']].tobytes();wrap={'Repeat':0,'Clamp':1,'Mirror':2};b.write(struct.pack('<6i',t['width'],t['height'],int(t['filter']!='Point'),wrap[t['wrapU']],wrap[t['wrapV']],len(data)));b.write(data)
 texture=np.asarray(Image.open(H/'face40/analysis-directed/SOURCE_WIDTH_MASK40.png').convert('RGBA'));paths=[]
 for f in frames:
  query=ActorQuery(root,f);_,_,width,mapped,anchors,vp,view,data=ribbon(root/'capture'/f['ribbon93']['file']);w=f['QROI'][2];origin=np.array([f['QROI'][0],272-f['QROI'][1]-w]);shift=np.array([anchors[2]-anchors[0],-(anchors[3]-anchors[1])]);path=G/f'fixture/frame{f["frame"]}.bin'
  with path.open('wb')as b:
   b.write(struct.pack('<ii2di2di',9702,f['frame'],*origin,w,*shift,sum(len(r['xy'])for r in query.rows)))
   for r in query.rows:
    mat=keys[r['renderer'],r['submesh']]
    for xy,z,uv in zip(r['xy'],r['z'],r['uv']):b.write(struct.pack('<i15d',mat,*xy.ravel(),*z,*uv.ravel()))
   b.write(struct.pack('<i',len(data)))
   for r in data:
    ends=np.stack([r[3:6],r[6:9]]).astype(float);norm=np.stack([r[9:12],r[12:15]]).astype(float);green=green_repeat_bilinear(texture,r[15:19].reshape(2,2),False)if mapped else np.ones(2);points=np.r_[ends,ends+norm*(width*green)[:,None]];q=np.c_[points,np.ones(4)]@vp.astype(float).T;xy=(q[:,:2]/q[:,3,None]*[1,-1]+1)*w*.5+origin+shift;z=-(np.c_[points,np.ones(4)]@view.astype(float).T)[:,2];b.write(struct.pack('<i12d',int(r[0]),*np.column_stack([xy,z]).ravel()))
  paths.append(path)
 csc=Path(os.environ['WINDIR'])/'Microsoft.NET/Framework64/v4.0.30319/csc.exe';exe=G/'build/JointLineFixture97.exe';r=subprocess.run([str(csc),'/nologo','/utf8output','/optimize+','/out:'+str(exe),str(H/'JointLine97.cs'),str(H/'JointLineFixture97.cs')],capture_output=True,text=True,encoding='utf-8');assert r.returncode==0,r.stdout+r.stderr;rows=[]
 for p in paths:
  output=p.with_suffix('.out97');r=subprocess.run([str(exe),str(G/'fixture/materials97.bin'),str(p),str(output)],capture_output=True,text=True);assert r.returncode==0,r.stdout+r.stderr;print(r.stdout,flush=True);raw=output.read_bytes();magic,frame,w,queries,visits,entries,fragments,cpu=struct.unpack_from('<7id',raw);assert magic==9703;pixels=np.frombuffer(raw,offset=36,dtype=np.dtype([('state','<i4'),('edge','<i4'),('values','<f8',(6,))])).reshape(w,w);assert np.isfinite(pixels['values']).all();rows.append({'frame':frame,'queries':queries,'visits':visits,'indexEntries':entries,'sourceFragments':fragments,'CPUWithFileReadAndAllocationMs':cpu,'visible':int((pixels['state']==1).sum()),'covered':int((pixels['state']==2).sum()),'unknown':int((pixels['state']==3).sum()),'output':str(output.relative_to(H))})
 (G/'CPU_FIXTURE97.json').write_text(json.dumps({'CPUOnly':True,'actualInputFrames':4,'samePointJointSourceAndDestination':True,'fullOpacityOrWorldCoverageSolved':False,'rows':rows},indent=2))
if __name__=='__main__':main()
