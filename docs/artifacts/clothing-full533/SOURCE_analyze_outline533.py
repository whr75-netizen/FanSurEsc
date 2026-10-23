from pathlib import Path
from collections import deque
import json,struct
import numpy as np
O=Path(__file__).resolve().parent;R=O/'GPU';OLD=O.parent/'Shape532/Adjacent'
FIELDS=['before','owner','postLine','audit','final','meta','uv','surface','torso','arms','palette','paletteAudit']
def data(f,tag):
 b=(R/f'{f:03d}_{tag}_SPARSE.bin').read_bytes();magic,n=struct.unpack_from('<2i',b);assert magic==533
 dt=np.dtype([('x','<i4'),('y','<i4'),('v','<f4',(12,4))]);a=np.frombuffer(b,dt,n,8);assert len(b)==8+n*200
 return{(int(q['x']),int(q['y'])):{k:q['v'][i].copy()for i,k in enumerate(FIELDS)}for q in a}
def old(f,tag,name,x,y):
 b=(OLD/f'{f:03d}_{tag}_{name}.bin').read_bytes();w,h,bx,by=struct.unpack_from('<4i',b);return np.frombuffer(b,'<f4',offset=16).reshape(h,w,4)[y-by,x-bx]
def flood(c):
 h,w=c.shape;d=np.full((h,w),-1,np.int32);todo=deque()
 for x,y in[(x,0)for x in range(w)]+[(x,h-1)for x in range(w)]+[(0,y)for y in range(h)]+[(w-1,y)for y in range(h)]:
  if not c[y,x]and d[y,x]<0:d[y,x]=0;todo.append((x,y))
 while todo:
  x,y=todo.popleft()
  if d[y,x]==752:continue
  for dx,dy in[(-1,0),(1,0),(0,-1),(0,1)]:
   u,v=x+dx,y+dy
   if 0<=u<w and 0<=v<h and not c[v,u]and d[v,u]<0:d[v,u]=d[y,x]+1;todo.append((u,v))
 return d>=0
def replay(samples,c,e,x,y):
 p=samples[x,y];own=p['owner'];role=round(float(own[0]))-1;part=round(float(own[1]));eligible=role in[7,8,9,10]or role>=11
 covered=lambda x,y:0<=x<480 and 0<=y<272 and bool(c[y,x])
 exterior=lambda x,y:not(0<=x<480 and 0<=y<272)or bool(e[y,x])
 partat=lambda x,y:round(float(samples[x,y]['owner'][1]))if covered(x,y)else 0
 def core(dx,dy):
  aa=covered(x+dx,y+dy);bb=covered(x+dx*2,y+dy*2)
  if 2<=part<=5:aa=aa and partat(x+dx,y+dy)==part;bb=bb and partat(x+dx*2,y+dy*2)==part
  return aa and bb
 def three(dx,dy):
  aa=partat(x-dx,y-dy)==part;bb=partat(x+dx,y+dy)==part
  return(aa and bb)or(aa and partat(x-dx*2,y-dy*2)==part)or(bb and partat(x+dx*2,y+dy*2)==part)
 outer=internal=thin=joint=False;dirs=[(-1,0),(1,0),(0,-1),(0,1)];trace=[]
 if covered(x,y)and eligible:
  for dx,dy in dirs:
   ex=exterior(x+dx,y+dy);co=core(-dx,-dy)
   if ex:outer=True;thin=thin or not co
   trace.append({'d':[dx,dy],'xy':[x+dx,y+dy],'covered':covered(x+dx,y+dy),'exterior':ex,'inwardTwo':co})
  if not outer and part in[2,3]:
   front,under=p['surface'],p['torso'];underTorso=under[0]>0 and round(float(under[2]))==1 and under[0]>front[0]
   if underTorso:
    for dx,dy in dirs:
     q=samples[x+dx,y+dy]['owner']
     if covered(x+dx,y+dy)and round(float(q[1]))==1 and q[2]>front[0]:
      if front[3]<0:joint=True
      elif core(-dx,-dy):internal=True
      else:thin=True
  if not outer and part==1 and role==10:raise RuntimeError('Unexpected torso/arm connectivity branch requires vertex input')
 if covered(x,y)and 2<=part<=5 and(not three(1,0)or not three(0,1)):thin=True
 reason=1 if outer and not thin and eligible else 2 if internal and not thin else 0
 return {'role':role,'part':part,'reason':reason,'outer':outer,'thin':thin,'joint':joint,'trace':trace}
targets={42:[(209,54),(210,55),(210,56),(210,57)],44:[(226,65)]};rows=[];coverChanges={}
for f,points in targets.items():
 s={tag:data(f,tag)for tag in['BASE','ALT']};c={tag:np.frombuffer((R/f'{f:03d}_{tag}_COVERAGE.bin').read_bytes(),'u1').reshape(272,480).astype(bool)for tag in s};ext={tag:flood(cc)for tag,cc in c.items()};m=json.loads((R/f'{f:03d}_META.json').read_text())
 coverChanges[str(f)]=[[int(x),int(y)]for y,x in np.argwhere(c['BASE']!=c['ALT'])]
 for x,y in points:
  row={'frame':f,'xy':[x,y],'replayed':{},'gpuAudit':{},'beforeRGBDifference':float(np.max(abs(s['BASE'][x,y]['before'][:3]-s['ALT'][x,y]['before'][:3]))),'currentFinalVsOriginal532':{},'currentUVVsOriginal532':{},'currentMetaVsOriginal532':{},'lineTone':m['lineTone'],'usePalette':m['usePalette']}
  for tag in s:
   p=s[tag][x,y];q=replay(s[tag],c[tag],ext[tag],x,y);audit=p['audit'];gpu=[int(round(float(a)))for a in audit];expected=[q['reason'],int(q['outer']),int(q['thin']),int(q['joint'])]
   row['replayed'][tag]=q;row['gpuAudit'][tag]=gpu;row[tag]={'before':p['before'].tolist(),'postLine':p['postLine'].tolist(),'final':p['final'].tolist(),'owner':p['owner'].tolist(),'paletteAudit':p['paletteAudit'].tolist(),'ownToneMaxError':float(np.max(abs(p['postLine'][:3]-p['before'][:3]*(m['lineTone']if q['reason']else 1)))),'postLineToFinalDifference':float(np.max(abs(p['postLine']-p['final'])))}
   row['currentFinalVsOriginal532'][tag]=float(np.max(abs(p['final']-old(f,tag,'FINAL',x,y))))
   row['currentUVVsOriginal532'][tag]=float(np.max(abs(p['uv']-old(f,tag,'UV',x,y))))
   row['currentMetaVsOriginal532'][tag]=float(np.max(abs(p['meta']-old(f,tag,'META',x,y))))
   assert gpu==expected,(f,x,y,tag,gpu,expected)
  row['classification']='SAME_INPUT_RGB_NEW_EXTERNAL_OUTLINE'if row['beforeRGBDifference']<1e-6 and row['gpuAudit']['BASE'][0]==0 and row['gpuAudit']['ALT'][0]==1 else'UNRESOLVED'
  rows.append(row)
result={'status':'FIRST_COLOUR_CHANGE_OWNERLINES_CONFIRMED'if all(q['classification']=='SAME_INPUT_RGB_NEW_EXTERNAL_OUTLINE'for q in rows)else'UNRESOLVED','rows':rows,'changedCoverage':coverChanges,'gpuAuditMatchesShaderReplayAll5':True,'sourceShader':'Assets/EUnityValidation01/GameMapIntegration333/Shaders/OwnerLines333.compute','entry':'FullFeature367.DispatchPost:prepared copy before OwnerLines;postLine copy after OwnerLines','newProductPatch':False,'designScope':'Correct external-boundary reclassification after selected clothing coverage changes; not proof that the new silhouette/gap design is aesthetically optimal.'}
(O/'OUTLINE_CAUSE533.json').write_text(json.dumps(result,indent=2))
print(json.dumps({'status':result['status'],'samples':[{'frame':q['frame'],'xy':q['xy'],'beforeDifference':q['beforeRGBDifference'],'audits':q['gpuAudit'],'original532RGBMaxError':max(q['currentFinalVsOriginal532'].values()),'ownToneMaxError':max(q[t]['ownToneMaxError']for t in['BASE','ALT'])}for q in rows],'changedCoverage':coverChanges}))
