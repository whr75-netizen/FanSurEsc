"""Repair64->contour handoff and audit whole observed paths in one frozen packet.
No RGB/Q writes, invented gaps, smoothing target or Unity calls.
"""
from pathlib import Path
import hashlib,json,sys
from collections import defaultdict
import numpy as np
from PIL import Image,ImageDraw
from probe69 import ROOT,PACKET,state,sibling,geometry,camera
from source_contours70 import trace_evidence,continuity_audit
def clip_segments(p0,p1,triangle):
 A=np.stack([triangle[1]-triangle[0],triangle[2]-triangle[0]],axis=1)
 if abs(np.linalg.det(A))<1e-12:return None
 inv=np.linalg.inv(A);b0=(p0-triangle[0])@inv.T;b1=(p1-triangle[0])@inv.T;l0=np.column_stack([1-b0.sum(1),b0]);dl=np.column_stack([1-b1.sum(1),b1])-l0;t0=np.zeros(len(p0));t1=np.ones(len(p0));valid=np.ones(len(p0),bool)
 for j in range(3):
  d=dl[:,j];v=l0[:,j];nz=abs(d)>1e-18;cross=np.divide(-v,d,out=np.zeros_like(v),where=nz);t0=np.where(d>0,np.maximum(t0,cross),t0);t1=np.where(d<0,np.minimum(t1,cross),t1);valid&=nz|(v>=0)
 valid&=(t1>t0)&(t1>0)&(t0<1);return valid,np.clip(t0,0,1),np.clip(t1,0,1),l0,dl
def main():
 old=sibling('uv-features64','2026-10-31-uv-features64');meta=json.loads((old/'SOURCE_RESULTS64.json').read_text());expected={r['name']:r['sha256'] for r in json.loads((old/'MANIFEST64.json').read_text())['files']};registry=json.loads((sibling('renderer-family59','2026-10-31-renderer-family59')/'SOURCE_REGISTRY59.json').read_text());gi,meshes=geometry(PACKET/'evaluated-source.geometry');cam=camera(PACKET/'source.camera');P=cam['gpuProjection'].copy();P[0]+=float(cam['nativeShift'][0])*P[3];P[1]+=float(cam['nativeShift'][1])*P[3];VP=P@cam['view']
 bindings=json.loads((PACKET/'offline68/SURFACE_BINDINGS68.json').read_text());faceWitness={tuple(r['nativeXY']):(r['mesh'],r['submesh'],r['primitive']) for r in bindings['mapped']};hairFaces={tuple([r['mesh'],r['submesh'],r['primitive']]) for r in bindings['mapped'] if r['hair']};mappedGroups=defaultdict(list)
 for f in hairFaces:mappedGroups[(f[0],f[1])].append(f[2])
 rows=[];graphs=[];allSegments=[];allCurve=[];allWitness=[];allPlacement=[];allFace=[];allParameter=[];curveStats=[];curveBase=0;placementIds={};placementLengths=defaultdict(float)
 for (mi,sm),ids in sorted(mappedGroups.items()):
  m=next(m for m in meshes if m['index']==mi);sub=m['submeshes'][sm];entry=next(e for e in registry['bindings'] if e['rendererOrdinal']==mi and e['subMesh']==sm);mid=entry['materialId'];file=old/f'SOURCE64-{mid}.npz';assert hashlib.sha256(file.read_bytes()).hexdigest()==expected[file.name];assert hashlib.sha256(m['uv'].astype('<f4').tobytes()).hexdigest()==entry['meshUVSHA256'];assert hashlib.sha256(sub['indices'].astype('<u4').tobytes()).hexdigest()==entry['indexSHA256']
  z=np.load(file);record=next(r for r in meta['materials'] if r['materialId']==mid);tier={name:{'x':z[x],'y':z[y]} for name,x,y in [('persistent','persistentX','persistentY'),('fine','fineX','fineY'),('uncertain','emergentX','emergentY')]};graph=trace_evidence(tier,record['cacheKey']);graphs.append({'materialId':mid,'mesh':mi,'submesh':sm,'globalCurveBase':curveBase,'sourceImageSHA256':entry['imageSHA256'],'graph':graph});summary=continuity_audit(graph);summary['materialId']=mid
  # An index-connected chart is only a projection-placement key. It is NOT a
  # semantic strand, colour family or independent sorting/occlusion owner.
  parent=np.arange(len(m['vertices']))
  def find(v):
   v=int(v)
   while parent[v]!=v:parent[v]=parent[parent[v]];v=int(parent[v])
   return v
  for part in m['submeshes']:
   for tri in part['indices']:
    for v in tri[1:]:
     aa,bb=find(tri[0]),find(v)
     if aa!=bb:parent[max(aa,bb)]=min(aa,bb)
  h,w=z['support'].shape;edgeCurve=[];edgeRank=[];p0=[];p1=[]
  for k,path in enumerate(graph['paths']):
   for rank,(a,b) in enumerate(zip(path['points'][:-1],path['points'][1:])):p0.append([a[0]/w,1-a[1]/h]);p1.append([b[0]/w,1-b[1]/h]);edgeCurve.append(k);edgeRank.append(rank)
  p0=np.array(p0,float);p1=np.array(p1,float);edgeCurve=np.array(edgeCurve,int);edgeRank=np.array(edgeRank,int);pathLength=np.zeros(len(graph['paths']));witnessLength=np.zeros(len(pathLength));outside=0;projected=0
  for pi in sorted(ids):
   ix=sub['indices'][pi];triUV=m['uv'][ix]*sub['st'][:2]+sub['st'][2:]
   if np.any(triUV<0) or np.any(triUV>1):outside+=1
   clipped=clip_segments(p0,p1,triUV)
   if clipped is None:continue
   ok,t0,t1,l0,dl=clipped;at=np.where(ok)[0]
   if not len(at):continue
   # Unit texture tile only. Runtime wrap/filter metadata was NOT captured.
   q0=l0[at]+dl[at]*t0[at,None];q1=l0[at]+dl[at]*t1[at,None];v0=q0@m['vertices'][ix];v1=q1@m['vertices'][ix];world0=np.c_[v0,np.ones(len(at))]@m['matrix'].T;world1=np.c_[v1,np.ones(len(at))]@m['matrix'].T;c0=world0@VP.T;c1=world1@VP.T;s0=np.column_stack([(c0[:,0]/c0[:,3]*.5+.5)*960,(.5-c0[:,1]/c0[:,3]*.5)*544]);s1=np.column_stack([(c1[:,0]/c1[:,3]*.5+.5)*960,(.5-c1[:,1]/c1[:,3]*.5)*544]);seg=np.stack([s0,s1],axis=1);length=np.linalg.norm(s1-s0,axis=1)/2;midpoint=(s0+s1)/2;witness=np.array([faceWitness.get((int(np.floor(p[0])),int(np.floor(p[1]))))==(mi,sm,pi) for p in midpoint]);np.add.at(pathLength,edgeCurve[at],length);np.add.at(witnessLength,edgeCurve[at],length*witness);allSegments.extend(seg);allCurve.extend((edgeCurve[at]+curveBase).tolist());allWitness.extend(witness.tolist());projected+=len(at)
   placementKey=(mi,find(ix[0]));placement=placementIds.setdefault(placementKey,len(placementIds));allPlacement.extend([placement]*len(at));allFace.extend([(mi,sm,pi)]*len(at))
   allParameter.extend(np.column_stack([edgeRank[at]+t0[at],edgeRank[at]+t1[at]]))
   for k,L,seen in zip(edgeCurve[at]+curveBase,length,witness):
    if seen:placementLengths[(int(k),placement)]+=float(L)
  for k,path in enumerate(graph['paths']):curveStats.append({'globalCurve':curveBase+k,'materialId':mid,'curveId':path['curveId'],'sourceEdges':path['edgeCount'],'uncertain':path['uncertain'],'projectedUnitTileLength':float(pathLength[k]),'nearestSamePrimitiveWitnessLength':float(witnessLength[k]),'closed':path['closed'],'pins':[path['pinnedStart'],path['pinnedEnd']],'visibilityFullyVerified':False})
  summary.update({'projectedClippedPieces':projected,'visibleTrianglesPartlyOutsideUnitUV':outside,'runtimeWrapFilterUncaptured':True,'projectionMeaning':'original source evidence on actually sampled triangles; clipped pieces are not a complete visible curve, no copy of source owner is created'});rows.append(summary);curveBase+=len(graph['paths'])
 np.savez_compressed(ROOT/'CURVE_PROJECTION70.npz',segments=np.asarray(allSegments),curve=np.asarray(allCurve),sourceParameter=np.asarray(allParameter),placement=np.asarray(allPlacement),face=np.asarray(allFace),nearestPrimitiveWitness=np.asarray(allWitness))
 (ROOT/'ORDERED_SOURCE70.json').write_text(json.dumps({'sourceId':state['sourceId'],'curvesAreEvidenceNotArtTruth':True,'sources':graphs},separators=(',',':'))+'\n',encoding='utf-8')
 bestKey=max(placementLengths,key=placementLengths.get);best=dict(curveStats[bestKey[0]]);best['placement']=bestKey[1];best['placementWitnessLength']=placementLengths[bestKey];best['totalLengthIsAcrossPlacementsNotOneVisibleCurve']=True;source=next(s for s in graphs if s['materialId']==best['materialId']);path=next(p for p in source['graph']['paths'] if p['curveId']==best['curveId']);original=Image.open(old/f'NATIVE_SOURCE64-{best["materialId"]}.png').convert('RGB');draw=ImageDraw.Draw(original);draw.line(path['points'],fill=(35,230,190),width=2);draw.ellipse((path['points'][0][0]-3,path['points'][0][1]-3,path['points'][0][0]+3,path['points'][0][1]+3),fill='red');original.save(ROOT/'SOURCE_CHAIN70.png')
 # Full output and head-local coordinates have different offsets. Never overlay them silently.
 overlay=Image.new('RGB',(960,544),(25,27,31));d=ImageDraw.Draw(overlay)
 for seg,c,seen,placement in zip(allSegments,allCurve,allWitness,allPlacement):
  if c==best['globalCurve'] and placement==best['placement']:
   xy=[(float(p[0]),float(544-p[1])) for p in seg];d.line(xy,fill=(35,230,190) if seen else (235,165,35),width=1)
 # Crop from selected projected pieces, never infer the main/head offset from a screenshot.
 chosen=np.asarray([s for s,c,p in zip(allSegments,allCurve,allPlacement) if c==best['globalCurve'] and p==best['placement']]);lo=chosen.reshape(-1,2).min(0);hi=chosen.reshape(-1,2).max(0);box=(max(0,int(lo[0])-5),max(0,544-int(hi[1])-5),min(960,int(hi[0])+6),min(544,544-int(lo[1])+6));small=overlay.crop(box);small.resize((small.width*6,small.height*6),Image.Resampling.NEAREST).save(ROOT/'PROJECTED_CHAIN70.png')
 report={'sourceId':state['sourceId'],'frame':state['frameIndex'],'nativeToLogicalScale':2,'materialSummaries':rows,'projectionPlacements':[{'id':v,'mesh':k[0],'indexComponent':k[1],'notSemanticFeatureOrSortingOwner':True} for k,v in placementIds.items()],'representative':best,'representativeSelection':'maximum nearest-primitive witnessed projected length, not artistic importance; current example is a straight source separator, not a complete highlight-band contour','curveCorrectionApplied':False,'noSelfSmoothedGroundTruth':True,'sourceCurveReference':'Unfiltered raster-edge evidence from immutable source64 masks; these are uncertain detections, not authored vector curves or an independently approved ideal curve.','projectionReference':'Captured evaluated geometry/view/projection, one nativeShift application; nearest-sample primitive agreement only, not complete subpixel visibility.','visibilityEndProtection':'Each clipped piece keeps source-arclength parameter, source primitive, placement and witness state. Unverified pieces do not become connected visible curves or known occlusion endpoints.','graphRepair':'Union evidence tiers before tracing; retain per-edge confidence, stable curve identity across tier changes, pin true graph endpoints/junctions, do not close gaps.','old64AlreadyHadPersistentAndFineContours':True,'missingWasUncertainTierAndOrderedCrossTierPaths':True,'limits':['No hard semantic feature masks supplied by64','No runtime wrap/filter metadata; only unit texture tile projected','Observed source paths can be fragments or branches; no arbitrary fragment bridging or new owner/layer sorting','No continuous ideal curve or independent high-density g supplied; no pixel output correction is claimed'],'originalQRGBPaletteChanged':False,'newUnityCalls':0}
 (ROOT/'CURVE_REPORT70.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps({'summaries':rows,'representative':best,'projectedPieces':len(allSegments)},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
