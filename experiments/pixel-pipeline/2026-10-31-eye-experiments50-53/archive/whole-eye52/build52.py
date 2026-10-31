"""Build one source-derived whole-eye cache. No source/product writes."""
from pathlib import Path
import hashlib,json,sys,struct
import numpy as np
from PIL import Image,ImageDraw
from whole52 import attach_carrier,bind_point,cache_key,polyline_distance
R=Path(__file__).resolve().parent;B=R.parent/'eye-candidate49';L=R.parent/'lid-evidence51'
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def scalar(v):
    if isinstance(v,np.ndarray):return v.tolist()
    if isinstance(v,np.generic):return v.item()
    raise TypeError(type(v).__name__)
def dump(n,d):(R/n).write_text(json.dumps(d,ensure_ascii=False,indent=2,default=scalar),encoding='utf8')
binding=load(R/'SOURCE_BINDING52.json');bundle=load(L/'KEYFORM_BUNDLE51.json');s=np.load(R/'SOURCE_SURFACES52.npz')
audit_path=Path('C:/Users/15352/Documents/Codex/2026-10-30/task/model-source/SOURCE_AUDIT.json')
audit=load(audit_path);material=next(m for m in audit['materials']if m['materialId']==6)
image_path=Path(material['image']['file']);assert sha(image_path)==material['image']['SHA256']
image=np.asarray(Image.open(image_path).convert('RGBA')).astype(float)/255
# Verify the PNG/UV convention against the original GLB accessor, rather than
# guessing from the resulting eyelash colour. Original UVs are top-origin PNG
# coordinates; the exact native Unity mesh flips V.
model_path=Path('C:/Users/15352/Desktop/작업폴더/AvatarSample_A.vrm')
raw=model_path.read_bytes();assert sha(model_path)=='0e2fd0fc90308da3172ecf4e674fdeb4f054ebd617005caa5b997a2ca339cce3'
size=struct.unpack_from('<I',raw,12)[0];glb=json.loads(raw[20:20+size]);binary=raw[28+size:]
accessor=glb['accessors'][2];view=glb['bufferViews'][accessor['bufferView']]
source_uv=np.ndarray((accessor['count'],2),'<f4',buffer=binary,
    offset=view.get('byteOffset',0)+accessor.get('byteOffset',0),strides=(view.get('byteStride',8),4))
uv_error=float(np.max(np.abs(source_uv*np.array([1,-1])+[0,1]-s['native_uv'])))
assert uv_error==0

def texel(uv):
    # Explicit original-PNG convention for this offline illustration. A later
    # GPU source check must validate sampler/mip/colour, not call this GPU RGB.
    x=(uv[0]%1)*image.shape[1]-.5;y=((1-uv[1])%1)*image.shape[0]-.5
    a,b=int(np.floor(x)),int(np.floor(y));u,v=x-a,y-b
    return ((1-u)*(1-v)*image[b%len(image),a%image.shape[1]]+
        u*(1-v)*image[b%len(image),(a+1)%image.shape[1]]+
        (1-u)*v*image[(b+1)%len(image),a%image.shape[1]]+
        u*v*image[(b+1)%len(image),(a+1)%image.shape[1]])

cells=[attach_carrier(c,s,binding)for c in bundle['cells']]
M=np.asarray(binding['eyes'][0]['projection3DToReference']);xyz=s['native_xyz_head'];uv=s['native_uv']
projected=np.c_[xyz,np.ones(len(xyz))]@M;tri=s['native_role6_tri']
eyes=[];native_rows=[];coverage=[]
for form in bundle['eyes']:
    eye=form['eye'];parent=np.asarray(form['parent']);native=next(q for q in bundle['nativeClosingMorphs']['Fcl_EYE_Close']['nativeRingStates']if q['eye']==eye)
    native_ref=projected[native['vertexIds']]
    # Nearest anatomical native boundary arc labels are derived geometry tags,
    # not a newly asserted semantic lid mask over general face skin.
    def arcs(points):
        left=int(np.argmin(points[:,0]));right=int(np.argmax(points[:,0]));out=[]
        for step in[1,-1]:
            ix=[left]
            while ix[-1]!=right:ix.append((ix[-1]+step)%len(points))
            out.append(points[ix])
        return sorted(out,key=lambda p:np.mean(p[:,1]))
    upper,lower=arcs(native_ref)
    # Native material6 is already a distinct mesh part. No face-skin source is
    # relabelled as lid. Spatially nearest eye is only a part-owner association.
    centres={e['eye']:np.mean(projected[e['nativeRingVertexIds']],axis=0)for e in bundle['eyes']}
    own=np.array([min(centres,key=lambda e:np.linalg.norm(projected[t].mean(axis=0)-centres[e]))for t in tri])
    source_tri=np.flatnonzero(own==eye)
    low=np.floor(projected[tri[source_tri]].min(axis=(0,1))).astype(int)
    high=np.ceil(projected[tri[source_tri]].max(axis=(0,1))).astype(int)
    for y in range(low[1],high[1]+1):
        for x in range(low[0],high[0]+1):
            p=np.array([x+.75,y+.25]);hits=bind_point(p,projected,tri[source_tri])
            for local,ids,w in hits:
                primitive=int(source_tri[local]);coord=w@uv[ids];rgba=texel(coord)
                if rgba[3]<=1e-6:continue
                du,dl=polyline_distance(p,upper),polyline_distance(p,lower)
                part='upper-lid'if du<dl else'lower-lid'
                native_rows.append(dict(cellId=f'eye{eye}:native6:reference:{x},{y}',eye=eye,role=6,part=part,
                    referenceXY=[x,y],rgba8=np.rint(rgba*255).astype(int).tolist(),
                    source=dict(kind='native-material6',materialRole=6,primitive=primitive+1,triangleVertexIds=ids.tolist(),
                        barycentric=w.tolist(),uv=coord.tolist(),restHeadPoint=(w@xyz[ids]).tolist(),
                        pigmentImageSHA256=material['image']['SHA256'],pigmentRendering='offline unlit PNG bilinear; not measured S3RGBA',
                        arcAssociation='nearest projected native upper/lower boundary; derived, not authored binary lid label',
                        upperDistance=du,lowerDistance=dl)))
                break
    eyes.append(dict(eye=eye,parent=form['parent'],iris=form['iris'],upperLidPath=parent[form['upperParentArcIndices']],
        lowerLidPath=parent[form['lowerParentArcIndices']],nativeRingVertexIds=form['nativeRingVertexIds'],
        nativeRingReference=native_ref,nativeBoundaryUV=uv[form['nativeRingVertexIds']],
        nativeBoundaryRestHead=xyz[form['nativeRingVertexIds']],nativeUpperPath=upper,nativeLowerPath=lower,
        nativeMaterial6Triangles=len(source_tri),skinCarrierSemantic='continuous deformation support; not a lid mask'))

states={'existing-open-reference':dict(pixelFormAvailable=True,cells=cells+native_rows,eyes=eyes,
    approval='Only Template iris/sclera is existing authored raster. Native lid raster is a source-derived candidate.')}
for name,morph in bundle['nativeClosingMorphs'].items():
    for weight in[50,100]:
        state=[]
        for q in morph['nativeRingStates']:
            geom=next(v for v in q['states']if v['weight']==weight)
            state.append(dict(eye=q['eye'],vertexIds=q['vertexIds'],UV=s['native_uv'][q['vertexIds']],
                restHeadPoints=geom['restHeadPoints'],referencePoints=np.c_[geom['restHeadPoints'],np.ones(24)]@M))
        states[f'{name}:{weight}']=dict(pixelFormAvailable=False,nativeGeometry=state,
            reason='Original native deformation exists; no registered low-resolution pigment/skin/lid key-form for this state')
result=dict(kind='whole-eye-source-keyform/v1',cacheKey=cache_key(binding,bundle,material['image']['SHA256']),
    sourceTopologySHA256=bundle['modelTopologySHA256'],referenceContourSHA256=bundle['referenceContourSHA256'],
    referenceAnchor=load(B/'fixtures/template43.json')['referenceAnchorCellCentre'],states=states,
    canonicalSample=[.75,.25],nativeLidColourVerifiedOnGPU=False,
    skinCarrierEvidence=dict(path='../lid-evidence51/SOURCE_SKIN_CONTROL_RECONSTRUCTION.json',
        sha256=sha(L/'SOURCE_SKIN_CONTROL_RECONSTRUCTION.json'),
        meaning='Reconstructed original S0 support/control; continuous aperture deformation weights, NOT a semantic lid mask',
        measuredGPUControl=False),
    missing=['S3RGBA/S3Shade for frozen six frames','original-source UV provenance of old authored205 palette creation',
        'registered low-resolution Close50/Close100 pixel key-forms','current Editor state, deliberately not queried'],
    productModified=False,GPUApplied=False,newUnityCalls=0,newCommit=False)
dump('WHOLE_KEYFORM52.json',result)
dump('CARRIER_ASSOCIATION52.json',dict(cells=cells,allLiteralCarrierSamplesAgree=all(c['source']['literalPaletteAgreement']for c in cells),
    mismatches=[c['cellId']for c in cells if not c['source']['literalPaletteAgreement']],nativeCells=native_rows,
    nativeImageSHA256=material['image']['SHA256'],sourceAuditSHA256=sha(audit_path),
    nativeUVConvention=dict(vertices=len(source_uv),UnityUEqualsGLTFU=True,UnityVEqualsOneMinusGLTFV=True,maxError=uv_error,
        pngRowRule='row=(1-UnityV)*height; bilinear with half-texel centres',GPUFilterMipAndShadeVerified=False)))
print(json.dumps(dict(templateCells=len(cells),sourceLidCells=len(native_rows),carrierAgreement=sum(c['source']['literalPaletteAgreement']for c in cells),
    nativeParts={p:sum(c['part']==p for c in native_rows)for p in['upper-lid','lower-lid']},GPUApplied=False),indent=2))
