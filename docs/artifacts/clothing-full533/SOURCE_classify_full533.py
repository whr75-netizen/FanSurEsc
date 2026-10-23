from pathlib import Path
import json,struct,math
import numpy as np
O=Path(__file__).resolve().parent;R=O/'FullLoop';j=json.loads((O/'FULL_RESULT533.json').read_text())
ns={'__file__':str(O/'analyze_outline533.py')};exec((O/'analyze_outline533.py').read_text().split('targets=')[0],ns);flood=ns['flood']
def fields(frame):
 b=(R/f'{frame:03d}_ALT_LINE_INPUTS.bin').read_bytes();magic,changed,n=struct.unpack_from('<3i',b);assert magic==534
 dt=np.dtype([('x','<i4'),('y','<i4'),('v','<f4',(2,5,4))]);a=np.frombuffer(b,dt,n,12);assert len(b)==12+n*168
 return{(int(q['x']),int(q['y'])):q['v'].copy()for q in a}
cache={};rows=[]
for q in j['noncloth']:
 f=q['frame'];x,y=q['xy']
 if f not in cache:
  s=fields(f);c=[np.frombuffer((R/f'{f:03d}_ALT_LINE_COVERAGE_{k}.bin').read_bytes(),'u1').reshape(272,480).astype(bool)for k in[0,1]];cache[f]=(s,c,[flood(v)for v in c])
 s,c,e=cache[f];v=s[x,y];before=float(np.max(abs(v[0,0]-v[1,0])));owner=float(np.max(abs(v[0,1]-v[1,1])));post=float(np.max(abs(v[0,2]-v[1,2])));line=float(.55);pred=[];tone=[];finalerr=[]
 for tag in[0,1]:
  p=v[tag];role=round(float(p[1,0]))-1;part=round(float(p[1,1]));eligible=role in[7,8,9,10]or role>=11
  ext=[bool(e[tag][y+dy,x+dx])for dx,dy in[(-1,0),(1,0),(0,-1),(0,1)]]
  outer=bool(c[tag][y,x]and eligible and any(ext));assert outer==bool(round(float(p[3,1]))),(f,x,y,tag,outer,p[3])
  pred.append({'role':role,'part':part,'reason':round(float(p[3,0])),'outer':bool(round(float(p[3,1]))),'thin':bool(round(float(p[3,2]))),'palette':p[4].tolist(),'exterior4':ext})
  tone.append(float(np.max(abs(p[2,:3]-p[0,:3]*(np.float32(line)if p[3,0]>0 else np.float32(1)))))if p[4,3]==0 else None)
  original=np.array(q['baseRGB'if tag==0 else'altRGB']);finalerr.append(float(np.max(abs(p[2,:3]-original))))
 if before<1e-6 and post>1e-6 and max(finalerr)<1e-6:
  if pred[0]['outer']!=pred[1]['outer'] and max(owner,0)<2e-6:category='EXTERNAL_OUTLINE_RECLASSIFICATION'
  else:category='OWNER_LINES_CHANGE_NEEDS_INTERNAL_OR_THICKNESS_CLASSIFICATION'
 elif before>1e-6:category='CHANGE_PRESENT_BEFORE_OWNERLINES_UNRESOLVED'
 else:category='CHANGE_AFTER_OWNERLINES_OR_UNRESOLVED'
 rows.append({'frame':f,'xy':[x,y],'sourceRole':q['role'],'sourcePrimitive':q['primitive'],'beforeDifference':before,'ownerDifference':owner,'postLineDifference':post,'lineToFinalErrors':finalerr,'ownToneErrors':tone,'branch':pred,'classification':category})
def region(f):
 b=(R/f'{f:03d}_ALT_REGION.bin').read_bytes();x,y,w,h=struct.unpack_from('<4i',b);n=w*h;a=np.zeros((272,480),np.float32);m=np.zeros((272,480),bool);a[y:y+h,x:x+w]=np.frombuffer(b,'<f4',n,16).reshape(h,w);m[y:y+h,x:x+w]=np.frombuffer(b,'?',n,16+n*4).reshape(h,w);return a,m
def buf(f,tag,name):
 b=(R/f'{f:03d}_{tag}_{name}.bin').read_bytes();w,h,x,y=struct.unpack_from('<4i',b);a=np.zeros((272,480,4),np.float32);a[y:y+h,x:x+w]=np.frombuffer(b,'<f4',offset=16).reshape(h,w,4);return a
tips=[]
for tip in j['tipCandidates']:
 if tip['tag']!='ALT':continue
 f=tip['frame'];x,y=tip['xy'];samples=[]
 for k in[f-1,f,f+1]:
  a,m=region(k);c=buf(k,'ALT','FINAL');meta=buf(k,'ALT','META');samples.append({'frame':k,'selected':bool(m[y,x]),'area':float(a[y,x]),'visible':bool(c[y,x,3]>.5 and meta[y,x,1]==11),'meta':meta[y,x].tolist(),'rows':[''.join('#'if m[yy,xx]else'.'for xx in range(x-3,x+4))for yy in range(y-3,y+4)]})
 tips.append({**tip,'samples':samples,'classification':'selected mask constant; visible-owner transition, actual front-surface cause not yet certified'if len(set(p['selected']for p in samples))==1 else'selected mask changes; inspect continuous/pixel boundary before quality verdict'})
known={}
for name,f,pts in[('source34',34,[(198,85)]),('source43',43,[(200,98),(200,99)]),('normal44',44,[(231,78)])]:
 known[name]=[]
 for k in[f-1,f,f+1]:
  a,m=region(k);bc=buf(k,'BASE','FINAL');ac=buf(k,'ALT','FINAL');bm=buf(k,'BASE','META');am=buf(k,'ALT','META');known[name].append({'frame':k,'baseVisible':[bool(bc[y,x,3]>.5 and bm[y,x,1]==11)for x,y in pts],'altVisible':[bool(ac[y,x,3]>.5 and am[y,x,1]==11)for x,y in pts],'selected':[bool(m[y,x])for x,y in pts]})
result={'nonclothSamples':len(rows),'colourClassCounts':{k:sum(r['classification']==k for r in rows)for k in sorted(set(r['classification']for r in rows))},'colourRows':rows,'tipCandidates':tips,'knownCases':known,'noNewPatch':True,'notAllPixelChangesAreErrors':True}
(O/'CLASSIFICATION533.json').write_text(json.dumps(result,indent=2));print(json.dumps({'colourClassCounts':result['colourClassCounts'],'noncloth':len(rows),'known':known,'tips':[{'frame':q['frame'],'xy':q['xy'],'selected':[p['selected']for p in q['samples']],'area':[p['area']for p in q['samples']]}for q in tips]}))
