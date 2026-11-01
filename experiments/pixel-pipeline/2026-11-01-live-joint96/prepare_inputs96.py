"""One-time immutable topology/registration and frozen oracle fixtures.

The runtime class builds/refits the same BVH and performs all queries/selection
on GPU. These files are validation inputs, never the per-frame runtime producer.
"""
from pathlib import Path
import json,struct,sys
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OLD=ROOT/'final-eye95'
sys.path.insert(0,str(ROOT/'native-feature89'));from analyse89 import packet,geometry,mesh,REST,PARTS,PROJ
sys.path.insert(0,str(ROOT/'apply-capture66'));from analyse_capture68 import camera

def string(f,s):
    b=s.encode();n=len(b)
    while n>=128:f.write(bytes([(n&127)|128]));n>>=7
    f.write(bytes([n]));f.write(b)
def main():
    out=HERE/'fixtures';out.mkdir(exist_ok=False);state=json.loads((OLD/'capture-scale-correct/STATE95B-0018-finished.json').read_text());proofs=json.loads((OLD/'VISIBILITY_PROOF95-source-cache-audit.json').read_text());pr={}
    for p in proofs:pr.setdefault(p['frame'],[]).append(p)
    topology=None;rows=[]
    for e in state['sequencePackets']:
        d=packet(Path(e['output']));m=d['m'];layers,physical,_=geometry(d);h,w=layers[0][0].shape[:2];positions=[];uvs=[];rests=[];tris=[];faceparts=[[]for _ in PARTS];materials=[];centres=np.asarray(m['eyeFeature']['centres']);owners=centres[np.argmin(((REST[:,None]-centres[None,:,:3])**2).sum(2),axis=1),3]
        for slot,name in [(0,'source-evaluated-0.mesh'),(1,'eye-evaluated.mesh'),(2,'source-evaluated-2.mesh')]:
            v,n,uv,indices,world=mesh(d['path']/name);start=len(positions);wp=np.c_[v,np.ones(len(v))]@world.T;positions.extend(wp);uvs.extend(uv);rests.extend(np.c_[REST,np.ones(len(v))]if slot==1 else np.zeros((len(v),4)))
            for sm,ix in enumerate(indices):
                mi=len(materials);materials.append([slot,sm])
                for primitive,vi in enumerate(ix):
                    ti=len(tris);tris.append((list(vi+start)+[mi],[slot,sm,primitive+1,0],list(owners[vi])+[0]if slot==1 else [0,0,0,0]))
                    if slot==1 and sm in PARTS:faceparts[PARTS.index(sm)].append(ti)
        stride=max(map(len,faceparts));mapping=np.full((4,stride),-1,'<i4')
        for p,x in enumerate(faceparts):mapping[p,:len(x)]=x
        static=b''.join(np.asarray(x,dtype).tobytes()for tri in tris for x,dtype in zip(tri,['<i4','<i4','<f4']))+np.asarray(uvs,'<f4').tobytes()+np.asarray(rests,'<f4').tobytes()+mapping.tobytes()
        if topology is None:
            topology=static
            with(out/'static96.bin').open('xb')as f:
                string(f,'whole-eye96-static/v1');f.write(struct.pack('<4i',len(positions),len(tris),len(materials),stride));f.write(np.asarray(materials,'<i4').tobytes());f.write(static)
            (out/'STATIC96.json').write_text(json.dumps({'vertices':len(positions),'triangles':len(tris),'materials':materials,'partPrimitiveStride':stride,'registry':{str(k):PROJ[k].tolist()for k in PROJ},'eyeIds':sorted(PROJ),'sourceTopologySHA256':m['eyeFeature']['topologySHA256']},indent=2)+'\n')
        else:assert topology==static,'Static topology/source registration changed across states'
        raw=np.asarray(layers,'<f4');direct=np.zeros((4,h,w,4),'<f4');direct[...,:2]=physical;direct[...,2]=raw[:,1,...,0];direct[...,3]=raw[:,1,...,2];expected=np.zeros((4,h,w,4),'<f4');expected[...,3]=-1
        for p in pr[e['frame']]:
            part=PARTS.index(p['part']);x,y=p['sample'];expected[part,y,x,:2]=np.asarray(p['visibility'])*raw[part,0,y,x,3];expected[part,y,x,2]=raw[part,1,y,x,0];expected[part,y,x,3]=1
        cam=camera(d['path']/'source.camera')
        with(out/f'frame{e["frame"]}.bin').open('xb')as f:
            string(f,'whole-eye96-frame/v1');string(f,m['sourceId']);f.write(struct.pack('<4i',e['frame'],e['serial'],w,h));f.write(cam['view'].astype('<f4').tobytes(order='F'));f.write(cam['projection'].astype('<f4').tobytes(order='F'));f.write(np.asarray(positions,'<f4').tobytes());f.write(raw.tobytes());f.write(direct.tobytes())
        z=np.load(OLD/f'candidate-source-cache-audit/frame{e["frame"]}.npz');np.savez_compressed(out/f'oracle{e["frame"]}.npz',visibility=expected,canonicalColour=z['canonicalColour'],canonicalIdentity=z['canonicalIdentity'],canonicalUnknown=z['canonicalUnknown'])
        rows.append({'frame':e['frame'],'sourceId':m['sourceId'],'serial':e['serial'],'width':w,'height':h,'expectedQueries':int((expected[...,3]>0).sum()),'Close':m['motion82']['getterClose']})
    (out/'FRAMES96.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
if __name__=='__main__':main()
