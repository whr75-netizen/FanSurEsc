"""Read-only current eye-path audit + isolated source-membership/cache prototype.
No Unity calls and no candidate final RGB is painted over the saved character.
"""
from pathlib import Path
import json,gzip,struct,re,hashlib,math,datetime
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parent;ROOT=R.parent.parent;O=R/'eye-cache42';O.mkdir(exist_ok=True)
PROJECT=Path('C:/Users/15352/Documents/work/Fantasy Survival Escape Game/Assets/EUnityValidation01')
load=lambda p:json.loads(p.read_text(encoding='utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def buffers(path):
 out={}
 with gzip.open(path,'rb')as f:
  def i():return struct.unpack('<i',f.read(4))[0]
  for _ in range(i()):
   key=f.read(i()).decode();w,h=i(),i();out[key]=np.frombuffer(f.read(w*h*16),'<f4').reshape(h,w,4)[::-1].copy()
 return out

def png(a):
 c=np.maximum(a[...,:3],0);c=np.where(c<=.0031308,12.92*c,1.055*c**(1/2.4)-.055);return Image.fromarray(np.rint(np.clip(np.concatenate([c,a[...,3:]],-1),0,1)*255).astype(np.uint8))

def xy(v):return np.array([v['x'],v['y']])
def vec(v,dtype=np.float32):return np.array([v['x'],v['y'],v['z']],dtype=dtype)

def classify(rest,params,eye,dtype=np.float32):
 rest=np.asarray(rest,dtype=dtype);d=rest-vec(params['centres'][eye],dtype);u=d@vec(params['axesX'][eye],dtype)/dtype(params['axesX'][eye]['w']);v=-(d@vec(params['axesY'][eye],dtype))/dtype(params['axesY'][eye]['w']);s=params['style'];up=dtype(s['upper']['x'])+dtype(s['upper']['y'])*u*u;lo=dtype(s['lower']['x'])+dtype(s['lower']['y'])*u*u
 ap=(np.abs(u)<=1.02)&(v>=up)&(v<=lo);lash=(np.abs(u)<=1.08)&(v>=up-.36)&(v<=up+.22);lid=(np.abs(u)<=.90)&(v>lo)&(v<=lo+.35);iris=ap&~lash&((np.abs(u)/s['irisRadii']['x'])**s['irisPower']+(np.abs(v+s['irisOffset'])/s['irisRadii']['y'])**s['irisPower']<=1)
 feat=np.where(lid,6,0);feat=np.where(ap&~iris&~lash,1,feat);feat=np.where(iris,np.where(v<.08,2,3),feat);catch=iris&(u>=s['catchU']['x'])&(u<=s['catchU']['y'])&(v>=s['catchV']['x'])&(v<=s['catchV']['y']);feat=np.where(catch,4,feat);return np.where(lash,5,feat),u,v

def iris_allocated(counts,competitors,uv):
 """Exact area/rank core of IrisAllocated19/BeforeIris19, CPU fixture only."""
 counts=np.asarray(counts,float);keys=[(float(competitors[i]-counts[i]),uv[i][0],uv[i][1],i)for i in range(len(counts))if counts[i]>0];budget=math.floor(float(counts.sum()/16)+.5);return sorted(k[-1]for k in sorted(keys)[:budget]),budget

def cache_key(topology,role_hash,rgba_hash,style_hash):
 return hashlib.sha256(json.dumps([topology,role_hash,rgba_hash,style_hash],separators=(',',':')).encode()).hexdigest()

class SourceFeatureCache42:
 """Isolated cache contract, not an eye rasterizer or final RGB renderer."""
 def __init__(self,key,template):self.key=key;self.canonical=json.loads(json.dumps(template))
 def check_binding(self,key):
  if key!=self.key:raise ValueError('Source/style changed; rebuild source feature adapter before reuse')
 def membership(self,key,eye,sourceRole,valid,normalizedSubtype,visible):
  self.check_binding(key)
  family={1:'iris',4:'sclera',6:'upperLine'}.get(sourceRole)
  if family is None:raise ValueError('Unbound source family; no colour/shape fallback')
  if str(eye)not in self.canonical:raise ValueError('Unknown source eye ID')
  # normalizedSubtype is retained as an attribute. It cannot rename the cached
  # source iris into sclera/skin merely because the normalized curve says so.
  return {'featureId':f'eye{eye}:{family}','intrinsicMask':np.asarray(valid,bool).copy(),'visibleMask':np.asarray(valid,bool)&np.asarray(visible,bool),'normalizedSubtype':np.asarray(normalizedSubtype).copy(),'canonicalCells':self.canonical[str(eye)].get(family,{}).get('cellIds',[])}

checks=[]
def check(name,ok):
 checks.append({'name':name,'pass':bool(ok)})
 if not ok:raise AssertionError(name)

def main():
 rolePath=PROJECT/'SocketTemplate216/Inputs/TemplateRole.asset';rgbaPath=PROJECT/'SocketTemplate216/Inputs/TemplateRGBA.asset'
 text=rolePath.read_text(encoding='utf8');role=np.frombuffer(bytes.fromhex(re.search(r'_typelessdata: ([0-9a-fA-F]+)',text).group(1)),'<f4').reshape(272,480,4)[::-1].copy()
 template={}
 for eye in [1,2]:
  feature={}
  for r,label in [(1,'iris'),(4,'sclera')]:
   yy,xx=np.where((np.rint(role[...,0])==r)&(np.rint(role[...,1])==eye));cells=[[int(x),int(y)]for y,x in zip(yy,xx)];feature[label]={'role':r,'cellIds':[f'eye{eye}:role{r}:template:{x},{y}'for x,y in cells],'referenceCells':cells,'adjacency4':[[i,j]for i,(x,y)in enumerate(cells)for j,(u,v)in enumerate(cells)if i<j and abs(x-u)+abs(y-v)==1]}
  template[str(eye)]=feature
 check('saved Template216 has four iris cells each, not a two-cell specification',all(len(x['iris']['cellIds'])==4 for x in template.values()))
 check('saved TemplateRole has no upper-eyeline role6',not np.any(np.rint(role[...,0])==6))
 (O/'TEMPLATE_FEATURE_GRAPH.json').write_text(json.dumps({'roleSHA256':sha(rolePath),'RGBASHA256':sha(rgbaPath),'referenceSize':[480,272],'referencePoseNotAllAngleMinimum':True,'sourceUVBindingComplete':False,'features':template,'scope':'Existing reference cell IDs/adjacency only. Do not stamp these four cells at every pose. Original mesh/UV colour-mask binding is not present in this asset.'},indent=2))
 prefab=PROJECT/'OriginalIntegration399/Export/ValidatedPresentation399.prefab';declaredTopology=re.search(r'modelTopologySHA256: ([0-9a-f]+)',prefab.read_text(encoding='utf8')).group(1);referenceStyle=load(ROOT/'final-validation/neutral/params.json')['style'];styleHash=hashlib.sha256(json.dumps(referenceStyle,sort_keys=True).encode()).hexdigest()
 key=cache_key(declaredTopology,sha(rolePath),sha(rgbaPath),styleHash);cache=SourceFeatureCache42(key,template);prototypeChecks=[]
 (O/'CACHE_BINDING.json').write_text(json.dumps({'candidateKey':key,'declaredPrefabTopologySHA256':declaredTopology,'topologyNotRevalidatedInLiveUnity':True,'referenceStyleSHA256':styleHash,'templateRoleSHA256':sha(rolePath),'templateRGBASHA256':sha(rgbaPath),'sourceColourRangeToUVMaskComplete':False,'fingerprintScope':'Source cache prototype based on existing declared adapter/reference assets; not a new live model binding.'},indent=2))
 files=[PROJECT/'EyeBoundaryRestore348/Shaders/EyeFeature348.compute',PROJECT/'EyeBoundaryRestore348/Runtime/EyeFeature348.cs',PROJECT/'EyeBoundaryRestore348/Runtime/EyeBoundaryBinding348.cs',PROJECT/'HeadLocal367/Runtime/EyeRenderer367.cs',PROJECT/'HeadLocal367/Runtime/HeadLocal367.cs',PROJECT/'GameMapIntegration333/Shaders/EyeCompose333.compute',PROJECT/'GameMapIntegration333/Shaders/EyeMerge333.compute',PROJECT/'HeadLocal367/Shaders/GridJoin367.compute',PROJECT/'EyeBoundaryRestore348/Shaders/EyeSurface348.shader',rolePath,rgbaPath];inputHashes={str(p):sha(p)for p in files}
 frames=[];discarded=[];colours={1:np.array([225,80,95]),2:np.array([90,200,150])}
 for name in ['neutral','walk-00','walk-01','walk-02','walk-03']:
  folder=ROOT/'final-validation'/name;params=load(folder/'params.json');b=buffers(folder/'buffers.gz');m=b['S2META'];point=b['S2POINT'];rgba=b['S2RGBA'];perEye=[];maskBefore=np.zeros((*m.shape[:2],4),np.uint8);maskAfter=maskBefore.copy();rawMask=maskBefore.copy()
  for eye in range(2):
   stable=int(params['centres'][eye]['w']);valid=(m[...,0]>0)&(m[...,1]>.5)&(m[...,3]>1e-6)&(np.rint(m[...,2])==stable)&(point[...,3]>.5);f,u,v=classify(point[...,:3],params,eye);f64,_,_=classify(point[...,:3],params,eye,np.float64);keep=valid&(f>=2)&(f<=4);lost=valid&~keep;weights=np.clip(m[...,3],0,1);rawArea=float(np.sum(weights[valid])/16);keptArea=float(np.sum(weights[keep])/16)
   # Isolated candidate: original source layer membership decides iris identity;
   # the normalized curve may choose its subtype, never erase that identity.
   packet=cache.membership(key,stable,1,valid,f,valid);candidate=packet['intrinsicMask'];prototypeChecks.append(np.array_equal(candidate,valid)and packet['featureId']==f'eye{stable}:iris'and len(packet['canonicalCells'])==4)
   rawMask[valid]=[*colours[stable],255];maskBefore[keep]=[*colours[stable],255];maskBefore[lost]=[205,75,40,255];maskAfter[candidate]=[*colours[stable],255]
   for yy,xx in np.argwhere(lost):
    sourceUV=b['S2UV'][yy,xx];discarded.append({'pose':name,'eyeId':stable,'sampleXY':[int(xx),int(yy)],'projectedLogicalTopXY':[params['roi']['x']+(float(xx)+.5)/4,params['roi']['y']+(float(yy)+.5)/4],'sourceUV':sourceUV[:2].tolist(),'sourcePrimitiveId':int(round(float(sourceUV[2])))-1,'sourceLayer':'S2 original iris submesh1','restHeadXYZ':point[yy,xx,:3].tolist(),'normalizedFeature':int(f[yy,xx]),'normalizedUV':[float(u[yy,xx]),float(v[yy,xx])],'sourceSurfaceRGBA':rgba[yy,xx].tolist(),'alphaWeight':float(weights[yy,xx]),'occlusionNotYetApplied':True})
   sourceCounts={str(int(q)):int(np.sum(valid&(f==q)))for q in np.unique(f[valid])};visible=b['eye-visible'];own=np.rint(visible[...,1])==stable;iris=own&np.isin(np.rint(visible[...,0]),[2,3,4]);yy,xx=np.where(iris)
   cluster=[[int(x)+params['roi']['x'],int(y)+params['roi']['y']]for y,x in zip(yy,xx)]
   perEye.append({'stableEyeId':stable,'rawIntrinsicS2Samples':int(valid.sum()),'classifiedIrisSamples':int(keep.sum()),'normalizedReclassifiedSamples':int(lost.sum()),'float32Vs64ClassificationDifferencesOnS2':int(np.sum(valid&(f!=f64))),'rawIntrinsicAreaCells':rawArea,'afterNormalizedIrisAreaCells':keptArea,'S2ClassificationDistribution':sourceCounts,'storedFinalIrisCells':cluster,'storedUpperCells':int(np.sum(own&np.isin(np.rint(visible[...,0]),[5,7]))),'prototypeCacheId':packet['featureId'],'prototypeCanonicalReferenceCellIds':packet['canonicalCells'],'occlusionCompleteForReplay':False,'warning':'These S2 numbers precede skin/hair/body depth occlusion; missing S0/S4/S5/S6 prevents full selector/GPU replay. Prototype is intrinsic feature membership, not final-eye rendering.'})
  for tag,image in [('raw-source-iris',rawMask),('normalized-gate',maskBefore),('cached-membership-prototype',maskAfter)]:Image.fromarray(image).resize((image.shape[1]*5,image.shape[0]*5),Image.Resampling.NEAREST).save(O/(name+'-'+tag+'.png'))
  # Actual saved final crop, RGBA preserved, original display pixel size.
  roi=params['roi'];off=params['offset'];origin=params['origin'];x=int(origin['x']+2*(roi['x']+off['x']));y=int(origin['y']+2*(roi['y']-off['y']));im=Image.open(folder/'final.png').convert('RGBA').crop((x,y,x+roi['width']*2,y+roi['height']*2));im.save(O/(name+'-saved-final-1x.png'));im.resize((im.width*12,im.height*12),Image.Resampling.NEAREST).save(O/(name+'-saved-final-12x.png'))
  png(b['head-colour']).resize((b['head-colour'].shape[1]*16,b['head-colour'].shape[0]*16),Image.Resampling.NEAREST).save(O/(name+'-saved-head-16x.png'))
  frames.append({'name':name,'sourcePhase':params['source'],'viewAngle':params['angle'],'iris582':params['iris582'],'lash583':params['lash583'],'style':params['style'],'eyes':perEye,'buffersSHA256':sha(folder/'buffers.gz'),'paramsSHA256':sha(folder/'params.json'),'sourceFacesSHA256':sha(folder/'source-face.bin')})
 check('prototype retains native source identity and reference-cell graph across ten stored eye inputs',all(prototypeChecks)and len(prototypeChecks)==10)
 # Demonstrate the exact rank/round rules without introducing a new design size.
 uv=[[-.5,-.5],[.5,-.5],[-.5,.5],[.5,.5]];cases=[]
 for counts in [[9,7,7,0],[9,8,8,0],[16,12,11,0],[16,12,13,0],[14,2,2,14]]:
  selected,budget=iris_allocated(counts,np.zeros(4),uv);cases.append({'subSampleCounts':counts,'areaCells':sum(counts)/16,'budget':budget,'selected2x2Cells':[[i%2,i//2]for i in selected]})
 check('synthetic same feature ID can switch one to two by area threshold',cases[0]['budget']==1 and cases[1]['budget']==2)
 check('synthetic two sub-samples can switch two to three',cases[2]['budget']==2 and cases[3]['budget']==3)
 check('synthetic selector permits disconnected diagonal iris cluster',cases[4]['selected2x2Cells']==[[0,0],[1,1]])
 rejected=0
 for changed in [('other',sha(rolePath),sha(rgbaPath),styleHash),(declaredTopology,'other',sha(rgbaPath),styleHash),(declaredTopology,sha(rolePath),'other',styleHash),(declaredTopology,sha(rolePath),sha(rgbaPath),'other')]:
  try:cache.check_binding(cache_key(*changed))
  except ValueError:rejected+=1
 check('candidate cache invalidates actual reuse on source role/colour/style/model change',rejected==4)
 hidden=cache.membership(key,2,1,np.ones(3,bool),np.array([0,1,5]),np.zeros(3,bool));check('hidden source iris keeps identity but yields no visible samples and preserves canonical graph',hidden['featureId']=='eye2:iris'and hidden['intrinsicMask'].sum()==3 and hidden['visibleMask'].sum()==0 and len(hidden['canonicalCells'])==4)
 rejected=False
 try:cache.membership(key,2,11,np.ones(1,bool),np.ones(1),np.ones(1,bool))
 except ValueError:rejected=True
 check('hair role cannot silently become iris palette family',rejected)
 check('all inspected product/template hashes unchanged',all(sha(Path(p))==h for p,h in inputHashes.items()))
 (O/'STORED_FRAME_EVIDENCE.json').write_text(json.dumps(frames,indent=2));(O/'DISCARDED_SOURCE_SAMPLES.json').write_text(json.dumps(discarded,indent=2));(O/'SYNTHETIC_SELECTOR_COUNTEREXAMPLES.json').write_text(json.dumps(cases,indent=2));(O/'VERIFIED.json').write_text(json.dumps({'passed':len(checks),'checks':checks,'productInputSHA256':inputHashes,'newUnityCalls':0,'actualFramesRecaptured':0,'syntheticOrOfflineOnly':True,'newFinalEyeImageRendered':False},indent=2))
 print(json.dumps({'checks':len(checks),'frames':[{'name':q['name'],'eyes':[{'id':e['stableEyeId'],'nativeSamples':e['rawIntrinsicS2Samples'],'afterClassify':e['classifiedIrisSamples'],'storedIrisCells':len(e['storedFinalIrisCells']),'upper':e['storedUpperCells']}for e in q['eyes']]}for q in frames],'noProductChange':True}))

if __name__=='__main__':main()
