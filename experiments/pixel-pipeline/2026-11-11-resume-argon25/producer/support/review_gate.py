"""Check actual source certificates, final LUT colours and evaluated blink."""
from pathlib import Path
import collections,hashlib,json,struct,sys
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;R=H.parents[2];G=H/'gate-alpha'
sys.path.insert(0,str(R/'bounded-form115/runtime24/full-render24'))
from report_full24 import read,plane,buffer,full,rgba

def columns(p):
 b=p.read_bytes();n,stride=struct.unpack_from('<II',b);assert stride==48 and len(b)==8+n*48
 return np.frombuffer(b,dtype='<f4',offset=8).reshape(n,3,4)

def main():
 global G
 surface='--surface'in sys.argv;native='--native-proof'in sys.argv or surface
 if native:G=H/('surface27'if surface else'native-proof')
 motion='--motion'in sys.argv
 pigment='--pigment'in sys.argv
 root=G/('pigment-motion'if motion and pigment else'motion-run'if motion else'pigment-run'if pigment else'typed-run'if native and not surface else'phase-run');s=read(next(root.glob('STATE113-*-finished.json')))
 assert s['PlayExited']and not s.get('error')and not s.get('restorationError')and not s['globalRestoreErrors']
 unavailable=[v for v in s['nativeComparisons72']if v['equal']is not True]
 assert not unavailable or native and unavailable==[{'equal':None,'path':'ProjectSettings/ProjectSettings.asset','status':'Unavailable','type':'UnityEditor.AssetImporter'}],unavailable
 assert s['motionRestoration82']['allRestored']
 assert all(s[k]for k in ['optionsRestored','pipelineRestored','timeRestored','backgroundRestored','observerRemoved'])
 lut=read(R/'argon23-runtime113/SOURCE113.json');out=root/'results';out.mkdir(exist_ok=True)
 rows=[];certRows=[];paletteCount=0;coordCount=0;cropCount=0;images=[];negative=[];phaseForms=[]
 for pi,pkt in enumerate(s['sequencePackets']):
  p=Path(pkt['output']);m=read(p/'RAW_MANIFEST.json');assert hashlib.sha256((p/'RAW_MANIFEST.json').read_bytes()).hexdigest()==(p/'RAW_COMPLETE76.marker').read_text().strip()
  assert m['sourceId']==pkt['sourceId']and m['frameUnchangedDuringReadback']and m['algorithmValid113']
  if not motion:assert m['motion82']['evaluatedStateConditionPassed']
  n=m['forward102'];cw,ch=np.array(n['canonicalSize'])//4;dw,dh=n['denseSize'];rx,ry,w,h=m['grid102']['eyeTopLeftROI'];o=np.array(n['headHair25']['origin'],np.float32)
  ids=buffer(p/'curve-identity.f32').reshape(ch,cw,4);sourceColour=buffer(p/'curve-colour.f32').reshape(ch,cw,4);cells=buffer(p/'REGION113-cells.f32').reshape(-1,7,4)[:cw*ch];vis=buffer(p/'dense-three-part-visibility.f32').reshape(3,dh*dw,4)
  if motion and pkt['testStage82']=='measured-phase':phaseForms.append({'parts':ids[...,:2].copy(),'colour':buffer(p/'curve-colour.f32').copy(),'origin':o.copy()})
  q=buffer(p/'ASSIGNED-depth24.f32').reshape(h,w,16,4);v=buffer(p/'ASSIGNED-visibility24.f32').reshape(h,w,16,4)
  cols=columns(p/'SOURCE-columns26.f32');proof=m['sourceWitnessColumns26'];assert proof['sourceId']==m['sourceId']and proof['sameFrame']==m['frameIndex']and proof['count']==len(cols)
  source={}
  for part,label in [(1,'D-part1'),(2,'D-part2'),(3,'D-lid')]:
   source[part]={field:plane(p/(label+'-'+field+'.plane'))[1][::-1].reshape(-1,4)for field in ['rgba','meta','uv']}
  for cy,cx in np.argwhere(ids[...,0]>0):
   role,owner=ids[cy,cx,:2].astype(int);part={1:1,4:2,6:3}[role];cert=cells[cy*cw+cx,6];witness=int(cert[part-1]);assert cert[3]==26
   if witness>0:
    at=witness-1;alpha=source[part]['rgba'][at,3];vv=vis[part-1,at];meta=source[part]['meta'][at];uv=source[part]['uv'][at]
    assert alpha>0 and np.all(vv[:2]==alpha)and round(float(meta[2]))==owner and vv[3]==0
    certRows.append({'sourceId':m['sourceId'],'canonical':[int(cx),int(cy)],'owner':int(owner),'part':part,'witnessIndex':at,
     'nativePrimitive':int(round(float(uv[2]))),'UV':uv[:2].tolist(),'intrinsicAlpha':float(alpha),'weightedVisibility':vv[:2].tolist(),'faceTransmittanceExactlyOne':True})
   elif witness<0:
    assert part==3;ci=-witness-1;col=cols[ci];assert col[1,3]>0 and np.all(col[2,:2]==1)and round(float(col[0,3]))==owner
    if native:
     nq=buffer(p/'COLUMN-native26.f32').reshape(-1,4)[ci]
     assert nq[2]>0 and nq[3]==owner and nq[2]==col[0,2]
    certRows.append({'sourceId':m['sourceId'],'canonical':[int(cx),int(cy)],'owner':int(owner),'part':part,'columnWitness':ci,
     'sourcePoint':col[1].tolist(),'faceVisibility':col[2,:2].tolist(),'faceTransmittanceExactlyOne':True})
  _,fo=plane(p/'F-FinalOwner.plane');_,fc=plane(p/'F-FinalRGBA.plane');_,eo=plane(p/'F-EyeOwner.plane');visible={};mapped=set();detail=[]
  for y in range(h):
   for x in range(w):
    c=np.floor(np.asarray([rx+x+.5,ry+h-y-.5],np.float32)-o).astype(int);cx,cy=c
    expected=o+c.astype(np.float32)+np.array([[(j%4+.5)/4,1-(j//4+.5)/4]for j in range(16)],np.float32);valid=q[y,x,:,2]>0
    assert np.array_equal(q[y,x,valid,:2],expected[valid]);coordCount+=int(valid.sum())
    if 0<=cx<cw and 0<=cy<ch and ids[cy,cx,0]>0:mapped.add((int(cx),int(cy)))
    role,owner=fo[y,x,:2].astype(int)
    if role in(2,5,7):
     assert np.array_equal(fc[y,x],sourceColour[cy,cx])and int(ids[cy,cx,0])+1==role and int(ids[cy,cx,1])==owner
     part=role-1;pal=lut['lidPalette']if part==6 else lut['keys'];a=np.array([v['linear']for v in pal if v['owner']==owner and(part==6 or v['part']==part)],np.float32)
     assert np.any(np.all(a==fc[y,x,:3],axis=1));paletteCount+=1;visible[int(cx),int(cy)]=[int(role),int(owner)]
    if (int(cx),int(cy))in[(10,4),(8,5),(10,3)]:detail.append({'canonical':[int(cx),int(cy)],'preHair':eo[y,x].tolist(),'final':fo[y,x].tolist(),'faceVisible16':v[y,x,:,:2].sum(0).tolist()})
  missing=[(int(x),int(y))for y,x in np.argwhere(ids[...,0]>0)if(int(x),int(y))not in mapped];cropCount+=len(missing);assert not missing
  product,sid=full(p,'product77');candidate,sid2=full(p,'candidate113');assert sid==sid2==m['sourceId']
  ox,oy=m['grid102']['headToMainOffset'];xx=rx+round(ox);yy=272-ry-h+round(oy);outside=np.ones(product.shape[:2],bool);outside[yy:yy+h,xx:xx+w]=False;assert np.array_equal(product[outside],candidate[outside])
  for name,a in [('control',product),('candidate',candidate)]:
   im=Image.fromarray(rgba(np.flipud(a)));im.save(out/f'{pi:02d}-{name}.png');im.crop((xx,272-yy-h,xx+w,272-yy)).resize((w*16,h*16),Image.Resampling.NEAREST).save(out/f'{pi:02d}-{name}-eye.png')
   if name=='candidate':images.append(im)
  close=m['motion82'].get('requestedClose');parts=dict(collections.Counter(str(tuple(fo[y,x,:2].astype(int)))for y in range(h)for x in range(w)if int(fo[y,x,0])in(2,5,7)))
  if close==100:assert not np.any(np.isin(fo[...,0],[2,5]))
  for y,x in np.argwhere(fo[...,3]<0):negative.append({'sourceId':sid,'frame':m['frameIndex'],'stage':pkt['testStage82'],'physicalROI':[int(x),int(y)],'owner':fo[y,x].tolist()})
  if not motion and not native:assert not np.any(fo[...,3]<0)
  rows.append({'sourceId':sid,'frame':m['frameIndex'],'requestedClose':close,'evaluatedMeshError':m['motion82'].get('evaluatedVsOwnedBakeMax'),
   'motion':m['motion82'],'testStage':pkt['testStage82'],'stageIndex':pkt['stageIndex82'],
   'ROI':[rx,ry,w,h],'finalParts':parts,'criticalCells':detail,'visibleCanonicalEyeLabels':{str(k):z for k,z in visible.items()}})
 if not motion:
  assert [v['requestedClose']for v in rows]==[0,75,100,0]
  assert rows[0]['visibleCanonicalEyeLabels']==rows[-1]['visibleCanonicalEyeLabels']
 else:assert len(rows)==28 and len(phaseForms)==10
 phaseChanges=[]
 if motion:
  for i in range(1,10):
   assert np.array_equal(phaseForms[0]['parts'],phaseForms[i]['parts'])and phaseForms[0]['colour'].tobytes()==phaseForms[i]['colour'].tobytes()
   before=rows[0]['visibleCanonicalEyeLabels'];after=rows[i]['visibleCanonicalEyeLabels']
   changed=[k for k in set(before)|set(after)if before.get(k)!=after.get(k)]
   if changed:phaseChanges.append({'frame':rows[i]['frame'],'changedCanonical':changed})
 result={'actualGPUStates':rows,'verifiedSelectedSourceCertificates':len(certRows),'sourceCertificateRows':certRows,'queryCoordinatesExact':coordCount,
  'sourceCellsClipped':cropCount,'eyeLinearPaletteExactTests':paletteCount,'paletteOutside':0,'finalNegativeStatus':len(negative),'negativeRows':negative,
  'eyeRGBADirectSourceExactTests':paletteCount,'unknownCarrierOrIntervalStatuses':sum(v['owner'][3]in[-116,-114,-113]for v in negative),
  'Close100IrisWhite':None if motion else 0,'openReopenLabelsEqual':None if motion else True,'phaseEyeLabelChanges':phaseChanges,
  'phaseOrigins':[v['origin'].tolist()for v in phaseForms],
  'nativeComparisonsEqual':sum(v['equal']is True for v in s['nativeComparisons72']),'nativeComparisonsUnavailable':unavailable,'PlayNormallyExited':True,'globalRestoreErrors':[],
  'inputSameReferenceAndJSON':s['editInputRestoration82']['sameAliveReference']and s['editInputRestoration82']['exactJSON'],
  'memoryBefore':s['beforeMemory'],'memoryAfter':s['afterMemory'],'allocatedDeltaBytes':s['afterMemory']['allocated']-s['beforeMemory']['allocated'],
  'product77DefaultChanged':False,'limits':['Four evaluated blink states, not complete motion/rotation/phase/multiview validation.',
   'Certificate proves selected original ray visibility, not visibility of every point in the source footprint.',
   'Active dominant-affiliation case only; optional two-ring policy not applied.','Full face UV hierarchy/palette/outline incomplete.']}
 (G if native else H).joinpath('GPU_MOTION26.json'if motion else'GPU_GATE26.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 selected=[0,1,8,9,10,17,18,27]if motion else list(range(4))
 dimensions={i:Image.open(out/f'{i:02d}-candidate-eye.png').size for i in selected}
 column=max(v[0]for v in dimensions.values())+16
 heights={i:dimensions[i][1]+40 for i in selected};tops={};height=0
 for i in selected:tops[i]=height;height+=heights[i]
 board=Image.new('RGB',(column*2,height),(32,32,32));draw=ImageDraw.Draw(board)
 for position,i in enumerate(selected):
  row=rows[i]
  for j,name in enumerate(['control','candidate']):
   label=f'{name} {row["testStage"]} {row["stageIndex"]}'if motion else f'{name} evaluated Close {row["requestedClose"]}'
   im=Image.open(out/f'{i:02d}-{name}-eye.png').convert('RGB');board.paste(im,(j*column,tops[i]+24));draw.text((j*column+4,tops[i]+4),label,fill='white')
 board.save((G if native else H)/('EYE_MOTION26.png'if motion else'EYE_GATE26.png'));images[0].save(out/('SEQUENCE_MOTION26.webp'if motion else'SEQUENCE_GATE26.webp'),save_all=True,append_images=images[1:],duration=180 if motion else 360,loop=0,lossless=True)
 if motion:
  thumbs=[Image.open(out/f'{i:02d}-candidate-eye.png').convert('RGB')for i in range(len(rows))]
  tw=max(im.width for im in thumbs)+16;th=max(im.height for im in thumbs)+40
  allFrames=Image.new('RGB',(tw*4,th*7),(32,32,32));ad=ImageDraw.Draw(allFrames)
  for i,im in enumerate(thumbs):
   x=(i%4)*tw;y=(i//4)*th;allFrames.paste(im,(x,y+24));ad.text((x+3,y+4),f'{rows[i]["testStage"]} {rows[i]["stageIndex"]} / f{rows[i]["frame"]}',fill='white')
  allFrames.save((G if native else H)/'ALL_MOTION_EYES26.png')
 print(json.dumps({'actualStates':len(rows),'sourceCertificatesVerified':len(certRows),'queryCoordinatesExact':coordCount,'sourceClipped':cropCount,'paletteOutside':0,'finalNegativeStatus':len(negative),
  'phaseEyeLabelChanges':len(phaseChanges),'Close100IrisWhite':None if motion else 0,'openReopenLabelsEqual':None if motion else True,'nativeEqual':result['nativeComparisonsEqual'],'allocatedDeltaMiB':result['allocatedDeltaBytes']/1048576}))
if __name__=='__main__':main()
