"""Source part decisions precede registered cache occupancy. Offline only."""
import math
import numpy as np

def native_lid_from_source(packet,m,eye,source_iris):
    """NativeLineAllocated19 with only source iris eligibility, never cache cells.

    A source upper-lid decision cannot migrate to a spare cell merely because
    another registered part occupies its original cell.
    """
    c=packet[eye];I=(c[...,2]+c[...,3])+c[...,4];h,w=I.shape
    padded=np.pad(I,((0,0),(1,1)))
    white=(c[...,1]>=1)&((padded[:,:w]>0)|(padded[:,2:]>0))
    white_count=int(white.sum());area=np.float32(0)
    for y in range(h-1,-1,-1):
        for x in range(w):area=np.float32(area+np.float32(c[y,x,5]/16))
    candidates=[(x,y)for y in range(h-1,-1,-1)for x in range(w)
        if c[y,x,5]>0 and not(white_count==1 and white[y,x])and(x,y)not in source_iris]
    costs=np.maximum(c[...,1],I)-c[...,5]
    candidates.sort(key=lambda q:(float(costs[q[1],q[0]]),-q[1],q[0]))
    return set(candidates[:math.floor(float(np.float32(area+.5)))]),float(area)

def compose_part_ids(rows,m,source_lids):
    """Keep native upper-lid footprint; never reallocate it around cache cells.

    Existing external source and final hair/body visibility is already present
    in rows. This emits a cache-only layer plus a separate native-lid ID mask,
    not a synthetic final face. Lower-lid/skin semantic ambiguity is not guessed.
    """
    out=[]
    for source in rows:
        row=dict(source)
        xy=(row['xy'][0]-m['x'],row['xy'][1]-m['y'])
        native=xy in source_lids[row['eye']]
        row['sourceLidFeatureID']=f"eye{row['eye']}:native-upper-lid" if native else None
        row['occludedByNativeLid50']=bool(row['visible']and native)
        row['visible']=bool(row['visible']and not native)
        out.append(row)
    return out
