"""Finite same-eye destination carrier scan for the Close75 counterexample.
This measures carrier geometry, not original bank-colour occupancy.
"""
from pathlib import Path
import json,numpy as np
from geometry111 import H,read,load,packet_list
from ray111 import NativeAlpha,FaceRay
from analyse111 import expose
def main():
    state,paths=packet_list();rows=[]
    for frame in [105,122,125,128]:
        p=next(p for p in paths if read(p/'RAW_MANIFEST.json')['frameIndex']==frame);ctx=load(p);alpha=NativeAlpha(ctx);rays=FaceRay(ctx,alpha);d=read(H/f'ANALYSIS111-frame{frame}.json');owner=2;e=next(e for e in d['eyes']if e['owner']==owner);cols=dict(e['curveColumns']);w,h=ctx['size'];out=[]
        for part in [1,2]:
            labels=np.zeros((h,w),np.int8)
            for x,y in cols.items():
                if 0<=x<w:
                    for yy in range(max(0,y+1),h):labels[yy,x]=part
            records=expose(ctx,alpha,rays,owner,labels)
            for c in records:
                c['sourceFaceCarrierNumerator']=[sum(s.get('sourceFaceAlphaBounds',[0,0])[k]for s in c['samples'])for k in [0,1]]
            out.append({'part':part,'records':records,'sourceFaceMajorityCells':[c['cellYX']for c in records if c['sourceFaceCarrierNumerator'][0]>=8],'finalMajorityCells':[c['cellYX']for c in records if c['visibleCarrierFractionBounds'][0]>=8],'singleSourceColourNotRequiredAtDestination':True})
        r={'sourceId':ctx['sourceId'],'frame':frame,'owner':owner,'candidateDomain':'same-eye native carrier and below native pigment boundary; original colour occupancy not a hard destination mask','parts':out,'thresholdMeaning':'8/16 is inherited pixel majority representability, not a fixed number of eye pixels; thin UpperLine uses separate boundary semantics','notFinalRGB':True};(H/f'DESTINATIONS111-frame{frame}.json').write_text(json.dumps(r,indent=2)+'\n');rows.append(r);print(json.dumps({'frame':frame,'parts':[{'part':v['part'],'faceMajority':v['sourceFaceMajorityCells'],'finalMajority':v['finalMajorityCells']}for v in out]}),flush=True)
if __name__=='__main__':main()
