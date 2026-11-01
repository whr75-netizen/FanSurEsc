"""Separate area distortion, minimum representable line, and carrier evidence."""
import json,numpy as np
from pathlib import Path
from native109 import H,R,read,bilinear,locate_uv
from geometry109 import prepare_packet,curve_distance
from io109 import entries,packet

def mesh_graph(triangles):
    edges={};g=[set()for _ in triangles]
    for i,t in enumerate(triangles):
        for a,b in zip(t,np.roll(t,-1)):
            edge=tuple(sorted([int(a),int(b)]))
            for j in edges.get(edge,[]):g[i].add(j);g[j].add(i)
            edges.setdefault(edge,[]).append(i)
    groups=np.full(len(g),-1,int);sizes=[]
    for i in range(len(g)):
        if groups[i]>=0:continue
        groups[i]=len(sizes);todo=[i];n=0
        while todo:
            q=todo.pop();n+=1
            for j in g[q]:
                if groups[j]<0:groups[j]=groups[i];todo.append(j)
        sizes.append(n)
    return g,groups,sizes

def hops(g,a,b):
    todo=[a];d={a:0}
    for q in todo:
        if q==b:return d[q]
        for j in g[q]:
            if j not in d:d[j]=d[q]+1;todo.append(j)
    return None

def line_metrics(curve,selected):
    total=0.;miss=0.;samples=[]
    for a,b in zip(curve,curve[1:]):
        length=float(np.linalg.norm(b-a))
        for t in [.125,.375,.625,.875]:
            q=a+(b-a)*t;y,x=np.floor(q[::-1]).astype(int);ok=(y,x)in selected;total+=length/4;miss+=0 if ok else length/4;samples.append(q)
    return {'unrepresentedCurveLengthPixels':miss,'sourceCurveLengthPixels':total,'unrepresentedLengthFraction':miss/total if total else None}

def main():
    domain=np.load(H/'NATIVE_DOMAIN109.npz');cache=read(H/'NATIVE_CACHE109.json');g,groups,sizes=mesh_graph(domain['triangles']);measure=[];source=read(H/'GEOMETRY109.json');seq=entries(H,'105',lambda:read(sorted((R/'closed-support105/direct').glob('STATE102-*'))[-1])['sequencePackets']);related=R/'joint-model108'if(R/'joint-model108').exists()else R/'2026-11-01-joint-objective108';base=read(related/'RESULTS108.json');rawimage=domain['rgba'].astype(float)/255;segmentsChecked=0;gaps=[]
    for c in cache['curves']:
        pts=[v for v in c['points']if not v.get('unresolved')]
        for a,b in zip(pts,pts[1:]):
            uv0=np.array(a['sourceUV']);uv1=np.array(b['sourceUV']);extent=np.max(abs((uv1-uv0)*[rawimage.shape[1],rawimage.shape[0]]));n=max(1,int(np.ceil(extent*4)))
            for t in np.linspace(0,1,n+1):
                uv=uv0+(uv1-uv0)*t;segmentsChecked+=1
                if bilinear(rawimage,uv)[3]<=0:gaps.append({'owner':c['owner'],'section':a['texelSection'],'UV':uv.tolist(),'reason':'zero-source-alpha-between-centres'})
        assert len({groups[p['primitive']-1]for p in pts})==1
    for entry in seq:
        p=packet(H,entry,'105');ctx=prepare_packet(p,domain,cache);m=ctx['manifest'];r=next(x for x in source if x['sourceId']==m['sourceId']);cw,ch=np.asarray(m['forward102']['canonicalSize'])//4
        for eye in r['eyes']:
            owner=eye['owner'];c=next(x for x in cache['curves']if x['owner']==owner);curve=np.array(eye['nativePigmentCurve']);path={tuple(map(int,q))for q in np.floor(curve[:,::-1]).astype(int)};inside={q for q in path if 0<=q[0]<ch and 0<=q[1]<cw};outside=path-inside
            # Actual mass reference is same-packet105, not107's similar pose.
            if m['motion82']['requestedClose']==100:q=base['closed105-frame104']['noCurve'][str(owner)];mass=q['sourceMassLower'][2];areaSet={tuple(pt)for pt,l in zip(q['points'],q['massFirst']['labels'])if l==3}
            else:mass=None;areaSet=None
            sourceTexels=np.argwhere(domain['components']==c['selectedComponent']);yy,xx=sourceTexels.T;tid=domain['primitive'][yy,xx];ids=domain['triangles'][tid];b=domain['barycentric'][yy,xx].astype(float);xy=np.einsum('ij,ijk->ik',b,ctx['maps'][owner][ids]);out=(xy[:,0]<0)|(xy[:,0]>=cw)|(xy[:,1]<0)|(xy[:,1]>=ch)
            destinations=[]
            for d in eye['destinations']:
                if d['status']!='actual-current-native-carrier':continue
                same=groups[d['sourcePrimitive']-1]==groups[d['targetPrimitive']-1];ids=domain['triangles'][d['targetPrimitive']-1];bary=np.array(d['targetBarycentric']);world=bary@ctx['world'][ids];depth=-float((ctx['view']@np.r_[world,1])[2]);reproj=bary@ctx['maps'][owner][ids];target=np.array(d['cellXY'])+.5
                destinations.append(d|{'sameConnectedCarrier':bool(same),'carrierTriangleHops':hops(g,d['sourcePrimitive']-1,d['targetPrimitive']-1),
                  'depthWorldEquationResidual':abs(depth-d['targetDepth']),'canonicalTargetResidual':float(np.linalg.norm(reproj-target)),'sourceColourNotTargetBlankTexel':d['targetOriginalAlpha']==0})
            measure.append({'frame':m['frameIndex'],'sourceId':m['sourceId'],'owner':owner,'Close':m['motion82']['requestedClose'],'sourceCurveFloorPathCellsInsideROI':len(inside),'sourceCurveFloorPathCellsOutsideROI':len(outside),
              'sourceNativeTexelsOnMainRibbon':len(xx),'sourceNativeTexelsClippedByOldROI':int(out.sum()),'clippedIsSourceUVTexelCountNotProjectedArea':True,'minimumThicknessPolicy':'one-cell-wide ordered path diagnostic, not a target count; no RGB generated',
              'measuredVisibleAreaCells':mass,'oneCellPathAreaExcessOverMeasuredArea':len(inside)-mass if mass is not None else None,
              'areaPriorityCurveLoss':line_metrics(curve,areaSet)if areaSet is not None else None,'curvePriorityCurveLoss':line_metrics(curve,inside),'destinations':destinations})
    out={'nativeCarrierTriangleComponents':sizes,'sourceCurveIntermediateAlphaProbes':segmentsChecked,'sourceCurveZeroAlphaGaps':gaps,'rows':measure,'modelApplied':False,
      'ROIConclusion':'captured ROI was authored-parent bounds plus fixed2 padding; actual native pigment extends beyond it. Derive source bounds from cached native feature footprint, not this padding.',
      'noNewCaptureRequiredForTheseCounterexamples':True,'externalHairDestinationVisibilityStillUnverified':True}
    (H/'MEASURE109.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps({'meshComponents':sizes,'sourceCentreSegmentsIntermediateChecks':segmentsChecked,'sourceAlphaGaps':len(gaps),'rows':[{k:v for k,v in x.items()if k!='destinations'}for x in measure]}))
if __name__=='__main__':main()
