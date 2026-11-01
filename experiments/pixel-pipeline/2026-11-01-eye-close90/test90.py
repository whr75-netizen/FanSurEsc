from pathlib import Path
import json,numpy as np
from surface_query90 import ProjectedSurface,visibility_bounds,choose_joint_bounds
from metadata90 import decode_independent_meta,clean_skin_underlay
HERE=Path(__file__).resolve().parent
def main(write=True):
 tests=[];world=np.array([[0,0,-2,1],[1,0,-2,1],[1,1,-2,1],[0,1,-2,1]],float);uv=world[:,:2];surface=ProjectedSurface(world,uv,np.array([[0,1,2],[0,2,3]]),np.eye(4),np.eye(4),[2,2]);hits=surface.hits([1.2,.2]);assert len(hits)==1 and hits[0]['primitive']==2;tests.append('query finds adjacent actual triangle rather than treating missed neighbour as transparent')
 hit={'depth':2,'queryKey':'q','projectedWinding':1};assert visibility_bounds([hit],3,{'q':[1,1]})['upper']==0;tests.append('opaque geometry blocks independently of expression getter')
 assert visibility_bounds([hit],1,{'q':[1,1]})['lower']==1;tests.append('behind surface does not occlude')
 assert visibility_bounds([hit],2,{'q':[1,1]})['lower']==1;tests.append('same surface is not self-occlusion')
 assert visibility_bounds([hit],3,{'q':[0,0]})['lower']==1;tests.append('transparent actual surface does not occlude')
 uncertain=visibility_bounds([hit],3,{});assert uncertain['lower']==0 and uncertain['upper']==1;decision=choose_joint_bounds(np.array([[0.]]),np.array([[1.]]),np.array([[2.]]),[4]);assert decision['winner']is None and not decision['paletteLookupAllowed'];tests.append('unknown visibility cannot silently become a visible palette selection')
 alpha=np.ones((1,16));alpha[0,0]=0;d=choose_joint_bounds(alpha,alpha,np.ones_like(alpha),[4]);assert d['winner']==4;tests.append('one occluded fragment does not reject whole important feature')
 d=choose_joint_bounds(np.zeros((1,16)),np.zeros((1,16)),np.ones((1,16)),[4]);assert d['winner']==0;tests.append('all genuinely occluded fragments do not emit source colour')
 assert decode_independent_meta([10,4,1,1])['role']==3 and decode_independent_meta([10,5,1,1])['role']==4;assert clean_skin_underlay([.2,.3,.4,1],[10,4,1,1])and clean_skin_underlay([1,1,1,1],[10,5,1,1])is None;tests.append('role+1 decode accepts skin4 and excludes native white5')
 assert decode_independent_meta([0,0,0,0])is None;assert clean_skin_underlay([.2,.3,.4,.5],[10,4,1,.5])is None;tests.append('clear and partial alpha are not invented opaque backing')
 r=json.loads((HERE/'CLOSE_RESULT90.json').read_text());assert r['target']['oldNeighbourSkin']['primitive']==3120;assert r['targetCorrection']['occluders'][0]['primitive']==3116;assert r['targetCorrection']['skinVisibilityBounds']==[0,0];tests.append('actual140 nearest3120/exact3116 counterexample closed')
 by={f['frame']:f for f in r['frames']};assert by[140]['whiteDefinitelyNotWinner']and by[141]['whiteDefinitelyNotWinner'];assert by[141]['getterClose']==0;tests.append('evaluated closed mesh is respected despite reopened getter lag')
 assert by[135]['robustDecision']==by[142]['robustDecision'];assert by[135]['robustDecision']['massBounds']['4'][1]>0;tests.append('actual reopened source matches original open bounds without a fixed pixel count')
 b=json.loads((HERE/'BACKING_RESULT90.json').read_text());assert b['focus140']['cleanSkinAlreadyRenderedCells']==5 and b['focus140']['genuinelyAbsentBaseBackingCells']==4;tests.append('actual140 backing false-missing5/9 distinguished from remaining4/9')
 g=json.loads((HERE/'GEOMETRY_WITNESS90.json').read_text());world=np.concatenate([np.asarray(t['worldVertices'])for t in g['triangles']]);uv=np.concatenate([np.asarray(t['UV'])for t in g['triangles']]);witness=ProjectedSurface(world,uv,np.arange(6).reshape(2,3),np.asarray(g['view']),np.asarray(g['projection']),g['viewport']);hits=witness.hits(g['query']);assert [h['primitive']for h in hits]==[2]and hits[0]['depth']<g['whiteDepth'];tests.append('portable actual world-space triangle witness independently rejects3120 and finds3116')
 report={'passed':len(tests),'tests':tests,'UnityPlayEntries':0,'productIntegration':False}
 if write:(HERE/'TEST90.json').write_text(json.dumps(report,indent=2)+'\n')
 return report
if __name__=='__main__':print(json.dumps(main(),indent=2))
