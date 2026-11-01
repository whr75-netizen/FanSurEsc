import json
from pathlib import Path
import numpy as np
from graph_regions104 import graph,partition,same_partition,stats

def main():
    mask=np.ones((48,96),bool)
    def run(rgb,m=mask):return partition(graph(rgb,m))
    ramp=np.broadcast_to(np.linspace(40,180,96).astype(np.uint8)[None,:,None],(48,96,3)).copy()
    step=np.full((48,96,3),45,np.uint8);step[:,48:]=225
    for i,v in enumerate([55,90,155,210]):step[:,46+i]=v
    stripe=np.full((48,96,3),210,np.uint8);stripe[:,47]=45
    corner=np.full_like(stripe,210);corner[15:34,42]=45;corner[33,42:57]=45
    hole=np.full_like(stripe,180);hole[18:30,40:54]=40;hole[22:26,44:50]=180
    out=[]
    for name,rgb in [('ramp',ramp),('aaStep',step),('oneTexelStripe',stripe),('Lcorner',corner),('hole',hole)]:
        a=run(rgb);rot=run(np.rot90(rgb),np.rot90(mask));invariant=same_partition(a,np.rot90(rot,-1),mask)
        assert invariant,name+' rotation changed source partition'
        out.append({'fixture':name,**stats(a,mask),'rotationEquivalent':invariant})
    # Equal RGB is not a reason to connect disconnected source support.
    disconnected=mask.copy();disconnected[:,48]=False
    a=run(np.full_like(stripe,120),disconnected)
    assert a[24,10]!=a[24,80]
    out.append({'fixture':'sameRGB_disconnectedSource',**stats(a,disconnected)})
    Path(__file__).with_name('SYNTHETIC104.json').write_text(json.dumps(out,indent=2))
    print(json.dumps(out),flush=True)
if __name__=='__main__':main()
