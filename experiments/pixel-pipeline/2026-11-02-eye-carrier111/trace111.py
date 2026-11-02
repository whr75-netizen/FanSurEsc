"""Frozen current-source provenance before allocation; no guessed source IDs."""
from pathlib import Path
import sys,json,gzip
import numpy as np
H=Path(__file__).resolve().parent;R=H.parent
def related(a,b):return R/a if(R/a).exists()else R/b
P22=related('argon22-boundary','2026-11-01-argon22-boundary');P110=related('joint-resolver110','2026-11-01-joint-resolver110');sys.path[:0]=[str(P22),str(P110)]
from stored110 import P108,P109,source_packet,load_fields
from history109 import source_histograms
from io109 import buffer,joint_arrays
def read(p):return json.loads(p.read_text(encoding='utf8'))
def components(points):
    left=set(points);result=[]
    while left:
        todo=[left.pop()];c=[]
        while todo:
            q=todo.pop();c.append(q);x,y=q
            for p in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
                if p in left:left.remove(p);todo.append(p)
        result.append(sorted(c))
    return result
def main():
    source=read(P109/'inputs/SOURCE_FIXTURE88.json');bank={(v['owner'],v['part'],v['x'],v['y']):source['paletteRGB8'][v['palette']]for v in source['source']};reg=read(P109/'inputs/REGISTRATION89.json');projection={e['eye']:np.array(e['nativeToAuthoredProjection'],np.float32)for e in reg['eyes']};rows=read(P108/'INPUT108.json');out=[];alloc=read(P22/'TOPOLOGY_RESULTS22.json')
    banks={str(owner):components([(v['x'],v['y'])for v in source['source']if v['owner']==owner and v['part']==4])for owner in [1,2]}
    for row in rows:
        if not row['name'].startswith('actual107')or row['frame']not in [99,101,103,105,107,109,115,121,125,129,204,207,210]:continue
        p=source_packet(row);m,scale,a,v=load_fields(p);lo,hi,*_=joint_arrays(a,v);assert m['sourceId']==row['sourceId'];cells,available,check=source_histograms(row,bank,projection,p);ownerRows=[]
        for owner in [1,2]:
            valid=np.rint(a[2,1,:,:,2])==owner;rawMass=float(v[2,:,:,0][valid].sum(dtype=np.float64)/scale**2);low=float(lo[1][valid].sum(dtype=np.float64)/scale**2);high=float(hi[1][valid].sum(dtype=np.float64)/scale**2);coarse={}
            for yy,xx in np.argwhere(valid&(hi[1]>0)):
                key=(int(yy)//scale,int(xx)//scale);q=coarse.setdefault(key,{'cellYX':list(key),'certainMass':0.,'possibleMass':0.,'faceCertainBeforeOtherEyeParts':0.,'fineSamples':[]});q['certainMass']+=float(lo[1,yy,xx])/scale**2;q['possibleMass']+=float(hi[1,yy,xx])/scale**2;q['faceCertainBeforeOtherEyeParts']+=float(v[2,yy,xx,0])/scale**2;q['fineSamples'].append({'fineYX':[int(yy),int(xx)],'sourceDepth':float(a[2,1,yy,xx,0]),'partVisibilityInterval':v[2,yy,xx,:2].tolist(),'jointIrisWhiteLidContributionInterval':[float(lo[1,yy,xx]),float(hi[1,yy,xx])],'sourceIDAtThis8xSampleRecorded':False})
            ah,ch=m['forward102']['canonicalSize'];aa=buffer(p/'canonical-layers.f32').reshape(4,5,ch,ah,4);vv=buffer(p/'canonical-visibility.f32').reshape(4,ch,ah,4);ll,hh,*_=joint_arrays(aa,vv);identity=[]
            for yy,xx in np.argwhere((ll[1]>0)&(np.rint(aa[2,1,:,:,2])==owner)):
                r=np.r_[aa[2,2,yy,xx,:3],np.float32(1)].astype(np.float32);q=r@projection[owner];k=(owner,4,*np.floor(q).astype(int));assert k in bank
                group=next(i for i,c in enumerate(banks[str(owner)])if tuple(k[2:])in c);identity.append({'fineYX':[int(yy),int(xx)],'cellYX':[int(yy)//4,int(xx)//4],'sourceKey':list(map(int,k)),'bankWhiteComponent':group,'nativePrimitive':int(round(float(aa[2,3,yy,xx,2]))),'sourceUV':aa[2,3,yy,xx,:2].tolist(),'sourceRestHead':aa[2,2,yy,xx,:3].tolist(),'sourceDepth':float(aa[2,1,yy,xx,0]),'certainJointWeight':float(ll[1,yy,xx])/16,'paletteRGB8':bank[k],'observedGPU4x':True})
            c=next(c for c in alloc['cases']if c['sourceId']==row['sourceId']and c['owner']==owner);labels=np.array(c['labels'][0]);massByGroup={str(i):sum(x['certainJointWeight']for x in identity if x['bankWhiteComponent']==i)for i in range(len(banks[str(owner)]))}
            for q in coarse.values():q['allocationLabel']=int(labels[tuple(q['cellYX'])]);q['boundaryRow']=dict(next(b for b in read(P22/'RESULTS22.json')['cases']if b['sourceId']==row['sourceId']and b['owner']==owner)['literalBoundaryRowsXY']).get(q['cellYX'][1])
            ownerRows.append({'owner':owner,'whiteFaceVisibleMassBeforeEyePartAttenuation':rawMass,'whiteJointMassBounds8x':[low,high],'whiteSourceIDMass4x':sum(x['certainJointWeight']for x in identity),'whiteBankComponentMass4x':massByGroup,'visibleSourceIdentities4x':identity,'sourceCells8x':list(coarse.values()),'selectedIrisWhiteLineCounts':c['counts'],'allocationObjective':c['allocation']['exactObjective'],'sourceAbsenceNotProvedWhenPositive':low>0,'externalHairDoesNotEnterSourceShapeQuery':True})
        out.append({'sourceId':row['sourceId'],'frame':row['frame'],'stage':row['stage'],'scaleOfAllocationInput':scale,'scaleOfRecordedSourceIDs':4,'exact8xSourceIDNotInvented':True,'check4x':check,'eyes':ownerRows})
    result={'bankWhiteComponents':banks,'frames':out,'newUnityCaptures':0,'limits':['4x source IDs and8x contribution buffers are the SAME frame/source, not the same subpixel samples.','Positive lower-bound source contribution proves current observed support, not a mandatory final pixel.','Eye part alpha attenuation is separate from external hair.','Final destination coverage/owner is not a source-mass statistic.']};(H/'WHITE_SOURCE111.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'frames':len(out),'bankWhiteComponents':banks,'focus':[{'frame':f['frame'],'eye':e['owner'],'joint8':e['whiteJointMassBounds8x'],'sourceIDs4':e['whiteBankComponentMass4x'],'labels':e['selectedIrisWhiteLineCounts']}for f in out if f['frame']in[105,109]for e in f['eyes']]}))
if __name__=='__main__':main()
