from pathlib import Path
import json,struct,sys,hashlib
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).parent/sys.argv[1]
state=json.loads((R/'status.json').read_text())
assert state['status']=='CAPTURED',state
def rd(n):
 b=(R/(n+'.bin')).read_bytes();w,h,_,_=struct.unpack_from('<4i',b)
 return np.frombuffer(b,'<f4',offset=16).reshape(h,w,4)
def singleton(m):
 p=np.pad(m,1);n=sum(p[1+y:1+y+m.shape[0],1+x:1+x+m.shape[1]].astype(int) for y,x in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)])
 return m&(n==0)
rows=[];bounds=[];records={}
for path in sorted(R.glob('*_pose.json')):
 p=path.name[:3];pose=json.loads(path.read_text());target=int((R/(p+'_target.txt')).read_text());m=rd(p+'_MASK');hair=m[:,:,1]>.5;parent=m[:,:,0]>.5;ox,oy=pose['offset']
 def shifted(mask):
  y,x=np.nonzero(mask);x=x+ox;y=y-oy;ok=(x>=0)&(x<480)&(y>=0)&(y<272);o=np.zeros_like(mask);o[y[ok],x[ok]]=True;return o
 ar=rd(p+'_ALT_RAW');au=rd(p+'_ALT_RAWUV');ah=rd(p+'_ALT_HAIR');hu=rd(p+'_ALT_HAIRUV');am=rd(p+'_ALT_META');bm=rd(p+'_BASE_META');ac=rd(p+'_ALT_FINAL');bc=rd(p+'_BASE_FINAL');av=rd(p+'_ALT_UV');bv=rd(p+'_BASE_UV');native=rd(p+'_ALT_NATIVE');bh=rd(p+'_BASE_HAIR')
 row={'capture':int(p),'target':target,'phase':pose['phase']%1,'pose':pose,'cost':json.loads((R/(p+'_cost.json')).read_text()),'runtime':json.loads((R/(p+'_auto.json')).read_text()),'outside':{},'packetMismatches':[]}
 for stage,v,h,par in [('Raw',ar,hair,parent),('HairLayer',ah,hair,parent),('Final',am,shifted(hair),shifted(parent)),('Native',native,np.repeat(np.repeat(hair,2,0),2,1),np.repeat(np.repeat(parent,2,0),2,1))]:
  role=np.rint(v[:,:,1]);cov=v[:,:,0]>0
  row['outside'][stage]={'hair':int((cov&(role>=12)&~h).sum()),'face':int((cov&(role>=1)&(role<=7)&~par).sum())}
 packets=json.loads((R/(p+'_packets.json')).read_text())['packets'];depth=[]
 for q in packets:
  x,y=q['x'],q['y'];role=12+q['submesh'];uv=[q['uv']['x'],q['uv']['y']]
  if ar[y,x,0]>0 and round(float(ar[y,x,1]))==role and (round(float(au[y,x,2]))!=q['primitive']+1 or round(float(au[y,x,3]))!=3 or np.max(abs(au[y,x,:2]-uv))>2e-5):row['packetMismatches'].append([x,y,'raw'])
  if ah[y,x,0]>0 and round(float(ah[y,x,1]))==role and np.max(abs(hu[y,x,:2]-uv))>2e-5:row['packetMismatches'].append([x,y,'layerUV'])
  n=native[2*y:2*y+2,2*x:2*x+2];same=np.rint(n[:,:,1])==role
  if np.any(same&(np.rint(n[:,:,3])!=q['primitive']+1)):row['packetMismatches'].append([x,y,'nativePrimitive'])
  depth.extend(abs(n[:,:,0][same]-q['depth']).tolist())
 row['maxNativeDepthError']=max(depth,default=0.)
 changed=np.any(abs(ac-bc)>1e-5,axis=2);same=np.all(abs(av-bv)<1e-5,axis=2)&(am[:,:,1]==bm[:,:,1])&(am[:,:,3]==bm[:,:,3])
 row['sameSurfaceColourDifferenceYX']={k:np.argwhere(changed&same&(am[:,:,0]>0)&np.isin(np.rint(am[:,:,1]),roles)).tolist() for k,roles in [('face',range(1,8)),('body',range(8,12)),('hair',range(12,16))]}
 row['sameRoleColourDifferenceYX']={k:np.argwhere(changed&(am[:,:,1]==bm[:,:,1])&(am[:,:,0]>0)&np.isin(np.rint(am[:,:,1]),roles)).tolist() for k,roles in [('face',range(1,8)),('body',range(8,12))]}
 row['roles']={k:{str(role):int(((v[:,:,0]>0)&(np.rint(v[:,:,1])==role)).sum())for role in range(1,16)}for k,v in [('original',bm),('candidate',am)]}
 source=(bh[:,:,0]>0)&(np.rint(bh[:,:,1])>=12);row['singletonYX']={'originalLayer':np.argwhere(singleton(source)).tolist(),'designedRegion':np.argwhere(singleton(hair)).tolist(),'candidateVisibleLayer':np.argwhere(singleton((ah[:,:,0]>0)&(np.rint(ah[:,:,1])>=12))).tolist()}
 row['hairCells']={'originalLayer':int(source.sum()),'designedRegion':int(hair.sum()),'candidateLayer':int(((ah[:,:,0]>0)&(np.rint(ah[:,:,1])>=12)).sum())}
 y,x=np.nonzero((am[:,:,0]>0)|(bm[:,:,0]>0));bounds.append([int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)])
 records[target]={'p':p,'mask':hair,'source':source,'meta':am,'baseMeta':bm,'pose':pose};rows.append(row)
events=[]
for row in rows:
 i=row['target']
 if i-1 not in records or i+1 not in records:continue
 a,b,c=(records[j] for j in [i-1,i,i+1]);pop=(a['mask']==c['mask'])&(a['mask']!=b['mask']);original=(a['source']==c['source'])&(a['source']!=b['source'])
 events.append({'target':i,'regionABA_YX':np.argwhere(pop).tolist(),'originalLayerABA_YX':np.argwhere(original).tolist(),'note':'Fixed-coordinate ABA observations are not automatically motion/design errors.'})
box=(2*(min(b[0]for b in bounds)-12),2*(min(b[1]for b in bounds)-8),2*(max(b[2]for b in bounds)+12),2*(max(b[3]for b in bounds)+8));w,h=box[2]-box[0],box[3]-box[1];frames=[]
for row in rows:
 p=f"{row['capture']:03d}";f=Image.new('RGB',(w*2+2,h+38),'#181818');d=ImageDraw.Draw(f)
 for k,tag in enumerate(['BASE','ALT']):f.paste(Image.open(R/(p+'_'+tag+'.png')).convert('RGB').crop(box),(k*(w+2),38))
 d.text((5,5),'CURRENT ORIGINAL / 348',fill='white');d.text((w+7,5),'AUTO CURVE 511 / DEFAULT OFF',fill='white');d.text((5,20),f"Walk {row['phase']:.4f} | target {row['target']}/80",fill='white');frames.append(f)
sheet=Image.new('RGB',(frames[0].width,len(frames)*frames[0].height))
for i,f in enumerate(frames):sheet.paste(f,(0,i*f.height))
pal=sheet.quantize(colors=256,method=Image.Quantize.MEDIANCUT);gif=R/'WALK511_FULLBODY_BEFORE_AFTER.gif';g=[f.quantize(palette=pal,dither=Image.Dither.NONE)for f in frames];g[0].save(gif,save_all=True,append_images=g[1:],duration=[100 if j==len(rows)-1 or rows[j+1]['target']==r['target']+1 else 500 for j,r in enumerate(rows)],loop=0,optimize=True,disposal=2)
out={'status':'ACTUAL_SHORT_WALK' if len(rows)>1 else 'FIRST_ACTUAL_WALK_POSE_ONLY','restoration':state,'rows':rows,'events':events,'allPoseLightMatched':all(r['pose']['sameBones']and r['pose']['sameLight']for r in rows),'outsideTotals':{s:{k:sum(r['outside'][s][k]for r in rows)for k in ['hair','face']}for s in ['Raw','HairLayer','Final','Native']},'packetMismatchTotal':sum(len(r['packetMismatches'])for r in rows),'maxNativeDepthError':max(r['maxNativeDepthError']for r in rows),'unsupportedTotal':sum(r['pose']['unsupported']for r in rows),'uniqueDeformedGeometry':len({hashlib.sha256((R/(f"{r['capture']:03d}.hairgeom")).read_bytes()).hexdigest()for r in rows}),'gif':{'path':str(gif),'bytes':gif.stat().st_size,'frames':len(rows),'nativePixelCrop':box,'interpolation':False,'note':'same-execution original/candidate, full body, time order, 500ms pause at group jumps; palette compression only; original PNG/float buffers preserved'},'limits':['Short intervals/current model/view only; not whole Walk or pixel-art acceptance.','Pre-occlusion region and visible final owner are separate.','Alpha-uncertain visibility tests defer to GPU; not CPU-certified.','Fixed-coordinate ABA is an observation, not proof of bad animation.','Editor RenderFrame wall time is not player FPS.']}
(R/'ANALYSIS511.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in out.items()if k not in ['rows','events','limits']}));print(json.dumps([{'target':r['target'],'hairCells':r['hairCells'],'sameSurfaceColourCounts':{k:len(v)for k,v in r['sameSurfaceColourDifferenceYX'].items()},'sameRoleColourCounts':{k:len(v)for k,v in r['sameRoleColourDifferenceYX'].items()}}for r in rows]))
