from pathlib import Path
import json,sys,hashlib,numpy as np
from PIL import Image,ImageDraw
from actor_visibility96 import packet,ActorQuery
from review_packed93 import ribbon
from review_motion64 import srgb
from stream_apng99 import APNG99
H=Path(__file__).resolve().parent

def main():
 root=H/'face99'/sys.argv[1];r=json.loads((root/'capture/COMPLETE.json').read_text());assert r['Edit']and r['packetComplete']and r['restorationChecksPass']and r['ownedResourcesReleased']and not r['errors'];stream=r['stream77'];assert stream['actualConsecutive']and stream['sourceAlpha97ManagedBytesAfterRelease']==0 and stream['sourceWidth99EntriesAfterRelease']==0;frames=stream['frames'];n=len(frames);writer=APNG99(root/'ACTUAL_LONG99.png',344,158,n);board=Image.new('RGB',(1376,4*158),'#20252c');selected=set(np.linspace(0,n-1,16).round().astype(int).tolist());pictures=0;previous=None;rows=[];maxGreen=0.;queryErrors=[];samples=0;transitions=0;knownTransitions=0;rgbErrors=0;maskErrors=0;sourceIds=set()
 for i,f in enumerate(frames):
  assert f['ordinal']==i and f['sourceId']not in sourceIds;assert (f['previousFrame']==-1 if i==0 else f['previousFrame']==f['frame']-1 and f['previousSourceId']==frames[i-1]['sourceId']);sourceIds.add(f['sourceId']);assert f['motion']['matches']and f['joint97']['sourceId']==f['sourceId']and f['coupled98']['sourceId']==f['sourceId'];a,world,depth=packet(root,f);states=a[3,:,:,0];pruned=a[8,:,:,3]==2;added=a[3,:,:,3]==1;unknown=states==3;assert np.array_equal(a[7][~pruned],a[12][~pruned])and np.array_equal(a[7][pruned],a[5][pruned]);assert np.array_equal(a[12][unknown],a[9][unknown]);plain=(~unknown)&(~added);assert np.array_equal(a[12][plain],a[5][plain]);ink=np.array(f['ribbon93']['originalInkLinear']+[1],np.float32);assert np.array_equal(a[12][added],np.broadcast_to(ink,(int(added.sum()),4)));assert not np.any(pruned&(~added));proof={tuple(v[:2]):v for v in f['coupled98']['rows']}
  for y,x in np.argwhere(pruned):
   mask=int(proof[x,y][2]);realized=[]
   for dy in range(-1,2):
    for dx in range(-1,2):
     if mask&(1<<((dy+1)*3+dx+1)):
      nx,ny=x+dx,y+dy;assert 0<=nx<states.shape[1]and 0<=ny<states.shape[0];realized.append(bool(a[3,ny,nx,3]==1 and not pruned[ny,nx]and proof[nx,ny][2]==0 and proof[nx,ny][4]>=0))
   assert any(realized)
  greens={int(v[0]):v[1:]for v in f['joint97']['sourceGreens']}
  for y,x in np.argwhere(a[6,:,:,0]>0):
   _,edge,t,g=a[6,y,x];ga,gb=greens[int(edge)];maxGreen=max(maxGreen,abs(ga+(gb-ga)*float(t)-float(g)))
  if previous is not None:
   transitions+=int((a[7]!=previous).any(2).sum())
  previous=a[7].copy()
  if'actorSource96'in f:
   q=ActorQuery(root,f);anchors=ribbon(root/'capture'/f['ribbon93']['file'])[4];shift=np.array([anchors[2]-anchors[0],-(anchors[3]-anchors[1])]);selectedRows={tuple(v[:2]):v for v in f['joint97']['rows']}
   for y,x in np.argwhere(states==1):
    v=selectedRows[x,y];point=np.array(v[4:6]);z=v[6]
    for label,p in [('source',point-shift),('destination',point)]:
     hit=q.query(p);samples+=1
     if not hit['known']or hit['hit']is not None and hit['hit']['depth']<z-1e-4:queryErrors.append({'frame':f['frame'],'xy':[int(x),int(y)],'at':label,'lineZ':z,'hit':hit})
  picture=Image.new('RGB',(344,158),'#20252c');draw=ImageDraw.Draw(picture);draw.text((4,3),f"Actual GPU frame {f['frame']}   source {i+1}/{n}",fill='white')
  for k,(plane,label)in enumerate([(11,'Native'),(12,'97 control'),(7,'98B + CPU99')]):
   picture.paste(srgb(a[plane,:,:,:3]).resize((104,104),Image.Resampling.NEAREST),(4+k*112,35));draw.text((4+k*112,20),label,fill='white')
  draw.text((4,142),f"removed {int(pruned.sum())}; unknown {int(unknown.sum())}",fill='white');writer.append(picture)
  if i in selected:board.paste(picture,((pictures%4)*344,(pictures//4)*158));pictures+=1
  rows.append({'frame':f['frame'],'inputStage':f['motion']['stage'],'CPUms':f['profile99']['totalMs'],'sourcePointQueries':f['joint97']['pointQueries'],'triangleVisits':f['joint97']['triangleVisits'],'fineEntries':f['joint97']['fineEntries99'],'widthEntries':f['profile99']['widthEntries99'],'unknown':int(unknown.sum()),'pruned':int(pruned.sum())})
  if i%120==0:print(json.dumps({'validatedFrames':i+1,'total':n}),flush=True)
 assert maxGreen<=1/128+16*float(np.finfo(np.float32).eps);assert not queryErrors;media=writer.finish();board.save(root/'CONTACT_LONG99.png');out={'actualFrames':n,'simulationSeconds':sum(f['deltaTime']for f in frames),'actualConsecutive':True,'sameFrameGeometrySelectionNotOfflineRGBReplay':True,'inputMatchedEveryFrame':True,'paletteInkAndUnknownExactEveryFrame':True,'maximumWidthGreenError':maxGreen,'sourceDestinationSamples':samples,'queryErrors':queryErrors,'sourceIDsDistinct':len(sourceIds),'RGBTransitions':transitions,'CPUmsMedian':float(np.median([v['CPUms']for v in rows])),'CPUmsMaximum':max(v['CPUms']for v in rows),'allPoseActorGeometryFrames':sum('actorSource96'in f for f in frames),'prunedCells':sum(v['pruned']for v in rows),'rows':rows,'animation':media,'generalOpacityOrContinuousWorldVisibilitySolved':False,'finalArtAdopted':False};(root/'LONG_VALIDATED99.json').write_text(json.dumps(out,indent=2));(root/'MEDIA_COMPLETE99.json').write_text(json.dumps(media,indent=2));print(json.dumps({k:v for k,v in out.items()if k not in ['rows','queryErrors']}))
if __name__=='__main__':main()
