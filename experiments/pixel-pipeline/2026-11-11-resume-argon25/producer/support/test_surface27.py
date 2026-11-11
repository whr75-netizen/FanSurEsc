"""Source correspondence and symmetry regressions on the same frozen inputs."""
from pathlib import Path
import json,sys
import numpy as np
H=Path(__file__).resolve().parent;R=H.parents[2];G=H/'surface27'
sys.path.insert(0,str(H));from surface27 import clip
from verify_native_proof import read,Source,geometry,offset
def main():
 d=read(G/'UV_SURFACE27.json');a=np.load(R/'pigment-carrier109/NATIVE_DOMAIN109.npz');uv=a['uv'];tri=a['triangles'];cache=read(R/'pigment-carrier109/NATIVE_CACHE109.json');curves=[(p,q)for c in cache['curves']for p,q in zip(c['points'],c['points'][1:])];tests=0
 for si,row in enumerate(d['segments']):
  if not row['originalCrossTriangle']:continue
  p,q=curves[si];aa=np.array(p['sourceUV']);bb=np.array(q['sourceUV']);baseIntervals,base=clip(aa,bb,tri,uv)
  expected=np.array(base)
  for matrix in [np.eye(2),np.array([[0,-1],[1,0]]),np.diag([-1,1]),np.array([[0,1],[1,0]])]:
   for order in [tri,tri[::-1,::-1]]:
    _,cuts=clip(aa@matrix.T,bb@matrix.T,order,uv@matrix.T);assert np.allclose(cuts,expected,atol=1e-10,rtol=0);tests+=1
  _,reverse=clip(bb,aa,tri,uv);assert np.allclose(1-np.array(reverse)[::-1],expected,atol=1e-10,rtol=0);tests+=1
 for start,count in d['ranges']:
  pieces=d['pieces'][start:start+count];assert pieces[0]['u'][0]==0 and pieces[-1]['u'][1]==1
  assert abs(sum(p['u'][1]-p['u'][0]for p in pieces)-1)<1e-12
 source=Source();frames=0;joins=0;maxGap=0.
 for run in ['typed-run','motion-run']:
  state=read(next((H/'native-proof'/run).glob('STATE113-*-finished.json')))
  for pkt in state['sequencePackets']:
   p=Path(pkt['output']);c=geometry(p,read(p/'RAW_MANIFEST.json'));base=offset(source,c)
   for start,count in d['ranges']:
    if count!=2:continue
    left,right=d['pieces'][start:start+count]
    x=np.array(left['barycentric'][1])@c['world4'][base+np.array(left['vertices'])]
    y=np.array(right['barycentric'][0])@c['world4'][base+np.array(right['vertices'])]
    gap=float(abs(x-y).max());assert gap<1e-10;maxGap=max(maxGap,gap);joins+=1
   frames+=1
 out={'symmetryAndOrderChecks':tests,'sameSourceActualFrames':frames,'deformedSharedEdgeChecks':joins,'maxJoinGapMetres':maxGap,'all846ParameterIntervalsComplete':True,'GPUOrUnityCalls':0,'geometryReference':'Existing native UV polyline, split at actual shared mesh edges; no shape redesign.'}
 (G/'CPU_SURFACE27.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps(out))
if __name__=='__main__':main()
