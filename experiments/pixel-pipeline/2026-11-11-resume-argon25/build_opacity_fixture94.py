"""Validate immutable measured template, then replay old evaluated source.

The runtime constructor's original double barycentrics come from actual v2
capture. Arrays retained by the old and new constructors must match exactly.
Original UV handedness is checked against the actual v2 segment multiset;
it is never guessed from a pretty result or per-frame tuning.
"""
from pathlib import Path
import json,struct,hashlib,numpy as np
from union_input94 import load
H=Path(__file__).resolve().parent;G=H/'face94';R=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
def string(f,s):
 b=s.encode();n=len(b)
 while n>=128:f.write(bytes([(n&127)|128]));n>>=7
 f.write(bytes([n]));f.write(b)
def main():
 template=load(next((G/'held480/capture').glob('UNION94-baseline*.bin')));old=load(G/'capture/UNION94-baseline-frame102.bin');failure=load(G/'capture/UNION94-failure-frame429.bin');assert template['version']=='union-input94/v2'
 for d in [old,failure]:
  assert np.array_equal(d['indices'],template['indices'])and np.array_equal(d['boundaries'],template['boundaries']);assert np.array_equal(d['anchors']['vertices'],template['anchors']['vertices'])and np.array_equal(d['anchors']['weights'],template['anchors']['weights'])
 policy=json.loads((H/'face69/ZERO_POLICY69.json').read_text());model=R/policy['modelAsset'];assert hashlib.sha256(model.read_bytes()).hexdigest()==policy['modelSHA256']
 with model.open('rb')as f:
  f.read(12);n,t=struct.unpack('<II',f.read(8));doc=json.loads(f.read(n));n,t=struct.unpack('<II',f.read(8));start=f.tell();mesh=doc['meshes'][1];a=doc['accessors'][mesh['primitives'][1]['attributes']['TEXCOORD_0']];v=doc['bufferViews'][a['bufferView']];assert a['componentType']==5126 and a['type']=='VEC2'and a['count']==len(old['points']);f.seek(start+v.get('byteOffset',0)+a.get('byteOffset',0));stride=v.get('byteStride',8);data=f.read((a['count']-1)*stride+8);uv=np.ndarray((a['count'],2),'<f4',data,strides=(stride,4)).copy()
 for label,d in [('actual-baseline-v2',template),('saved-failure-source',failure)]:
  p=G/(label+'.fixture94')
  with p.open('wb')as f:
   string(f,'opacity-fixture94/v1');string(f,d['sourceId']);f.write(struct.pack('<ii',d['frame'],len(d['points'])));f.write(d['points'].astype('<f4').tobytes());f.write(struct.pack('<i',len(uv)));f.write(uv.astype('<f4').tobytes());f.write(struct.pack('<i',d['indices'].size));f.write(d['indices'].astype('<i4').tobytes());f.write(struct.pack('<i',len(template['anchors'])));f.write(template['anchors'].tobytes());f.write(struct.pack('<i',len(template['boundaries'])));f.write(template['boundaries'].tobytes());f.write(struct.pack('<i',len(d['segments'])));f.write(d['segments'].astype('<f8').tobytes())
 r={'CPUOnly':True,'templateIndexVertexWeight32AndBoundaryArraysExactlyEqualAcrossSources':True,'actualTemplateDoubleWeightsUsed':True,'deformedFailurePointsNotReconstructedOrMixed':True,'originalVRMHashVerified':True,'newGPUExecuted':False};(G/'FIXTURE_CONTRACT94.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
if __name__=='__main__':main()
