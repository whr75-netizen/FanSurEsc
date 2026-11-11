"""Source-backed shared-skin cache and gated counterfactual, CPU only.

This does not expand any live mask. A source-visible witness is necessary;
matching a destination triangle alone never establishes source visibility.
"""
from pathlib import Path
import hashlib,json,os,sys
import numpy as np
H=Path(__file__).resolve().parent;R=H.parents[2]
os.environ['PIXEL111_FROZEN_INPUTS']='1';sys.path.insert(0,str(R/'support-contract112'))
from source112 import Source,load,packet_list,read
from support112 import Support

def eligible(mask,primitive,eye,sourceInterval,gap,limit,renderer=1,submesh=3):
 return renderer==1 and submesh==3 and sourceInterval==[1.,1.] and gap>=0 and gap<=limit and bool(int(mask[primitive-1])&(1<<eye))

def main():
 src=Source();_,paths=packet_list();c=load(paths[3]);s=Support(src,c)
 base=read(R/'argon23-runtime113/SOURCE113.json');old=np.asarray(base['ownSkinMask'],np.uint32);new=np.zeros_like(old)
 assert len(old)==len(s.tri)
 mapping={int(v[2]):i for i,v in enumerate(c['sources'])if list(v[:2])==[1,3]}
 for primitive,vertices in enumerate(s.tri,1):
  row=mapping[primitive];assert set(c['triangles'][row,:3]-s.m['faceVertexOffset'])==set(vertices)
  owners=np.rint(c['triOwners'][row,:3]).astype(int)
  norms={eye:np.linalg.norm(s.deltas[eye][vertices].astype(np.float64),axis=1)for eye in [1,2]}
  for eye in [1,2]:
   # Exact nonzero source morph deltas, not noisy evaluated world displacement.
   # No epsilon, distance expansion or optional two-ring policy is invented.
   if np.sum(owners==eye)>=2 and norms[eye].sum()>=norms[3-eye].sum()and norms[eye].max()>0:new[primitive-1]|=1<<eye
 extra=new&~old
 facts=read(R/'bounded-form115/runtime24/full-render24/carrier-fix24/VALIDATED_FIX24.json')['close75SkinEvidence']
 affiliation=read(R/'bounded-form115/runtime24/full-render24/carrier-fix24/CLOSE75_SKIN_AFFILIATION24.json')
 assert s.key==affiliation['immutableSourceCacheKey']
 packetMap={}
 for mode in ['close','motion']:
  state=read(next((R/'bounded-form115/runtime24/full-render24/carrier-fix24'/mode).glob('STATE113-*-finished.json')))
  packetMap.update({v['sourceId']:Path(v['output'])for v in state['sequencePackets']})
 rows=[];cases=0
 for f in facts:
  assert f['sourceFaceVisibility']['faceInterval']==[1.,1.]and not f['sourceFaceVisibility']['hits']
  m=read(packetMap[f['sourceId']]/'RAW_MANIFEST.json');ns=f['nativeSource'];triangle=ns['triangle']
  assert list(c['sources'][triangle,:2])==[1,6]and int(c['sources'][triangle,2])==ns['sourcePrimitive']
  eye=int(np.floor(np.dot(ns['barycentric'],c['triOwners'][triangle,:3])+.5));assert eye in [1,2]
  limit=m['runtime24']['socketDiameters'][eye-1]
  before=[];after=[]
  for ray in f['destinationFaceVisibility']:
   a=b=1.
   for hit in ray['hits']:
    gap=hit['depthGapMetres'];primitive=hit['sourcePrimitive']
    if not hit['exempt113']:a*=1-hit['alphaBounds'][1]
    exempt=hit['exempt113']or eligible(extra,primitive,eye,[1.,1.],gap,limit)
    if not exempt:b*=1-hit['alphaBounds'][1]
    if primitive in [v['primitive']for v in affiliation['rows']]:
     for interval in [[0.,0.],[0.,1.],[.5,.5]]:
      assert not eligible(extra,primitive,eye,interval,gap,limit);cases+=1
     assert not eligible(extra,primitive,3-eye,[1.,1.],gap,limit);cases+=1
     assert not eligible(extra,primitive,eye,[1.,1.],limit+1,limit);cases+=1
     assert not eligible(extra,primitive,eye,[1.,1.],gap,limit,renderer=2,submesh=0);cases+=1
   before.append(a);after.append(b)
  rows.append({'sourceId':f['sourceId'],'ownerFromNativeBarycentric':eye,'actualSocketLimit':limit,'sourceNativeWitness':f['nativeSource'],'sourceFaceInterval':[1.,1.],
   'oldVisible16':before,'gatedCounterfactualVisible16':after,'sourceWitnessAlreadyMeasured':True})
  assert all(v==1 for v in after)
 cache={'sourceTopology':base['sourceTopology'],'sourceCacheKey':s.key,'sourceModelSHA256':read(R/'support-contract112/SOURCE112.json')['modelSHA256'],
  'maskIsAffiliationNotPigment':True,'policy':'Argon2.5 active exact source morph + ipsilateral majority/dominance; no two-ring extension',
  'primitiveCount':len(extra),'additionalBits':extra.tolist(),'requiresSameFrameSourceCertificate':True,'liveUploadImplemented':False}
 cp=H/'SHARED_SOURCE_MASK26.json';cp.write_text(json.dumps(cache,indent=2)+'\n',encoding='utf-8')
 result={'cacheSHA256':hashlib.sha256(cp.read_bytes()).hexdigest(),'additionalTriangles':int(np.sum(extra!=0)),
  'knownNineEligible':all(int(extra[v['primitive']-1])&2 for v in affiliation['rows']),
  'sameOriginalSourceCounterfactuals':rows,'occludedUnknownContralateralFarAndHairRejected':cases,
  'GPUOrUnityExecuted':False,'liveMaskChanged':False,
  'runtimeMissing':'PrepareCells113 must carry selected source sample/curve witness and strict visibility in reserved channel6; Write113/AssignedVisibility24 must reference the chosen part certificate. New mask may only affect destination, never source visibility production.',
  'certificateSemantics':'A selected original ray witness is not an all-footprint visibility proof. Do not substitute mass/colour similarity or positive partial visibility for exact source face visibility1.',
  'remainingPolicy':'Optional two-ring extension and full footprint transport of partially exposed source have not been adopted.'}
 (H/'SOURCE_GATE26.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'knownNineEligible':result['knownNineEligible'],'additionalTriangles':result['additionalTriangles'],
  'rejectedCounterexamples':cases,'oldVisible':[sum(v['oldVisible16'])for v in rows],'CPUCounterfactualVisible':[sum(v['gatedCounterfactualVisible16'])for v in rows], 'liveMaskChanged':False}))
if __name__=='__main__':main()
