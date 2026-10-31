"""Freeze existing source surfaces/UV and reconstruct authored reference mapping.

No Unity, project writes, UI control, capture or commit.
"""
from pathlib import Path
import hashlib,json,re,struct
import numpy as np
R=Path(__file__).resolve().parent
P=Path('C:/Users/15352/Documents/work/Fantasy Survival Escape Game/Assets/EUnityValidation01')
B=R.parent/'eye-candidate49';L=R.parent/'lid-evidence51'
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dump(n,o):
    (R/n).write_text(json.dumps(o,ensure_ascii=False,indent=2,default=lambda v:v.tolist()if isinstance(v,np.ndarray)else v.item()),encoding='utf8')
expected={f['file']:f['sha256']for f in load(L/'INPUTS.json')['files']}
for row in load(L/'PALETTE_AND_CARRIER_PROVENANCE.json')['carriers']:
    expected[row['mesh']]=row['meshSHA256'];expected[row['palette']]=row['paletteSHA256']
def pin(p):
    p=Path(p);actual=sha(p)
    if str(p)in expected:assert actual==expected[str(p)],'Saved source changed; no live Editor assumptions: '+str(p)
    return p.read_text(encoding='utf8')
def mesh(p):
    s=pin(p);part=s[s.index('  m_VertexData:'):];n=int(re.search(r'm_VertexCount: (\d+)',part).group(1))
    channels=[tuple(map(int,q))for q in re.findall(r'- stream: (\d+)\n\s+offset: (\d+)\n\s+format: (\d+)\n\s+dimension: (\d+)',part.split('m_DataSize:')[0])]
    raw=bytes.fromhex(re.search(r'_typelessdata: ([0-9a-fA-F]+)',part).group(1));stride={}
    for st,off,fmt,dim in channels:
        if dim:stride[st]=max(stride.get(st,0),off+dim*4)
    starts={};at=0
    for st,step in sorted(stride.items()):starts[st]=at;at+=step*n
    assert at==len(raw),(p,at,len(raw))
    def attr(i):
        st,off,fmt,dim=channels[i];assert dim>0 and fmt==0
        return np.ndarray((n,dim),'<f4',buffer=raw,offset=starts[st]+off,strides=(stride[st],4)).copy()
    fmt=int(re.search(r'm_IndexFormat: (\d+)',s).group(1));size=4 if fmt else 2
    ix=np.frombuffer(bytes.fromhex(re.search(r'm_IndexBuffer: ([0-9a-fA-F]+)',s).group(1)),'<u4'if fmt else'<u2')
    subs=[(int(a),int(b))for a,b in re.findall(r'firstByte: (\d+)\n\s+indexCount: (\d+)',s[:s.index('  m_Shapes:')])]
    groups=[ix[a//size:a//size+b].astype(np.int32)for a,b in subs]
    return dict(vertices=attr(0),uv=attr(4)[:,:2].copy(),groups=groups,text=s)
face=mesh(P/'EyeContoursLayers202/Meshes/FaceSourceOwner202.asset')
bptext=face['text'][face['text'].index('  m_BindPose:'):face['text'].index('  m_BoneNameHashes:')]
q=re.findall(r'e(\d)(\d): ([^\n]+)',bptext);bp=np.zeros((len(q)//16,4,4),np.float32)
for n,(a,b,v)in enumerate(q):bp[n//16,int(a),int(b)]=float(v)
H=bp[18].astype(float);rest=(np.c_[face['vertices'],np.ones(len(face['vertices']))]@H.T)[:,:3]
bundle=load(L/'KEYFORM_BUNDLE51.json');inputs={};eyes=[]
# Use BOTH authored white planes to calibrate one common reference projection.
# A first draft incorrectly assumed the eye-bone order; reject that draft rather
# than accepting its approximately two-cell residual as an artistic tolerance.
whites=[];targets=[]
for index,eye_id in[(0,2),(1,1)]:
    w=mesh(P/f'EyeAuthoredSurface205/Meshes/Eye{index}_White.asset')
    f=next(f for f in bundle['eyes']if f['eye']==eye_id)
    whites.append(w['vertices'][:-1]);targets.append(f['parent'])
X=np.c_[np.vstack(whites),np.ones(48)];Y=np.vstack(targets)
M,_,rank,_=np.linalg.lstsq(X,Y,rcond=None)
projection_error=np.linalg.norm(X@M-Y,axis=1)
assert rank==4 and projection_error.max()<1e-4,('Authored reference mapping not exact',projection_error.max())
for index,eye_id in[(0,2),(1,1)]:
    form=next(f for f in bundle['eyes']if f['eye']==eye_id)
    white=mesh(P/f'EyeAuthoredSurface205/Meshes/Eye{index}_White.asset')
    iris=mesh(P/f'EyeAuthoredSurface205/Meshes/Eye{index}_IrisPupil.asset')
    wi=white['vertices'].astype(float)
    matches=[]
    for bone in[19,20]:
        transform=H@np.linalg.inv(bp[bone].astype(float))
        q=(np.c_[iris['vertices'],np.ones(len(iris['vertices']))]@transform.T)[:,:3]
        err=np.linalg.norm(np.c_[q[:-1],np.ones(16)]@M-form['iris'],axis=1)
        matches.append((float(err.max()),bone,q))
    matches.sort(key=lambda q:q[0]);iris_error,iris_bone,ii=matches[0]
    assert iris_error<.002 and matches[1][0]>1,('No unique original eye-bone correspondence',[(a,b)for a,b,_ in matches])
    error=np.linalg.norm(np.c_[np.vstack([wi[:-1],ii[:-1]]),np.ones(40)]@M-np.vstack([form['parent'],form['iris']]),axis=1)
    reference={}
    for name,data,xyz,targets in[('white',white,wi,form['parent']),('iris',iris,ii,form['iris'])]:
        prefix=f'eye{eye_id}_{name}';inputs[prefix+'_xyz']=xyz;inputs[prefix+'_uv']=data['uv'];inputs[prefix+'_tri']=data['groups'][0].reshape(-1,3)
        pal=P/f'EyeAuthoredSurface205/Palettes/Eye{index}_{"White"if name=="white"else"IrisPupil"}.asset';s=pin(pal)
        w=int(re.search(r'm_Width: (\d+)',s).group(1));h=int(re.search(r'm_Height: (\d+)',s).group(1))
        inputs[prefix+'_palette']=np.frombuffer(bytes.fromhex(re.search(r'_typelessdata: ([0-9a-fA-F]+)',s).group(1)),np.uint8).reshape(h,w,4)
        # Existing UVs encode the exact reference image coordinates. Retain that
        # independent source association; no nearest-colour attribution.
        U=np.c_[data['uv'][:-1],np.ones(len(targets))]
        UV,_,uv_rank,_=np.linalg.lstsq(U,targets,rcond=None)
        uv_error=np.linalg.norm(U@UV-targets,axis=1)
        assert uv_rank==3 and uv_error.max()<1e-4
        inputs[prefix+'_reference']=np.c_[data['uv'],np.ones(len(data['uv']))]@UV
        reference[name]=dict(vertices=len(xyz),triangles=len(data['groups'][0])//3,referencePolygon=targets,
            uvToReference=UV,maxUVFitError=float(uv_error.max()))
    eyes.append(dict(eye=eye_id,projection3DToReference=M,rank=int(rank),irisBoneIndex=iris_bone,
        alternativeBoneError=matches[1][0],maxReferenceFitError=float(error.max()),rmsReferenceFitError=float(np.sqrt(np.mean(error**2))),surfaces=reference))
inputs['native_xyz_head']=rest;inputs['native_uv']=face['uv']
for role in[1,3,4,6]:inputs[f'native_role{role}_tri']=face['groups'][role].reshape(-1,3)
np.savez_compressed(R/'SOURCE_SURFACES52.npz',**inputs)
dump('SOURCE_BINDING52.json',dict(eyes=eyes,inputs=expected,sourceBundleSHA256=sha(L/'KEYFORM_BUNDLE51.json'),
    source47Sequence='counts47-087454994917423fa13c5fe72eceb7f4',liveEditorState='unknown; not queried',
    note='One common affine projection calibrated from both old authored white planes; each iris bone uniquely cross-validated against retained contours. Initial eye-bone-order draft rejected, not used.',newUnityCalls=0,newCommit=False))
print(json.dumps({'fits':[{k:v for k,v in e.items()if k!='surfaces'and k!='projection3DToReference'}for e in eyes],'bytes':(R/'SOURCE_SURFACES52.npz').stat().st_size},indent=2))
