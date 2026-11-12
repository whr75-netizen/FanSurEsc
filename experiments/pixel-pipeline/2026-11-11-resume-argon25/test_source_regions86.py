from pathlib import Path
import json,numpy as np
from source_regions86 import connected4,partition,colour_fields
def equivalent(a,b):
 ids={}
 for x,y in zip(a.ravel(),b.ravel()):
  if bool(x)!=bool(y):return False
  if x and x in ids and ids[x]!=y:return False
  if x:ids[x]=y
 return len(set(ids.values()))==len(ids)
def main():
 checks=0
 for fixture in [np.eye(5,dtype=bool),np.ones((5,7),bool),np.array([[1,0,0],[1,1,1],[0,0,0]],bool)]:
  original,n=connected4(fixture)
  for flip in [False,True]:
   for k in range(4):
    q=np.fliplr(fixture)if flip else fixture;q=np.rot90(q,k);labels,nn=connected4(q);labels=np.rot90(labels,-k);labels=np.fliplr(labels)if flip else labels;assert nn==n and equivalent(original,labels);checks+=1
 fg=np.zeros((9,11),bool);fg[2:4,1:8]=True;fg[6:8,1:8]=True;mask=np.ones_like(fg);p=partition(mask,fg);assert p['pigmentCount']==2 and p['pigment'][2,2]!=p['pigment'][6,2];checks+=1
 # A continuous gradient crossing an arbitrary old colour bin remains one
 # support region; no old parent/palette id is an input to this API.
 rgb=np.tile(np.arange(11,dtype=np.uint8)[None,:,None],(9,1,3));rows=colour_fields(rgb,p);assert rows[0]['affineWithinNativeHalfCodeInterval']and not rows[0]['exactConstantRGB'];checks+=1
 assert np.array_equal(p['foreground'],fg)and np.array_equal(p['mask'],mask);checks+=1
 try:partition(np.zeros((2,2),bool),np.ones((2,2),bool));raise AssertionError('unsupported fill admitted')
 except ValueError:checks+=1
 d={'CPUChecks':checks,'D4PartitionEquivalent':True,'sameRGBSeparatedStructuresRemainDistinct':True,'gradientNotFlattenedToConstantReference':True,'noParentColourBinsOrUnknownGapFilling':True};g=Path(__file__).resolve().parent/'face86';g.mkdir(exist_ok=True);(g/'CPU_REGIONS86.json').write_text(json.dumps(d,indent=2));print(json.dumps(d))
if __name__=='__main__':main()
