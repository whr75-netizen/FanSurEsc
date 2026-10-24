from pathlib import Path
import csv,json,struct,sys
import numpy as np
R=Path(__file__).parent;C=R/'Runtime581/Samples17To19';OLD=R.with_name('HairEye580')/'Runtime579/Wider100To170'
f32=np.float32
TRIAL='--aperture' in sys.argv
def buf(p):
 d=p.read_bytes();w,h,x,y=struct.unpack_from('<4i',d);return x,y,np.frombuffer(d,'<f4',offset=16).reshape(h,w,4)
def config(p):return {q[0]:np.array(q[1:],dtype='f4')for q in csv.reader(p.open(),delimiter='\t')}
def matrix(c,key):return np.array([c[key+'.row'+str(i)]for i in range(4)],dtype='f4')
def covered(m):return m[0]>0 and m[1]>.5 and m[3]>1e-6
def aperture(ss):
 # Same-ray front-to-back source coverage. Equal-depth tie order follows
 # the original Face submesh draw order with ZTest LEqual:4,3,1.
 layers=[(ss[1]['m'],True),(ss[0]['m'],False),(ss[2]['m'],True)]
 layers=sorted(layers,key=lambda z:float(z[0][0])if covered(z[0])else float('inf'))
 trans=f32(1);amount=f32(0)
 for m,eye in layers:
  if not covered(m):continue
  alpha=f32(np.clip(m[3],0,1))
  if eye and round(float(m[2]))==2:amount+=trans*alpha
  trans*=1-alpha
 return f32(np.clip(amount,0,1))
def choose(c):
 ir=c[2]+c[3]+c[4];total=c[5]+ir+c[1]
 if total>=4:
  if c[5]>=5 and ir<=4:return 5
  if ir>=5:return 4 if c[4]>=4 else 2 if c[2]>=c[3]else 3
  if c[1]>=3:return 1
  if c[5]>=3:return 7
 elif c[6]>=5:return 6
 return 0
def classify(rest,c,e):
 d=rest-c['Centres348.'+str(e)][:3];ax=c['AxesX348.'+str(e)];ay=c['AxesY348.'+str(e)];u=np.dot(d,ax[:3])/ax[3];v=-np.dot(d,ay[:3])/ay[3];a=c['UpperLower348'];ir=c['Iris348'];cat=c['Catch348'];up=a[0]+a[1]*u*u;lo=a[2]+a[3]*u*u
 ap=abs(u)<=f32(1.02)and v>=up and v<=lo;lash=abs(u)<=f32(1.08)and v>=up-f32(.36)and v<=up+f32(.22);lid=abs(u)<=f32(.90)and v>lo and v<=lo+f32(.35);iris=ap and not lash and (abs(u)/ir[0])**ir[3]+(abs(v+ir[2])/ir[1])**ir[3]<=1
 f=6 if lid else 0
 if ap and not iris and not lash:f=1
 if iris:f=2 if v<f32(.08)else 3
 if iris and u>=cat[0]and u<=cat[1]and v>=cat[2]and v<=cat[3]:f=4
 if lash:f=5
 return f,float(u),float(v)
def read_samples(p):
 out={}
 for q in csv.DictReader(p.open(),delimiter='\t'):
  out[(int(q['cellX']),int(q['cellY']),int(q['k']),int(q['support']))]={name:np.array([q[k]for k in keys],dtype='f4')for name,keys in [('m',['depth','role','eye','alpha']),('p',['restX','restY','restZ','pointValid']),('u',['uvX','uvY','primitive','uvW'])]}
 return out
def cell_data(p):
 return {(int(q['cellX']),int(q['cellY']),q['buffer']):np.array([q[k]for k in ['r','g','b','a']],dtype='f4')for q in csv.DictReader(p.open(),delimiter='\t')}
frames=[];allrows=[]
for frame in range(3):
 p={s:C/f'{frame:03}_{s}'for s in ['OFF','ON']};samples={s:read_samples(Path(str(p[s])+'_SUBPIXELS581.tsv'))for s in p};cells={s:cell_data(Path(str(p[s])+'_CELLS581.tsv'))for s in p};cfg={s:config(Path(str(p[s])+'_CONFIG581.tsv'))for s in p}
 entry={'queryFrame':frame,'originalFrame':frame+17,'savedInputs':{},'cells':[]};matches=[]
 for s in p:
  actual=json.loads(Path(str(p[s])+'_PARAMS.json').read_text());original=json.loads((OLD/f'{frame+17:03}_{s}_PARAMS.json').read_text());entry['savedInputs'][s]={'phase':actual['phase'],'originalPhase':original['phase'],'phaseDelta':actual['phase']-original['phase']}
  for field in ['EYE_INTRINSIC','EYE_VISIBLE']:
   a=buf(Path(str(p[s])+'_'+field+'.bin'));b=buf(OLD/f'{frame+17:03}_{s}_{field}.bin');assert a[:2]==b[:2];entry['savedInputs'][s][field+'_differentCells']=int(np.any(a[2]!=b[2],axis=2).sum())
 entry['rawSourceSupportSameOFFON']=all(np.array_equal(samples['OFF'][key][field],samples['ON'][key][field])for key in samples['OFF']if key[3]in[0,1,2,3,5,6]for field in ['m','p','u'])
 for y in [52,53]:
  for x in [223,224]:
   for s in ['OFF','ON']:
    c=cfg[s];e=next(i for i in range(2)if round(float(c['Centres348.'+str(i)][3]))==2);plane=c['Plane348.'+str(e)];hist=np.zeros(8,dtype='f4');intr=np.zeros(8,dtype='f4');sub=[]
    for k in range(16):
     ss={a:samples[s][x,y,k,a]for a in range(7)};st=np.array([x+(k%4+.5)/4,y+1-(k//4+.5)/4],dtype='f4');near=c['RayBase348'][:3]+st[0]*c['RayX348'][:3]+st[1]*c['RayY348'][:3];pd=-(np.dot(plane[:3],near)+plane[3])/np.dot(plane[:3],c['RayDepth348'][:3]);hyp=(matrix(c,'WorldToHead348')@np.r_[near+pd*c['RayDepth348'][:3],f32(1)])[:3]
     support=next((a for a in range(4)if covered(ss[a]['m'])and round(float(ss[a]['m'][2]))==2 and ss[a]['p'][3]>.5),-1);rest=ss[support]['p'][:3]if support>=0 else hyp;feat,u,v=classify(rest,c,e)
     if feat:intr[feat]+=1
     if feat in [5,6]:support=0 if covered(ss[0]['m'])and round(float(ss[0]['m'][2]))==2 and ss[0]['p'][3]>.5 else 3 if feat==5 and covered(ss[3]['m'])and round(float(ss[3]['m'][2]))==2 and ss[3]['p'][3]>.5 else -1
     depth=ss[support]['m'][0]if support>=0 and feat in [5,6]else pd;weight=f32(1 if support>=0 and feat>0 else 0);hair=cells[s][x,y,'HairMETA']if s=='ON'else ss[4]['m'];blocked=[]
     apertureWeight=aperture(ss)
     if feat and support>=0:
      if TRIAL and feat in [1,2,3,4]:weight*=apertureWeight
      for tag,m in [('hair',hair),('brow',ss[5]['m'])]:
       if covered(m)and m[0]<depth:weight*=1-np.clip(m[3],0,1);blocked.append(tag)
      if covered(ss[6]['m'])and ss[6]['m'][0]<depth:weight=f32(0);blocked.append('body')
      hist[feat]+=weight
     sub.append({'k':k,'label':feat,'support':support,'u':u,'v':v,'planeDepth':float(pd),'shaderDepth':float(depth),'weight':float(weight),'apertureWeight':float(apertureWeight),'blockers':blocked,'nativeHairDepth':float(ss[4]['m'][0]),'nativeHairAlpha':float(ss[4]['m'][3]),'shaderHairDepth':float(hair[0]),'shaderHairAlpha':float(hair[3]),'bodyDepth':float(ss[6]['m'][0]),'nativeIrisDepth':float(ss[2]['m'][0]),'nativeIrisAlpha':float(ss[2]['m'][3])})
    gpu=cells[s][x,y,'EyeVisible'];gpuintr=cells[s][x,y,'EyeIntrinsic'];winner=choose(hist);iw=choose(intr);final=winner;rep=-1;nearest=1e20
    for sample in sub:
     label=sample['label'];match=label==5 if winner==7 else label in[2,3,4]if winner in[2,3,4]else label==winner
     k=sample['k'];dd=((k%4+.5)/4-.5)**2+((k//4+.5)/4-.5)**2
     if winner>0 and match and sample['support']>=0 and sample['weight']>0 and dd<nearest:rep=k;nearest=dd
    bm=cells[s][x,y,'BaseMETA'];back=cells[s][x,y,'BackingMETA'];bm=back if covered(back)and(not covered(bm)or back[0]<bm[0])else bm
    depth=f32(sub[rep]['shaderDepth'])if rep>=0 else bm[0];hairCell=cells[s][x,y,'HairMETA'];browCell=cells[s][x,y,'BrowMETA'];late=[]
    if covered(hairCell)and hairCell[0]<depth:depth=hairCell[0];final=0;late.append('hair-centre')
    if covered(browCell)and browCell[0]<depth and(not covered(hairCell)or hairCell[0]>=browCell[0]):final=0;late.append('brow-centre')
    same=final==round(float(gpu[0]))and iw==round(float(gpuintr[0]));matches.append(same)
    row={'x':x,'y':y,'side':s,'visibleCounts':hist.tolist(),'intrinsicCounts':intr.tolist(),'replayedWinner':winner,'replayedFinalVisible':final,'representative':rep,'lateOcclusion':late,'gpuVisible':gpu.tolist(),'replayedIntrinsic':iw,'gpuIntrinsic':gpuintr.tolist(),'winnerMatchesGPU':same,'gpuHistVisible':cells[s][x,y,'EyeHistVisible'].tolist(),'gpuHistIntrinsic':cells[s][x,y,'EyeHistIntrinsic'].tolist(),'samples':sub};entry['cells'].append({k:v for k,v in row.items()if k!='samples'});allrows.append(dict(queryFrame=frame,originalFrame=frame+17,**row))
 entry['allWinnerReplayMatchesGPU']=all(matches);frames.append(entry)
result={'captureStatus':json.loads((C/'status.json').read_text()),'completedPairFiles':3,'thirdPairSavedBeforeFloatRotationGuardFailure':True,'sourceCodeChanged':False,'offlineApertureTrial':TRIAL,'frames':frames}
(R/('APERTURE581.json'if TRIAL else'ANALYSIS581.json')).write_text(json.dumps(result,indent=2)+'\n');(R/('SUBPIXEL_APERTURE581.json'if TRIAL else'SUBPIXEL_REPLAY581.json')).write_text(json.dumps(allrows,indent=2)+'\n')
print(json.dumps({'frames':[{'frame':f['originalFrame'],'supportSame':f['rawSourceSupportSameOFFON'],'originalMatches':f['savedInputs'],'winnerReplayMatches':f['allWinnerReplayMatchesGPU'],'irisCell':[{k:z[k]for k in ['x','y','side','visibleCounts','intrinsicCounts','replayedWinner','gpuVisible']}for z in f['cells']if z['y']==53]}for f in frames]}))
