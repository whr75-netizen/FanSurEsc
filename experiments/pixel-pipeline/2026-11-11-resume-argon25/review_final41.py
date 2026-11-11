from pathlib import Path
import json,numpy as np,sys
from PIL import Image,ImageDraw
from final_contour41 import resolve,coordinates
H=Path(__file__).resolve().parent;G=H/'face41';worldCase='--world'in sys.argv;G=G/'world'if worldCase else G;C=G/'capture';O=G/'analysis'
def main():
 r=json.loads((C/'COMPLETE.json').read_text());assert r['restorationChecksPass']and r['ownedResourcesReleased']and not r['errors']and r['pendingOwners']==0;O.mkdir(exist_ok=True);rows=[];images=[]
 if worldCase:
  state=r['worldFixture41After'];assert state['disposed']and not any(state[k]for k in ['ownedGoAlive','ownedMeshAlive','ownedMaterialAlive'])
 for f in r['frames']:
  p=next(p for p in r['planes']if p['frame']==f['frame']);a=np.fromfile(C/p['file'],dtype='<f4').reshape(p['height'],p['width'],4);x,y,w,h=f['QROI'];assert p['width']==15*w;fields=[a[:,i*w:(i+1)*w]for i in range(15)];info=f['frameInfo']['finalComposite41'];assert info['sameFrame']==f['frame']and info['sourceId']==f['sourceId'];main,out,inside=coordinates(f['QROI'],[480,272],info['joinOffset'],info['composeDelta']);assert info['headTextureOrigin']==[x,272-y-h]
  ink=np.asarray(f['frameInfo']['sourceOutlineRGB39'],np.float32);expected,gate=resolve(fields[3],fields[4],fields[9],fields[12],fields[13],inside,info['depthOffset'],ink);assert expected.tobytes()==fields[10].tobytes()and gate.tobytes()==fields[11].tobytes();source=gate[:,:,0]==1;use=gate[:,:,3]==1
  points=[];planeDepth=None;planeErrors=[]
  if worldCase:
   from trace_contour40 import geometry
   geom=geometry(C/('geometry-frame'+str(f['frame'])+'.bin'));assert geom['sourceId']==f['sourceId'];fixture=f['frameInfo']['worldFixture41'];assert fixture['frame']==f['frame']and not fixture['disposed'];planeDepth=float(-(geom['view']@np.r_[fixture['position'],1])[2]+info['depthOffset']);planeErrors=[float(v-planeDepth)for v in fields[13][:,:,0][source&(gate[:,:,2]==0)]]
  for yy,xx in np.argwhere(source):points.append({'local':[int(xx),int(yy)],'mainTexture':main[yy,xx].tolist(),'outputTexture':out[yy,xx].tolist(),'sourceEdgeId':int(fields[4][yy,xx,1]),'sourceHeadDepth':float(fields[4][yy,xx,0]),'transportedDepth':float(np.float32(fields[4][yy,xx,0]+np.float32(info['depthOffset']))),'mainResolvedMeta':fields[12][yy,xx].tolist(),'worldInfo':fields[13][yy,xx].tolist(),'gate':gate[yy,xx].tolist()})
  rows.append({'frame':f['frame'],'sourceId':f['sourceId'],'sourceLineCells':int(source.sum()),'selected':int(use.sum()),'styleRejected':int((source&(gate[:,:,1]==0)).sum()),'worldRejected':int((source&(gate[:,:,2]==0)).sum()),'invalid':int((gate[:,:,3]<0).sum()),'CPURGBByteEqual':True,'CPUGateByteEqual':True,'paletteMismatch':int((fields[10][use,:3]!=ink).any(1).sum()),'unselectedChanged':int((fields[10][~use]!=fields[9][~use]).any(1).sum()),'motion':f['frameInfo']['motion40'],'expectedFixturePlaneDepth':planeDepth,'actualWorldDepthMinusFixturePlaneDepth':planeErrors,'cells':points})
  def display(z):
   z=np.clip(z[::-1,:,:3],0,1);z=np.where(z<=.0031308,12.92*z,1.055*z**(1/2.4)-.055);return Image.fromarray(np.uint8(np.rint(z*255)))
  board=Image.new('RGB',(720,340),(35,37,43));d=ImageDraw.Draw(board)
  for i,(name,img)in enumerate([('Actual main INTERMEDIATE RGB',fields[9]),('Intermediate contour candidate',fields[10])]):
   im=display(img);board.paste(im,(i*360+6,35));board.paste(im.resize((w*8,h*8),Image.Resampling.NEAREST),(i*360+65,35));d.text((i*360+5,10),name+' F'+str(f['frame']),fill='white')
  d.text((8,307),'source '+str(source.sum())+'; selected '+str(use.sum())+'; style rejected '+str(rows[-1]['styleRejected'])+'; world rejected '+str(rows[-1]['worldRejected']),fill='white');board.save(O/('frame'+str(f['frame'])+'.png'));images.append(board)
 result={'actualFrames':[x['frame']for x in rows],'CPUByteMatches':len(rows),'restoration':True,'intermediateProposalActualGPU':True,'actualDeliveredNative395FinalObserved':False,'product77Changed':False,'worldFixtureCase':worldCase,'actualWorldOcclusionObserved':any(x['worldRejected']for x in rows),'faceColourRegionAndVariableThicknessComplete':False,'artAndTemporalStabilityPassed':False,'rows':rows};(O/'ACTUAL_FINAL41.json').write_text(json.dumps(result,indent=2),encoding='utf-8',newline='\n')
 strip=Image.new('RGB',(1440,1120),(35,37,43));d=ImageDraw.Draw(strip);d.text((10,10),'INTERMEDIATE DEPTH GATE 41 | NOT delivered Native395 final | 6 actual game-input frames',fill='white')
 for i,im in enumerate(images):strip.paste(im,((i%2)*720,50+(i//2)*340))
 d.text((10,1080),'Private candidate; product77 unchanged. Source outline colour only; full face palette / variable thickness incomplete.',fill='white');strip.save(G/'FACE_FINAL_DEPTH41.png');images[0].save(G/'FACE_FINAL_DEPTH41_MOTION.webp',save_all=True,append_images=images[1:],duration=200,loop=0,lossless=True)
 print(json.dumps({'frames':result['actualFrames'],'CPUMatches':len(rows),'selected':[x['selected']for x in rows],'styleRejected':[x['styleRejected']for x in rows],'worldRejected':[x['worldRejected']for x in rows],'invalid':[x['invalid']for x in rows]}))
if __name__=='__main__':main()
