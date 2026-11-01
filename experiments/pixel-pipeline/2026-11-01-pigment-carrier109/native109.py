"""Source UV pigment ribbon/cache. No colour threshold, Unity or RGB averaging.

The optional centre curve is explicitly alpha-mass-centred in native texel
cross sections. It is an operational reference, not recovered artist intent.
Every centre must map to a real original UV triangle with nonzero bilinear
source alpha; otherwise it stays unresolved. No nearest filling is performed.
"""
from pathlib import Path
import json,sys,hashlib,collections
import numpy as np
from PIL import Image,ImageDraw,ImageFont
H=Path(__file__).resolve().parent;R=H.parent
def font(n):return ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',n)

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8')if hasattr(p,'read_text')else Path(p).read_text(encoding='utf-8'))
def static(name,fallback):return H/'inputs'/name if(H/'inputs'/name).exists()else fallback
def components(mask,diagonal=True):
    labels=np.full(mask.shape,-1,np.int32);out=[];shifts=[(-1,0),(1,0),(0,-1),(0,1)]
    if diagonal:shifts +=[(-1,-1),(-1,1),(1,-1),(1,1)]
    h,w=mask.shape
    for yy,xx in np.argwhere(mask):
        y,x=int(yy),int(xx)
        if labels[y,x]>=0:continue
        k=len(out);todo=[(y,x)];labels[y,x]=k;points=[]
        while todo:
            a,b=todo.pop();points.append((a,b))
            for dy,dx in shifts:
                c,d=a+dy,b+dx
                if 0<=c<h and 0<=d<w and mask[c,d]and labels[c,d]<0:labels[c,d]=k;todo.append((c,d))
        out.append(np.array(points,int))
    return labels,out

def uv_bary(t,p):
    A=(t[1:]-t[0]).T
    if abs(np.linalg.det(A))<1e-18:return None
    q=np.linalg.solve(A,(np.asarray(p)-t[0]).T).T
    return np.c_[1-q.sum(1),q]if q.ndim==2 else np.r_[1-q.sum(),q]

def bilinear(image,uv):
    h,w=image.shape[:2];q=np.array([uv[0]*w-.5,(1-uv[1])*h-.5]);i=np.floor(q).astype(int);f=q-i
    return sum(image[np.clip(i[1]+dy,0,h-1),np.clip(i[0]+dx,0,w-1)]*((f[0]if dx else 1-f[0])*(f[1]if dy else 1-f[1]))for dy in [0,1]for dx in [0,1])

def locate_uv(uv,vertices,triangles,rest):
    found=[]
    for i,ids in enumerate(triangles):
        b=uv_bary(vertices[ids],np.asarray(uv))
        if b is not None and b.min()>=-1e-10:found.append((i,b,b@rest[ids]))
    if not found:return None,'no-carrier'
    positions=np.array([x[2]for x in found])
    if np.max(np.linalg.norm(positions-positions[0],axis=1))>1e-7:return None,'multiple-distinct-carriers'
    # A shared triangulation edge is one physical point. Primitive order only
    # chooses an equivalent carrier representation, never colour or eye shape.
    return found[0], 'shared-physical-edge'if len(found)>1 else'exact-interior'

def section_centres(xy,alpha,corners):
    """Native-texel cross sections, not output-pixel bins. Integer weighted
    sums are invariant to source storage order. A diagonal-axis tie is exposed.
    """
    delta=np.asarray(corners[1])-corners[0];axes=np.where(abs(delta)==abs(delta).max())[0]
    if len(axes)!=1:return None,[],True
    axis=int(axes[0]);direction=1 if delta[axis]>=0 else-1;longitudinal=xy[:,axis];out=[]
    for value in sorted(np.unique(longitudinal),reverse=direction<0):
        take=longitudinal==value;a=np.asarray(alpha[take],np.int64);num=((np.asarray(xy[take],np.int64)*2+1)*a[:,None]).sum(0);pixel=num/(2*int(a.sum()));out.append((int(value),pixel))
    return axis,out,False

def cache_key(rest,uv,tris,material,registration):
    h=hashlib.sha256(b'native-pigment-ribbon109/v1')
    for x in [rest,uv,tris]:h.update(np.ascontiguousarray(x).tobytes())
    h.update(json.dumps(material,sort_keys=True).encode());h.update(json.dumps(registration,sort_keys=True).encode());return h.hexdigest()

def create_cache():
    H.mkdir(exist_ok=True);s=np.load(static('SOURCE_SURFACES52.npz',R/'whole-eye52/SOURCE_SURFACES52.npz'));rest=s['native_xyz_head'];uv=s['native_uv'];tris=s['native_role6_tri'];reg=read(static('REGISTRATION89.json',R/'native-feature89/REGISTRATION89.json'))
    audit=read(static('SOURCE_AUDIT.json',Path(r'C:\Users\15352\Documents\Codex\2026-10-30\task\model-source\SOURCE_AUDIT.json')));mat=next(x for x in audit['materials']if x['materialId']==6);tex=static('image-9.png',Path(mat['image']['file']));assert sha(tex)==mat['image']['SHA256']
    uvTransform=mat['baseColorTexture'].get('extensions',{}).get('KHR_texture_transform',{})
    assert mat['alphaMode']=='BLEND'and mat['baseColorFactorLinear']==[1,1,1,1]
    assert uvTransform.get('offset',[0,0])==[0,0]and uvTransform.get('scale',[1,1])==[1,1]and uvTransform.get('rotation',0)==0,'Current source extractor requires audited identity texture UV transform'
    image=np.asarray(Image.open(tex).convert('RGBA'));h,w=image.shape[:2];prim=np.full((h,w),-1,np.int32);bc=np.zeros((h,w,3),np.float32);ambiguous=np.zeros((h,w),bool)
    for k,ids in enumerate(tris):
        t=uv[ids].astype(float);q=t*[w,-h]+[0,h];lo=np.maximum(0,np.floor(q.min(0)).astype(int));hi=np.minimum([w,h],np.ceil(q.max(0)).astype(int))
        yy,xx=np.mgrid[lo[1]:hi[1],lo[0]:hi[0]];b=uv_bary(t,np.c_[(xx.ravel()+.5)/w,1-(yy.ravel()+.5)/h])
        if b is None:continue
        valid=(b.min(1)>=0)&(image[yy.ravel(),xx.ravel(),3]>0);xs=xx.ravel()[valid];ys=yy.ravel()[valid];bs=b[valid]
        for x,y,bary in zip(xs,ys,bs):
            if prim[y,x]>=0:
                old=bc[y,x]@rest[tris[prim[y,x]]];new=bary@rest[ids]
                if np.linalg.norm(old-new)>1e-7:ambiguous[y,x]=True
            else:prim[y,x]=k;bc[y,x]=bary
    mask=(prim>=0)&~ambiguous;labels,cc=components(mask);_,cc4=components(mask,False)
    centres={e['eye']:rest[e['nativeRingVertexIds']].mean(0)for e in reg['eyes']};records=[];curves=[]
    for k,points in enumerate(cc):
        yy,xx=points.T;b=bc[yy,xx];indices=tris[prim[yy,xx]];xyz=np.einsum('ij,ijk->ik',b,rest[indices]);alpha=image[yy,xx,3].astype(float)/255
        near=np.array([np.linalg.norm(xyz-centres[o],axis=1)for o in [1,2]]);owners=np.array([1,2])[near.argmin(0)];owner=int(np.unique(owners)[0])if len(np.unique(owners))==1 else 0
        key=hashlib.sha256(np.asarray(sorted(map(tuple,points)),dtype='<i4').tobytes()+mat['image']['SHA256'].encode()).hexdigest()
        records.append({'component':k,'sourceKey':key,'eyeOwnerFromRestGeometry':owner,'texels':len(points),'alphaMass':float(alpha.sum()),'boundsXY':[int(xx.min()),int(yy.min()),int(xx.max()),int(yy.max())]})
    for e in reg['eyes']:
        owner=e['eye'];ring=np.array(e['nativeRingVertexIds']);parent=np.array(e['authoredParent']);endids=[ring[np.argmin(parent[:,0])],ring[np.argmax(parent[:,0])]];ends=[]
        for vertex in endids:
            choices=[]
            for k,points in enumerate(cc):
                if records[k]['eyeOwnerFromRestGeometry']!=owner:continue
                yy,xx=points.T;xyz=np.einsum('ij,ijk->ik',bc[yy,xx],rest[tris[prim[yy,xx]]]);dist=np.linalg.norm(xyz-rest[vertex],axis=1);i=int(dist.argmin())
                choices.append((float(dist[i]),k,int(xx[i]),int(yy[i])))
            choices.sort();ends.append({'ringVertex':int(vertex),'nearestPigment':choices[0],'nextComponentDistance':choices[1][0]if len(choices)>1 else None})
        chosen=ends[0]['nearestPigment'][1]if ends[0]['nearestPigment'][1]==ends[1]['nearestPigment'][1]else None
        curve={'owner':owner,'cornerMatches':ends,'selectedComponent':chosen,'selection':'both aperture corners nearest the same actual pigment component; no area ranking','points':[]}
        if chosen is not None:
            points=cc[chosen];xy=points[:,::-1];a=image[points[:,0],points[:,1],3];axis,sections,axisAmbiguous=section_centres(xy,a,[ends[0]['nearestPigment'][2:],ends[1]['nearestPigment'][2:]]);curve['crossSectionAxisAmbiguous']=axisAmbiguous
            for value,pixel in sections:
                sourceUV=[pixel[0]/w,1-pixel[1]/h];carrier,status=locate_uv(sourceUV,uv,tris,rest);rgba=bilinear(image.astype(float)/255,sourceUV)
                row={'texelSection':int(value),'sourceUV':sourceUV,'sourceAlpha':float(rgba[3]),'carrierStatus':status,'colourAveraged':False}
                if carrier is not None and rgba[3]>0:
                    tid,bary,xyz=carrier;row|={'primitive':tid+1,'vertices':tris[tid].tolist(),'barycentric':bary.tolist(),'restHead':xyz.tolist()}
                else:row['unresolved']=True
                curve['points'].append(row)
            curve['longitudinalNativePixelAxis']=axis
        curves.append(curve)
    (H/'NATIVE_CACHE109.json').write_text(json.dumps({'cacheKey':cache_key(rest,uv,tris,mat,reg),'cacheInvalidation':'source rest/UV/topology/material/texture identity/registration/policy; not current pose. View layout history is separately scoped.','material':mat,'textureSHA256':sha(tex),'sourceTopologySHA256':read(static('WHOLE_KEYFORM52.json',R/'whole-eye52/WHOLE_KEYFORM52.json'))['sourceTopologySHA256'],
      'components8':records,'componentCount4':len(cc4),'ambiguousCarrierTexels':int(ambiguous.sum()),'sourcePrimitiveCount':len(tris),'texelsOnCarrier':int(mask.sum()),'curves':curves,
      'referenceDefinition':'alpha-mass centred actual UV ribbon, not an authored skeleton; all components retained, only two-corner connected component has a centre reference'},indent=2)+'\n',encoding='utf8')
    np.savez_compressed(H/'NATIVE_DOMAIN109.npz',primitive=prim,barycentric=bc,ambiguous=ambiguous,components=labels,rgba=image,rest=rest,uv=uv,triangles=tris)
    view=Image.new('RGB',(1024,400),'#17222e');view.paste(Image.fromarray(image),(0,20),Image.fromarray(image[...,3]));dr=ImageDraw.Draw(view)
    for e in curves:
        pts=[(p['sourceUV'][0]*w,20+(1-p['sourceUV'][1])*h)for p in e['points']if not p.get('unresolved')]
        if len(pts)>1:dr.line(pts,fill='#42fff5',width=2)
        for end in e['cornerMatches']:
            _,_,x,y=end['nearestPigment'];dr.ellipse((x-4,y+16,x+4,y+24),outline='#ffcf66',width=2)
    dr.text((18,300),'Native UV pigment / cyan: alpha-centred reference / yellow: aperture-corner nearest pigment',font=font(17),fill='white')
    dr.text((18,340),'All disconnected native components remain cached. No source RGB averaging or new colour.',font=font(17),fill='#a7c8df');view.save(H/'NATIVE_UV109.png')
    print(json.dumps({'sourceComponents8':len(cc),'sourceComponents4':len(cc4),'carrierTexels':int(mask.sum()),'ambiguousCarrierTexels':int(ambiguous.sum()),'curves':[{'owner':e['owner'],'component':e['selectedComponent'],'sections':len(e['points']),'unresolved':sum(p.get('unresolved',False)for p in e['points']),'cornerMatches':e['cornerMatches']}for e in curves]}))
    return H/'NATIVE_CACHE109.json'
if __name__=='__main__':create_cache()
