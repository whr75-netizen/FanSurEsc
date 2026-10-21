from pathlib import Path
import json,struct,gzip,hashlib,collections,numpy as np
from PIL import Image,ImageDraw,features
W=Path(__file__).parent;R=W/'Loop514';a=json.loads((R/'ANALYSIS514.json').read_text());c=json.loads((R/'CAUSE514.json').read_text());r=json.loads((R/'REVIEW514.json').read_text())
def rd(i,tag):
 b=gzip.decompress((R/(f'{i:03d}_'+tag+'.bin.gz')).read_bytes());w,h,_,_=struct.unpack_from('<4i',b);return np.frombuffer(b,'<f4',offset=16).reshape(h,w,4)
body=[]
for row in a['rows']:
 for y,x in row['sameRoleColourDifferenceYX']['body']:
  i=row['target'];d={'target':i,'mainXY':[x,y],'buffers':{}}
  for tag in ['BASE','ALT']:d['buffers'][tag]={key:rd(i,tag+'_'+key)[y,x].tolist()for key in ['META','UV','OWNER','FINAL']}
  body.append(d)
light=[]
for row in a['rows']:
 cfg=json.loads((R/(f"{row['target']:03d}_ALT_projection.json")).read_text());light.append({k:cfg[k]for k in ['hour','ambientIntensity','directionalIntensity','directionalColour','directionalRotation']})
flash=[]
for f in c['internalColourScreening']:
 reasons=[s['reconstructedHairLineReason']for s in f['lineReconstruction']];flash.append({'target':f['observation']['target'],'xy':f['observation']['xy'],'alsoOriginal':f['alsoScreenedInOriginal'],'class':'OUTER_THIN_LINE_RULE_CONSISTENT'if reasons[0]==reasons[2]!=reasons[1]else'SOURCE_COLOUR_OR_SHADING_NOT_FIRST_STAGE_CERTIFIED','line':reasons})
wholeSeam=[]
for tag in ['BASE','ALT']:
 ma,mb=(rd(i,tag+'_META')for i in [0,80]);ca,cb=(rd(i,tag+'_FINAL')for i in [0,80]);pa,pb=(np.array(Image.open(R/f'{i:03d}_{tag}.png').convert('RGB'))for i in [0,80]);cov=(ma[:,:,0]>0)&(mb[:,:,0]>0);co2=np.repeat(np.repeat(cov,2,0),2,1);d=np.max(abs(pa.astype(int)-pb.astype(int)),axis=2)
 wholeSeam.append({'version':tag,'roleDifferences':int((ma[:,:,1]!=mb[:,:,1]).sum()),'alphaDifferences':int((ca[:,:,3]!=cb[:,:,3]).sum()),'screenMaxByteOnCoveredBoth':int(d[co2].max(initial=0)),'screenMaxByteOutsideCharacter':int(d[~co2].max(initial=0)),'preworldLinearMax':float(np.max(abs(ca-cb)))})
# Actual native screenshot crops. Yellow boxes annotate only the observed cell.
cases=[('region',51,234,43),('region',51,218,55),('line-rule',1,223,58),('new-line-rule',59,224,58),('unresolved-colour',65,229,48)];sheet=Image.new('RGB',(900,len(cases)*182),'#202020');draw=ImageDraw.Draw(sheet)
for line,(name,i,x,y)in enumerate(cases):
 draw.text((3,line*182+2),f'{name} phase{i/80:.4f} head({x},{y}) | each pose ORIGINAL348 / CURVES511+BODY512',fill='white')
 for step,t in enumerate([i-1,i,i+1]):
  pose=json.loads((R/f'{t:03d}_pose.json').read_text());ox,oy=pose['offset'];mx,my=x+ox,y-oy
  for col,tag in enumerate(['BASE','ALT']):
   im=Image.open(R/f'{t:03d}_{tag}.png').convert('RGB').crop((2*(mx-4),2*(my-4),2*(mx+5),2*(my+5))).resize((144,144),Image.Resampling.NEAREST);d=ImageDraw.Draw(im);d.rectangle((64,64,79,79),outline='#ffdd00',width=1);px=step*300+col*148;sheet.paste(im,(px,line*182+34));draw.text((px+2,line*182+18),f'{t/80:.4f} '+tag,fill='white')
sheet.save(R/'CASES514_NATIVE_REVIEW.png')
# Preserve every recorded loop sample at normal speed in an additional lossless
# animated WebP. GIF remains the requested normal-speed presentation artifact.
webp=None
if features.check('webp_anim'):
 box=tuple(a['gif']['nativePixelCrop']);w,h=box[2]-box[0],box[3]-box[1];frames=[];times=[]
 for i in range(81):
  cfg=json.loads((R/f'{i:03d}_ALT_projection.json').read_text());times.append(cfg['gameTime'])
  if i==80:continue
  canvas=Image.new('RGB',(w*2+2,h+38),'#181818');d=ImageDraw.Draw(canvas)
  for k,tag in enumerate(['BASE','ALT']):canvas.paste(Image.open(R/f'{i:03d}_{tag}.png').convert('RGB').crop(box),(k*(w+2),38))
  d.text((5,5),'CURRENT ACTIVE348 ORIGINAL',fill='white');d.text((w+7,5),'CURVES511 + BODY512 / OFF',fill='white');d.text((5,20),f'Walk {i/80:.4f} | all60fps samples {i}/80',fill='white');frames.append(canvas)
 elapsed=np.array(times)-times[0];ms=np.rint(elapsed*1000).astype(int);dur=np.diff(ms).tolist();target=R/'WALK514_NORMAL60_ALL_FRAMES.webp';frames[0].save(target,format='WEBP',save_all=True,append_images=frames[1:],duration=dur,loop=0,lossless=True,quality=100,method=4)
 webp={'path':str(target),'bytes':target.stat().st_size,'frames':80,'durationMs':sum(dur),'allLoopSamples':True,'pixelLossless':True,'resampling':False,'note':'duplicate endpoint used for seam check; all80 intervals shown at original nominal60fps,16/17ms frame durations'}
out={'status':'NOT_ADOPTED; GLOBAL_BOUNDARY_PACKET_PASS_WITH_REMAINING_TEMPORAL_REGION_AND_COLOUR_QUALITY','geometryInvariants':{'outside':a['outsideTotals'],'packetMismatchTotal':a['packetMismatchTotal'],'unsupportedTotal':a['unsupportedTotal'],'bodyReferenceErrors':r['bodyReferenceErrors'],'maxBodyRayDepthError':r['maxBodyRayDepthError'],'allPoseLightMatched':a['allPoseLightMatched']},'stableRecordedDirectionalLightAll81':all(v==light[0]for v in light),'recordedLight':light[0],'regionSummary':[{'xy':e['headXY'],'curveArea':[v['curveCellArea']for v in e['steps']],'sourceMeshArea':[v['sourceMeshUnion']['area']for v in e['steps']],'fillMinusEmptyCost':[v['fixedNeighbourFillMinusEmptyEnergy']for v in e['steps']],'toggleCost':[v['costToToggleWithCurrentNeighbours']for v in e['steps']]}for e in c['regionEpisodes']],'colourScreeningClasses':flash,'colourClassCounts':dict(collections.Counter(f['class']for f in flash)),'sameRoleBodyColourDifferences':body,'seamWholeCharacter':wholeSeam,'seamHead':c['seam'],'normalGif':a['gif'],'allFramesInspectionGif':a['inspectionGif'],'normalAllFramesWebP':webp,'remainingLimits':['Observed contour/input motion is real; pulse selection is not declared perceptually acceptable merely because the energy prefers it.','No new temporal filter, layer or production patch was applied.','Line-rule classification is reconstruction; GPU Before/Flood/Audit and complete world-shadow inputs were not captured.','The remaining source-colour/shading observations are not certified as normal or bugs.','Same directional light and frozen hour do not prove static world-shadow/other-light inputs.','Normal GIF uses67 nearest time samples; source frame51 is absent from it. All-frame inspection GIF,80-frame lossless normal WebP and original81 records retain the two one-frame observations.','Original348 and candidate are compared in this run; these changes cannot all be attributed to512 alone.']}
(R/'FINAL_REVIEW514.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k not in ['sameRoleBodyColourDifferences','seamHead','remainingLimits']}));print(json.dumps({'bodyColourDifferences':body}))
