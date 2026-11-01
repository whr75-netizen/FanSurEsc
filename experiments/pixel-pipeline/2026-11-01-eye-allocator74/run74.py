"""One conditional candidate, current73 plus frozen47 counterexamples only."""
from pathlib import Path
import sys,json,hashlib,struct,ast,math
import numpy as np
from PIL import Image,ImageDraw
from allocator74 import legacy,connected,components
R=Path(__file__).resolve().parent
def sibling(a,b):
 p=R.parent/a
 return p if p.exists() else R.parent/b
OLD=sibling('continuous47-counts','2026-10-30-continuous47-counts/archive');NEW=sibling('eye-observer73','2026-11-01-eye-observer73');K52=sibling('whole-eye52','2026-10-31-eye-experiments50-53/archive/whole-eye52');K49=sibling('eye-candidate49','2026-10-30-eye-candidate49')
def defs(path,names,ns):
 s=path.read_text(encoding='utf-8-sig');t=ast.parse(s);fs=[x for x in t.body if isinstance(x,ast.FunctionDef) and x.name in names];assert {x.name for x in fs}==set(names);exec(compile(ast.Module(body=fs,type_ignores=[]),str(path),'exec'),ns)
def metrics(I,selected):
 yy,xx=np.indices(I.shape);total=float(I.sum());centre=np.array([(xx*I).sum(),(yy*I).sum()])/total if total else None
 c=None if not selected else np.mean(sorted(selected),axis=0)
 return {'components4':len(components(selected)),'retainedIrisWeight':sum(float(I[y,x])for x,y in selected),'sourceWeightedCentre':None if centre is None else centre.tolist(),'outputCentre':None if c is None else c.tolist(),'centreSquaredError':None if c is None or centre is None else float(np.sum((c-centre)**2))}
def main():
 verify=sys.argv[1:]==['--verify']
 assert verify or not (R/'RESULT74.json').exists(),'Preserve existing result; use--verify for read-only replay'
 ns={'np':np,'math':math,'json':json,'struct':struct}
 cache=sibling('author33','2026-10-30-source-diagnostics/archive/exp27/author33')/'feature34/eye_cache42.py';defs(cache,['vec','classify'],ns)
 defs(OLD/'analyse_counts.py',['read','cov','valid','weight_occlusion','replay_packets','final_gate'],ns);defs(K49/'verify49.py',['native_line'],ns)
 keyform=json.loads((K52/'WHOLE_KEYFORM52.json').read_text());cells=keyform['states']['existing-open-reference']['cells'];sourceproof=[]
 for sid in [1,2]:
  points=[tuple(c['referenceXY'])for c in cells if c['eye']==sid and c['part']=='iris'];assert len(components(points))==1;sourceproof.append({'stableId':sid,'referenceIrisCells':points,'referenceComponents4':1})
 contract={'connectivity':4,'provenance':'Existing52 source-keyform Template216/205 iris is4-connected; conditional design constraint, not a universal pixel-art rule or complete pose binding'}
 inputs=[];panels=[];hashes={};replayerr=[]
 fixture=K49/'fixtures';z=np.load(fixture/'replay-inputs.npz');metas=json.loads((fixture/'frames.json').read_text())
 for index,m in enumerate(metas):
  prefix=f'f{index:02d}_';packet=z[prefix+'GPU'].copy();d={k[len(prefix):]:z[k].copy()for k in z.keys()if k.startswith(prefix)and k!=prefix+'GPU'};w,h=m['width'],m['height'];cpu,depth=ns['replay_packets'](m,d);err=float(np.max(np.abs(cpu-packet)));assert err<1e-4;replayerr.append(err)
  record={'sourceId':m['sourceId'],'frame':m['frame'],'dataset':'frozen47','eyes':[]};actual=d['eye-visible'];plateOld=Image.new('RGB',(w,h),(25,27,32));plateNew=plateOld.copy();do=ImageDraw.Draw(plateOld);dn=ImageDraw.Draw(plateNew)
  for eye in range(2):
   sid=round(m['centres'][eye]['w']);o=legacy(packet[eye]);c=connected(packet[eye],contract);a=set(o['selected']);b=set(c['selected']);gate=ns['final_gate'](d,depth[eye]);observed={(int(x),int(y))for y,x in np.argwhere((np.rint(actual[...,1])==sid)&np.isin(np.rint(actual[...,0]),[2,3,4]))}
   predicted={p for p in a if gate[p[1],p[0]]};assert observed==predicted,(m['frame'],sid,'legacy replay mismatch');candidateV={p for p in b if gate[p[1],p[0]]}
   lineA=ns['native_line'](packet,m,eye,a);lineB=ns['native_line'](packet,m,eye,b);xy=lambda pts:[[x+m['x'],y+m['y']]for x,y in sorted(pts)]
   changes=[]
   for x,y in sorted(b-a):changes.append({'xyTopLeft':[x+m['x'],y+m['y']],'replacesActualFeature':actual[y,x].tolist(),'sourcePacket':packet[eye,y,x].tolist(),'legacyFinalVetoPass':bool(gate[y,x])})
   row={'stableId':sid,'legacy':{'area':o['area'],'budget':o['budget'],'selected':xy(a),'metrics':metrics(o['iris'],a)},'candidate':{**{k:v for k,v in c.items()if k not in ['selected','ranked']},'selected':xy(b),'metrics':metrics(o['iris'],b)},'actualVisibleIris':xy(observed),'candidateAfterLegacyFinalVeto':xy(candidateV),'NativeLineAllocationChanged':lineA!=lineB,'nativeLineBefore':xy(lineA),'nativeLineAfter':xy(lineB),'newlyOccupiedCells':changes,'vacatedCellsNeedSameSourceCleanBacking':xy(a-b),'vetoMeaning':'Exact old product logical final-veto predicate only; not physical partial-occlusion proof. No any(front) or guessed refill.'};record['eyes'].append(row)
   colour=(80,190,230)if sid==2 else(240,135,95)
   for x,y in observed:do.point((x,y),fill=colour)
   for x,y in candidateV:dn.point((x,y),fill=colour)
  actualRGB=Image.open(fixture/f'actual-{m["frame"]}.png').convert('RGB')
  board=Image.new('RGB',(w*3+8,h),(25,27,32));board.paste(actualRGB,(0,0));board.paste(plateOld,(w+4,0));board.paste(plateNew,(2*w+8,0));panels.append((m['frame'],board));inputs.append(record)
 # Current73 is a different one-frame source; do not splice it into47 time.
 state=json.loads((NEW/'RESULT73.json').read_text());allrows=json.loads((NEW/'CELL_RECORDS73.json').read_text());p=np.zeros((2,8,16,12),np.float32)
 for row in allrows['rows']:
  x,y=row['xyTopLeft'];p[:,y-49,x-212]=row['countsBothEyes']
 current=[]
 for eye,sid in enumerate([2,1]):
  a=legacy(p[eye]);b=connected(p[eye],contract);assert not b['changed'];current.append({'stableId':sid,'legacy':a['selected'],'candidate':b['selected'],'area':a['area'],'budget':a['budget'],'changed':b['changed'],'fullRGBComparison':'unchanged selection; actual73 RGB retained, not newly rendered candidate'})
 for f in [NEW/'RESULT73.json',NEW/'CELL_RECORDS73.json',K52/'WHOLE_KEYFORM52.json',K49/'REPORT_KO.md',R.parent/'joint-eye53/REPORT_KO.md',R.parent/'partial-occlusion55/RESULTS.json',fixture/'frames.json',fixture/'replay-inputs.npz']:
  if f.exists():hashes[str(f.relative_to(R.parent))]=hashlib.sha256(f.read_bytes()).hexdigest()
 frame=Image.new('RGB',(max(p.width for _,p in panels),sum(p.height+3 for _,p in panels)),(25,27,32));y=0
 for _,p in panels:frame.paste(p,(0,y));y+=p.height+3
 if not verify:
  frame.save(R/'OLD47_COMPARISON1x.png');frame.resize((frame.width*12,frame.height*12),Image.Resampling.NEAREST).save(R/'OLD47_COMPARISON12x.png')
  eye=Image.open(NEW/'EYE73.png');eye.save(R/'CURRENT73_UNCHANGED.png');eye.resize((eye.width*20,eye.height*20),Image.Resampling.NEAREST).save(R/'CURRENT73_UNCHANGED20x.png')
 rows=[e for f in inputs for e in f['eyes']];changed=[e for e in rows if e['candidate']['changed']]
 result={'currentSourceId':state['sourceId'],'sourceTopologyMatches52':json.loads(next(NEW.glob('STATE73-*-finished.json')).read_text())['eyeFeature']['topologySHA256']==keyform['sourceTopologySHA256'],'sourceReference':sourceproof,'contract':contract,'oldFrames':inputs,'current73':current,'summary':{'historicalEyeFrames':len(rows),'disconnectedLegacyAllocations':sum(e['legacy']['metrics']['components4']>1 for e in rows),'connectedCandidateAllocations':sum(e['candidate']['metrics']['components4']==1 for e in rows),'changedEyeFrames':len(changed),'budgetsUnchanged':all(e['legacy']['budget']==e['candidate']['budget']for e in rows),'NativeLineAllocationChanges':sum(e['NativeLineAllocationChanged']for e in rows),'maxHistoricalCountReplayError':max(replayerr),'current73Changes':sum(e['changed']for e in current),'retainedIrisWeightChange':[e['candidate']['metrics']['retainedIrisWeight']-e['legacy']['metrics']['retainedIrisWeight']for e in changed],'centreErrorChange':[e['candidate']['metrics']['centreSquaredError']-e['legacy']['metrics']['centreSquaredError']for e in changed]},'limits':['Conditional4-connected design test, not full reference-shape preservation','Same mesh topology as52, but73 full style/Template bank/state binding not captured; no production adoption','Current73 has one frame; frozen47 has historical6frames but candidate not rendered in a live sequence','NativeLine allocation replay unchanged does not prove all sclera/lid/colour composition unchanged','Old vacated/new pigment pixels lack same-source clean underlay/template-bank verification; old candidate images are feature-ID diagnostics, not actual new RGB','Positive source counts are already post-sampling/visibility; no splitting genuine occlusion nor spatial source identity inferred','Tiny continuous score changes can still swap connected subsets; cache/continuous motion is not solved','Count and centre errors are tradeoffs, not art-quality proof'],'newUnityCalls':0,'productChanges':0,'candidateAdopted':False,'inputSHA256':hashes}
 if verify:
  expected=json.loads((R/'RESULT74.json').read_text());normalized=json.loads(json.dumps(result));assert normalized['summary']==expected['summary'] and normalized['oldFrames']==expected['oldFrames'] and normalized['current73']==expected['current73'];print('Archived49 input fixture replay equals original47 raw-input result; no outputs rewritten')
 else:
  with (R/'RESULT74.json').open('x',encoding='utf-8')as f:json.dump(result,f,ensure_ascii=False,indent=2)
 print(json.dumps(result['summary'],indent=2))
if __name__=='__main__':main()
