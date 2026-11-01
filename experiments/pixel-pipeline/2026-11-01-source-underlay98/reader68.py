"""One saved packet only. No Unity/API calls, inferred fill, palette change or history mixing."""
from pathlib import Path
import hashlib,json,math,struct
import numpy as np
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent
STATE=HERE/'retry-background/CAPTURE_STATE66.json'
class Reader:
 def __init__(self,path):self.path=path;self.f=path.open('rb')
 def i(self):return struct.unpack('<i',self.f.read(4))[0]
 def q(self):return struct.unpack('<q',self.f.read(8))[0]
 def s(self):
  n=0;shift=0
  while True:
   b=self.f.read(1)[0];n|=(b&127)<<shift
   if not b&128:break
   shift+=7;assert shift<35
  return self.f.read(n).decode('utf-8')
 def a(self,n,dtype='<f4'):return np.frombuffer(self.f.read(n*np.dtype(dtype).itemsize),dtype=dtype).copy()
 def mat(self):return self.a(16).reshape((4,4),order='F').astype(np.float64)
 def identity(self):return {'sourceId':self.s(),'viewId':self.s(),'frameIndex':self.i(),'renderSerial':self.i()}
 def end(self):assert self.f.read(1)==b'',self.path;self.f.close()
def plane(path):
 r=Reader(path);assert r.i()==0x34365052 and r.i()==1;h=r.identity()
 h.update(zip(['producer','channel','encoding','yConvention'],[r.s() for _ in range(4)]));h['size']=[r.i(),r.i()];h['roi']=[r.i() for _ in range(4)]
 a=r.a(h['roi'][2]*h['roi'][3]*4).reshape((h['roi'][3],h['roi'][2],4));r.end();return h,a
def camera(path):
 r=Reader(path);assert r.i()==0x34365043 and r.i()==1;h=r.identity();h['phase']=r.i();h['sourceFrame']=float(r.a(1)[0]);h['evaluatedFrame']=float(r.a(1)[0])
 for k in ['view','projection','effective','gpuProjection','gpuEffective']:h[k]=r.mat()
 for k in ['viewport','clipShift','nativeShift']:h[k]=r.a(4)
 h['logicalSize']=r.a(2,'<i4');h['nativeSize']=r.a(2,'<i4');h['convention']=r.s();h['sampler']=r.s();h['flags']=r.s();r.end();return h
def geometry(path):
 r=Reader(path);assert r.i()==0x34364353 and r.i()==1;identity=r.identity();meshes=[]
 for _ in range(r.i()):
  m={'index':r.i(),'guid':r.s(),'localId':r.q(),'matrix':r.mat()};n=r.i();m['vertices']=r.a(n*3).reshape((-1,3));m['normals']=r.a(n*3).reshape((-1,3));m['uv']=r.a(n*2).reshape((-1,2));m['submeshes']=[]
  for _ in range(r.i()):
   ix=r.a(r.i(),'<u4');assert len(ix)%3==0 and (len(ix)==0 or ix.max()<n)
   m['submeshes'].append({'indices':ix.reshape((-1,3)),'materialGUID':r.s(),'materialLocalId':r.q(),'st':r.a(4),'textureGUID':r.s(),'textureLocalId':r.q(),'factor':r.a(4)})
  m['bones']=[(r.s(),r.mat()) for _ in range(r.i())];m['sourceMatrix']=r.mat();m['bindposes']=[r.mat() for _ in range(r.i())];m['morphs']=[(r.s(),float(r.a(1)[0])) for _ in range(r.i())];meshes.append(m)
 r.end();return identity,meshes
def rgb8(linear):
 c=np.clip(linear,0,1);return np.rint(np.where(c<=.0031308,c*12.92,1.055*np.power(c,1/2.4)-.055)*255).astype(np.uint8)
def save_rgb(name,a):Image.fromarray(np.flipud(rgb8(a[...,:3]))).save(OUT/name)
def identity_check(h,state):
 assert h['sourceId']==state['sourceId'] and h['frameIndex']==state['frameIndex'] and h['renderSerial']==state['mainRenderedSerial335']
def main():
 global OUT
 state=json.loads(STATE.read_text(encoding='utf-8'));assert state['stage']=='finished' and state['PlayExited'] and not state.get('error') and state['frameUnchangedDuringReadback']
 packet=Path(state['output']);OUT=packet/'offline68';OUT.mkdir(exist_ok=True)
 planes={};headers={};fileHashes={}
 for e in state['planes']:
  path=packet/e['file'];h,a=plane(path);identity_check(h,state);assert h['viewId']==e['viewId'];assert h['roi']==e['roiBottomLeft'];assert np.isfinite(a).all(),path
  planes[path.stem]=a;headers[path.stem]=h;fileHashes[path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
 gi,meshes=geometry(packet/'evaluated-source.geometry');identity_check(gi,state);cam=camera(packet/'source.camera');identity_check(cam,state)
 final=np.zeros((544,960,4),np.float32);covered=np.zeros((544,960),bool)
 for name,a in planes.items():
  if name.startswith('final-strip-'):
   x,y,w,h=headers[name]['roi'];assert not covered[y:y+h,x:x+w].any();final[y:y+h,x:x+w]=a;covered[y:y+h,x:x+w]=True
 assert covered.all();save_rgb('final-960x544.png',final)
 raw=planes['unlit-source'];endpoint=planes['native-endpoint'];uv=planes['native-uv'];world=planes['world'];classes=planes['style-class'];hair=(endpoint[...,0]>0)&(endpoint[...,1]>=11.5)&(endpoint[...,1]<=15.5)
 save_rgb('source-unlit-roi.png',raw);save_rgb('source-current-roi.png',planes['source-final'])
 q=classes[...,0];g=classes[...,1];gvis=np.zeros_like(raw);gvis[...,:3]=np.clip(g,0,1)[...,None];gvis[...,3]=hair;save_rgb('g-debug-not-hair-colour.png',gvis)
 # Derive candidates from captured mesh index + submesh-local primitive and UV.
 # No material-name/role mapping: compare each actual submesh candidate to captured world position.
 mappings=[];failed=[];reprojection=[];worldErrors=[];ambiguous=[]
 bymesh={m['index']:m for m in meshes};P=cam['gpuProjection'].copy();P[0]+=float(cam['nativeShift'][0])*P[3];P[1]+=float(cam['nativeShift'][1])*P[3];VP=P@cam['view']
 ox,oy,ww,hh=headers['native-endpoint']['roi'];sourceDebug=np.zeros_like(raw)
 for y,x in np.argwhere(endpoint[...,0]>0):
  mi=int(round(float(uv[y,x,3])))-1;pi=int(round(float(uv[y,x,2])))-1;m=bymesh.get(mi);choices=[]
  if m is not None:
   for sm,part in enumerate(m['submeshes']):
    if pi<0 or pi>=len(part['indices']) or np.any(np.abs(part['st'][:2])<1e-12):continue
    ids=part['indices'][pi];triUV=m['uv'][ids].astype(np.float64);sampleUV=(uv[y,x,:2].astype(np.float64)-part['st'][2:])/part['st'][:2]
    A=np.stack([triUV[1]-triUV[0],triUV[2]-triUV[0]],axis=1)
    if abs(np.linalg.det(A))<1e-12:continue
    b=np.linalg.solve(A,sampleUV-triUV[0]);weights=np.array([1-b.sum(),b[0],b[1]])
    if weights.min()<-.002 or weights.max()>1.002:continue
    local=weights@m['vertices'][ids];wpos=(m['matrix']@np.r_[local,1])[:3];err=float(np.linalg.norm(wpos-world[y,x,:3]));choices.append((err,sm,weights,wpos))
  choices.sort(key=lambda c:c[0])
  if not choices or choices[0][0]>.0001:
   failed.append({'nativeXY':[int(x+ox),int(y+oy)],'mesh':mi,'primitive':pi,'candidateWorldErrors':[c[0] for c in choices]});continue
  err,sm,bary,wpos=choices[0]
  if len(choices)>1 and choices[1][0]<=.0001:ambiguous.append([int(x+ox),int(y+oy)]);continue
  clip=VP@np.r_[wpos,1];ndc=clip[:3]/clip[3];pred=np.array([(ndc[0]*.5+.5)*960,(.5-ndc[1]*.5)*544]);pixel=np.array([x+ox+.5,y+oy+.5]);pe=float(np.linalg.norm(pred-pixel));part=m['submeshes'][sm]
  mappings.append({'nativeXY':[int(x+ox),int(y+oy)],'mesh':mi,'submesh':sm,'primitive':pi,'barycentric':bary.tolist(),'materialGUID':part['materialGUID'],'textureGUID':part['textureGUID'],'sourceUV':uv[y,x,:2].astype(float).tolist(),'worldError':err,'reprojectionPixels':pe,'hair':bool(hair[y,x])});worldErrors.append(err);reprojection.append(pe)
  hue=(mi*7+sm+1)*.61803398875%1;import colorsys
  sourceDebug[y,x,:3]=colorsys.hsv_to_rgb(hue,.7,.9)
 save_rgb('material-provenance-debug.png',sourceDebug)
 eye=[]
 for part in range(13):
  rgba=planes[f'eye-{part}-rgba'];meta=planes[f'eye-{part}-meta'];puv=planes[f'eye-{part}-uv'];vis=(meta[...,0]>0)&(rgba[...,3]>0)
  eye.append({'part':part,'rgbaVisibleCells':int((rgba[...,3]>0).sum()),'metaDepthCells':int((meta[...,0]>0).sum()),'jointVisibleCells':int(vis.sum()),'sourceUVRange':None if not vis.any() else [puv[vis,:2].min(0).tolist(),puv[vis,:2].max(0).tolist()]})
  if part==10:save_rgb('eye-clean-backing-part10.png',rgba)
 stats=lambda xs:None if not xs else {'min':min(xs),'median':float(np.median(xs)),'max':max(xs)}
 report={'sourceId':state['sourceId'],'frameIndex':state['frameIndex'],'renderSerial':state['mainRenderedSerial335'],'planeCount':len(planes),'planeHeaderIdentityAndFinitePassed':True,'rawPacketBytes':sum(p.stat().st_size for p in packet.iterdir() if p.is_file()),'geometry':[{'mesh':m['index'],'vertices':len(m['vertices']),'submeshes':len(m['submeshes']),'triangles':sum(len(x['indices']) for x in m['submeshes']),'bones':len(m['bones']),'morphs':len(m['morphs'])} for m in meshes],'finalStripCoverage':int(covered.sum()),'nativeVisibleSamples':int((endpoint[...,0]>0).sum()),'hairNativeSamples':int(hair.sum()),'sourceMappingUnique':len(mappings),'sourceMappingUnresolved':len(failed),'sourceMappingAmbiguous':len(ambiguous),'worldErrorMetres':stats(worldErrors),'reprojectionPixels':stats(reprojection),'reprojectionConvention':'gpuProjection + nativeShift once; D3D SV_Position y=(1-ndcY)*height/2; data rows retained without implicit flip','hairGRange':None if not hair.any() else [float(g[hair].min()),float(g[hair].max())],'hairQValues':np.unique(q[hair]).astype(float).tolist(),'eyeLayers':eye,'imageEncoding':'Captured linear float RT -> standard sRGB8, clamped for PNG, no extra tonemap; PNG is a diagnostic readback preview, not a screen capture','missingOrUnverified':['UV source-feature boundary graph not yet projected/validated','Six historical backing destinations have not been surface-mapped into this new sourceId; current complete part10 is captured','EyeFeature/count/records buffers omitted by global FindObjectsByType observer lookup; direct host.headEyes lookup patch prepared but not executed','Partial continuous cell coverage not yet integrated from geometry','Only one pose/frame; no motion/blink/temporal validation','Palette/family/region IDs are not provided by this legacy product capture; no inferred IDs inserted'],'rawFileSHA256':fileHashes}
 (OUT/'INPUT_CHECK68.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(OUT/'SURFACE_BINDINGS68.json').write_text(json.dumps({'sourceId':state['sourceId'],'mapped':mappings,'unresolved':failed,'ambiguous':ambiguous},ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
 # Integer enlargement only, after conversion; source/final diagnostic images remain separate.
 base=Image.open(OUT/'final-960x544.png');base.resize((1920,1088),Image.Resampling.NEAREST).save(OUT/'final-nearest2.png')
 for n in ['source-unlit-roi','source-current-roi','material-provenance-debug','eye-clean-backing-part10']:
  a=Image.open(OUT/(n+'.png'));a.resize((a.width*4,a.height*4),Image.Resampling.NEAREST).save(OUT/(n+'-nearest4.png'))
 (OUT/'INDEX.html').write_text('<!doctype html><meta charset="utf-8"><title>68 실제 입력 검증</title><style>body{background:#26262b;color:#eee;font:16px sans-serif}img{image-rendering:pixelated;max-width:100%}section{display:flex;gap:20px;flex-wrap:wrap}figure{margin:10px}a{color:#9cf}</style><h1>단일 실제 프레임 입력 검증</h1><p>'+state['sourceId']+' / frame '+str(state['frameIndex'])+' / 원본 제품 경로. 보정 후보 적용 결과가 아닙니다.</p><p>linear RT → sRGB8 진단 PNG입니다. g/debug의 흰색은 머리색이 아닙니다. 새 palette·영역·눈 보정은 적용하지 않았습니다.</p><a href="INPUT_CHECK68.json">입력 검사와 한계</a><section>'+''.join('<figure><figcaption>'+n+'</figcaption><img src="'+n+'.png"></figure>' for n in ['final-960x544','source-unlit-roi-nearest4','source-current-roi-nearest4','material-provenance-debug-nearest4','eye-clean-backing-part10-nearest4'])+'</section>',encoding='utf-8')
 print(json.dumps({k:v for k,v in report.items() if k not in ['rawFileSHA256','eyeLayers']},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
