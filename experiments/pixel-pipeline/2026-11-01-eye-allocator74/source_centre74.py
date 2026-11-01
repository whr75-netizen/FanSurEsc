"""Independent measured3D-centre diagnostic; not an optical-design target."""
from pathlib import Path
import ast,json,numpy as np
from run74 import R,K49
def main():
 s=(K49/'candidate49.py').read_text(encoding='utf-8-sig');f=next(x for x in ast.parse(s).body if isinstance(x,ast.FunctionDef)and x.name=='projected_anchor');ns={'np':np};exec(compile(ast.Module(body=[f],type_ignores=[]),'frozen49-projection','exec'),ns)
 result=json.loads((R/'RESULT74.json').read_text());metas={m['frame']:m for m in json.loads((K49/'fixtures/frames.json').read_text())};rows=[]
 for frame in result['oldFrames']:
  _,centres=ns['projected_anchor'](metas[frame['frame']])
  for e in frame['eyes']:
   sid=e['stableId'];ref=centres[sid];a=np.mean(e['legacy']['selected'],axis=0)+.5;b=np.mean(e['candidate']['selected'],axis=0)+.5
   rows.append({'sourceId':frame['sourceId'],'frame':frame['frame'],'stableId':sid,'sourceGeometryProjectedCentre':ref.tolist(),'legacyCellCentresMean':a.tolist(),'candidateCellCentresMean':b.tolist(),'legacySquaredDistance':float(np.sum((a-ref)**2)),'candidateSquaredDistance':float(np.sum((b-ref)**2)),'outputChanged':e['candidate']['changed']})
 out={'reference':'Existing source modelEye.centre transformed by measured head matrix and camera ray basis; not fitted to candidate, not an approved optical-design centre','displayConvention':'selected integer pixel plus(.5,.5) as square-footprint centre; actual representative sub-sample can differ','rows':rows,'changedRowsImproved':sum(x['outputChanged'] and x['candidateSquaredDistance']<x['legacySquaredDistance']for x in rows),'changedRowsWorsened':sum(x['outputChanged'] and x['candidateSquaredDistance']>x['legacySquaredDistance']for x in rows)}
 p=R/'SOURCE_CENTRE74.json'
 if p.exists():assert json.loads(p.read_text())==out;print('Source-centre reference replay matches; no rewrite')
 else:
  with p.open('x')as f:json.dump(out,f,indent=2)
 print('improved',out['changedRowsImproved'],'worsened',out['changedRowsWorsened'])
if __name__=='__main__':main()
