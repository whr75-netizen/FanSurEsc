"""Inspect an explicit SOURCE-bank canvas-binding hypothesis, not anatomy.

Nearest-eye owner tags on face triangles label whole face halves. They are NOT
semantic feature IDs. Test actual registered source bank footprints instead;
do not skip all skin or treat an inferred canvas binding as native lid data.
"""
import json,numpy as np
from geometry111 import H,read,load,packet_list
from analyse111 import bank_data

def source_domain(ctx,owner,hit,bank):
    tid=hit['triangle'];ids=ctx['triangles'][tid,:3];uv=ctx['uv'][ids];a=np.stack([uv[1]-uv[0],uv[2]-uv[0]],axis=1)
    if abs(np.linalg.det(a))<1e-16:return {'status':'unknown UV degeneracy'}
    q=np.linalg.solve(a,np.array(hit['UV'])-uv[0]);b=np.r_[1-q.sum(),q];rest=np.r_[b@ctx['rest'][ids],1];xy=np.array([rest@ctx['projectionX'][owner],rest@ctx['projectionY'][owner]]);pixel=np.floor(xy).astype(int);keys=[k for k in bank if k[0]==owner and tuple(k[2:])==tuple(pixel)];return {'status':'inside registered source bank footprint'if keys else'outside source bank footprint','sourceRestHead':rest[:3].tolist(),'sourceXY':xy.tolist(),'bankKeys':[list(k)for k in keys],'notAnatomicalLidClassification':True}

def main():
    _,paths=packet_list();bank,_=bank_data();out=[]
    for frame in [105,122,125,128]:
        p=next(p for p in paths if read(p/'RAW_MANIFEST.json')['frameIndex']==frame);ctx=load(p);analysis=read(H/f'ANALYSIS111-frame{frame}.json');eye=analysis['eyes'][1];variant=next(v for v in eye['variants']if v['componentFirst']);rows=[]
        for labelIndex,cells in enumerate(variant['exposure']):
            for cell in cells:
                if cell['part']not in[1,2]:continue
                points=[]
                for sample in cell['samples']:
                    hits=[source_domain(ctx,2,h,bank)for c in sample.get('frontCarriers',[])for h in c['face']['hits']];points.append({'fine':sample['fine'],'physicalVisible':sample['visibleBounds'],'faceHits':hits,'allBlockingFacesInsideSourceBank':bool(hits)and all(h['status']=='inside registered source bank footprint'for h in hits)})
                rows.append({'layout':labelIndex,'cellYX':cell['cellYX'],'part':cell['part'],'strictPhysicalVisible':cell['visibleCarrierFractionBounds'],'denominator':16,'samples':points,'insideSourceBankBlockingSamples':sum(v['allBlockingFacesInsideSourceBank']for v in points)})
        out.append({'sourceId':ctx['sourceId'],'frame':frame,'owner':2,'cells':rows})
    result={'hypothesis':'Registered immutable SOURCE bank footprint binds a local feature canvas; source availability/Close resolved before stylized allocation, external occlusion after. Not adopted.','actualOwnerTagCode':'EyeFeature348.Initialise assigns every face vertex to whichever eye centre is closer (UV7); this alone cannot distinguish generic skin from actual lid.','frames':out,'sourceDomainIsNotNativeLidTruth':True,'noNewUnityOrGPU':True};(H/'CANVAS_BINDING111.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps([{'frame':r['frame'],'cells':[{'part':c['part'],'cell':c['cellYX'],'physical':c['strictPhysicalVisible'],'sourceDomainBlockers':c['insideSourceBankBlockingSamples']}for c in r['cells']]}for r in out]))
if __name__=='__main__':main()
