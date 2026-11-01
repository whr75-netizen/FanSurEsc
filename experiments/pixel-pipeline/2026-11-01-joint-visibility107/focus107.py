"""Explicit remaining geometry/feature tradeoffs and phase source-colour audit."""
from pathlib import Path
import sys,json
import numpy as np
H=Path(__file__).resolve().parent;R=H.parent
sys.path.insert(0,str(R/'forward-eye102'));from analyse102 import load,buffer,components
from analyse_capture68 import plane,rgb8
sys.path.insert(0,str(R/'live-curve106'));from analyse106 import curve_segments,signature
from curve_reference106 import intersects
from joint_reference107 import contributions
def main():
    s=load(sorted((H/'capture-final').glob('STATE107-*'))[-1]);rows=[];phase={}
    for e in s['sequencePackets']:
        if not('measured-phase'in e['testStage82']or e['frame']in [99,101,103,107,192]):continue
        p=Path(e['output']);m=load(p/'RAW_MANIFEST.json');w,h=m['forward102']['denseSize'];cw,ch=w//8,h//8
        ls=np.zeros((4,5,h,w,4),np.float32);v=np.zeros((4,h,w,4),np.float32)
        for part in [1,2]:ls[part,1]=np.flipud(plane(p/('D-part'+str(part)+'-meta.plane'))[1])
        for channel,name in enumerate(['rgba','meta','rest','uv']):ls[3,channel]=np.flipud(plane(p/('D-lid-'+name+'.plane'))[1])
        v[1:4]=buffer(p/'dense-three-part-visibility.f32').reshape(3,h,w,4);ids=buffer(p/'curve-identity.f32');col=buffer(p/'curve-colour.f32');audit=buffer(p/'curve-audit.f32');bi=buffer(p/'canonical-identity.f32');seg=curve_segments(p/'curve-segments106.f32')
        if'measured-phase'in e['testStage82']:
            phase.setdefault(e['testStage82'],[]).append({'frame':e['frame'],'signature':signature(ids.reshape(ch,cw,4),col.reshape(ch,cw,4),m['forward102']['nativeRegistration']['bounds'][:2])})
        if e['frame']not in [99,101,103,107,192]:continue
        focus=[]
        for k in range(cw*ch):
            y,x=divmod(k,cw)
            if e['frame']==101 and[x,y]not in [[3,3],[4,3],[5,3],[12,3],[13,3],[11,4],[14,3],[7,4]]:continue
            if e['frame']==192 and[x,y]not in [[4,4],[5,4],[4,5],[3,6],[4,6],[3,9]]:continue
            if e['frame']in [99,103,107]and not((ids[k,0]==6 and bi[k,0]in [1,4])or(ids[k,0]==6 and not any(intersects(q[0,:2],q[1,:2],[x,y])for q in seg))):continue
            support={str(eye):{'jointLowerMass':np.zeros(3),'dominantSamples':np.zeros(3,dtype=int)}for eye in [1,2]}
            for yy in range(y*8,y*8+8):
                for xx in range(x*8,x*8+8):
                    lo,hi=contributions(ls,v,yy,xx)
                    for part in range(3):
                        eye=round(float(ls[part+1,1,yy,xx,2]));r=support.get(str(eye))
                        if r is None:continue
                        r['jointLowerMass'][part]+=lo[part]
                        if all(lo[part]>hi[q]for q in range(4)if q!=part):r['dominantSamples'][part]+=1
            for r in support.values():r['jointLowerMass']=(r['jointLowerMass']/64).tolist();r['dominantSamples']=r['dominantSamples'].tolist()
            focus.append({'canonicalXY':[x,y],'old102':bi[k].tolist(),'new107':ids[k].tolist(),'audit':audit[k].tolist(),'perEyeSource':support,'curveTouched':any(intersects(q[0,:2],q[1,:2],[x,y])for q in seg)})
        rows.append({'frame':e['frame'],'sourceId':m['sourceId'],'stage':e['testStage82'],'cells':focus})
    phaseReport={}
    for stage,seq in phase.items():
        base=seq[0]['signature'];changes=[]
        for entry in seq[1:]:
            for k in base.keys()&entry['signature'].keys():
                if base[k]!=entry['signature'][k]:changes.append({'frame':entry['frame'],'sourceLocalKey':list(k),'beforeRGB8':base[k],'afterRGB8':entry['signature'][k]})
        phaseReport[stage]={'frames':len(seq),'RGB8changedObservations':len(changes),'maximumCodeDelta':max([max(abs(a-b)for a,b in zip(r['beforeRGB8'],r['afterRGB8']))for r in changes]or[0]),'changes':changes}
    result={'focus':rows,'phaseRGB':phaseReport,'interpretation':'a front-visible witness justifies source eligibility, not a unique whole-cell artistic winner; remaining source-supported conflicts require joint shape allocation, not another blanket priority'}
    (H/'FOCUS107.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps({'phase':{k:{a:b for a,b in v.items()if a!='changes'}for k,v in phaseReport.items()},'focusCells':sum(len(r['cells'])for r in rows)}))
if __name__=='__main__':main()
