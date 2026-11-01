from pathlib import Path
import sys,json,hashlib,math
import numpy as np
from PIL import Image,ImageDraw
from probe69 import ROOT,PACKET,state,planes,counts,geometry,rgb8,sibling
from coverage_boundary69 import both_diagonals
from schema69 import shade_labels
from metrics69 import iso_segments,fixed_reference,reference_gate
sys.path.insert(0,str(sibling('uv-features64','2026-10-31-uv-features64')))
from uv_features64 import edge_components
def main():
 a=planes();ox,oy,ww,hh=state['sourceROIBottomLeft'];meta=np.zeros((272,480,4),np.float32)
 for name,v in a.items():
  if name.startswith('source-meta-strip-'):y=int(name.rsplit('-',1)[1]);meta[y:y+len(v)]=v
 lm=meta[oy:oy+hh,ox:ox+ww];mask=(lm[...,0]>0)&(lm[...,1]>=11.5)&(lm[...,1]<=15.5);nm=a['native-endpoint'];nativeMask=(nm[...,0]>0)&(nm[...,1]>=11.5)&(nm[...,1]<=15.5)
 steps=int(state['modeFlags']['surfaceSteps'])
 if steps!=2:raise ValueError('This frozen area diagnostic is binary; do not collapse3/4-step shade IDs')
 q=shade_labels(a['shade-class480'],mask,'LegacySignals335.classifier_after_ShadeBoundary',steps);g=a['style-class'][...,1]
 _,meshes=geometry(PACKET/'evaluated-source.geometry');faceVertices={}
 for m in meshes:
  for sm,s in enumerate(m['submeshes']):
   for pi,tri in enumerate(s['indices']):faceVertices[(m['index'],sm,pi)]=set((m['index'],int(v)) for v in tri)
 binding=json.loads((PACKET/'offline68/SURFACE_BINDINGS68.json').read_text());faces={(r['nativeXY'][0]-2*ox,r['nativeXY'][1]-2*oy):(r['mesh'],r['submesh'],r['primitive']) for r in binding['mapped']}
 candidate,bright,dark,unknown,guides,rejected=both_diagonals(q,mask,g,nativeMask,faces,faceVertices)
 # Counterfactual without ownership: expose, rather than hide, a tempting bad cleanup.
 allFace={(x,y):(0,0,0) for y,x in np.argwhere(nativeMask)};naive,_,_,_,_,_=both_diagonals(q,mask,g,nativeMask,allFace,{(0,0,0):{0}})
 before=counts(q,mask);after=counts(candidate,mask);loose=counts(naive,mask);changes=[]
 referenceMetrics=[]
 for diagonal,guide in enumerate(guides):
  segments=iso_segments(guide)
  referenceMetrics.append({'diagonal':diagonal,'before':fixed_reference(q,mask,segments),'candidate':fixed_reference(candidate,mask,segments),'unsafe':fixed_reference(naive,mask,segments)})
 for y,x in np.argwhere(mask&(candidate!=q)):
  changes.append({'xyDown':[int(x+ox),int(271-y-oy)],'before':int(q[y,x]),'after':int(candidate[y,x]),'centreG':float(a['shade-class480'][y,x,1]),'brightAreaLower':float(bright[y,x]),'darkAreaLower':float(dark[y,x]),'unknownArea':float(unknown[y,x])})
 representatives=[]
 for x,y in before['singletons']:
  neighborhood=mask[max(0,y-1):y+2,max(0,x-1):x+2];cardinals=sum(0<=x+dx<ww and 0<=y+dy<hh and mask[y+dy,x+dx] for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]);case='silhouette/gap: no same-domain cardinal neighbour' if cardinals==0 else 'silhouette-adjacent; different visible source surfaces' if not neighborhood.all() else 'internal point classification near threshold; visible source surfaces differ'
  representatives.append({'xyDown':[x+ox,271-y-oy],'classification':case,'centreG':float(a['shade-class480'][y,x,1]),'Q':int(q[y,x]),'meta':lm[y,x].tolist(),'nativeG2x2':g[2*y:2*y+2,2*x:2*x+2].tolist(),'nativeFaces2x2':[[list(faces[(xx,yy)]) if (xx,yy) in faces else None for xx in range(2*x,2*x+2)] for yy in range(2*y,2*y+2)],'areaKnown':float(bright[y,x]+dark[y,x]),'areaUnknown':float(unknown[y,x]),'naiveWithoutSourceConnectivity':int(naive[y,x]),'sourceConnectedCandidate':int(candidate[y,x])})
 #64 already retained uncertain transition pixels, but omitted them from its
 # contour hierarchy. Export them explicitly as SOFT evidence, never hard locks.
 registry=json.loads((sibling('renderer-family59','2026-10-31-renderer-family59')/'SOURCE_REGISTRY59.json').read_text());soft=[];sourceOld=sibling('uv-features64','2026-10-31-uv-features64')
 activeMeshes={r['mesh'] for r in binding['mapped'] if r['hair']}
 for m in meshes:
  if m['index'] not in activeMeshes:continue
  for sm,sub in enumerate(m['submeshes']):
   b=next(x for x in registry['bindings'] if x['rendererOrdinal']==m['index'] and x['subMesh']==sm);mid=b['materialId']
   assert hashlib.sha256(m['uv'].astype('<f4').tobytes()).hexdigest()==b['meshUVSHA256']
   assert hashlib.sha256(sub['indices'].astype('<u4').tobytes()).hexdigest()==b['indexSHA256']
   image=sourceOld/f'NATIVE_SOURCE64-{mid}.png';assert hashlib.sha256(image.read_bytes()).hexdigest()==b['imageSHA256']
   z=np.load(sourceOld/f'SOURCE64-{mid}.npz');groups,_=edge_components(z['emergentX'],z['emergentY']);soft.append({'materialId':mid,'UVAndIndexHashMatchedCurrentGeometry':True,'oldCoarseRegionCount':len(np.unique(z['coarse'][z['support']])),'uncertainEdges':int(z['emergentX'].sum()+z['emergentY'].sum()),'uncertainContourComponents':len(groups),'contours':groups,'hardFeatureLock':False,'sourceImageSHA256':b['imageSHA256'],'runtimeTextureFilterVerified':False})
  # No source renderer names, colour constants or triangle-number ranges used as semantic labels.
 collisions=[{'xyDown':[int(x+ox),int(271-y-oy)],'postEyeUVz':float(a['selected-uv'][y,x,2]),'shadeQ':int(q[y,x]),'producer':'EyeFeature348.compute Evaluate:217 raw UV provenance; Merge:222'} for y,x in np.argwhere(mask&((a['selected-uv'][...,2]<0)|(a['selected-uv'][...,2]>1)))]
 gate=reference_gate(referenceMetrics)
 np.savez_compressed(ROOT/'CANDIDATE69.npz',mask=mask,QBefore=q,QCandidate=candidate,QAccepted=q,QUnsafeCounterfactual=naive,knownArea=bright+dark,unknownArea=unknown)
 summary=lambda c:{k:c[k] for k in ['components','singletons','sharedEdges','paths']}
 report={'sourceId':state['sourceId'],'paletteCreated':False,'gOrThresholdChanged':False,'sourceRGBUVGeometryChanged':False,'shadeBefore':summary(before),'sourceConnectedCandidate':summary(after),'unsafeWithoutSourceConnectivity':summary(loose),'candidateChanges':changes,'representatives':representatives,'validReferenceTriangles':[len(r) for r in guides],'rejectedReferenceTriangles':rejected,'fixedReferenceMetrics':referenceMetrics,'referenceMeaning':'interval over BOTH diagonal piecewise-linear STORED native-g estimates, not exact continuous lighting/coverage','schemaCollisionCells':collisions,'source64SoftContours':soft,'adopted':False,'decision':'No aesthetic adoption. Area reference alone is not a curvature/feature-quality objective. Reject changes that merely reduce singleton counts or interpolate through different visible surfaces. Source64 uncertain-contour export is an input representation repair, not a rendered correction.','missing':['Eye feature/count records not captured; direct-host patch is offline only','UV source uncertain curves are not authored semantic boundaries','No consecutive pose/blink samples; temporal stability not tested']}
 report['referenceGate']=gate;report['acceptedOutputChanges']=0;report['connectivityGateLimit']='Shared source vertices are a conservative local witness, not a complete visibility test. Rejected guide triangles are UNKNOWN, not all proven occlusions. Broader surface traversal can be investigated offline from existing geometry.'
 (ROOT/'RESULT69.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 yy,xx=np.where(mask);x0,y0,x1,y1=xx.min(),yy.min(),xx.max()+1,yy.max()+1;ims=[]
 for title,labels in [('Original Q',q),('Source-connected area',candidate),('UNSAFE no-source counterfactual',naive)]:
  c=np.zeros((*mask.shape,3),np.uint8);c[mask& (labels==0)]=[25,120,170];c[mask&(labels==1)]=[235,160,35];im=Image.fromarray(np.flipud(c[y0:y1,x0:x1]));im=im.resize((im.width*12,im.height*12),Image.Resampling.NEAREST);ims.append((title,im))
 board=Image.new('RGB',(sum(im.width+16 for _,im in ims),max(im.height for _,im in ims)+45),(28,29,34));d=ImageDraw.Draw(board);x=8
 for title,im in ims:d.text((x,8),title,fill='white');board.paste(im,(x,35));x+=im.width+16
 board.save(ROOT/'CANDIDATE69.png')
 print(json.dumps({k:v for k,v in report.items() if k not in ['source64SoftContours','representatives','schemaCollisionCells']},ensure_ascii=False,indent=2));print('SOFT_CONTOURS',[{k:v for k,v in r.items() if k!='contours'} for r in soft]);print('REPRESENTATIVES',representatives)
if __name__=='__main__':main()
