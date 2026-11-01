from pathlib import Path
import json
import numpy as np
from graph_regions104 import same_partition
from watershed104 import segment

def main():
    mask=np.ones((48,96),bool)
    ramp=np.broadcast_to(np.linspace(40,180,96).astype(np.uint8)[None,:,None],(48,96,3)).copy()
    step=np.full((48,96,3),45,np.uint8);step[:,48:]=225
    for i,v in enumerate([55,90,155,210]):step[:,46+i]=v
    stripe=np.full_like(step,210);stripe[:,47]=45
    corner=np.full_like(step,210);corner[15:34,42]=45;corner[33,42:57]=45
    out=[]
    for name,rgb in [('ramp',ramp),('aaStep',step),('oneTexelStripe',stripe),('Lcorner',corner)]:
        a=segment(rgb,mask);rot=segment(np.rot90(rgb),np.rot90(mask));b=np.rot90(rot['labels'],-1)
        # Exact watershed ties remain visible in the fixture, not counted as a
        # complete partition or hidden by a later nearest-neighbour fill.
        valid=mask&(a['labels']>=0)&(b>=0)
        same=same_partition(a['labels'],b,valid)
        assert same and np.array_equal(a['labels']==-2,b==-2),name+' orientation bias'
        row={'fixture':name,'markers':a['markerCount'],'regions':len(np.unique(a['labels'][a['labels']>=0])),
             'uncertain':int((a['labels']==-2).sum()),'rotationEquivalent':same}
        if name in ('oneTexelStripe','Lcorner'):
            fg=rgb[...,0]==45;row['originalFeatureRegionIds']=np.unique(a['labels'][fg]).tolist()
            row['featureFullyOneRegion']=len(row['originalFeatureRegionIds'])==1 and row['originalFeatureRegionIds'][0]>=0
        out.append(row)
    Path(__file__).with_name('WATERSHED_SYNTHETIC104.json').write_text(json.dumps(out,indent=2))
    print(json.dumps(out),flush=True)
if __name__=='__main__':main()
