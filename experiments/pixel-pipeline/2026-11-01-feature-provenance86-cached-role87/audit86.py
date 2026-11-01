from pathlib import Path
import sys,json,hashlib,re,numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OUT=HERE/'offline';OUT.mkdir(exist_ok=False)
sys.path.insert(0,str(ROOT/'input-event83'));from validate_motion85 import packet,rgb8
bundle=json.loads((ROOT/'lid-evidence51/KEYFORM_BUNDLE51.json').read_text());prefab=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game/Assets/EUnityValidation01/OriginalIntegration399/Export/ValidatedPresentation399.prefab');assert bundle['referenceContourSHA256']in prefab.read_text(encoding='utf-8-sig')
forms={int(x['eye']):x for x in bundle['eyes']}
def inside(p,poly):
 p=np.asarray(p,np.float32);poly=np.asarray(poly,np.float32);yes=False
 for a,b in zip(poly,np.roll(poly,1,axis=0)):
  if (a[1]>p[1])!=(b[1]>p[1]) and p[0]<np.float32((b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0]):yes=not yes
 return yes
def local(p,inverse):
 m=np.asarray(inverse,np.float32).reshape(4,4,order='F');q=m@np.array([p[0],p[1],1,0],np.float32);return q[:2]/q[2]
def classify(q,form):return 0 if not inside(q,form['parent'])else 1 if inside(q,form['iris'])else 4
def distance(p,poly):
 p=np.asarray(p,float);poly=np.asarray(poly,float);best=1e30
 for a,b in zip(poly,np.roll(poly,1,axis=0)):
  t=np.clip(np.dot(p-a,b-a)/np.dot(b-a,b-a),0,1);best=min(best,np.linalg.norm(p-(a+t*(b-a))))
 return float(best)
sourceChecks=[]
expected={(int(c['referenceXY'][0]),int(c['referenceXY'][1]),int(c['eye']),int(c['role']))for c in bundle['cells']}
for sample in [[.75,.25],[.5,.5]]:
 got=set()
 for sid,f in forms.items():
  allp=np.asarray(f['parent']);lo=np.floor(allp.min(0)).astype(int)-1;hi=np.ceil(allp.max(0)).astype(int)+1
  for y in range(lo[1],hi[1]):
   for x in range(lo[0],hi[0]):
    role=classify([x+sample[0],y+sample[1]],f)
    if role:got.add((x,y,sid,role))
 sourceChecks.append({'sample':sample,'cells':len(got),'exactTemplateCellSet':got==expected,'missing':sorted(expected-got),'extra':sorted(got-expected)})
st=json.loads(sorted((ROOT/'input-event83/motion85').glob('STATE85*'))[-1].read_text());entries=st['sequencePackets'];frames={};membership=[]
for entry in entries:
 d=packet(Path(entry['output']));frames[entry['frame']]=d;x,y,w,h=d['roi'];e=d['manifest']['eyeFeature'];row=[]
 for ei,centre in enumerate(e['centres']):
  sid=int(centre[3]);f=forms[sid];pred=[];actual=[];early=[]
  for yy in range(h):
   for xx in range(w):
    p=[xx+x+.5,271-(yy+y)+.5];role=classify(local(p,e['inverse'][ei]),f)
    old=d['arrays']['old-eye-owner'][yy,xx];intr=d['arrays']['old-intrinsic'][yy,xx]
    if role==1:pred.append([int(xx+x),int(271-yy-y)])
    if round(float(intr[0]))==1 and round(float(intr[1]))==sid:actual.append([int(xx+x),int(271-yy-y)])
    if role==1 and round(float(old[0]))==7 and round(float(old[1]))==sid:early.append([int(xx+x),int(271-yy-y)])
  row.append({'eye':sid,'cpuUnoccludedIris':pred,'gpuIntrinsicIris':actual,'nativeEarlyReturnIrisCells':early,'unexplainedIntrinsicDifference':sorted(set(map(tuple,pred))-set(map(tuple,actual))-set(map(tuple,early)))})
 membership.append({'frame':entry['frame'],'eyes':row})
events=[]
for px,py in [(222,52),(223,52),(222,53),(223,53)]:
 row={'xyTopLeft':[px,py],'frames':[]}
 for frame in [118,119]:
  d=frames[frame];e=d['manifest']['eyeFeature'];ei=next(i for i,v in enumerate(e['centres'])if int(v[3])==1);q=local([px+.5,py+.5],e['inverse'][ei]);f=forms[1];x,y,w,h=d['roi'];xx,yy=px-x,271-py-y;rx,ry,rw,rh=d['eyeROI'];cx,cy=px-rx,271-py-ry;r=d['records'][cy,cx];native=d['arrays']['S3-meta'][cy*4:cy*4+4,cx*4:cx*4+4];iris=d['arrays']['S2-meta'][cy*4:cy*4+4,cx*4:cx*4+4]
  row['frames'].append({'frame':frame,'phaseIndex':d['manifest']['modeFlags']['phaseIndex'],'referencePoint':q.tolist(),'contourRoleAtCentre':classify(q,f),'distanceToIrisContourReferencePixels':distance(q,f['iris']),'oldEyeOwner':d['arrays']['old-eye-owner'][yy,xx].tolist(),'oldIntrinsic':d['arrays']['old-intrinsic'][yy,xx].tolist(),'oldEyeAudit':d['arrays']['old-eye-audit'][yy,xx].tolist(),'baselineOwner':d['baseline'][yy,xx,1].tolist(),'RGB8':rgb8(r[0,:3]).tolist(),'outputFeature':r[3].tolist(),'pigmentProvenance':r[7].tolist(),'sourceSurfaceUVPrimitive':r[6].tolist(),'sourceBarycentric':r[10].tolist(),'rawIrisCoverageAreaCell':float(np.where((iris[...,0]>0)&(np.rint(iris[...,2])==1),np.clip(iris[...,3],0,1),0).sum()/16),'rawNativeCoverageAreaCell':float(np.where((native[...,0]>0)&(np.rint(native[...,2])==1),np.clip(native[...,3],0,1),0).sum()/16),'baseMeta':d['arrays']['base-meta'][yy,xx].tolist(),'hairMeta':d['arrays']['hair-meta'][yy,xx].tolist(),'browMeta':d['arrays']['brow-meta'][yy,xx].tolist()})
 events.append(row)
colour=json.loads((ROOT/'input-event83/SOURCE_TRACE85.json').read_text())['phaseColourExamples'][0];lo=np.array(colour['before']['pre348RGBA'][:3]);hi=np.array(colour['after']['pre348RGBA'][:3]);ratio=(lo/hi).tolist();assert np.max(abs(lo-hi*np.float32(.72)))<1e-7
out={'source':'actual motion85; authored contour payload from prior source-keyform51 whose SHA matches current prefab, actual runtime pointer not separately captured85','referenceContourSHA':bundle['referenceContourSHA256'],'sourceTemplateRasterChecks':sourceChecks,'frameMembership':membership,'loss118To119':events,'colour':{'example':colour,'linearChannelRatios':ratio,'exactOldProfilePair':'.72 vs1','classificationSource':'Prepare333 currentLit=step(Profile.y,physical.x)*step(Profile.z,physical.y); RestoreStyle335 may replace with legacy class endpoint, runtime flags/physical inputs missing85','missingObservation':['main centre/native Raw+Physical+Original+UV/metadata, Map, legacy colour/lit/shade/class at corresponding3x3 ROI','actual shadeProfile and RestoreStyle modes','actual typed contours/reference sample and bank identity per sourceId']},'doNotConclude':['Two iris cells disappeared for different reasons: centre-contour relabel and source native-line priority; neither is caused by palette corruption.','No fixed-minimum-pixel or visibility bypass proposed.','RGB .72 ratio alone cannot decide physical lighting change vs unstable threshold/sample selection.','Original canonical sample mismatch is tested against actual authored raster; no offset is silently applied.']};(OUT/'AUDIT86.json').write_bytes((json.dumps(out,ensure_ascii=False,indent=2)+'\n').encode())
sheet=Image.new('RGB',(w*12*2,h*12+28),'#171d24');draw=ImageDraw.Draw(sheet)
for i,frame in enumerate([118,119]):
 d=frames[frame];im=Image.fromarray(np.flipud(rgb8(d['arrays']['head-final'][...,:3]))).resize((w*12,h*12),Image.Resampling.NEAREST);sheet.paste(im,(i*w*12,28));draw.text((i*w*12+4,6),'actual '+str(frame),fill='white')
 for px,py in [(222,52),(223,52)]:draw.rectangle((i*w*12+(px-x)*12,28+(py-(272-y-h))*12,i*w*12+(px-x+1)*12-1,28+(py-(272-y-h)+1)*12-1),outline='#ff4488',width=1)
sheet.save(OUT/'iris-loss-118-119-nearest12.png')
print(json.dumps({'sourceRaster':sourceChecks,'loss':[(v['xyTopLeft'],[(z['frame'],z['referencePoint'],z['contourRoleAtCentre'],z['oldEyeOwner'][0])for z in v['frames']])for v in events],'ratio':ratio,'unexplainedCount':sum(len(e['unexplainedIntrinsicDifference'])for r in membership for e in r['eyes'])},ensure_ascii=False,indent=2))
