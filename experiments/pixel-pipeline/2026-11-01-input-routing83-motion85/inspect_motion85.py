from pathlib import Path
import json,sys,numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OUT=HERE/'visual85-v2';OUT.mkdir(exist_ok=False)
from validate_motion85 import packet,rgb8,geometry
sys.path.insert(0,str(ROOT/'apply-capture66'));from analyse_capture68 import camera
state=json.loads(sorted((HERE/'motion85').glob('STATE85*'))[-1].read_text());entries=state['sequencePackets'];actual=json.loads((HERE/'result85-v2/RESULT85.json').read_text())['rows'];source=np.load(ROOT/'whole-eye52/SOURCE_SURFACES52.npz');rest=source['native_xyz_head'];tri=source['native_role6_tri'];rows=[];frames=[];projectionErrors=[];anchors=[];phaseRecords=[]
for n,entry in enumerate(entries):
 path=Path(entry['output']);d=packet(path);a=d['arrays'];rec=d['records'];manifest=d['manifest'];motion=manifest['motion82'];rx,ry,rw,rh=d['eyeROI'];x,y,w,h=d['roi'];cam=camera(path/'source.camera');gi,meshes=geometry(path/'evaluated-source.geometry');m=meshes[1];assert gi==d['identity'];assert np.array_equal(m['submeshes'][6]['indices'],tri)
 # Same original primitive and barycentric position across frames, not screen RGB
 # equality. These centroids are references, not claims of continuous visibility.
 centroids=m['vertices'][tri].mean(1);world=np.c_[centroids,np.ones(len(centroids))]@m['matrix'].T;view=world@cam['view'].T;clip=view@cam['effective'].T;xy=(clip[:,:2]/clip[:,3:4]*.5+.5)*[480,272];anchors.append(xy)
 sm=a['S3-meta'];pt=a['S3-point'];uv=a['S3-uv'];valid=(sm[...,0]>0)&(pt[...,3]>.5)&(sm[...,3]>0);errors=[]
 for sy,sx in np.argwhere(valid):
  primitive=int(round(float(uv[sy,sx,2])))-1;ids=tri[primitive];src=rest[ids];q=pt[sy,sx,:3].astype(float);weights=np.linalg.lstsq(np.c_[src,np.ones(3)].T,np.r_[q,1],rcond=None)[0];position=m['matrix']@np.r_[weights@m['vertices'][ids],1];vv=cam['view']@position;cc=cam['effective']@vv;projected=(cc[:2]/cc[3]*.5+.5)*[480,272];errors.append([float(np.linalg.norm(projected-[rx+(sx+.5)/4,ry+(sy+.5)/4])),abs(float(-vv[2]-sm[sy,sx,0]))])
 if errors:projectionErrors.append(np.max(errors,axis=0).tolist())
 eyeRows=[]
 for ei,centre in enumerate(manifest['eyeFeature']['centres']):
  sid=int(centre[3]);mask=(np.rint(rec[...,3,1])==sid)&np.isin(np.rint(rec[...,3,0]),[2,3,4]);irisCounts=d['counts'][ei,...,2:5].sum(-1,dtype=np.float32);area=np.float32(0)
  for value in irisCounts.flat:area=np.float32(area+np.float32(value/16))
  raw=a['S2-meta'];rawArea=float(np.where((raw[...,0]>0)&(np.rint(raw[...,2])==sid),np.clip(raw[...,3],0,1),0).sum()/16)
  native=next(z for z in actual[n]['eyes']if z['eye']==sid);old=d['original'][ry-y:ry-y+rh,rx-x:rx-x+rw];oldIris=(np.rint(old[...,3,1])==sid)&np.isin(np.rint(old[...,3,0]),[2,3,4]);protected=rec[...,14,2]>.5;eyeRows.append({'eye':sid,'irisVisibleWeightedArea':float(area),'irisRawS2Area':rawArea,'roundedIrisBudget':int(np.floor(np.float32(area+.5))),'outputIrisCells':int(mask.sum()),'protectedIrisCells':int((mask&protected).sum()),'newIrisCells':int((mask&~protected).sum()),'frozen76IrisCells':int(oldIris.sum()),'sameFrame76To77IrisShapeEqual':bool(np.array_equal(mask,oldIris)),'irisCellsXYTopLeft':[[int(xx+rx),int(271-(yy+ry))]for yy,xx in np.argwhere(mask)],'upperOutputCells':native['reserved']+len(native['selected']),'upperIntrinsicArea':native['intrinsicArea'],'upperVisibleArea':native['visibleArea'],'newUpperCells':native['selected']})
 close={k:v for k,v in m['morphs']if 'eye' in k.lower()and 'close'in k.lower()}
 row={'frame':entry['frame'],'serial':entry['serial'],'stage':entry['testStage82'],'stageIndex':entry['stageIndex82'],'sourceId':entry['sourceId'],'topologySHA':manifest['eyeFeature']['topologySHA256'],'eyes':eyeRows,'closeMorphs':close,'playerPosition':motion['playerPosition'],'avatarRotation':motion['avatarRotation'],'animatorSpeed':motion['animatorSpeed'],'sourceFrame':manifest['sourceFrame'],'normalizedTime':motion['normalizedTime'],'captureDeltaTime':motion['captureDeltaTime'],'cellPitch':motion['cellPitch'],'nativeDeliveredDeltaCells':motion['deliveredDelta'],'historyReset':motion['historyResetRequested']};rows.append(row)
 if entry['testStage82']=='phase':phaseRecords.append({'records':rec.copy(),'headRGB8':rgb8(a['head-final'][...,:3]),'pose':m['vertices'].copy(),'centredNative':centroids-centroids.mean(0)})
 # Actual saved final ROI is distinct from logical pre-presentation head colour.
 head=Image.fromarray(np.flipud(rgb8(a['head-final'][...,:3])));native=Image.fromarray(np.flipud(rgb8(a['native-eye-rgba'][...,:3])));head.save(OUT/('head-'+str(entry['frame'])+'-1x.png'));native.save(OUT/('native-'+str(entry['frame'])+'-1x.png'))
 frames.append((entry,head,native))
for stage,scale in [('phase',8),('walk',7),('turn',6)]:
 group=[x for x in frames if x[0]['testStage82']==stage];w,h=group[0][1].size;sheet=Image.new('RGB',(w*scale*len(group),h*scale+24),'#171b22');draw=ImageDraw.Draw(sheet);gif=[]
 for i,(entry,head,native)in enumerate(group):
  tile=head.resize((w*scale,h*scale),Image.Resampling.NEAREST);sheet.paste(tile,(i*w*scale,24));draw.text((i*w*scale+3,5),stage+' '+str(entry['frame']),fill='white');gif.append(tile)
 sheet.save(OUT/(stage+'-head-nearest.png'));gif[0].save(OUT/(stage+'-head-slow-review.gif'),save_all=True,append_images=gif[1:],duration=120,loop=0,disposal=2)
 # Native-final images have their original raster sizes, no claimed extra pixels.
 maxw=max(z[2].width for z in group);maxh=max(z[2].height for z in group);sheet=Image.new('RGB',(maxw*3*len(group),maxh*3+24),'#333843');draw=ImageDraw.Draw(sheet)
 for i,(entry,head,native)in enumerate(group):sheet.paste(native.resize((native.width*3,native.height*3),Image.Resampling.NEAREST),(i*maxw*3,24));draw.text((i*maxw*3+3,5),'native '+str(entry['frame']),fill='white')
 sheet.save(OUT/(stage+'-native-nearest3.png'))
first=phaseRecords[0];phase=[]
for n,d in enumerate(phaseRecords):
 r=d['records'];base=first['records'];phase.append({'frame':rows[n]['frame'],'visibleFeatureEyeLabelsEqualToFirst':bool(np.array_equal(r[...,3,:2],base[...,3,:2])),'headRGB8ChangedPixels':int(np.any(d['headRGB8']!=first['headRGB8'],axis=-1).sum()),'headRGB8MaxAbsDelta':int(np.max(abs(d['headRGB8'].astype(int)-first['headRGB8'].astype(int)))),'eyeRecordRGB8ChangedCells':int(np.any(rgb8(r[...,0,:3])!=rgb8(base[...,0,:3]),axis=-1).sum()),'eyeRecordRGB8MaxAbsDelta':int(np.max(abs(rgb8(r[...,0,:3]).astype(int)-rgb8(base[...,0,:3]).astype(int)))),'evaluatedVertexCoordinateMaxDelta':float(np.max(abs(d['pose']-first['pose']))),'nativeCentredCoordinatesMaxDelta':float(np.max(abs(d['centredNative']-first['centredNative']))),'samePrimitiveCentroidMaxProjectedDeltaPixels':float(np.max(np.linalg.norm(anchors[n]-anchors[0],axis=1)))})
assert all(x['visibleFeatureEyeLabelsEqualToFirst']for x in phase)
assert all(not x['historyReset']for x in rows)
out={'rows':rows,'phaseChecks':phase,'sourceProjectionMaxErrorPixels':float(np.max(np.array(projectionErrors)[:,0])),'sourceDepthMaxErrorMetres':float(np.max(np.array(projectionErrors)[:,1])),'phaseDeliveredDeltaPeakToPeakCells':np.ptp([r['nativeDeliveredDeltaCells']for r in rows[:6]],axis=0).tolist(),'upperOutputPerEyeDuringPhaseWalk':[[r['frame'],[e['upperOutputCells']for e in r['eyes']]]for r in rows[:14]],'limits':['Actual6 phase/8 walk/10 turn frames are separate contiguous segments;8 warmup frames between phase and walk were not captured.','Quarter-cell world movement is real, but the following camera largely cancels its projected phase. It is not a full0..1 display-pixel phase sweep.','Iris visible output count varies during walk and turn; source visibility and changing pose are recorded. Count alone is not classified as flicker or a legitimate design.','GIFs are slowed120ms/frame for inspection, not realtime playback.','Native final strips retain actual saved ROI; gray padding outside each ROI is unobserved, not invented backing.']}
(OUT/'TEMPORAL85.json').write_bytes((json.dumps(out,indent=2)+'\n').encode());print(json.dumps({'frames':len(rows),'phaseLabelStable':all(x['visibleFeatureEyeLabelsEqualToFirst']for x in phase),'phaseScreenSpan':out['phaseDeliveredDeltaPeakToPeakCells'],'sourceProjectionError':out['sourceProjectionMaxErrorPixels'],'phaseHeadRGBChanges':[x['headRGB8ChangedPixels']for x in phase],'walkUpperTotals':[[e['upperOutputCells']for e in r['eyes']]for r in rows[6:14]]},indent=2))
