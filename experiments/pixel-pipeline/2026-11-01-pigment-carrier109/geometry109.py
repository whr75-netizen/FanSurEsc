"""Same-frame105 native pigment -> evaluated carrier -> canonical/physical map.

Uses saved direct eyeInverse and full evaluated mesh, not a fitted warp or a
different sourceId. Canonical triangle interpolation follows NativeSurface89's
actual vertex shader: divide projective xy at VERTICES, then orthographic
raster interpolation. Projecting an interpolated world point is different.
"""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image,ImageDraw
from native109 import H,R,read,bilinear,uv_bary,font,static
from io109 import mesh,intersects,buffer,entries,packet

def transform(m,p):return np.c_[p,np.ones(len(p))]@m.T
def physical(view,projection,world):
    v=transform(view,world);p=v@projection.T
    return np.c_[(p[:,0]/p[:,3]*.5+.5)*480,(.5-p[:,1]/p[:,3]*.5)*272],-v[:,2],p[:,3]

def prepare_packet(p,domain,cache):
    m=read(p/'RAW_MANIFEST.json');identity,model,current,uv,indices=mesh(p/'current-face105.mesh')
    assert identity['sourceId']==m['sourceId'];assert np.array_equal(uv,domain['uv'])and np.array_equal(indices[6],domain['triangles'])
    world=transform(model,current)[:,:3];head=np.array(m['headMatrix105']).reshape(4,4,order='F');headq=transform(np.linalg.inv(head),world);nr=m['forward102']['nativeRegistration'];offset=np.array(nr['anchor'])+np.array(nr['bounds'][:2]);view=np.array(nr['physicalView']).reshape(4,4,order='F');projection=np.array(m['grid102']['headProjection']).reshape(4,4,order='F')
    reg=read(static('REGISTRATION89.json',R/'native-feature89/REGISTRATION89.json'));centres={e['eye']:domain['rest'][e['nativeRingVertexIds']].mean(0)for e in reg['eyes']};owners=np.array([1,2])[np.argmin(np.array([np.linalg.norm(domain['rest']-centres[o],axis=1)for o in [1,2]]),axis=0)]
    maps={}
    for e in reg['eyes']:
        owner=e['eye'];inv=np.array(next(q for q in m['existingEyeInverse105']if q['eye']==owner)['inverseHomography']).reshape(4,4,order='F');inv[3,3]=1;forward=np.linalg.inv(inv)[:3,:3]
        native=headq@np.asarray(e['nativeToAuthoredProjection']);q=np.c_[native,np.ones(len(native))]@forward.T;maps[owner]=q[:,:2]/q[:,2:3]-offset
    pxy,z,cw=physical(view,projection,world)
    return {'manifest':m,'world':world,'uv':uv,'indices':indices,'owners':owners,'maps':maps,'depth':z,'physicalXY':pxy,'physicalW':cw,'view':view,'projection':projection}

def carrier_hits(q,owner,ctx,part=6):
    out=[]
    for tid,ids in enumerate(ctx['indices'][part]):
        # Reproduce native source owner interpolation, not index ranges.
        b=uv_bary(ctx['maps'][owner][ids],np.asarray(q,float))
        if b is None or b.min()<-1e-10 or round(float(b@ctx['owners'][ids]))!=owner:continue
        out.append({'primitive':tid+1,'vertices':ids,'barycentric':b,'world':b@ctx['world'][ids],'UV':b@ctx['uv'][ids],'depth':float(b@ctx['depth'][ids])})
    return sorted(out,key=lambda x:x['depth'])

def front_geometry(point,ctx,part=3):
    query,depth,_=physical(ctx['view'],ctx['projection'],np.asarray(point)[None]);xy=ctx['physicalXY'];hits=[]
    for tid,ids in enumerate(ctx['indices'][part]):
        b=uv_bary(xy[ids],query[0])
        if b is None or b.min()<-1e-10:continue
        perspective=b/ctx['physicalW'][ids];perspective/=perspective.sum();z=float(perspective@ctx['depth'][ids])
        if z<float(depth[0])-3e-5:hits.append({'part':part,'primitive':tid+1,'barycentric':perspective.tolist(),'UV':(perspective@ctx['uv'][ids]).tolist(),'depth':z,'margin':float(depth[0])-z})
    return sorted(hits,key=lambda x:x['depth'])

class FaceRays:
    """Complete captured face, bounded32 queries, two-sided conservative test.
    No hit is geometrically clear of this complete face. A hit remains only a
    potential blocker until actual material alpha/culling is established.
    """
    def __init__(self,ctx):
        self.ctx=ctx;self.ids=ctx['indices'][3];self.xy=ctx['physicalXY'][self.ids];self.z=ctx['depth'][self.ids];self.w=ctx['physicalW'][self.ids]
        d=np.stack([self.xy[:,1]-self.xy[:,0],self.xy[:,2]-self.xy[:,0]],axis=2);det=np.linalg.det(d);self.good=abs(det)>1e-18;self.inv=np.zeros_like(d);self.inv[self.good]=np.linalg.inv(d[self.good])
    def query(self,world):
        xy,z,_=physical(self.ctx['view'],self.ctx['projection'],np.asarray(world));out=[]
        for start in range(0,len(xy),32):
            q=xy[start:start+32];v=q[None]-self.xy[:,0,None];ab=np.einsum('tij,tqj->tqi',self.inv,v);b=np.concatenate([1-ab.sum(2,keepdims=True),ab],axis=2);pw=b/self.w[:,None];pw/=pw.sum(2,keepdims=True);depth=(pw*self.z[:,None]).sum(2)
            front=self.good[:,None]&(b.min(2)>=-1e-10)&(depth<z[None,start:start+32]-3e-5)
            for j in range(len(q)):
                ix=np.where(front[:,j])[0];out.append({'geometricallyClear':not len(ix),'potentialBlockerCount':len(ix),'nearestPotentialPrimitive':int(ix[np.argmin(depth[ix,j])])+1 if len(ix)else None})
        return out

def probe_source(ctx,p):
    m=ctx['manifest'];w,h=m['forward102']['canonicalSize'];a=buffer(p/'canonical-layers.f32').reshape(4,5,h,w,4);errors=[];alpha=[];ownerErrors=0
    tex=domain['rgba'].astype(float)/255
    for yy,xx in np.argwhere(a[3,1,:,:,0]>0):
        row=a[3,:,yy,xx];owner=round(float(row[1,2]));tid=round(float(row[3,2]))-1;ids=ctx['indices'][6][tid];b=uv_bary(ctx['uv'][ids],row[3,:2].astype(float))
        xy=b@ctx['maps'][owner][ids];z=b@ctx['depth'][ids];errors.append([float(np.linalg.norm(xy-[(xx+.5)/4,(yy+.5)/4])),abs(float(z-row[1,0]))]);ownerErrors+=round(float(b@ctx['owners'][ids]))!=owner
        alpha.append(abs(float(bilinear(tex,row[3,:2])[3])-float(row[1,3])))
    return {'sampleCount':len(errors),'maxCanonicalPixels':float(np.max(errors,axis=0)[0]),'maxPhysicalDepth':float(np.max(errors,axis=0)[1]),'sourceOwnerMismatch':ownerErrors,
      'maxOriginalBilinearVsGPUSourceAlpha':max(alpha),'alphaComparisonIsNotAllMipDerivativeEquivalence':True}

def curve_distance(points,curve):
    points=np.asarray(points);a=curve[:-1];b=curve[1:];d=b-a;den=np.maximum((d*d).sum(1),1e-30);v=points[:,None]-a[None];t=np.clip((v*d[None]).sum(2)/den[None],0,1);delta=v-t[:,:,None]*d[None];return np.sqrt((delta*delta).sum(2)).min(1)

def main():
    global domain
    domain=np.load(H/'NATIVE_DOMAIN109.npz');cache=read(H/'NATIVE_CACHE109.json');seq=entries(H,'105',lambda:read(sorted((R/'closed-support105/direct').glob('STATE102-*'))[-1])['sequencePackets']);old=read(static('SOURCE_CURVE105.json',R/'closed-support105/direct/SOURCE_CURVE105.json'));results=[]
    board=Image.new('RGB',(1200,800),'#111923');dr=ImageDraw.Draw(board);dr.text((20,10),'109: actual UV pigment reference versus skin-ring / same-source105 evaluated geometry',font=font(21),fill='white');dr.text((20,45),'White: recorded GPU native alpha. Cyan: native pigment centre. Yellow: old skin-ring.',font=font(17),fill='#aacbdd')
    for ri,e in enumerate(seq):
        p=packet(H,e,'105');ctx=prepare_packet(p,domain,cache);m=ctx['manifest'];rays=FaceRays(ctx);record={'frame':m['frameIndex'],'sourceId':m['sourceId'],'Close':m['motion82']['requestedClose'],'geometrySource':'same-packet full current-face105.mesh + direct public eyeInverse','probe':probe_source(ctx,p),'eyes':[]}
        w,h=m['forward102']['canonicalSize'];cw,ch=w//4,h//4;a=buffer(p/'canonical-layers.f32').reshape(4,5,h,w,4);alpha=a[3,1,:,:,3];pic=Image.fromarray(np.repeat(np.clip(np.rint(alpha*255),0,255).astype('uint8')[...,None],3,axis=2));scale=7;pic=pic.resize((w*scale,h*scale),Image.Resampling.NEAREST);origin=np.array([20,100+ri*230]);board.paste(pic,tuple(origin));dr.text((560,int(origin[1])),f"frame{m['frameIndex']} / evaluated Close {record['Close']}",font=font(18),fill='white')
        for c in cache['curves']:
            owner=c['owner'];valid=[v for v in c['points']if not v.get('unresolved')];q=[];z=[]
            for v in valid:
                ids=np.array(v['vertices']);b=np.array(v['barycentric']);q.append(b@ctx['maps'][owner][ids]);z.append(float(b@ctx['depth'][ids]))
            q=np.array(q);ring=np.array(next(ee for oo in old if oo['sourceId']==m['sourceId']for ee in oo['eyes']if ee['eye']==owner)['canonicalCurve'])
            touched=np.zeros((ch,cw),bool);ringtouch=touched.copy()
            for y in range(ch):
                for x in range(cw):
                    touched[y,x]=any(intersects(a,b,x,y)for a,b in zip(q,q[1:]));ringtouch[y,x]=any(intersects(a,b,x,y)for a,b in zip(ring,ring[1:]))
            dd=curve_distance(ring,q);rr=curve_distance(q,ring)
            # Destination centre candidates all lie on a real current native6
            # triangle. Source colour transport remains a separate reference.
            destinations=[]
            for y,x in np.argwhere(touched):
                hits=carrier_hits([x+.5,y+.5],owner,ctx)
                if not hits:destinations.append({'cellXY':[int(x),int(y)],'status':'no-native-carrier-at-cell-centre'});continue
                target=hits[0];nearest=int(np.argmin(np.linalg.norm(q-[x+.5,y+.5],axis=1)));src=valid[nearest];ids=np.array(src['vertices']);b=np.array(src['barycentric']);srcworld=b@ctx['world'][ids]
                front=front_geometry(target['world'],ctx);destinations.append({'cellXY':[int(x),int(y)],'status':'actual-current-native-carrier','targetPrimitive':target['primitive'],'targetBarycentric':target['barycentric'].tolist(),'targetUV':target['UV'].tolist(),'targetWorld':target['world'].tolist(),'targetDepth':target['depth'],
                  'sourcePrimitive':src['primitive'],'sourceUV':src['sourceUV'],'sourceBarycentric':src['barycentric'],'sourceAlpha':src['sourceAlpha'],'targetOriginalAlpha':float(bilinear(domain['rgba'].astype(float)/255,target['UV'])[3]),'sourceDepth':float(b@ctx['depth'][ids]),
                  'sourceToTargetCanonicalPixels':float(np.linalg.norm(q[nearest]-[x+.5,y+.5])),'sourceToTargetWorldMetres':float(np.linalg.norm(srcworld-target['world'])),
                  'sourceDepthWouldBeWrongBy':float(b@ctx['depth'][ids])-target['depth'],'frontFaceGeometryHits':front,'geometricallyClearOfFullCapturedFace':not front,'externalHairAlphaNotRequeried':True,'renderCandidateAccepted':False})
            curveworld=np.array([np.array(v['barycentric'])@ctx['world'][np.array(v['vertices'])]for v in valid]);visibility=rays.query(curveworld)
            er={'owner':owner,'nativePigmentCurve':q.tolist(),'curveDepth':z,'oldSkinRingCurve':ring.tolist(),'nativeCurveTouchedCellsXY':np.argwhere(touched)[:,::-1].tolist(),'skinRingTouchedCellsXY':np.argwhere(ringtouch)[:,::-1].tolist(),
              'curveFaceGeometryClearPoints':sum(v['geometricallyClear']for v in visibility),'curveFaceGeometryPotentiallyBlockedPoints':sum(not v['geometricallyClear']for v in visibility),
              'curveExternalHairVisibilityNotObservedAtEveryReferencePoint':True,
              'skinRingToPigmentCurveDistanceMaxPixels':float(dd.max()),'pigmentToSkinRingCurveDistanceMaxPixels':float(rr.max()),'destinations':destinations,'minimumOneCellLineRepresentationIsNotMassRounding':True}
            record['eyes'].append(er)
            for line,col in [(ring,'#ffcc58'),(q,'#00eee5')]:dr.line([tuple(origin+v*4*scale)for v in line],fill=col,width=2)
            dr.text((560,int(origin[1]+36+owner*36)),f"eye{owner}: pigment path {int(touched.sum())} cells / skin-ring {int(ringtouch.sum())}",font=font(17),fill='#b8dbe7')
        results.append(record)
    board.save(H/'PIGMENT_VS_RING109.png');(H/'GEOMETRY109.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf8')
    print(json.dumps([{'frame':r['frame'],'Close':r['Close'],'probe':r['probe'],'eyes':[{'owner':e['owner'],'nativeCells':len(e['nativeCurveTouchedCellsXY']),'ringCells':len(e['skinRingTouchedCellsXY']),'ringToPigmentMax':e['skinRingToPigmentCurveDistanceMaxPixels'],
       'realDestinations':sum(d['status']=='actual-current-native-carrier'for d in e['destinations']),'geometricallyClearDestinations':sum(d.get('geometricallyClearOfFullCapturedFace',False)for d in e['destinations'])}for e in r['eyes']]}for r in results]))
if __name__=='__main__':main()
