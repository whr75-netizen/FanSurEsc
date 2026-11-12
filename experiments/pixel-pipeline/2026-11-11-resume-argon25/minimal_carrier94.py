"""Keep the measured tiny opacity loop; remove only premature float rounding.

Uses recorded float barycentrics as input, not a claim to reconstruct the
discarded original double barycentrics. Runtime candidate retains those at
creation; this conservative test proves the precise observed failure mechanism.
"""
from pathlib import Path
import json,struct,numpy as np
from union_input94 import load
H=Path(__file__).resolve().parent;G=H/'face94'
def main():
 d=load(G/'capture/UNION94-failure-frame429.bin');a=d['anchors'];b=d['boundaries'];v=d['points'][a['vertices']];p=(v[:,0]*a['weights'][:,0,None]+v[:,1]*a['weights'][:,1,None])+v[:,2]*a['weights'][:,2,None];grid=np.rint(p.astype(float)*1e8).astype(np.int64);w=a['weights'].astype(float);vv=v.astype(float);precise=vv[:,0]+(vv[:,1]-vv[:,0])*w[:,1,None]+(vv[:,2]-vv[:,0])*w[:,2,None];ring=np.array(json.loads((G/'EXACT_FRAGMENT94.json').read_text())['inputCyclesThroughFailingDirectedEdge'][0]['vertices'],np.int64);support=b[b['primitive']==290];ids=np.unique(np.r_[support['a'],support['b']]);chosen=[]
 for q in ring:
  options=ids[(grid[ids]==q).all(1)];assert len(options)>0,(q,options);assert np.array_equal(precise[options],np.tile(precise[options[0]],(len(options),1)));chosen.append(int(options[0]))
 original=ring.astype(float)/1e8;exact=precise[chosen];n=len(exact)-1
 for name,points in [('float-before',original),('relative-double',exact)]:
  with(G/('MINIMAL94-'+name+'.d94')).open('wb')as f:
   f.write(struct.pack('<i',n));f.write(np.stack([points[:-1],points[1:]],axis=1).astype('<f8').tobytes())
 def area(q):return float(np.sum(q[:-1,0]*q[1:,1]-q[:-1,1]*q[1:,0])*.5)
 r={'actualPrimitive':290,'frame':d['frame'],'sourceId':d['sourceId'],'closedLoopEdges':n,'sameMeasuredSourceAnchors':True,'floatBarycentricsRetainedNotInvented':True,'doubleBarycentricsFromOriginalUVNotAvailableInThisOldPacket':True,'originalSignedArea':area(original),'relativeDoubleSignedArea':area(exact),'maxPointCorrectionCells':float(abs(original-exact).max()),'droppedLoopOrChangedCutoff':False,'sourceTriangle':d['points'][d['indices'][290]].tolist(),'anchorIndices':chosen};(G/'MINIMAL_CARRIER94.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
if __name__=='__main__':main()
