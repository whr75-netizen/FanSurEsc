"""Compare identical 4x coordinates to113's 8x-nearest references.
Current source geometry and exact source IDs only. No live GPU claim.
"""
from pathlib import Path
import sys,json,collections
import numpy as np
from paths114 import H,R,folder
P=folder('113')
sys.path.insert(0,str(P))
from inputs113 import load_packets,plane,buffer
from trace114 import geometry,read
from geometry114 import mapped,Face114,carriers
def compose(case,vis,depth,canvas,canvas_meta,selected,part,owner,hairmeta,hairrgba):
    choose=vis[:,0].sum()>=8;known=np.isfinite(depth);colour=canvas.copy();role=4 if canvas_meta[0]>0 else 0;own=float(canvas_meta[2])if role else 0;z=float(canvas_meta[0])if role else 0;status=0
    if choose:
        colour=selected.copy();role=part+1;own=owner;z=float(np.min(depth[known&(vis[:,1]>0)]))
    else:status=-114 if vis[:,1].sum()>=8 else -116 if known.sum()<8 else -117
    hair_lo=np.float32(0);hair_hi=np.float32(0);best=-1;hc=hm=None
    for i,f in enumerate(case['fine']):
        x,y=f['fineXY'];h=hairmeta[y,x];v=hairrgba[y,x]
        if h[0]<=0 or h[3]<=0 or v[3]<=0:continue
        weight=np.float32(np.clip(h[3],0,1));front=bool(known[i]and h[0]<depth[i]-3e-5)if choose else z<=0 or h[0]<z-3e-5;uncertain=choose and not known[i]
        if front:hair_lo=np.float32(hair_lo+weight);hair_hi=np.float32(hair_hi+weight)
        elif uncertain:hair_hi=np.float32(hair_hi+weight)
        if(front or uncertain)and weight>best:best=weight;hc=v;hm=h
    if hair_lo>=8:colour=np.r_[hc[:3],np.float32(1)];role=int(np.rint(hm[1]));own=float(np.rint(hm[2]));z=float(hm[0]);status=0
    elif hair_hi>=8:colour=canvas.copy();role=4;own=float(canvas_meta[2]);z=float(canvas_meta[0]);status=-113
    return {'status':int(status),'role':role,'owner':own,'depth':z,'linearRGBA':colour.tolist(),'hairInterval':[float(hair_lo),float(hair_hi)],'eyeChosenBeforeHair':bool(choose)}
def main():
    trace=read(H/('TRACE_ALL114.json'if'--all-selected'in sys.argv else'TRACE114.json'));source=read(P/'SOURCE113.json');reg=read(H/'REGISTRATION_CURRENT102.json');_,packets=load_packets(P);rows=[];gpu_checks=[];scale=[];scale_queries=[];membership=[]
    for (entry,path),issues in zip(packets,trace['frames']):
        m=read(path/'RAW_MANIFEST.json');ctx=geometry(path,m);origin=np.asarray(issues['carrierOrigin']);ctx=mapped(ctx,reg,origin);face=Face114(ctx,source['ownSkinMask']);r=[];canvas=plane(path/'L0-RGBA.plane')[1];canvasmeta=plane(path/'L0-META.plane')[1];hairmeta=plane(path/'S4-meta.plane')[1];hairrgba=plane(path/'S4-rgba.plane')[1];final=plane(path/'F-FinalRGBA.plane')[1];finalowner=plane(path/'F-FinalOwner.plane')[1];colour=buffer(path/'curve-colour.f32').reshape(-1,4);cw=m['forward102']['canonicalSize'][0]//4
        for case in issues['issues']:
            owner=case['owner'];part={1:1,4:2,6:3}[case['part']];known=[v for v in case['fine']if v['validNativeCarrier']]
            eight=carriers(ctx,owner,part,np.array([v['queryPhysicalXY']for v in case['fine']])-origin)
            for f,hh in zip(case['fine'],eight):
                if bool(hh)!=f['validNativeCarrier']:membership.append({'frame':entry['frame'],'mainXY':case['mainXYBottomLeft'],'fineXY':f['fineXY'],'CPU8x':bool(hh),'GPU8x':f['validNativeCarrier']})
            paired=face.query([v['queryPhysicalXY']for v in known],[v['rawCarrierDepth']for v in known],owner)
            for a,b in zip(known,paired):
                error=max(abs(np.array(b['faceInterval'])-a['faceInterval']));gpu_checks.append({'frame':entry['frame'],'mainXY':case['mainXYBottomLeft'],'fineXY':a['fineXY'],'error':float(error)})
                visibility=[]
                for scale_factor in[.5,1,2]:
                    lo=hi=1.
                    for hit in b['hits']:
                        if not(hit['unilateralRingComponent']and hit['depthGapMetres']*scale_factor<=.012):lo*=1-hit['alphaBounds'][1];hi*=1-hit['alphaBounds'][0]
                    visibility.append([lo,hi])
                scale_queries.append({'frame':entry['frame'],'mainXY':case['mainXYBottomLeft'],'fineXY':a['fineXY'],'visibilityAtHalfCurrentDoubleScale':visibility})
                for hit in b['hits']:scale.append({'frame':entry['frame'],'eye':owner,'mainXY':case['mainXYBottomLeft'],'unilateralRingComponent':hit['unilateralRingComponent'],'depthGapMetres':hit['depthGapMetres'],'exemptAtHalfScale':hit['unilateralRingComponent']and hit['depthGapMetres']*.5<=.012,'exemptAtCurrentScale':hit['exempt113'],'exemptAtDoubleScale':hit['unilateralRingComponent']and hit['depthGapMetres']*2<=.012})
            points=np.array([v['desiredPhysicalXY']for v in case['fine']]);hits=carriers(ctx,owner,part,points-origin);current=[];depths=[];indices=[]
            for i,h in enumerate(hits):
                if h:depths.append(h[0]['depth']);indices.append(i)
            q=face.query(points[indices],depths,owner);vis=np.zeros((16,2));depth=np.full(16,np.nan)
            for i,z,b in zip(indices,depths,q):vis[i]=b['faceInterval'];depth[i]=z
            # Same old16-point decision, now with geometry/depth at the
            # identical point used by S4. Reproduce definite hair overdraw
            # even when the eye was rejected; status0 alone is NOT eye success.
            face_sum=vis.sum(0);px,py=case['tileXYBottomLeft'];cx,cy=case['canonicalXY'];selected=colour[cy*cw+cx];canvas_pixel=canvas[py*4+1,px*4+1];canvas_m=canvasmeta[py*4+1,px*4+1];hm=hairmeta[py*4:py*4+4,px*4:px*4+4];hr=hairrgba[py*4:py*4+4,px*4:px*4+4]
            oldvis=np.array([f['faceInterval']if f['validNativeCarrier']else[0,0]for f in case['fine']]);olddepth=np.array([f['queryDepth']if f['validNativeCarrier']else np.nan for f in case['fine']]);old=compose(case,oldvis,olddepth,canvas_pixel,canvas_m,selected,case['part'],owner,hm,hr);new=compose(case,vis,depth,canvas_pixel,canvas_m,selected,case['part'],owner,hm,hr)
            assert old['status']==case['finalStatus']and np.array_equal(old['linearRGBA'],final[py,px])and old['role']==finalowner[py,px,0]and old['owner']==finalowner[py,px,1],'Reference does not reproduce actual final GPU composition'
            r.append({'mainXY':case['mainXYBottomLeft'],'canonicalXY':case['canonicalXY'],'part':case['part'],'owner':owner,'oldStatus':case['finalStatus'],'oldValidCarrier16':case['knownCarrier16'],'correctPointCarrier16':len(indices),'oldFaceInterval':case['face16Interval'],'correctPointFaceInterval':face_sum.tolist(),'correctPointHairInterval':new['hairInterval'],'correctPointStatus':new['status'],'samePointQueryHasEvidence':len(indices)>0,'missingDepth':sum(not np.isfinite(d)for d in depth),'perFineDepthMinMax':[float(np.nanmin(depth)),float(np.nanmax(depth))]if indices else None,'oldFinal':old,'correctPointFinal':new,'finalRGBAChanged':not np.array_equal(old['linearRGBA'],new['linearRGBA']),'finalRoleChanged':old['role']!=new['role']or old['owner']!=new['owner'],'CPUActualCarriersAt4x':[[{k:h[k]for k in['primitive','depth','UV','barycentric']}for h in hs]for hs in hits],'faceHits4x':q})
        rows.append({'sourceId':entry['sourceId'],'frame':entry['frame'],'issues':r})
    assert gpu_checks and max(q['error']for q in gpu_checks)==0,'CPU reference does not reproduce recorded GPU face query; do not accept correction'
    out={'rows':rows,'knownGPUQueryComparisons':len(gpu_checks),'knownGPUQueryMaxError':max(q['error']for q in gpu_checks),'carrier8xMembershipChecks':sum(len(c['fine'])for r in trace['frames']for c in r['issues']),'carrier8xMembershipMismatches':membership,'samePoint4xGPUNotExecuted':True,'sourceGeometryReconstructed':False,'scaleTestsAreAnalyticSameGeometryNotNewCapturedPoses':True,'scalingCrosses12mm':sum(v['exemptAtHalfScale']!=v['exemptAtDoubleScale']for v in scale),'scaleChangesQueryVisibility':sum(q['visibilityAtHalfCurrentDoubleScale'][0]!=q['visibilityAtHalfCurrentDoubleScale'][2]for q in scale_queries),'scaleQueryRecords':scale_queries,'scaleHitRecords':scale,'oldToCorrectPointStatus':{str(k):n for k,n in collections.Counter((v['oldStatus'],v['correctPointStatus'])for r in rows for v in r['issues']).items()}}
    filename='PAIRING_ALL114.json'if'--all-selected'in sys.argv else'PAIRING114.json';(H/filename).write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'file':filename,'comparedGPUQueries':len(gpu_checks),'maxError':out['knownGPUQueryMaxError'],'changedCases':[{'frame':r['frame'],**{k:q[k]for k in['mainXY','part','oldStatus','correctPointStatus','oldValidCarrier16','correctPointCarrier16','correctPointFaceInterval']}}for r in rows for q in r['issues']if q['oldStatus']!=q['correctPointStatus']],'scaleCrossings':out['scalingCrosses12mm'],'scaleChangesQueryVisibility':out['scaleChangesQueryVisibility'],'status':out['oldToCorrectPointStatus']},ensure_ascii=False))
if __name__=='__main__':main()
