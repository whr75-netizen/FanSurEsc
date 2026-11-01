"""A carrier is a clipped surface footprint, not the cell-centre depth.
Returns all real same-component triangle pieces with barycentric/depth/UV
fields. It DOES NOT turn one point or one front piece into whole-cell ownership.
"""
import numpy as np,json
from native109 import H,read
from io109 import packet
from geometry109 import prepare_packet
from measure109 import mesh_graph

def clip(triangle,cell):
    p=[np.r_[q,b]for q,b in zip(triangle,np.eye(3))]
    for axis in [0,1]:
        for edge,sign in [(cell[axis],1),(cell[axis]+1,-1)]:
            out=[]
            if not p:break
            for a,b in zip(p,p[1:]+p[:1]):
                da=(a[axis]-edge)*sign;db=(b[axis]-edge)*sign
                if da>=0:out.append(a)
                if(da<0)!=(db<0):out.append(a+(b-a)*(da/(da-db)))
            p=out
    return np.array(p).reshape(-1,5)
def area(p):
    if len(p)<3:return 0.
    q=np.roll(p,-1,axis=0);return abs(float(np.sum(p[:,0]*q[:,1]-p[:,1]*q[:,0])))*.5
def tests():
    tri=np.array([[0.,0.],[.2,0.],[0.,.2]]);base=area(clip(tri,[0,0]));assert abs(base-.02)<1e-15
    for f in [lambda p:p[:,::-1],lambda p:1-p,lambda p:p*[1,-1]+[0,1]]:
        for shift in range(3):assert abs(area(clip(np.roll(f(tri),shift,axis=0),[0,0]))-base)<1e-15
    assert area(clip(tri+2,[0,0]))==0
    assert area(clip(np.array([[1.,0.],[1.,1.],[2.,0.]]),[0,0]))==0
    return {'rotationReflectionAndCyclicOrderCases':9,'cornerFootprintExistsWithoutCellCentre':True,'outsideAndTangentDoNotOwnCell':True}
def main():
    domain=np.load(H/'NATIVE_DOMAIN109.npz');cache=read(H/'NATIVE_CACHE109.json');entry=next(e for e in read(H/'RAW_INPUT109_INDEX.json')['entries105']if e['frame']==104);ctx=prepare_packet(packet(H,entry,'105'),domain,cache);_,groups,_=mesh_graph(domain['triangles']);out=[]
    for r in read(H/'REJECTED_CARRIERS109.json'):
        component=r['sourceCarrierComponent'];matched=[c for c in cache['curves']if groups[c['points'][0]['primitive']-1]==component];assert len(matched)==1;owner=matched[0]['owner'];cell=r['cellXY'];pieces=[]
        for tid,ids in enumerate(domain['triangles']):
            if groups[tid]!=component:continue
            p=clip(ctx['maps'][owner][ids],cell);a=area(p)
            if a<=0:continue
            b=p[:,2:];pieces.append({'primitive':tid+1,'polygonCanonicalXY':p[:,:2].tolist(),'polygonBarycentric':b.tolist(),'polygonWorld':(b@ctx['world'][ids]).tolist(),'polygonUV':(b@ctx['uv'][ids]).tolist(),'polygonDepth':(b@ctx['depth'][ids]).tolist(),'projectedGeometryArea':a})
        assert pieces;out.append({'sourceId':ctx['manifest']['sourceId'],'frame':104,'cellXY':cell,'component':component,'sameCarrierCentreHitCount':r['sameCarrierAlternativeCount'],'sameCarrierFootprintPieces':pieces,'sumPieceAreaIsNotDepthResolvedUnionCoverage':True,'wholeCellOwnerChosen':False})
    report={'cases':out,'tests':tests(),'actualExternalHairMaterialVisibilityNotResolved':True,'newGPU':0};(H/'FOOTPRINT109.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print(json.dumps({'cases':[{'cell':x['cellXY'],'pieces':len(x['sameCarrierFootprintPieces']),'centreHitCount':x['sameCarrierCentreHitCount']}for x in out],'tests':report['tests']}))
if __name__=='__main__':main()
