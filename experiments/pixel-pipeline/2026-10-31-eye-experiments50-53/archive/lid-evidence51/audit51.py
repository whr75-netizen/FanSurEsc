"""Existing mesh/control/contour audit; no Unity, UI or product mutations."""
from pathlib import Path
import hashlib,json,re,struct
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parent
P=Path('C:/Users/15352/Documents/work/Fantasy Survival Escape Game')
A=P/'Assets/EUnityValidation01';B=R.parent/'eye-candidate49'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def scalar(o):
    if isinstance(o,np.ndarray):return o.tolist()
    if isinstance(o,np.generic):return o.item()
    raise TypeError(type(o).__name__)
def dump(n,o):(R/n).write_text(json.dumps(o,ensure_ascii=False,indent=2,default=scalar),encoding='utf8')
checks=[]
def check(n,v):
    if not bool(v):raise AssertionError(n)
    checks.append(n)
prefab=A/'OriginalIntegration399/Export/ValidatedPresentation399.prefab';text=prefab.read_text()
blocks={re.match(r'!u!\d+ &(-?\d+)',b).group(1):b for b in text.split('\n--- ')[1:]}
find=lambda name:next(b for b in blocks.values()if 'Assembly-CSharp::'+name+'\n'in b)
surface=find('CurrentSurface330');feature=find('EyeFeature348');full=find('Full319View335')
skinids=re.findall(r'fileID: (\d+)',re.search(r'  source:\n(.*?)  outputs:',surface,re.S).group(1))
skin=blocks[skinids[1]]
mesh=A/'EyeContoursLayers202/Meshes/FaceSourceOwner202.asset';s=mesh.read_text()
guid=re.search(r'guid: (\w+)',Path(str(mesh)+'.meta').read_text()).group(1)
check('actual prefab face source points to Owner202',guid in re.search(r'm_Mesh: (.*)',skin).group(1))
vpart=s[s.index('  m_VertexData:'):]
n=int(re.search(r'm_VertexCount: (\d+)',vpart).group(1))
ch=re.findall(r'- stream: (\d+)\n\s+offset: (\d+)\n\s+format: (\d+)\n\s+dimension: (\d+)',vpart.split('m_DataSize:')[0])
ch=[tuple(map(int,c))for c in ch]
raw=bytes.fromhex(re.search(r'_typelessdata: ([0-9a-fA-F]+)',vpart).group(1))
strides={}
for stream,offset,fmt,dim in ch:
    if dim:strides[stream]=max(strides.get(stream,0),offset+4*dim)
starts={};at=0
for st,stride in sorted(strides.items()):starts[st]=at;at+=stride*n
check('vertex streams match declared raw bytes',at==len(raw)==int(re.search(r'm_DataSize: (\d+)',vpart).group(1)))
def attribute(i):
    st,off,fmt,dim=ch[i];check('float attribute '+str(i),fmt==0 and dim>0)
    return np.ndarray((n,dim),dtype='<f4',buffer=raw,offset=starts[st]+off,strides=(strides[st],4)).copy()
vertices=attribute(0);uv=attribute(4)[:,:2].copy();control=attribute(6);owner=attribute(11)
indices=np.frombuffer(bytes.fromhex(re.search(r'm_IndexBuffer: ([0-9a-fA-F]+)',s).group(1)),'<u4')
subs=[(int(a),int(b))for a,b in re.findall(r'firstByte: (\d+)\n\s+indexCount: (\d+)',s[:s.index('  m_Shapes:')])]
groups=[indices[a//4:a//4+b].copy()for a,b in subs]
bptext=s[s.index('  m_BindPose:'):s.index('  m_BoneNameHashes:')]
entries=re.findall(r'e(\d)(\d): ([^\n]+)',bptext)
bp=np.zeros((len(entries)//16,4,4),np.float32)
for i,(x,y,val)in enumerate(entries):bp[i//16,int(x),int(y)]=float(val)
digest=hashlib.sha256();digest.update(struct.pack('<i',n));digest.update(vertices.astype('<f4').tobytes());digest.update(uv.astype('<f4').tobytes())
for g in groups:digest.update(g.astype('<u4').tobytes())
digest.update(bp.transpose(0,2,1).astype('<f4').tobytes())
expected=re.search(r'modelTopologySHA256: (\w+)',feature).group(1)
check('decoded mesh exactly matches runtime topology/bind hash',digest.hexdigest()==expected)
bones=re.findall(r'fileID: (\d+)',re.search(r'  m_Bones:\n(.*?)  m_BlendShapeWeights:',skin,re.S).group(1))
names=[]
for t in bones:
    go=re.search(r'm_GameObject: \{fileID: (\d+)',blocks[t]).group(1)
    names.append(re.search(r'm_Name: (.*)',blocks[go]).group(1))
head=names.index('J_Bip_C_Head')
rest=(np.c_[vertices,np.ones(n,dtype=np.float32)]@bp[head].T)[:,:3]
models=[]
for b in feature.split('  - stableId: ')[1:]:
    eye=int(b.splitlines()[0]);ring=np.frombuffer(bytes.fromhex(re.search(r'closedBoundary: (\w+)',b).group(1)),'<i4').copy()
    models.append(dict(eye=eye,ring=ring,rest=rest[ring]))

# Native, author-named blendshape data is already in the exact source mesh.
# Its affected support is not automatically a binary eyelid semantic label.
shape_text=s[s.index('  m_Shapes:'):s.index('  m_BindPose:')]
vertex_text=shape_text.split('    vertices:')[1].split('    shapes:')[0]
vs=re.findall(r'- vertex: \{x: ([^,]+), y: ([^,]+), z: ([^}]+)\}\n\s+normal: [^\n]+\n\s+tangent: [^\n]+\n\s+index: (\d+)',vertex_text)
frames=[tuple(map(int,q))for q in re.findall(r'- firstVertex: (\d+)\n\s+vertexCount: (\d+)',shape_text)]
channels=re.findall(r'- name: ([^\n]+)\n\s+nameHash: [^\n]+\n\s+frameIndex: (\d+)\n\s+frameCount: (\d+)',shape_text)
morphs={};skin_ids=np.unique(groups[3])
for name,fi,fc in channels:
    if name not in['Fcl_EYE_Close','Fcl_EYE_Close_R','Fcl_EYE_Close_L']:continue
    check('native close morph has one recorded frame '+name,int(fc)==1)
    start,count=frames[int(fi)];delta=np.zeros((n,3),np.float32)
    for x,y,z,idx in vs[start:start+count]:delta[int(idx)]=[float(x),float(y),float(z)]
    ring_states=[]
    for model in models:
        states=[]
        for weight in[0.,50.,100.]:
            posed=vertices+delta*(weight/100)
            points=(np.c_[posed[model['ring']],np.ones(len(model['ring']))]@bp[head].T)[:,:3]
            states.append(dict(weight=weight,restHeadPoints=points))
        ring_states.append(dict(eye=model['eye'],vertexIds=model['ring'],states=states))
    morphs[name]=dict(channelFrame=int(fi),sourceChangedVertices=count,
        affectedSkinVertices=int((np.linalg.norm(delta[skin_ids],axis=1)>0).sum()),nativeRingStates=ring_states,
        semantics='native closing deformation, not approved low-resolution pixel shape')
check('all native close morph names preserved',len(morphs)==3)

cont=full[full.index('  contours:'):full.index('  templateRGBA:')]
source_hash=re.search(r'sourceSHA256: (\w+)',cont).group(1)
def points(st):return [list(map(float,q))for q in re.findall(r'\{x: ([^,]+), y: ([^}]+)\}',st)]
forms=[]
def arc(path):
    q=np.array(path);left=int(np.argmin(q[:,0]));right=int(np.argmax(q[:,0]));chains=[]
    for step in[1,-1]:
        ids=[left];at=left
        while at!=right:at=(at+step)%len(q);ids.append(at)
        p=q[ids];length=np.linalg.norm(np.diff(p,axis=0),axis=1);mean=float(np.sum((p[:-1,1]+p[1:,1])*.5*length)/length.sum());chains.append((mean,ids))
    chains.sort();return chains[0][1],chains[1][1]
for b in cont.split('    - owner: ')[1:]:
    eye=int(b.splitlines()[0]);parent=points(b.split('      parent:')[1].split('      iris:')[0]);iris=points(b.split('      iris:')[1].split('      pivot:')[0]);upper,lower=arc(parent)
    check('existing parent24 iris16 '+str(eye),len(parent)==24 and len(iris)==16)
    check('derived arcs cover original closed parent, same endpoints',set(upper)|set(lower)==set(range(24)) and upper[0]==lower[0] and upper[-1]==lower[-1])
    form=dict(eye=eye,parent=parent,iris=iris,upperParentArcIndices=upper,lowerParentArcIndices=lower,
        pivot=points(b.split('      pivot:')[1].split('      irisAnchor:')[0])[0],irisAnchor=points(b.split('      irisAnchor:')[1])[0],
        nativeRingVertexIds=next(m['ring']for m in models if m['eye']==eye),
        controlChannel=int(np.argmax(control[next(m['ring']for m in models if m['eye']==eye),:2].mean(axis=0))),
        lidPigmentSourceRole=6,lowerLidPigmentSource='existing FaceLidShadeEndpoint; not native lid label',
        state='existing open reference only; not rotation/blink approved')
    forms.append(form)
def inside(p,poly):
    x,y=p;flag=False
    for i,a in enumerate(poly):
        b=poly[(i+1)%len(poly)]
        if(a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:flag=not flag
    return flag
template=load(B/'fixtures/template43.json');classified=[];mismatch=[]
for c in template['cells']:
    f=next(f for f in forms if f['eye']==c['eye']);q=np.array(c['referenceXY'])+[.75,.25]
    role=(1 if inside(q,f['iris'])else 4)if inside(q,f['parent'])else 0
    classified.append(dict(cell=c['cellId'],storedRole=c['role'],contourRole=role))
    if role!=c['role']:mismatch.append(classified[-1])

stats=[]
for role,g in enumerate(groups):
    ids=np.unique(g);v=control[ids,:2];carrier=v.max(axis=1)>1e-5
    stats.append(dict(materialRole=role,vertices=len(ids),carrierVertices=int(carrier.sum()),controlMin=v.min(axis=0),controlMax=v.max(axis=0),nonbinaryValues=int(((v>1e-5)&(v<1-1e-5)).sum())))

# Reconstruct already-stored source skin samples from the exact original triangle
# surface, then interpolate the existing control. This is not semantic relabelling.
tri=rest[groups[3].reshape(-1,3)].astype(float);u=tri[:,1]-tri[:,0];v=tri[:,2]-tri[:,0]
aa=np.einsum('ij,ij->i',u,u);bb=np.einsum('ij,ij->i',v,v);ab=np.einsum('ij,ij->i',u,v);det=aa*bb-ab*ab
good=det>0
def reconstruct(p):
    d=p-tri[:,0];du=np.einsum('ij,ij->i',d,u);dv=np.einsum('ij,ij->i',d,v)
    b=np.divide(bb*du-ab*dv,det,out=np.zeros_like(det),where=good);c=np.divide(aa*dv-ab*du,det,out=np.zeros_like(det),where=good)
    rr=d-b[:,None]*u-c[:,None]*v;err=np.linalg.norm(rr,axis=1)
    ok=good&(b>=-1e-4)&(c>=-1e-4)&(b+c<=1.0001);j=int(np.argmin(np.where(ok,err,np.inf)))
    if not ok[j]or err[j]>1e-6:return dict(matched=False,minError=float(err.min()))
    bary=np.array([1-b[j]-c[j],b[j],c[j]]);ids=groups[3].reshape(-1,3)[j]
    alternatives=np.flatnonzero(ok&(err<=1e-6))
    controls=[];uvs=[]
    for k in alternatives:
        ba=np.array([1-b[k]-c[k],b[k],c[k]]);ix=groups[3].reshape(-1,3)[k]
        controls.append(ba@control[ix,:2]);uvs.append(ba@uv[ix])
    return dict(matched=True,nearestPrimitive=j+1,bary=bary,control=bary@control[ids,:2],uv=bary@uv[ids],error=float(err[j]),
        compatiblePrimitives=(alternatives+1).tolist(),controlSpread=np.ptp(controls,axis=0).max(),uvSpread=np.ptp(uvs,axis=0).max())
npz=np.load(B/'fixtures/replay-inputs.npz');meta=load(B/'fixtures/frames.json');result49=load(B/'RESULTS.json');samples=[]
for i,m in enumerate(meta):
    m0=npz[f'f{i:02}_S0META'];p0=npz[f'f{i:02}_S0POINT'];m1=npz[f'f{i:02}_S1META']
    for row in result49[i]['cells']:
        if row['role']!=4 or row['representative'].get('support'):continue
        x,y=row['xy'][0]-m['x'],row['xy'][1]-m['y']
        for k in range(16):
            xx=x*4+k%4;yy=y*4+3-k//4;skin0=m0[yy,xx];white=m1[yy,xx]
            if not(skin0[0]>0 and white[0]>0 and skin0[0]<white[0]and round(float(skin0[2]))==row['eye']and p0[yy,xx,3]>.5):continue
            match=reconstruct(p0[yy,xx,:3].astype(float));samples.append(dict(frame=m['frame'],cellId=row['cellId'],xy=row['xy'],k=k,**match))
matched=[q for q in samples if q['matched']]
check('stored skin points have exact original mesh correspondence',len(matched)==len(samples)and len(matched)>0)
bundle=dict(kind='existing-source-eye-keyform/v1',referenceContourSHA256=source_hash,modelTopologySHA256=expected,
    templateRoleSHA256=template['productSHA256'][str(A/'SocketTemplate216/Inputs/TemplateRole.asset').replace('/','\\')],
    cells=template['cells'],eyes=forms,skinControlSemantics='continuous aperture deformation carrier, NOT an actual eyelid semantic mask',
    registeredStates=['stored open reference only'],unregisteredStates=['blink50','blink100','unvalidated yaw'],
    fieldsAddedRelativeTo49=['parent','iris','upperParentArcIndices','lowerParentArcIndices','nativeRingVertexIds','sourceContourSHA256'],
    nativeClosingMorphs=morphs,newDesignShape=False,GPUApplied=False)
dump('KEYFORM_BUNDLE51.json',bundle);dump('SOURCE_SKIN_CONTROL_RECONSTRUCTION.json',samples)
summary=dict(modelHashExact=True,faceSourceGUID=guid,vertexCount=n,headBoneIndex=head,controlChannelsPresent=True,
    controlStatistics=stats,sourceParentContourExists=True,parentCounts=[len(f['parent'])for f in forms],irisCounts=[len(f['iris'])for f in forms],
    referenceTemplateVsContourMismatches=mismatch,referenceTemplateCells=len(classified),matchedSkinSamples=len(matched),
    maxSkinRestPositionError=max(q['error']for q in matched),controlCarrierOnBlockedSamples=sum(float(max(q['control']))>1e-5 for q in matched),
    ambiguousPrimitiveSamples=sum(len(q['compatiblePrimitives'])>1 for q in matched),maxControlSpread=max(q['controlSpread']for q in matched),
    nativeCloseMorphs={name:dict(sourceChangedVertices=q['sourceChangedVertices'],affectedSkinVertices=q['affectedSkinVertices'])for name,q in morphs.items()},
    trueSkinVsLidSemanticMaskFound=False,carrierIsSameMaterialAsFace=True,keyFormOriginalLidPigmentRoleAbsent=True,
    newUnityCalls=0,productModified=False,newCommit=False,checks=len(checks))
dump('SUMMARY.json',summary);dump('TESTS.json',checks)
dump('INPUTS.json',dict(files=[dict(file=str(p),sha256=sha(p))for p in[prefab,mesh,A/'EyeContoursLayers202/Runtime/Eye202PartFeature.cs',A/'EyeContoursLayers202/Shaders/Eye202Fragment.hlsl',A/'EyeBoundaryRestore348/Shaders/EyeSurface348.shader']],sourceSequence=meta[0]['sequenceId']))
# Existing source curves and literal template cells in their reference space.
x0,y0,w,h=210,75,16,8;scale=32;im=Image.new('RGB',(w*scale,h*scale),(25,29,36));draw=ImageDraw.Draw(im)
for c in template['cells']:
    x,y=c['referenceXY'];draw.rectangle(((x-x0)*scale,(y-y0)*scale,(x-x0+1)*scale-1,(y-y0+1)*scale-1),fill=tuple(c['rgba8'][:3]))
for f in forms:
    q=np.array(f['parent'])
    for ids,col in[(f['upperParentArcIndices'],(70,225,245)),(f['lowerParentArcIndices'],(255,193,77))]:
        draw.line([tuple((p-[x0,y0])*scale)for p in q[ids]],fill=col,width=2)
    q=np.array(f['iris']);draw.line([tuple((p-[x0,y0])*scale)for p in np.vstack([q,q[0]])],fill=(250,90,155),width=2)
im.save(R/'existing-reference-curves.png')
print(json.dumps({k:v for k,v in summary.items()if k!='controlStatistics'},ensure_ascii=False,indent=2,default=scalar))
