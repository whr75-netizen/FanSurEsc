"""Separate full-cell opacity expansion from source-ribbon sample occlusion."""
from pathlib import Path
import json,sys,numpy as np
from review_footprint95 import frame
from review_packed93 import ribbon
from native_width86 import green_repeat_bilinear
from projected_ribbon93 import clip_triangle
from PIL import Image
H=Path(__file__).resolve().parent
def inside(p,t):
 a,b,c=t;ab=b-a;ac=c-a;d=p-a;det=np.linalg.det(np.array([ab,ac]));
 if det==0:return False
 u=(d[0]*ac[1]-d[1]*ac[0])/det;v=(ab[0]*d[1]-ab[1]*d[0])/det;return u>=0 and v>=0 and u+v<=1
def main():
 root=Path(sys.argv[1]);r=json.loads((root/'capture/COMPLETE.json').read_text());width_tex=np.asarray(Image.open(H/'face40/analysis-directed/SOURCE_WIDTH_MASK40.png').convert('RGBA'));rows=[]
 for f in r['stream77']['frames']:
  a,_=frame(root,f);sid,fr,width,mapped,anchor,vp,view,data=ribbon(root/'capture'/f['ribbon93']['file']);assert sid==f['sourceId']and fr==f['frame'];by_edge={int(v[0]):v for v in data};w=f['QROI'][2];shift=np.array(f['sourceFootprint95']['nativeExtraSourceCells']);head_origin=np.array([f['QROI'][0],272-f['QROI'][1]-w]);world_origin=np.array(f['nativeOrigin']);delta=np.array(f['delta']);join=np.array(f['join']);z=a[19,:,:,0]+f['depthOffset'];used=a[23,:,:,3]==1;all_quads=[]
  for source in data:
   ends=np.stack([source[3:6],source[6:9]]).astype(float);norm=np.stack([source[9:12],source[12:15]]).astype(float);uv=source[15:19].reshape(2,2);g=green_repeat_bilinear(width_tex,uv,False)if mapped else np.ones(2);points=np.r_[ends,ends+norm*(width*g)[:,None]];q=np.c_[points,np.ones(4)]@vp.astype(float).T;ndc=q[:,:2]/q[:,3,None];p=(ndc*np.array([1,-1])+1)*w*.5;p+=np.array([anchor[2]-anchor[0],-(anchor[3]-anchor[1])]);all_quads.append((p,p.min(0),p.max(0)))
  for yy,xx in np.argwhere(used):
   row=by_edge[int(a[19,yy,xx,1])];ends=np.stack([row[3:6],row[6:9]]).astype(float);norm=np.stack([row[9:12],row[12:15]]).astype(float);uv=row[15:19].reshape(2,2);g=green_repeat_bilinear(width_tex,uv,False)if mapped else np.ones(2);points=np.r_[ends,ends+norm*(width*g)[:,None]];q=np.c_[points,np.ones(4)]@vp.astype(float).T;ndc=q[:,:2]/q[:,3,None];screen=(ndc*np.array([1,-1])+1)*w*.5;screen+=np.array([anchor[2]-anchor[0],-(anchor[3]-anchor[1])]);triangles=[screen[[0,1,3]],screen[[0,3,2]]];areas=[clip_triangle(t,[xx+.5,yy+.5])[0]for t in triangles];head_blocked=[];world_blocked=[]
   for sample in range(4):
    hp=np.array([xx,yy])+(np.array([sample&1,sample>>1])+.5)*.5-shift;wp=(a[4+sample,yy,xx,2:]+.5-world_origin)*.5-delta-join-head_origin
    head_front=a[8+sample,yy,xx,0]>0 and a[8+sample,yy,xx,0]+f['depthOffset']+.0001<z[yy,xx];world_front=a[4+sample,yy,xx,0]+.0001<z[yy,xx]
    if head_front:head_blocked.append({'sample':sample,'localPoint':hp.tolist(),'insideRibbon':any(inside(hp,t)for t in triangles),'insideAnySourceRibbon':any(any(inside(hp,polygon[t])for t in [[0,1,3],[0,3,2]])for polygon,lo,hi in all_quads if np.all(hp>=lo)and np.all(hp<=hi)),'role':int(a[8+sample,yy,xx,1])})
    if world_front:world_blocked.append({'sample':sample,'localPoint':wp.tolist(),'insideRibbon':any(inside(wp,t)for t in triangles)})
   # All source edges can contribute to one output cell. The selected edge's
   # own area is NOT an upper bound on their union. Sum all intersecting source
   # triangles (overlap may be counted twice), then cap at the cell area.
   all_area=0.;overlapping=0
   for polygon,lo,hi in all_quads:
    if np.any(lo>=np.array([xx+1,yy+1]))or np.any(hi<=np.array([xx,yy])):continue
    value=sum(clip_triangle(polygon[t],[xx+.5,yy+.5])[0]for t in [[0,1,3],[0,3,2]])
    if value>0:all_area+=value;overlapping+=1
   rows.append({'frame':f['frame'],'sourceId':sid,'localXY':[int(xx),int(yy)],'edge':int(row[0]),'selectedEdgeUnoccludedAreaCells':float(sum(areas)),'unoccludedSourceRibbonAreaUpperBoundCells':float(min(1.,all_area)),'allIntersectingSourceEdges':overlapping,'allSourceTrianglesIncludedOverlapCountedConservatively':True,'GPUFloatPolygonBitExactClaimed':False,'opaqueOutputAreaCells':1,'sourceRibbonPolygon':screen.tolist(),'headSamplesInFront':head_blocked,'worldSamplesInFront':world_blocked,'ribbonDepthBeforeFullPixelProof':False})
 areas=np.array([x['unoccludedSourceRibbonAreaUpperBoundCells']for x in rows]);out={'actualFrames':len(r['stream77']['frames']),'actualOpaqueAddedCellSamples':len(rows),'sourceRibbonAreaUpperBoundTotal':float(areas.sum()),'opacityAreaExpansionLowerBound':float(len(rows)/areas.sum()),'areaQuantiles':np.quantile(areas,[0,.5,.95,1]).tolist(),'allSourceEdgesIncluded':True,'sourceGeometryCPUCalculationNotGPUFloatBitExactBound':True,'cellSamplesWithFrontHeadSample':sum(bool(x['headSamplesInFront'])for x in rows),'frontHeadSamplesInsideSelectedRibbon':sum(sum(p['insideRibbon']for p in x['headSamplesInFront'])for x in rows),'frontHeadSamplesInsideAnyRibbon':sum(sum(p['insideAnySourceRibbon']for p in x['headSamplesInFront'])for x in rows),'frontWorldSamplesInsideSelectedRibbon':sum(sum(p['insideRibbon']for p in x['worldSamplesInFront'])for x in rows),'frontSampleOutsideRibbonIsNotAReasonToRejectEntireCell':True,'sourceAlphaBetweenSamplesAndCompleteVisibleRibbonAreaUnknown':True,'selectedOpacityPolicyOrProductChanged':False,'rows':rows};(root/'LINE_SUPPORT95.json').write_text(json.dumps(out,indent=2));print(json.dumps({k:v for k,v in out.items()if k!='rows'}))
if __name__=='__main__':main()
