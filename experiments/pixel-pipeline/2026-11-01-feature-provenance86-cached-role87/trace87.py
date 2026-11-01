"""Projection, source deformation and physical-light provenance of real87."""
from pathlib import Path
import json,sys,hashlib,numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OUT=HERE/'result87'
from analyse87 import load,local_grid,texture
sys.path.insert(0,str(ROOT/'whole-eye76'));from validate_final76 import Reader

def mesh(path):
 r=Reader(path);assert r.s()=='aux-mesh67/v1';sid,view,frame,serial=r.s(),r.s(),r.i(),r.i();matrix=r.mat();v=r.a(r.i()*3).reshape(-1,3);normals=r.a(r.i()*3).reshape(-1,3);uv=r.a(r.i()*2).reshape(-1,2)
 for _ in range(r.i()):r.a(r.i(),'<i4')
 r.end();return v,matrix

def shape(mask):
 y,x=np.where(mask)
 return []if not len(x)else sorted((np.stack([x-x.min(),y-y.min()],-1)).tolist())

def main():
 st=json.loads(sorted((HERE/'run87').glob('STATE87*.json'))[-1].read_text());result=json.loads((OUT/'RESULT87.json').read_text());_,_,role=texture('TemplateRole.asset','<f4');rows=[];sweep=[];blink=[];firstSweep=None;previous=None
 for entry in st['sequencePackets']:
  d=load(Path(entry['output']));m=d['manifest'];a=d['arrays'];v,matrix=mesh(Path(entry['output'])/'eye-evaluated.mesh');close=m['eyeFeature']['closeMorphs']['Fcl_EYE_Close'];vid=int(np.argmax(v[:,1]));world=matrix@np.r_[v[vid],1];cam=m['camera86'];vp=np.array(cam['worldProjection']).reshape(4,4,order='F')@np.array(cam['worldView']).reshape(4,4,order='F');clip=vp@world;projected=[float((clip[0]/clip[3]+1)*240),float((clip[1]/clip[3]+1)*136)];keys=[]
  for ei,sid in enumerate([int(z[3])for z in m['eyeFeature']['centres']]):
   q=local_grid(d,ei);k=np.floor(q).astype(int);valid=(k[...,0]>=0)&(k[...,0]<480)&(k[...,1]>=0)&(k[...,1]<272);k=np.clip(k,[0,0],[479,271]);sr=role[k[...,1],k[...,0]];mask=valid&(sr[...,0]==1)&(sr[...,1]==sid);keys.append({'eye':sid,'unoccludedCachedIrisCount':int(mask.sum()),'translationNormalisedShape':shape(mask)})
  areas=[]
  for sid in [2,1]:
   sm=a['S2-meta'];areas.append(float(np.where((sm[...,0]>0)&(np.rint(sm[...,2])==sid),sm[...,3],0).sum()/16))
  row={'frame':entry['frame'],'stage':entry['testStage82'],'index':entry['stageIndex82'],'sourceFrame':m['sourceFrame'],'declaredSourceClose':close,'evaluatedVertexSHA256':hashlib.sha256(v.tobytes()).hexdigest(),'evaluatedSameAsPrevious':previous is not None and np.array_equal(v,previous),'maxEvaluatedVertexDelta':None if previous is None else float(abs(v-previous).max()),'sourceIrisRasterArea':areas,'projectedSameVertex':projected,'vertex':vid,'cachedShape':keys,'sky':m['sky87'],'q':a['main-legacy480-3'][2,2].tolist(),'physical':a['main-centre-raw3'][2,2].tolist()}
  rows.append(row);previous=v
  if entry['testStage82']=='sweep':sweep.append(row)
  if entry['testStage82']=='blink':blink.append(row)
 x=[r['projectedSameVertex'][0]for r in sweep];y=[r['projectedSameVertex'][1]for r in sweep];assert max(x)-min(x)>.99 and max(x)-min(x)<1.01;assert sweep[0]['vertex']==sweep[-1]['vertex'];assert sweep[0]['evaluatedVertexSHA256']==sweep[-1]['evaluatedVertexSHA256']
 proof={'sweepXSpanLogicalCells':max(x)-min(x),'sweepYSpanLogicalCells':max(y)-min(y),'sweepReturnDeltaCells':(np.array(sweep[-1]['projectedSameVertex'])-sweep[0]['projectedSameVertex']).tolist(),'sameEvaluatedMeshAcrossSweep':len({r['evaluatedVertexSHA256']for r in sweep})==1,'unoccludedCachedShapeCountsByEye':[[r['cachedShape'][ei]['unoccludedCachedIrisCount']for r in sweep]for ei in range(2)],'unoccludedUniqueTranslationNormalisedShapesByEye':[len({json.dumps(r['cachedShape'][ei]['translationNormalisedShape'])for r in sweep})for ei in range(2)],'observedSkyAutomatic':all(r['sky']['auto']for r in rows),'observedHourStartEnd':[rows[0]['sky']['hour'],rows[-1]['sky']['hour']],'observedDistinctSunDirections':len({tuple(r['sky']['sunForward'])for r in rows}),'blink':blink,'rows':rows,'conclusion':['Candidate87 joins source role and pigment provenance, but nearest warped source pixels do not preserve a small cluster shape through a full measured phase sweep. Do not activate product default.','Declared source morph getter is taken after host afterPose; evaluated mesh and source raster demonstrate the actual deformation timing separately. Source getter is not proof the same frame was already evaluated at that weight.','Scene auto clock and sun direction demonstrably change; raw-light/threshold transitions cannot all be attributed to feature sampling.']}
 (OUT/'TRACE87.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({k:v for k,v in proof.items()if k not in ['rows','blink']},indent=2));print(json.dumps([{'frame':r['frame'],'declared':r['declaredSourceClose'],'sameMesh':r['evaluatedSameAsPrevious'],'delta':r['maxEvaluatedVertexDelta'],'irisArea':r['sourceIrisRasterArea']}for r in blink],indent=2))

if __name__=='__main__':main()
