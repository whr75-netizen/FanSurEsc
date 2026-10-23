from pathlib import Path
import struct,json,math
import numpy as np
O=Path(__file__).resolve().parent;R=O/'Reentry530B'
def read(stage):
    b=(R/f'0_{stage}_SPARSE.bin').read_bytes();n,physical=struct.unpack_from('<2i',b);stride=56+16*physical;assert len(b)==8+n*stride
    out=[]
    for i in range(n):
        x,y=struct.unpack_from('<2i',b,8+i*stride);v=np.frombuffer(b,'<f4',12+4*physical,16+i*stride).reshape(-1,4)
        out.append({'xy':[x,y],'rgba':v[0].tolist(),'meta':v[1].tolist(),'uv':v[2].tolist(),'physical':v[3].tolist()if physical else None})
    return out
stages={n:read(n)for n in ['HEAD_SOURCE','HEAD_PROVIDER8','HEAD_PREPARED','MAIN_FINAL','HEAD_LEGACY_CLASS']}
def err(a,b):return float(np.max(abs(np.array(a)-np.array(b))))
def at(stage,xy):return next((p for p in stages[stage]if p['xy']==xy),None)
matches=[];unmatched=[]
for p in stages['HEAD_PROVIDER8']:
    s=min(stages['HEAD_SOURCE'],key=lambda s:err(s['uv'][:2],p['uv'][:2]));uvError=err(s['uv'][:2],p['uv'][:2])
    if uvError>1e-5:unmatched.append({'xy':p['xy'],'nearestUVError':uvError});continue
    litError=err(p['rgba'][:3],s['rgba'][:3]);shadeError=err(p['rgba'][:3],np.array(s['rgba'][:3])*.72)
    row={'providerXY':p['xy'],'sourceXY':s['xy'],'sameMaterialUVError':uvError,'sourceRGBA':s['rgba'],'providerRGBA':p['rgba'],
         'sourceMeta':s['meta'],'providerMeta':p['meta'],'sourcePhysical':s['physical'],'litError':litError,'own072Error':shadeError,
         'classification':'OWN072_SHADE'if shadeError<.001 else'OWN_LIT'if litError<.001 else'OTHER_UNRESOLVED'}
    c=at('HEAD_LEGACY_CLASS',s['xy'])
    if c:row['sourceLegacyClassifier']=c['meta'];row['sourceLegacyRGB']=c['rgba'];row['legacyUVError']=err(c['uv'][:2],s['uv'][:2])
    for name in ['HEAD_PREPARED','MAIN_FINAL']:
        q=min(stages[name],key=lambda q:err(q['uv'][:2],p['uv'][:2]))
        if q:row[name]={'xy':q['xy'],'coordinateDelta':[q['xy'][i]-p['xy'][i]for i in range(2)],'rgba':q['rgba'],'uvError':err(q['uv'][:2],p['uv'][:2]),'signedDepthDifference':q['meta'][0]-p['meta'][0],'providerRGBError':err(q['rgba'][:3],p['rgba'][:3])}
    matches.append(row)
stats={n:{'skinRole4Count':len(rows),'nearNeutralCount':sum(max(p['rgba'][:3])-min(p['rgba'][:3])<1e-5 for p in rows),
          'minRGBChroma':min(max(p['rgba'][:3])-min(p['rgba'][:3])for p in rows),'maxRGBChroma':max(max(p['rgba'][:3])-min(p['rgba'][:3])for p in rows)}for n,rows in stages.items()if n!='HEAD_LEGACY_CLASS'}
counts={name:sum(p['classification']==name for p in matches)for name in ['OWN072_SHADE','OWN_LIT','OTHER_UNRESOLVED']}
rest=json.loads((R/'status.json').read_text())
result={'status':'SPARSE_FLOAT_RECOVERED_NO_PRODUCT_PATCH','scope':'one controlled paused-entry reentry first produced render; initial2 PNGs retained; no Walk/full-loop capture',
        'startupTransitions':rest['transitions'],'sampleCounts':stats,'sameMaterialUVMatches':len(matches),'providerUVUnmatched':unmatched,'shadeClassifications':counts,
        'matches':matches,'limits':['UV match proves intrinsic texture lookup equivalence, not identical triangle topology between source and provider meshes.',
        'Initial530 nested custom lists were omitted by JSON serializer; sparse530B is independent binary evidence.',
        'Controlled pause may warm asynchronous resources; unpaused cold-load timing equivalence not established.',
        'Canvas before presentSerial>0 is an observed startup readiness gap; not established as a face-only gray cause.',
        'Reported recurring gray transition and other-session trigger are not automatically reproduced by an existing .72 shade.']}
(O/'SPARSE_REVIEW530.json').write_bytes(json.dumps(result,indent=2).encode())
print(json.dumps({'status':result['status'],'counts':stats,'UVMatches':len(matches),'unmatched':len(unmatched),'shadeClassifications':counts,
                 'examples':[{k:p[k]for k in ['providerXY','sameMaterialUVError','sourceRGBA','providerRGBA','own072Error','classification','sourceLegacyClassifier']if k in p}for p in matches[:8]]}))
