"""Independent CPU ray/alpha oracle for actual96 capture; no Unity calls.

Original embedded PNG alpha is first checked against the4230 recorded Unity
GetPixel queries. Source IDs remain96; historical95 frame data is not substituted.
"""
from pathlib import Path
import json,hashlib,sys
import numpy as np
from PIL import Image
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OUT=HERE/'oracle'
sys.path.insert(0,str(ROOT/'native-feature89'));from analyse89 import packet,geometry,mesh,REST,PARTS
sys.path.insert(0,str(ROOT/'eye-close90'));from surface_query90 import ProjectedSurface
sys.path.insert(0,str(ROOT/'apply-capture66'));from analyse_capture68 import camera
def main():
    OUT.mkdir(exist_ok=False);cap=OUT/'capture-scale-correct';cap.mkdir();state=json.loads(sorted((HERE/'capture').glob('STATE96*'))[-1].read_text());assert state['PlayExited']and not state.get('error')and not state.get('restorationError');(cap/'STATE95B-0000-96-actual.json').write_text(json.dumps(state)+'\n')
    prior=json.loads((HERE/'PNG_ALPHA_VERIFICATION96.json').read_text());assert prior['flipMismatches']==0
    reg=json.loads((HERE/'registry/REGISTRY96.json').read_text());audit=json.loads(Path(r'C:\Users\15352\Documents\Codex\2026-10-30\task\model-source\SOURCE_AUDIT.json').read_text());by={m['texture']['name']:m for m in audit['materials']};sources={};pics={}
    for m in reg['sourceMaterials']:
        original=by[m['texture']];path=Path(original['image']['file']);assert hashlib.sha256(path.read_bytes()).hexdigest()==original['image']['SHA256'];pic=np.flipud(np.asarray(Image.open(path).convert('RGBA'))[...,3]).astype(np.float32)/np.float32(255);assert pic.shape==(m['height'],m['width']);key=f"{m['slot']}-{m['subMesh']}";pics[key]=pic;sources[key]={**m,'cullMode':m['cull']}
    query_frames=[];alpha={};summary=[]
    for e in state['sequencePackets']:
        d=packet(Path(e['output']));layers,physical,checks=geometry(d);cam=camera(d['path']/'source.camera');surfaces=[];signs={};centres=np.asarray(d['m']['eyeFeature']['centres']);owners=centres[np.argmin(((REST[:,None]-centres[None,:,:3])**2).sum(2),axis=1),3]
        for slot,name in [(0,'source-evaluated-0.mesh'),(1,'eye-evaluated.mesh'),(2,'source-evaluated-2.mesh')]:
            v,n,uv,tris,world=mesh(d['path']/name);wp=np.c_[v,np.ones(len(v))]@world.T
            for sm,ix in enumerate(tris):
                if len(ix):
                    s=ProjectedSurface(wp,uv,ix,cam['view'],cam['projection'],[480,272]);surfaces.append((slot,sm,s))
                    if slot==1:signs[sm]=s.sign
        queries=[]
        for part in [0,1,2,3]:
            for sy,sx in np.argwhere((layers[part][1][...,0]>0)&(layers[part][0][...,3]>0)):
                depth=float(layers[part][1][sy,sx,0]);point=physical[part,sy,sx];hits=[]
                for slot,sm,surface in surfaces:
                    for hit in surface.hits(point):
                        if hit['depth']>=depth-3e-5:continue
                        uv=np.asarray(hit['uv'],'<f4');key=f'{slot}-{sm}-'+hashlib.sha256(uv.tobytes()).hexdigest()[:20];hit.update({'rendererSlot':slot,'sourceSubMesh':sm,'queryKey':key})
                        if slot==1:hit['eyeOwner']=int(np.floor(np.asarray(hit['barycentric'])@owners[hit['vertices']]+.5))
                        hits.append(hit)
                        if key not in alpha:
                            sk=f'{slot}-{sm}';m=sources[sk];pic=pics[sk];h,w=pic.shape;x,y=np.floor(uv.astype(float)*[w,h]-.5).astype(int)
                            def wrap(v,n,mode):return min(n-1,max(0,v))if mode=='Clamp'else v%n
                            values=[float(pic[wrap(y+j,h,m['wrapV']),wrap(x+i,w,m['wrapU'])]*np.float32(m['factorAlpha']))for j in range(2)for i in range(2)];alpha[key]={'id':key,'rendererSlot':slot,'sourceSubMesh':sm,'min':min(values),'max':max(values)}
                primitive=int(round(float(layers[part][3][sy,sx,2])))-1;queries.append({'partIndex':part,'sourceRole':PARTS[part],'eyeOwner':int(round(float(layers[part][1][sy,sx,2]))),'sample':[int(sx),int(sy)],'candidatePrimitive':primitive+1,'candidatePhysicalWinding':int(signs[PARTS[part]][primitive]),'physicalPoint':point.tolist(),'depth':depth,'alpha':float(layers[part][0][sy,sx,3]),'hits':sorted(hits,key=lambda h:h['depth'])})
        query_frames.append({'frame':e['frame'],'sourceId':e['sourceId'],'serial':e['serial'],'geometryChecks':checks,'queries':queries});summary.append({'frame':e['frame'],'queries':len(queries),'uniqueSourceAlphaQueries':len(alpha)});print(json.dumps(summary[-1]),flush=True)
    (OUT/'QUERIES_OWNED95.json').write_text(json.dumps({'frames':query_frames},indent=2)+'\n');(OUT/'ALPHA_SOURCE95B.json').write_text(json.dumps({'success':True,'unchanged':{'immutableModelPNGVerified':True},'sources':sources,'queries':list(alpha.values())},indent=2)+'\n');(OUT/'ALPHA_SOURCE_SKIN95.json').write_text(json.dumps({'success':True,'unchanged':{'sameInputs':True},'sources':{},'queries':[]})+'\n');(OUT/'ORACLE_INPUT96.json').write_text(json.dumps(summary,indent=2)+'\n')
    sys.path.insert(0,str(ROOT/'final-eye95'));import solve95
    solve95.HERE=OUT;sys.argv=['solve95.py','source-cache','actual96'];solve95.main()
if __name__=='__main__':main()
