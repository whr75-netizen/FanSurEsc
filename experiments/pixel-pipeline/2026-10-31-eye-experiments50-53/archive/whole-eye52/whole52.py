"""Source-bound whole-eye adapter. Pure offline; no Unity or product imports.

Retained artist contours/Template216, authored205 carrier UVs and native role6
geometry are different provenances. They stay distinct in the cache. A native
geometry-derived raster is a candidate, not an approved new pixel design.
"""
import copy,hashlib,json
import numpy as np

def barycentric(p,triangle):
    t=np.asarray(triangle,float);p=np.asarray(p,float)
    a=t[1]-t[0];b=t[2]-t[0];d=p-t[0]
    D=np.column_stack([a,b]);q=np.linalg.lstsq(D,d,rcond=None)[0]
    w=np.array([1-q.sum(),q[0],q[1]])
    return w,float(np.linalg.norm(D@q-d))

def bind_point(p,points,triangles):
    hits=[]
    for primitive,ids in enumerate(triangles):
        w,err=barycentric(p,points[ids])
        if err<1e-7 and w.min()>=-1e-7 and w.max()<=1+1e-7:
            hits.append((primitive,ids,w))
    return hits

def polyline_distance(p,path):
    a=np.asarray(path[:-1]);b=np.asarray(path[1:]);v=b-a
    t=np.clip(np.sum((p-a)*v,axis=1)/np.maximum(np.sum(v*v,axis=1),1e-30),0,1)
    return float(np.linalg.norm(p-a-t[:,None]*v,axis=1).min())

class WholeEye52:
    """One registered state and common placement for parent + every child.

    Unsupported states return their real native geometry plus an explicit
    missing-pixel-form result. They do not reuse the open raster.
    """
    def __init__(self,bundle,reference_anchor):
        self.bundle=copy.deepcopy(bundle)
        self.anchor=np.asarray(reference_anchor,float)
        self.key=bundle['cacheKey']
    def request(self,key,state,anchor,phase=(0,0)):
        if key!=self.key:raise ValueError('Source/contour/UV/pigment contract changed; rebind required')
        if state not in self.bundle['states']:raise ValueError('Unknown source state; no inferred eye')
        data=copy.deepcopy(self.bundle['states'][state])
        if not data['pixelFormAvailable']:
            data.update(status='source-geometry-only; pixel key-form missing',cells=[],translation=None)
            return data
        shift=np.floor(np.asarray(anchor)+np.asarray(phase)-self.anchor+.5).astype(int)
        data['translation']=shift.tolist()
        for row in data['cells']:row['xy']=(np.array(row['referenceXY'])+shift).tolist()
        for eye in data['eyes']:
            for field in ['parent','iris','upperLidPath','lowerLidPath']:
                eye[field]=(np.asarray(eye[field])+shift).tolist()
        data['status']='open-source-candidate; not GPU integrated or artist-approved whole-eye raster'
        return data

def attach_carrier(c,surfaces,binding):
    """Exact existing carrier triangle/UV + literal Template pigment provenance."""
    row=copy.deepcopy(c);eye=c['eye'];family='iris'if c['role']==1 else'white';prefix=f'eye{eye}_{family}'
    p=np.array(c['referenceXY'])+[.75,.25]
    hits=bind_point(p,surfaces[prefix+'_reference'],surfaces[prefix+'_tri'])
    if not hits:raise ValueError('Registered Template point has no original carrier surface')
    primitive,ids,w=hits[0];uv=w@surfaces[prefix+'_uv'][ids]
    pal=surfaces[prefix+'_palette'];h,width=pal.shape[:2]
    # Unity point sampler uses floor(uv * size), clamped; this source palette is
    # already serialized bottom-up, unlike a PNG. No RGB nearest-match search.
    ij=np.clip(np.floor(uv*np.array([width,h])).astype(int),[0,0],[width-1,h-1])
    rgba=pal[ij[1],ij[0]]
    row['part']='iris'if c['role']==1 else'sclera'
    row['source']={'kind':'authored205-carrier','eye':eye,'materialRole':1 if family=='iris'else 4,
        'primitive':primitive+1,'triangleVertexIds':ids.tolist(),'barycentric':w.tolist(),
        'uv':uv.tolist(),'restHeadPoint':(w@surfaces[prefix+'_xyz'][ids]).tolist(),
        'paletteTexel':ij.tolist(),'carrierSampleRGBA8':rgba.tolist(),
        'templateRGBA8':c['rgba8'],'literalPaletteAgreement':bool(np.array_equal(rgba,c['rgba8'])),
        'nativeOriginalUVNotProven':True}
    # A mismatch must remain visible; never replace the approved Template colour
    # by an inferred nearest source colour.
    return row

def cache_key(binding,bundle,native_image_sha):
    contract=dict(inputs=binding['inputs'],bundleSHA=binding['sourceBundleSHA256'],nativeImageSHA=native_image_sha,
        nativeMorphNames=sorted(bundle['nativeClosingMorphs']),registeredRasterStates=['existing-open-reference'],
        canonicalSample=[.75,.25],placement='one common integer translation for all parts',version=52)
    return hashlib.sha256(json.dumps(contract,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def compose_registered(cells):
    """Opaque logical-cell diagnostic. Preserve unresolved overlaps explicitly.

    The existing iris/sclera Template is disjoint. If a native eyeline candidate
    occupies the same cell, emit a conflict instead of silently deleting either
    source feature or inventing a replacement cell. A caller can inspect each
    source layer; this is intentionally not a claimed final GPU compositor.
    """
    at={}
    for row in cells:at.setdefault(tuple(row['xy']),[]).append(row)
    out=[];conflicts=[]
    for xy,rows in sorted(at.items()):
        if len(rows)>1:
            conflicts.append({'xy':list(xy),'parts':[r['part']for r in rows],
                'ids':[r['cellId']for r in rows],'status':'one opaque output cannot show both source parts at this cell'})
        else:out.append(rows[0])
    return out,conflicts

def native_representative(d,m,row,final_occlusion):
    """Actual material6 support, retaining the original depth/alpha occluders.

    This does not derive a lid from ordinary skin or restore a missing source.
    It is a source eligibility diagnostic, not a fabricated S3RGBA sample.
    """
    x,y=row['xy'][0]-m['x'],row['xy'][1]-m['y']
    if not(0<=x<m['width']and 0<=y<m['height']):return {'support':False,'reason':'outside stored source ROI'}
    hits=[];count=0;blocks=set()
    for k in range(16):
        xx=x*4+k%4;yy=y*4+3-k//4
        v=d['S3META'][yy,xx];point=d['S3POINT'][yy,xx]
        if not(v[0]>0 and v[1]>.5 and v[3]>1e-6 and round(float(v[2]))==row['eye']and point[3]>.5):continue
        count+=1;weight=float(np.clip(v[3],0,1));dep=float(v[0])
        for name in['S0META','S4META','S5META','S6META']:
            o=d[name][yy,xx]
            if not(o[0]>0 and o[1]>.5 and o[3]>1e-6 and o[0]<dep):continue
            if name=='S0META'and(round(float(o[2]))!=row['eye']or d['S0POINT'][yy,xx,3]<=.5):continue
            weight*=0 if name=='S6META'else 1-float(np.clip(o[3],0,1));blocks.add(name)
        if weight>0:hits.append((((k%4+.5)/4-.5)**2+((k//4+.5)/4-.5)**2,k,dep,weight))
    if not hits:return dict(support=False,sourceSamples=count,sampleBlockers=sorted(blocks))
    _,k,dep,weight=min(hits)
    veto=final_occlusion(d,m,row['xy'],dep)
    return dict(support=not veto,source=3,k=k,depth=dep,weight=weight,sourceSamples=count,
        sampleBlockers=sorted(blocks),knownFinalBlocks=veto)
