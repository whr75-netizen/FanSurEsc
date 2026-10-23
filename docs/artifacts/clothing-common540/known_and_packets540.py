from pathlib import Path
import json,struct,math
import numpy as np
O=Path(__file__).resolve().parent;R=O/'FullLoop540'
def mask(frame,part):
 raw=(R/f'{frame:03d}_CLOTH_PART{part}.bin').read_bytes();x,y,w,h=struct.unpack_from('<4i',raw);o=np.zeros((272,480),bool);o[y:y+h,x:x+w]=np.frombuffer(raw,'?',w*h,16+4*w*h).reshape(h,w);return o
tests={'frame43SpurCellsRemoved':not bool(mask(43,3)[98,200]or mask(43,3)[99,200]),'frame44NormalCellRetained':bool(mask(44,3)[78,231]),'frame34OriginalSleeveCellRemoved':not bool(mask(34,3)[85,198]),'frame50LeftBoundary':{str(y):next((x for x in range(196,208)if mask(50,3)[y,x]),None)for y in range(95,104)}}
packets=[];fail=[]
for path in sorted(R.glob('*_CLOTH_packets.json')):
 f=int(path.name[:3]);j=json.loads(path.read_text());values=j.get('values',[])
 for p in values:
  part=p['submesh'];xy=(p['x'],p['y']);v=p['barycentric'];total=v['x']+v['y']+v['z'];q=p['sourceProjection'];distance=math.hypot(q['x']-xy[0]-.5,q['y']-xy[1]-.5)
  checks={'activePart':part in[1,2,3],'selectedDestination':bool(mask(f,part)[xy[1],xy[0]]),'barycentric':abs(total-1)<2e-6 and min(v.values())>=0,'positiveDepth':p['depth']>0,'distanceConsistent':abs(distance-p['distance'])<2e-5,'finite':all(math.isfinite(n)for k in ['uv','world','sourceProjection','barycentric']for n in p[k].values())}
  packets.append({'frame':f,'submesh':part,'primitive':p['primitive'],'xy':xy,'checks':checks})
  if not all(checks.values()):fail.append(packets[-1])
facefiles=sorted(R.glob('*_OFF_FACE.txt'));facechanges=[]
for p in facefiles:
 other=p.with_name(p.name.replace('_OFF_','_CLOTH_'))
 if p.read_bytes()!=other.read_bytes():facechanges.append(int(p.name[:3]))
result={'known':tests,'packetsChecked':len(packets),'packetFailures':fail,'packetChecks':packets,'faceStateBytesChangedPoses':facechanges,'noPacketUploadIsNotEmptyMask':True,'notes':'Checks validate the recorded carrier tuple and selected destination; do not certify every unrecorded occlusion or global pixel-art quality. Actual geometry/UV support is constructed by the existing visible-triangle computation.'}
(O/'KNOWN_PACKETS540.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items()if k!='packetChecks'}))
