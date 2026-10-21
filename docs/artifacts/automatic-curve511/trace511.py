from pathlib import Path
import json,struct,collections,numpy as np
R=Path(__file__).parent/'Walk511';review=json.loads((R/'REVIEW511.json').read_text());analysis=json.loads((R/'ANALYSIS511.json').read_text());by={r['target']:r for r in analysis['rows']};cache={}
def rd(p,n):
 key=(p,n)
 if key not in cache:
  b=(R/(p+'_'+n+'.bin')).read_bytes();w,h,_,_=struct.unpack_from('<4i',b);cache[key]=np.frombuffer(b,'<f4',offset=16).reshape(h,w,4)
 return cache[key]
def shifted(a,ox,oy):
 yy,xx=np.indices((272,480));mx=xx+ox;my=yy-oy;ok=(mx>=0)&(mx<480)&(my>=0)&(my<272);o=np.zeros_like(a);o[ok]=a[my[ok],mx[ok]];return o
traces=[]
for e in review['finalVisibleRoleABA']:
 if e['version']!='candidate':continue
 i=e['target'];x,y=e['headXY'];steps=[]
 for n in [i-1,i,i+1]:
  r=by[n];p=f"{r['capture']:03d}";ox,oy=r['pose']['offset'];bm=shifted(rd(p,'BASE_META'),ox,oy);hp=rd(p,'BASE_PREPARED');valid=(hp[:,:,0]>=12)&(hp[:,:,2]>0)&(bm[:,:,1]==hp[:,:,0])&(bm[:,:,0]>0);ds=bm[:,:,0][valid]-hp[:,:,2][valid];off=float(np.median(ds));asprep=rd(p,'ALT_PREPARED')[y,x];fm=rd(p,'ALT_META')[y-oy,x+ox]
  native=rd(p,'ALT_NATIVE')[2*y:2*y+2,2*x:2*x+2]
  step={'target':n,'mask':rd(p,'MASK')[y,x,:2].tolist(),'headRaw':rd(p,'ALT_RAW')[y,x].tolist(),'headLayer':rd(p,'ALT_HAIR')[y,x].tolist(),'headPreparedOwner':asprep.tolist(),'finalMainMeta':fm.tolist(),'baselineMainMeta':bm[y,x].tolist(),'headToMainDepthOffsetFromStoredMatchedHairMedian':off,'depthOffsetSpreadMax':float(np.max(abs(ds-off))),'headMainDepth':float(asprep[2]+off),'joinDepthMarginBeyondBodyPlusEpsilon':float(asprep[2]+off-fm[0]-.0001),'nativeRoles':native[:,:,1].tolist()}
  steps.append(step)
 traces.append({'event':e,'steps':steps,'limit':'Depth offset inferred from stored same-frame matched hair. Body meta is observed when body wins. Does not certify the same continuous ray/surface before and after pixel-region design.'})
def exterior(m):
 h,w=m.shape;e=np.zeros_like(m);q=collections.deque()
 for y,x in [(0,x)for x in range(w)]+[(h-1,x)for x in range(w)]+[(y,0)for y in range(h)]+[(y,w-1)for y in range(h)]:
  if not m[y,x] and not e[y,x]:e[y,x]=True;q.append((y,x))
 while q:
  y,x=q.popleft()
  for dy,dx in [(0,1),(0,-1),(1,0),(-1,0)]:
   yy,xx=y+dy,x+dx
   if 0<=yy<h and 0<=xx<w and not m[yy,xx] and not e[yy,xx]:e[yy,xx]=True;q.append((yy,xx))
 return e
lineChecks=[]
for detail in json.loads((R/'COLOUR_DETAILS511.json').read_text()):
 if detail['change']['pngMaxByteDelta']<2:continue
 n=detail['change']['target'];p=f"{by[n]['capture']:03d}";x,y=detail['change']['mainXY'];row={'target':n,'mainXY':[x,y],'versions':{},'note':'Reconstruction from captured FINAL alpha/OWNER, not an observed GPU Before/Flood/Audit attachment. Eye changes could affect a general reconstruction; inspect local semantic neighbourhood.'}
 for tag in ['BASE','ALT']:
  cov=rd(p,tag+'_FINAL')[:,:,3]>.5;own=rd(p,tag+'_OWNER');ext=exterior(cov);dirs=[(-1,0),(1,0),(0,-1),(0,1)];outer=False;thin=False
  for dx,dy in dirs:
   if ext[y+dy,x+dx]:outer=True;thin|=not(cov[y-dy,x-dx]and cov[y-2*dy,x-2*dx])
  row['versions'][tag]={'outer':bool(outer),'thin':bool(thin),'reasonForHair':int(outer and not thin),'covered3x3':cov[y-1:y+2,x-1:x+2].astype(int).tolist(),'roles3x3':own[y-1:y+2,x-1:x+2,0].tolist()}
 row['linearRatio']=(np.array(detail['buffers']['FINAL']['ALT'][:3])/np.array(detail['buffers']['FINAL']['BASE'][:3])).tolist();lineChecks.append(row)
out={'candidateVisibleTransitions':traces,'lineChecks':lineChecks,'noNewCapture':True,'noProductChange':True}
(R/'FIRST_STAGE_TRACE511.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
