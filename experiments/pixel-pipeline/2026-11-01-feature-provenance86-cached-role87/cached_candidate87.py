from pathlib import Path
import json,hashlib,sys,numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OUT=HERE/'candidate87';OUT.mkdir(exist_ok=False)
REPO=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');SOURCE=REPO/'Assets/EUnityValidation01/GameMapIntegration333/Shaders/EyeCompose333.compute';text=SOURCE.read_text(encoding='utf-8-sig')
old='float4 template262(float2 p,int eye){if((eye==0?_Visible262_0:_Visible262_1)==0)return 0;float2 q=local262(p,eye);if(!inside295(q,eye,false))return 0;return float4(inside295(q,eye,true)?1:4,eye==0?2:1,0,0);}'
new='''// Source pixels define the authored feature; continuous contours are its authoring input.
// The already-bound role cache is also used by ownColour295, so shape and colour
// now refer to the same source texel/owner. Actual depth/alpha gates below remain.
float4 template262(float2 p,int eye){
 if((eye==0?_Visible262_0:_Visible262_1)==0)return 0;
 float2 q=local262(p,eye);int2 k=(int2)floor(q);
 if(any(k<0)||any(k>=_TemplateSize))return 0;
 float4 source=_TemplateRole.Load(int3(k.x,_TemplateSize.y-1-k.y,0));
 int owner=eye==0?2:1;int role=(int)round(source.x);
 if(round(source.y)!=owner||(role!=1&&role!=4))return 0;
 return float4(role,owner,0,0);
}'''
assert text.count(old)==1;candidate=text.replace(old,new);(OUT/'CachedSourceRole87.compute').write_bytes(candidate.encode());(OUT/'EyeCompose333.before87.compute').write_bytes(SOURCE.read_bytes())
bundle=json.loads((ROOT/'lid-evidence51/KEYFORM_BUNDLE51.json').read_text());bank={(int(c['referenceXY'][0]),int(c['referenceXY'][1])):(int(c['role']),int(c['eye']))for c in bundle['cells']}
def lookup(q,owner,bank,size=(480,272)):
 x,y=np.floor(q).astype(int)
 if x<0 or y<0 or x>=size[0]or y>=size[1]:return 0
 role,sid=bank.get((int(x),int(y)),(0,0));return role if sid==owner and role in [1,4]else 0
tests=[]
for name,b,size in [('authored20',bank,(480,272)),('different-L', {(0,0):(1,2),(0,1):(1,2),(1,1):(4,2)},(3,2)),('other-owner',{(1,1):(4,1),(2,1):(1,1),(3,2):(1,1),(4,2):(4,2)},(5,4))]:
 expected={(x,y,r,o)for(x,y),(r,o)in b.items()};got=set()
 for y in range(size[1]):
  for x in range(size[0]):
   for owner in [1,2]:
    role=lookup([x+.5,y+.5],owner,b,size)
    if role:got.add((x,y,role,owner))
 assert got==expected;assert lookup([-1,.5],1,b,size)==lookup([size[0]+.5,.5],2,b,size)==0
 tests.append({'case':name,'exactSourceCellRoleOwner':True,'sourceCount':len(expected)})
# Re-use captured inverse mappings; this is membership only, not a fabricated
# RGB/occlusion result. Existing source native/skin/hair gates are tested on GPU.
sys.path.insert(0,str(ROOT/'input-event83'));from validate_motion85 import packet
state=json.loads(sorted((ROOT/'input-event83/motion85').glob('STATE85*'))[-1].read_text());rows=[]
for entry in state['sequencePackets']:
 d=packet(Path(entry['output']));x,y,w,h=d['roi'];eyes=[]
 for ei,centre in enumerate(d['manifest']['eyeFeature']['centres']):
  sid=int(centre[3]);matrix=np.array(d['manifest']['eyeFeature']['inverse'][ei],np.float32).reshape(4,4,order='F');cells=[]
  for yy in range(h):
   for xx in range(w):
    p=matrix@np.array([x+xx+.5,271-y-yy+.5,1,0],np.float32);q=p[:2]/p[2];role=lookup(q,sid,bank)
    if role==1:cells.append([x+xx,271-y-yy])
  eyes.append({'eye':sid,'unoccludedCachedIrisCells':cells,'count':len(cells)})
 rows.append({'frame':entry['frame'],'stage':entry['testStage82'],'eyes':eyes})
result={'status':'OFFLINE_SOURCE_MEMBERSHIP_ONLY_NOT_APPLIED','sourcePath':str(SOURCE),'sourceSHA':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'candidateSHA':hashlib.sha256((OUT/'CachedSourceRole87.compute').read_bytes()).hexdigest(),'change':'Use existing TemplateRole cache for feature membership instead of re-rasterizing continuous contours at every screen centre; same texel provides pigment. No offset/min-size/colour correction.','sourceTests':tests,'actualSavedInverseMembership':rows,'remaining':['Actual native/skin/hair occlusion and final348 blend must be tested before adoption.','Nearest transformed source image can still alias under large rotation/scale; no universal phase/shape guarantee.','Only existing open key-form is available; native blink regression is required, no unregistered closed template invented.']};(OUT/'CANDIDATE87.json').write_bytes((json.dumps(result,indent=2)+'\n').encode());print(json.dumps({'tests':tests,'frame118_119':[r for r in rows if r['frame']in [118,119]],'candidateSHA':result['candidateSHA']},indent=2))
