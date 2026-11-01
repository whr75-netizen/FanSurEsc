"""Stored source -> current carrier footprint + bounded visibility adapter.

Original GPU samples are the reference for iris/white. Native lid reference is
109's actual UV pigment curve, not skin-ring. Full105 is direct captured mesh;
107 uses the explicitly tested reconstruction hypothesis (see reconstruction).
The output retains ALL clipped triangles, barycentric/UV/world/depth vertices,
and per-fine-sample visibility. It does not declare whole-cell visibility.
External hair is only certified at its recorded display-sample coordinates.
"""
from pathlib import Path
import sys,json,math
import numpy as np
from PIL import Image
from stored110 import H,R,P109,P108,source_packet,plane,load_fields
from native109 import read,uv_bary,components
from geometry109 import physical,prepare_packet
from footprint109 import clip,area
from measure109 import mesh_graph
from reconstruct110 import template,recover
from io109 import buffer,packet,joint_arrays

class FaceVisibility:
    """Same face Query alpha interval semantics, two-sided source face (cull0).
    No hit is clear of the reconstructed face hypothesis, not all geometry.
    Full footprint queries are kept distinct; depth ties remain unknown.
    """
    def __init__(self,ctx):
        self.ctx=ctx;self.ids=ctx['indices'][3];self.xy=ctx['physicalXY'][self.ids];self.z=ctx['depth'][self.ids];self.w=ctx['physicalW'][self.ids]
        a=np.stack([self.xy[:,1]-self.xy[:,0],self.xy[:,2]-self.xy[:,0]],axis=2);det=np.linalg.det(a);self.good=abs(det)>1e-18;self.inv=np.zeros_like(a);self.inv[self.good]=np.linalg.inv(a[self.good])
        self.alpha=np.asarray(Image.open(H/'inputs/image-5.png').convert('RGBA'))[:,:,3]/255.
    def query(self,points):
        if not len(points):return []
        points=np.asarray(points);q,z,_=physical(self.ctx['view'],self.ctx['projection'],points);out=[];tex=self.alpha;hh,ww=tex.shape
        for start in range(0,len(q),32):
            v=q[None,start:start+32]-self.xy[:,0,None];ab=np.einsum('tij,tqj->tqi',self.inv,v);b=np.concatenate([1-ab.sum(2,keepdims=True),ab],axis=2);pw=b/self.w[:,None];pw/=pw.sum(2,keepdims=True);depth=(pw*self.z[:,None]).sum(2)
            front=self.good[:,None]&(b.min(2)>=-1e-7)&(depth<z[None,start:start+32]-3e-5)
            for j in range(len(v[0])):
                ix=np.where(front[:,j])[0];lo=hi=1.;hits=[]
                for t in ix:
                    uv=pw[t,j]@self.ctx['uv'][self.ids[t]];pos=np.array([uv[0]*ww-.5,(1-uv[1])*hh-.5]);xx,yy=np.floor(pos).astype(int)
                    a=[tex[np.clip(yy+dy,0,hh-1),np.clip(xx+dx,0,ww-1)]for dy in [0,1]for dx in [0,1]];al=1. if min(a)>=.5 else 0.;ah=0. if max(a)<.5 else 1.
                    lo*=1-ah;hi*=1-al
                    if ah:hits.append({'primitive':int(t+1),'depth':float(depth[t,j]),'UV':uv.tolist(),'alphaBounds':[al,ah]})
                out.append({'visibleBounds':[lo,hi],'frontAlphaFaces':hits})
        return out

def source_points(row,ctx,owner,cache):
    p=source_packet(row);m,scale,ls,vis=load_fields(p);lo,hi,*_=joint_arrays(ls,vis);refs={};uncertain={};keys={}
    for part,i in [(1,0),(4,1)]:
        a=(lo[i]>0)&(np.rint(ls[i+1,1,:,:,2])==owner);b=(hi[i]>lo[i])&(np.rint(ls[i+1,1,:,:,2])==owner)
        refs[{1:1,4:2}[part]]=np.argwhere(a)[:,::-1]/scale+.5/scale;uncertain[str(part)]=int(b.sum())
    curve=next(c for c in cache['curves']if c['owner']==owner);valid=[v for v in curve['points']if not v.get('unresolved')];points=[];world=[]
    for v in valid:
        ids=np.array(v['vertices']);b=np.array(v['barycentric']);points.append(b@ctx['maps'][owner][ids]);world.append(b@ctx['world'][ids])
    visibility=FaceVisibility(ctx).query(world);q=np.array(points);visible=np.array([v['visibleBounds'][0]>0 for v in visibility]);refs[3]=q[visible]
    # Never join a reference arc through a blocked or unknown interval.
    runs=[];current=[]
    for i,yes in enumerate(visible):
        if yes:current.append(i)
        elif current:runs.append(current);current=[]
    if current:runs.append(current)
    return refs,{'sourceId':row['sourceId'],'owner':owner,'nativeCurvePoints':q.tolist(),'nativeCurveWorld':np.array(world).tolist(),'nativeCurveVisibility':visibility,'nativeVisibleRuns':runs,
      'uncertainGPUReferenceSamples':uncertain,'sourceReferenceBeforeExternalHair':True,'independentLightingAndRGBNotUsed':True},ls,vis

def build(row,owner,domain,templates,cache):
    direct=row['name'].startswith('closed105')
    if direct:
        ctx=prepare_packet(source_packet(row),domain,cache);cal=[];c=float(ctx['manifest']['motion82']['requestedClose'])/100
    else:ctx,cal,c=recover(row,domain,templates)
    refs,reference,ls,vis=source_points(row,ctx,owner,cache);m=ctx['manifest'];ww,hh=m['forward102']['canonicalSize'];w,h=ww//4,hh//4
    active=[p for p,q in refs.items()if len(q)];source=np.concatenate([refs[p]for p in active])if active else np.empty((0,2));cells=[(y,x)for y in range(h)for x in range(w)]
    eligible=np.zeros((len(cells),4),bool);eligible[:,0]=True;records=[];rays=FaceVisibility(ctx);_,groups,_=mesh_graph(domain['triangles']);upper=next(v for v in cache['curves']if v['owner']==owner);component=groups[upper['points'][0]['primitive']-1]
    pp=source_packet(row);hair=np.flipud(plane(pp/'S4-meta.plane')[1]);hairRGBA=np.flipud(plane(pp/'S4-rgba.plane')[1]);roi=np.array(m['grid102']['eyeTopLeftROI']);nr=m['forward102']['nativeRegistration'];offset=np.array(nr['anchor'])+np.array(nr['bounds'][:2])
    # Current carrier footprints, independent of native destination pigment.
    # Transporting pigment onto an alpha0 destination still requires real
    # carrier geometry and current per-sample face/hair visibility.
    for pi,part in [(1,1),(2,4),(3,6)]:
        if pi not in active:continue
        for ci,(y,x)in enumerate(cells):
            # Canonical layout is continuous-anchor local. Its destination
            # display pixel has a phase-shifted footprint. Evaluate geometry
            # at EXACT captured S4 sample positions, not a nearby canonical
            # point with a copied depth or nearest hair value.
            display=np.floor(np.array([x,y])+offset-roi[:2]+.5).astype(int);origin=roi[:2]+display-offset
            pieces=[];samples=[]
            for tid,ids in enumerate(ctx['indices'][part]):
                if part==6 and groups[tid]!=component:continue
                if np.min(ctx['owners'][ids])!=owner or np.max(ctx['owners'][ids])!=owner:continue
                t=ctx['maps'][owner][ids]
                if np.any(t.max(0)<origin)or np.any(t.min(0)>origin+1):continue
                polygon=clip(t,origin);a=area(polygon)
                if a<=0:continue
                b=polygon[:,2:];pieces.append({'primitive':tid+1,'XY':polygon[:,:2].tolist(),'barycentric':b.tolist(),'world':(b@ctx['world'][ids]).tolist(),'UV':(b@ctx['uv'][ids]).tolist(),'depth':(b@ctx['depth'][ids]).tolist(),'areaNotUnion':a})
                yy,xx=np.mgrid[0:4,0:4];q=np.c_[(xx.ravel()+.5)/4,(yy.ravel()+.5)/4]+origin;bb=uv_bary(t,q)
                if bb is None:continue
                for si in np.where(bb.min(1)>=-1e-10)[0]:
                    point=q[si];bary=bb[si];samples.append({'XY':point.tolist(),'world':(bary@ctx['world'][ids]).tolist(),'depth':float(bary@ctx['depth'][ids]),'UV':(bary@ctx['uv'][ids]).tolist(),'primitive':tid+1,'barycentric':bary.tolist(),'displaySampleIndexYX':[int(display[1]*4+yy.ravel()[si]),int(display[0]*4+xx.ravel()[si])]})
            if not pieces:continue
            # Avoid making a missed 8x sample a geometric absence. The polygon
            # centroid is an extra carrier witness, not extra measured mass.
            if not samples:
                for piece in pieces:
                    samples.append({'XY':np.mean(piece['XY'],0).tolist(),'world':np.mean(piece['world'],0).tolist(),'depth':float(np.mean(piece['depth'])),'UV':np.mean(piece['UV'],0).tolist(),'primitive':piece['primitive'],'barycentric':np.mean(piece['barycentric'],0).tolist(),'polygonInteriorWitnessNotCoverageSample':True})
            for sample,v in zip(samples,rays.query([s['world']for s in samples])):
                sample.update(v);sample['faceVisibleBounds']=v['visibleBounds'].copy();i=sample.get('displaySampleIndexYX')
                if i is None or not(0<=i[0]<len(hair)and 0<=i[1]<hair.shape[1]):
                    sample['externalHairVisibilityUnobserved']=True;sample['visibleBounds']=[0,v['visibleBounds'][1]];continue
                hm=hair[tuple(i)];hc=hairRGBA[tuple(i)];front=hm[0]>0 and hm[3]>0 and hc[3]>0 and hm[0]<sample['depth']-3e-5;coverage=float(np.clip(hm[3],0,1))if front else 0.
                sample['externalHair']={'sourceId':row['sourceId'],'sameRecordedSample':True,'metadata':hm.tolist(),'inFrontOfThisSurface':bool(front),'coverage':coverage};sample['visibleBounds']=[b*(1-coverage)for b in v['visibleBounds']]
            eligible[ci,pi]=any(s['visibleBounds'][0]>0 for s in samples)
            records.append({'cellYX':[y,x],'part':pi,'sourcePart':part,'displayCellTopLeft':(roi[:2]+display).tolist(),'targetOriginCanonical':origin.tolist(),'pieces':pieces,'samples':samples,'eligibleWitnessNotWholeCellOwner':bool(eligible[ci,pi]),'wholeCellVisibilityCertified':False})
    # Restrict finite solve to cells with an actual currently eligible carrier.
    keep=np.where(eligible[:,1:].any(1))[0];cells=[cells[i]for i in keep];eligible=eligible[keep]
    # Connectivity is imposed only when certain current source support has ONE
    # component. Occlusion-split references are not forcibly reconnected.
    connectivity={}
    carrierCC={}
    for p in [1,2,3]:
        mask=np.zeros((h,w),bool)
        for i,(y,x)in enumerate(cells):mask[y,x]=eligible[i,p]
        _,cc=components(mask,p==3);carrierCC[p]=len(cc)
    for p in [1,2]:
        if len(refs[p]):
            mask=np.zeros((hh*2,ww*2),bool);q=np.floor(refs[p]*8).astype(int);mask[q[:,1],q[:,0]]=True
            _,cc=components(mask,False)
            if len(cc)==1 and carrierCC[p]==1:connectivity[p]=False
    if len(reference['nativeVisibleRuns'])==1 and carrierCC[3]==1:connectivity[3]=True
    reference['currentCarrierComponents']=carrierCC
    reference['doNotForceConnectivityAcrossCurrentOcclusion']=True
    return {'cells':cells,'eligibility':eligible,'references':refs,'connectivity':connectivity},reference,records,{'Close':c,'calibration':cal,'sourceId':row['sourceId'],'frame':row['frame'],'reconstructedGeometry':not direct,'canonicalSize':[w,h],'carrierIncludesSameFrameExternalHairPerRecordedSample':True,'referenceCurveExternalHairVisibilityBetweenSamplesUnobserved':True},ctx
