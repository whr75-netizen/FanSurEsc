from pathlib import Path
import sys,json,hashlib,struct,numpy as np
from PIL import Image,ImageDraw
from frame_bytes77 import decode
from history75 import preference
from test_flat67 import region_at
from review_motion64 import srgb
from variable_exterior72 import resolve
H=Path(__file__).resolve().parent;G=H/'face77'/sys.argv[1];C=G/'capture'
def pose(frame,triangle_count):
 raw=(C/f'pose-frame{frame}.bin').read_bytes();p=0;size=0;shift=0
 while True:
  b=raw[p];p+=1;size|=(b&127)<<shift
  if b<128:break
  shift+=7
 assert raw[p:p+size]==b'projected-source75/v1';p+=size;actual,n=struct.unpack_from('<ii',raw,p);p+=8;assert actual==frame and len(raw)==p+16*n
 return np.frombuffer(raw,dtype='<f4',offset=p).reshape(-1,4)[:triangle_count*3].reshape(triangle_count,3,4).copy()
def main():
 report=json.loads((C/'COMPLETE.json').read_text());s=report['stream77'];frames=s['frames'];assert report['packetComplete']and report['restorationChecksPass']and report['ownedResourcesReleased']and report['pendingOwners']==0 and not report['errors']and not report['globalErrors'];assert len(frames)==s['target']==s['received']==s['submitted']and s['actualConsecutive'];assert s['poolSlots']==6 and s['peakPending']<=6
 table=json.loads((C/'SOURCE_TABLE77.json').read_text());enabled=np.zeros(16,bool);maximum=np.zeros(16,int);inks=np.zeros((16,3),np.float32)
 for row in table:role=row['role'];enabled[role]=row['sourceEnabled'];maximum[role]=row['triangles'];inks[role]=row['sourceInkLinear']
 pinfo=report['sourcePalette67'];palette=np.asarray(pinfo['paletteLinear'],np.float32).reshape(-1,4);sp=json.loads((H/'face67/SOURCE_FLAT67.json').read_text());mask=np.fromfile(H/'face67/REGION_BOTTOM67.rgba',np.uint8).reshape(sp['sourceHeight'],sp['sourceWidth'],4);zinfo=pinfo['zeroWidth69'];zero=np.fromfile(H/'face69/ZERO_TRIANGLES69.r8',np.uint8);results=[];previous=None;previous_pose=None;cpu_history_frames=0;hist_total=0;file_total=0;film=[];selected=[];stored_max=0
 for fi,f in enumerate(frames):
  assert f['ordinal']==fi and (fi==0 or f['frame']==frames[fi-1]['frame']+1);assert f['previousFrame']==(-1 if fi==0 else frames[fi-1]['frame']);assert f['previousSourceId']==('warm'if fi==0 else frames[fi-1]['sourceId']);assert f['nativeSerial']>(frames[fi-1]['nativeSerial']if fi else 0)
  w,h=f['QROI'][2:];expected=f['bytes'];raw=decode((C/f['compressedFile']).read_bytes(),expected);assert hashlib.sha256(raw).hexdigest()==f['rawSHA256'];layers=expected//(w*h*16);data=np.frombuffer(raw,'<f4').reshape(h,w*layers,4);parts=[data[:,i*w:(i+1)*w]for i in range(layers)];before,after,key,meta,world,cell,owner,uv,source,trace,receipt,domain=parts[:12];assert np.isfinite(data).all();file_total+=f['storedBytes'];stored_max=max(stored_max,f['storedBytes']);yy,xx=np.indices((h,w));origin=np.array([f['QROI'][0]+f['join'][0],272-f['QROI'][1]-h+f['join'][1]]);q=np.stack([xx+origin[0],yy+origin[1]],2);valid=(cell[:,:,:2]==q).all(2);actor=cell[:,:,2]==1;designed=domain[:,:,0]>=.5;roles=np.rint(owner[:,:,0]).astype(int);ix=np.clip(roles,0,15);ordinary=valid&actor&~designed&(roles>0)&(roles<16)&(owner[:,:,0]==roles)&(source[:,:,0]==owner[:,:,2])&(source[:,:,1]==owner[:,:,0])&(source[:,:,2]==owner[:,:,1])&(source[:,:,3]>=1)&(source[:,:,3]==np.rint(source[:,:,3]))&(source[:,:,3]<=maximum[ix]);source_keys=np.stack([owner[:,:,0],source[:,:,3],uv[:,:,0],uv[:,:,1]],2);eligible=ordinary&enabled[ix];tri=np.clip(np.rint(source[:,:,3]).astype(int)-1,0,zinfo['triangles']-1);eligible&=~((roles==zinfo['role'])&(zero[tri]>0));used=key[:,:,0]>=100;assert not(used&actor).any();expectedRGB=before.copy();expectedReceipt=np.zeros_like(receipt);expectedReceipt[:,:,1]=-1;known=np.zeros(actor.shape,bool)
  for y,x in np.argwhere(ordinary&(roles==zinfo['role'])):
   expectedReceipt[y,x,2]=uv[y,x,2];region=region_at(mask,uv[y,x,:2],pinfo['wrap'])
   if region:k=round(float(uv[y,x,2])*(len(palette)-1));known[y,x]=True;expectedRGB[y,x,:3]=palette[k,:3];expectedReceipt[y,x]=[region,k,uv[y,x,2],1]
  assert np.array_equal(receipt,expectedReceipt),('palette receipt',f['frame']);assert np.array_equal(trace[:,:,2]==1,used);current_pose=pose(f['frame'],zinfo['triangles'])if f['poseSaved']else None;history_checked=0
  pnow=pold=oldorigin=None
  if current_pose is not None and previous is not None and previous_pose is not None:
   prev_f,prev_key=previous;oldorigin=np.array([prev_f['QROI'][0]+prev_f['join'][0],272-prev_f['QROI'][1]-h+prev_f['join'][1]]);pnow=current_pose[:,:,2:4].astype(float).copy();pold=previous_pose[:,:,2:4].astype(float).copy();pnow[:,:,0]+=-.5+f['join'][0];pnow[:,:,1]=272-pnow[:,:,1]-.5+f['join'][1];pold[:,:,0]+=-.5+prev_f['join'][0];pold[:,:,1]=272-pold[:,:,1]-.5+prev_f['join'][1]
  def history(yy,xx,y,x,key):
   if pnow is None:return False
   return preference(np.array([xx,yy])+origin,np.array([x,y])+origin,key,current_pose[:,:,:2],pnow,pold,previous[1],oldorigin,zinfo['role'])
  full_optimality=False
  if layers==13:
   scalar=parts[12];assert np.array_equal(scalar[:,:,3],owner[:,:,0]);radius=np.rint(scalar[:,:,1]).astype(int);assert np.array_equal(radius,np.floor(2*scalar[:,:,0]+np.float32(.5)).astype(int))and(radius>=0).all()and(radius<=2).all();eligible&=scalar[:,:,2]==1
   oracle,ow,om,ort=resolve(before,actor,eligible,owner[:,:,2],np.where(valid,world[:,:,0],0),meta[:,:,0],source_keys,inks[ix],radius,history_preference=history);oracle[known,:3]=palette[np.rint(uv[known,2]*(len(palette)-1)).astype(int),:3];core=np.zeros(actor.shape,bool);core[2:-2,2:-2]=True;assert np.array_equal(after[core],oracle[core]),('full selection RGB',f['frame']);assert np.array_equal(used[core],om[core]);wanted=ow[om].copy();wanted[:,0]+=100;assert np.array_equal(key[om],wanted)and np.array_equal(trace[:,:,1][core].astype(int),ort[core]);full_optimality=True
  for y,x in np.argwhere(used):
   role=int(key[y,x,0])-100;wanted=key[y,x].copy();wanted[0]=role;hit=(source_keys==wanted).all(2)&eligible;coords=np.argwhere(hit);accepted=[]
   for sy,sx in coords:
    ch=max(abs(int(sy)-int(y)),abs(int(sx)-int(x)));z=owner[sy,sx,2]
    if ch<1 or ch>trace[y,x,1]or trace[y,x,1]!=np.floor(np.float32(2)*trace[y,x,0]+np.float32(.5))or trace[y,x,0]<0 or trace[y,x,0]>1:continue
    if world[y,x,0]<=0 or z>np.float32(world[y,x,0]+np.float32(.0001))or(meta[y,x,0]>0 and z>np.float32(meta[y,x,0]+np.float32(.0001))):continue
    accepted.append((int(sy),int(sx)))
   # The outer2 rows are an observation border. Source queries use the full
   # current grids, so an exterior source can legitimately be outside this file.
   core=2<=y<h-2 and 2<=x<w-2
   if core:assert accepted,('owner/current source admission',f['frame'],x,y,key[y,x].tolist())
   expectedRGB[y,x]=[*inks[role],1]
   if core and current_pose is not None and(previous is None or previous_pose is not None):
    desired=False
    if previous is not None:
     sy,sx=accepted[0];desired=history(sy,sx,y,x,tuple(wanted))
    assert bool(trace[y,x,3]==1)==desired,('history',f['frame'],x,y,trace[y,x].tolist(),desired);history_checked+=1
  assert np.array_equal(after,expectedRGB),('RGB input contracts',f['frame']);assert not(used&known).any();hist=int((trace[:,:,3]==1).sum());hist_total+=hist;cpu_history_frames+=current_pose is not None and(previous is None or previous_pose is not None);results.append({'ordinal':fi,'frame':f['frame'],'sourceId':f['sourceId'],'outlinePixels':int(used.sum()),'LUTPixels':int(known.sum()),'historyMatchedWinnerPixels':hist,'historyWinnerCPUChecks':history_checked,'RGBAndCurrentOwnerAdmissionExact':True,'fullOptimalityRecomputed':full_optimality});previous=(f,key.copy());previous_pose=current_pose
  if fi%max(1,len(frames)//180)==0:film.append(srgb(after).resize((w*6,h*6),Image.Resampling.NEAREST))
  if fi in set(np.linspace(0,len(frames)-1,8).astype(int)):selected.append((f,srgb(before),srgb(after)))
  if fi and fi%20==0:print(json.dumps({'reviewed':fi,'total':len(frames)}),flush=True)
 board=Image.new('RGB',(900,len(selected)*230+40),(27,29,35));draw=ImageDraw.Draw(board)
 for i,(f,b,a)in enumerate(selected):
  for j,(im,title)in enumerate([(b,'Actual native'),(a,'Actual private width/history + partial LUT')]):draw.text((j*450+8,i*230+8),f"F{f['frame']} {title}",fill='white');board.paste(im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST),(j*450+8,i*230+32));board.paste(im.resize((im.width*5,im.height*5),Image.Resampling.NEAREST),(j*450+100,i*230+32))
 draw.text((8,len(selected)*230+8),'Actual frames. Partial LUT art remains rejected; owner history is not whole-shape stability.',fill='white');board.save(G/'ACTUAL_STREAM77.png')
 if film:film[0].save(G/'ACTUAL_STREAM77.webp',save_all=True,append_images=film[1:],duration=100,loop=0,lossless=True)
 result={'actualFrames':len(frames),'actualConsecutive':True,'simulatedSeconds':sum(f['deltaTime']for f in frames),'poolSlots':6,'peakPending':s['peakPending'],'maxEncodedFrameBytes':stored_max,'totalStoredFrameBytes':file_total,'allCurrentRGBAndOwnerAndPaletteChecksPass':True,'poseHistoryCPUChecked':cpu_history_frames==len(frames),'historyPoseCheckedFrames':int(cpu_history_frames),'matchedHistoryWinnerPixels':hist_total,'fullOptimalityRecomputed':all(f['fullOptimalityRecomputed']for f in results),'outerTwoCellObservationBorderExcludedFromOwnerOracle':True,'restorationChecksPass':report['restorationChecksPass'],'resourcesReleased':report['ownedResourcesReleased'],'product77Changed':False,'fullFaceRegionsAndArtAdopted':False,'rows':results};(G/'ACTUAL_STREAM77.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items()if k!='rows'}))
if __name__=='__main__':main()
