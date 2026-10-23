from pathlib import Path
import json,struct,math
import numpy as np
O=Path(__file__).resolve().parent;R=O/'Math';REF=O.parent/'Outline533/FullLoop'
ns={'__file__':str(O/'transform_audit534.py')};exec((O/'transform_audit534.py').read_text().split('rows=[]')[0],ns);read=ns['read'];Reader=ns['Reader']
j=json.loads((O/'TRANSFORM_AUDIT534.json').read_text());loop=json.loads((O/'LOOP_INPUT_AUDIT534.json').read_text())
def curves_saved(f):
 r=Reader((REF/f'{f:03d}_ALT_GEOMETRY.bin').read_bytes());groups=[]
 for _ in range(2):groups.append([r.a('<f4',r.n()*2).reshape(-1,2)for _ in range(r.n())])
 return groups[1]
def delta(box,a,m,x,y):
 bx,by,w,h=box;old=bool(m[y-by,x-bx]);aa=float(a[y-by,x-bx]);unary=(2*aa-1)if old else(1-2*aa);boundary=0.
 for dx in[-1,0,1]:
  for dy in[-1,0,1]:
   if dx or dy:
    other=bool(m[y+dy-by,x+dx-bx]);weight=float(np.float32(.14)*np.float32(.29289322 if dx and dy else .58578644));boundary+=weight*(int((not old)!=other)-int(old!=other))
 return {'currentlySelected':old,'flipUnaryDelta':unary,'flipBoundaryDelta':boundary,'flipTotalDelta':unary+boundary}
for q in j['rows']:
 f=q['frame'];rs,box,a,m=read(R/f'{f}_area.bin');actual=curves_saved(f);q['exactAreaReplayVsRuntime']['curveFloatArraysExact']=len(rs)==len(actual)and all(np.array_equal(x,y)for x,y in zip(rs,actual));assert q['exactAreaReplayVsRuntime']['curveFloatArraysExact']
 q['opacityCurveUsedInStoredRun']='usedOpacityCurve=True'in(REF/f'{f:03d}_cost.txt').read_text()
 q['flipCosts']={}
 for v in['source','distance','area']:
  _,box,a,m=read(R/f'{f}_{v}.bin');q['flipCosts'][v]=delta(box,a,m,201,97)
(O/'TRANSFORM_AUDIT534.json').write_text(json.dumps(j,indent=2))
# Three same-source transformations at50 in the common logical grid.
f=50;variants={v:read(R/f'{f}_{v}.bin')for v in['source','distance','area']};box=(199,95,205,102);scale=38
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="385" viewBox="0 0 1080 385"><rect width="1080" height="385" fill="white"/><g font-family="sans-serif" fill="#222"><text x="14" y="22">534 same saved Source / current compiled operations / frame50 - no new render</text>']
for k,(v,(rs,b,a,m))in enumerate(variants.items()):
 ox=k*360+38;oy=67;xy=lambda p:(ox+(float(p[0])-box[0])*scale,oy+(float(p[1])-box[1])*scale)
 svg.append(f'<text x="{k*360+10}" y="47" font-size="15">{v}: A(201,97)={float(a[97-b[1],201-b[0]]):.6f}, selected={bool(m[97-b[1],201-b[0]])}</text>')
 svg.append(f'<defs><clipPath id="clip{k}"><rect x="{ox}" y="{oy}" width="{(box[2]-box[0])*scale}" height="{(box[3]-box[1])*scale}"/></clipPath></defs><g clip-path="url(#clip{k})">')
 for y in range(box[1],box[3]):
  for x in range(box[0],box[2]):
   if m[y-b[1],x-b[0]]:
    px,py=xy((x,y));svg.append(f'<rect x="{px}" y="{py}" width="{scale}" height="{scale}" fill="#d9e8f4"/>')
 for x in range(box[0],box[2]+1):
  px,py=xy((x,box[1]));svg.append(f'<path d="M{px} {py}v{(box[3]-box[1])*scale}" stroke="#ddd" fill="none"/>')
 for y in range(box[1],box[3]+1):
  px,py=xy((box[0],y));svg.append(f'<path d="M{px} {py}h{(box[2]-box[0])*scale}" stroke="#ddd" fill="none"/>')
 for r in rs:
  ps=' '.join(f'{xy(p)[0]},{xy(p)[1]}'for p in list(r)+[r[0]]);svg.append(f'<polyline points="{ps}" fill="none" stroke="#23669c" stroke-width="2"/>')
 px,py=xy((201,97));svg.append(f'<rect x="{px}" y="{py}" width="{scale}" height="{scale}" fill="none" stroke="#c05522" stroke-width="3"/></g>')
svg.append('<text x="14" y="361" font-size="14">Blue=continuous curve; light fill=selected cells; orange=(201,97). Area fit skips one local source point.</text></g></svg>')
(O/'SAME_SOURCE_TRANSFORM534.svg').write_text(''.join(svg),encoding='utf-8')
r50=next(q for q in j['rows']if q['frame']==50);m=r50['localAcceptedAreaChord']['metrics']
summary={'status':'LOCAL_INFORMATION_LOSS_CONFIRMED_NO_GENERAL_FIX_APPLIED','sameSourceMathReplayFrames':[49,50,51],'newRenderedFrames':0,'newPlaySessions':0,'newProductCode':False,'sourcePoint':r50['localAcceptedAreaChord']['skippedVertices'][0],'areaChordError':m['implementedNormalizedArea'],'independentAreaError':m['absoluteAreaError'],'pointwiseError':m['maxPerpendicularError'],'distanceBound':.09375,'sourceAndDistanceCell97':r50['variants']['distance']['cells'][1],'areaCell97':r50['variants']['area']['cells'][1],'pixelFlipCosts':r50['flipCosts'],'actualEqualAreaTieProved':False,'equalAreaGeometryControlsCollapse':True,'firstBinaryNotch':'SelectRegions on area-fitted coverage','earliestCausalInformationLoss':'FitArea532 accepts low integral error while dropping the distance-retained local point','conversionOrSignedCancellationBugFound':False,'neededInformation':'Spatial distribution/local displacement and reference-to-output boundary feature/width/span fidelity; scalar area/perimeter does not encode these. No new threshold, exception or paper term implemented.','loopRegressionVerdict':'not established: endpoint inputs not identical; all28 area samples equal same-run distance control at both endpoints','originalOFFHistoricalApproxColourChanges':loop['historicalOriginalOFF']['approxSurfaceRGBSamples'],'historicalCoordinatesShared':loop['sameCoordinatesInHistoricalOFF'],'mainRemainsCandidateOFF':True}
(O/'SUMMARY534.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary))
