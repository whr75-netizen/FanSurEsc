"""Add original frozen-input Evaluate kernel to the owned diagnostic asset."""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent
s=(HERE/'EyeFeature348.before76.compute').read_text();start=s.rfind('[numthreads',0,s.index('void Evaluate'));end=s.index('[numthreads',s.index('void UnpackA')-30)
k=s[start:end];assert 'void Evaluate('in k and 'UnpackA'not in k
k=k.replace('void Evaluate(', 'void OriginalEvaluate76(').replace('int2 p=id.xy;', 'int2 p=_ProbeROI76.xy+id.xy;if(any(id.xy>=_ProbeROI76.zw))return;int localIndex76=(p.y-_ProbeROI76.y)*_ProbeROI76.z+p.x-_ProbeROI76.x;')
for texture,field in [('Colour','colour'),('Owner','owner'),('Meta','meta'),('UV','uv'),('Domain','domain')]:k=k.replace('_Baseline'+texture+'348.Load(int3(p,0))','_Baseline76[localIndex76].'+field)
k=k.replace('_RecordsWrite348[p.y*480+p.x]', '_RecordsWrite348[localIndex76]')
assert 'ComposedSource76'not in k and 'p=id.xy'not in k and '_BaselineColour348.Load'not in k
probe=(HERE/'BaselineProbe76.final.compute').read_text();out='#pragma kernel OriginalEvaluate76 ORIGINAL76\n'+probe+'\n// Original algorithm, only dispatch/record indexing and frozen baseline inputs adapted.\n'+k
(HERE/'BaselineProbe76.paired.compute').write_bytes(out.encode());(HERE/'FROZEN_CONTRACT76.json').write_text(json.dumps({'originalProductSHA256':hashlib.sha256((HERE/'EyeFeature348.before76.compute').read_bytes()).hexdigest(),'changes':['Global p recovered from compact dispatch ROI','Only five baseline loads redirected to actual pre-Evaluate captured buffer','Only record stores use compact owned output buffer'],'originalAlgorithmBodyOtherwiseUnchanged':True,'bufferStride':256,'maxOriginalReadbackBytes':24*16*256,'noProductTextureWrites':True},indent=2)+'\n');print('Prepared frozen original diagnostic kernel')
