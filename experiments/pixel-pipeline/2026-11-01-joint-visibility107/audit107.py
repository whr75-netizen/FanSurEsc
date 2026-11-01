"""Frozen106 evidence: source parts, skin visibility, depth-aware competition.
No Unity calls, no colour/geometry tuning. Does not promote102 ownership to truth.
"""
from pathlib import Path
import sys,json,collections
import numpy as np
H=Path(__file__).resolve().parent;R=H.parent
sys.path.insert(0,str(R/'forward-eye102'));from analyse102 import load,buffer
sys.path.insert(0,str(R/'live-curve106'));from analyse106 import curve_segments
from curve_reference106 import intersects,distance
F=np.float32

def main():
    rows=[];states=load(sorted((R/'live-curve106/capture').glob('STATE106-*'))[-1])
    for entry in states['sequencePackets']:
        if entry['frame']not in [99,101,103,107,190,192]:continue
        p=Path(entry['output']);m=load(p/'RAW_MANIFEST.json');w,h=m['forward102']['canonicalSize']
        a=buffer(p/'canonical-layers.f32').reshape(4,5,h,w,4);v=buffer(p/'canonical-visibility.f32').reshape(4,h,w,4)
        ids=buffer(p/'canonical-identity.f32');audit=buffer(p/'curve-audit.f32');seg=curve_segments(p/'curve-segments106.f32')
        for k in np.flatnonzero(np.isin(audit[:,0],[2,-1])):
            y,x=divmod(int(k),w//4);eyes=sorted({round(float(s[0,3]))for s in seg if intersects(s[0,:2],s[1,:2],[x,y])})
            samples=[];totals=np.zeros(4,np.float32);candidate=[]
            for yy in range(y*4,y*4+4):
                for xx in range(x*4,x*4+4):
                    parts=[]
                    for part,role in [(1,1),(2,4),(3,6)]:
                        meta=a[part,1,yy,xx];vv=v[part,yy,xx]
                        if meta[0]<=0 or a[part,0,yy,xx,3]<=0:continue
                        parts.append({'role':role,'owner':round(float(meta[2])),'depth':float(meta[0]),'alpha':float(a[part,0,yy,xx,3]),'visibility':vv[:2].tolist(),'UVPrimitive':a[part,3,yy,xx].tolist()})
                    order=sorted(parts,key=lambda q:q['depth']);lo=F(1);hi=F(1)
                    for item in order:
                        vl,vh=map(F,item['visibility']);item['frontLoHi']=[float(F(lo*vl)),float(F(hi*vh))]
                        totals[{1:0,4:1,6:2}[item['role']]]+=F(lo*vl)
                        lo=F(lo*F(1-vh));hi=F(hi*F(1-vl))
                    totals[3]+=lo
                    lid=next((q for q in parts if q['role']==6 and q['owner']in eyes),None)
                    if lid is not None and lid['visibility'][0]>0 and lid['visibility'][0]==lid['visibility'][1]:
                        d=min(distance(np.array([xx+.5,yy+.5],np.float32)*F(.25),s[0,:2],s[1,:2])for s in seg if round(s[0,3])==lid['owner'])
                        candidate.append((float(d),-lid['visibility'][0],xx,yy,lid))
                    if parts:samples.append({'sampleXY':[xx,yy],'parts':parts})
            candidate.sort(key=lambda q:(q[0],q[1]))
            chosen=None if not candidate else{'sampleXY':[candidate[0][2],candidate[0][3]],'distanceSquared':candidate[0][0],**candidate[0][4]}
            row={'frame':entry['frame'],'sourceId':m['sourceId'],'canonicalXY':[x,y],'curveEyes':eyes,'audit106':audit[k].tolist(),'selected102':ids[k].tolist(),'jointVisibleMassIrisWhiteLidCanvas':totals.tolist(),'closestSkinVisibleLid':chosen,'samples':samples}
            rows.append(row)
            print(json.dumps({k:v for k,v in row.items()if k!='samples'}),flush=True)
    (H/'AUDIT107.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
if __name__=='__main__':main()
