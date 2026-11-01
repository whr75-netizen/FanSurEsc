"""Existing real87 consecutive inputs: source-UV carrier correspondence only.
Not a new renderer, final colour/cluster stability test, or history RGB filter.
"""
from pathlib import Path
import json,sys,numpy as np
from native109 import H,R,read
from geometry109 import transform,physical,FaceRays
from io109 import mesh,entries,packet

def main():
    cache=read(H/'NATIVE_CACHE109.json');domain=np.load(H/'NATIVE_DOMAIN109.npz');seq=entries(H,'87',lambda:read(sorted((R/'feature-audit86/run87').glob('STATE87*.json'))[-1])['sequencePackets']);result=[];arrays={};previous=None
    refs=[]
    for c in cache['curves']:
        points=[p for p in c['points']if not p.get('unresolved')];refs.append((c['owner'],np.array([p['vertices']for p in points]),np.array([p['barycentric']for p in points])))
    for e in seq:
        if e['testStage82']not in ['walk','sweep','blink']:continue
        p=packet(H,e,'87');m=read(p/'RAW_MANIFEST.json');identity,model,current,uv,indices=mesh(p/'eye-evaluated.mesh');assert identity['sourceId']==m['sourceId'];assert m['eyeFeature']['topologySHA256']==cache['sourceTopologySHA256'];assert np.array_equal(uv,domain['uv'])and np.array_equal(indices[6],domain['triangles'])
        world=transform(model,current)[:,:3];head=np.array(m['eyeFeature']['headMatrix']).reshape(4,4,order='F');local=transform(np.linalg.inv(head),world);view=np.array(m['motion82']['worldView']).reshape(4,4,order='F');projection=np.array(m['motion82']['worldProjection']).reshape(4,4,order='F');xy,z,cw=physical(view,projection,world);ctx={'indices':indices,'physicalXY':xy,'depth':z,'physicalW':cw,'view':view,'projection':projection};rays=FaceRays(ctx);row={'sourceId':m['sourceId'],'frame':m['frameIndex'],'serial':m['hostMainRenderSerial'],'sourceFrame':m['sourceFrame'],'deltaTime':m['deltaTime'],'stage':e['testStage82'],'evaluatedClose':m['eyeFeature']['closeMorphs']['Fcl_EYE_Close'],'eyes':[]};currentArrays=[]
        for owner,ids,bary in refs:
            points=np.einsum('ij,ijk->ik',bary,world[ids]);screen,depth,_=physical(view,projection,points);visibility=rays.query(points);currentArrays.append(points)
            row['eyes'].append({'owner':owner,'pointIdentities':len(points),'pointMeanPhysicalScreen':screen.mean(0).tolist(),'sameCurrentFacePotentiallyOccludedPoints':sum(not v['geometricallyClear']for v in visibility),'geometryVisibilityIsNotFullMaterialHairVisibility':True})
            arrays[f'f{m["frameIndex"]}-eye{owner}-world']=points;arrays[f'f{m["frameIndex"]}-eye{owner}-physical']=screen
        allpoints=np.concatenate(currentArrays);row['adjacentPreviousFrame']=previous['frame']if previous is not None and m['frameIndex']==previous['frame']+1 else None
        if row['adjacentPreviousFrame']is not None:
            row['maxCorrespondedWorldMotionMetres']=float(np.linalg.norm(allpoints-previous['points'],axis=1).max());row['correspondedPointIdentityChanges']=0
        previous={'frame':m['frameIndex'],'points':allpoints};result.append(row)
    np.savez_compressed(H/'REAL_CARRIER_TRAJECTORIES109.npz',**arrays)
    out={'sourceSequence':result[0]['sourceId'].rsplit('-frame',1)[0],'originalInputPackets':len(result),'newFrames':0,'sourceIdentityNotScreenRGB':True,'pointsPerFrame':sum(len(x[1])for x in refs),'adjacentPairs':sum(x['adjacentPreviousFrame']is not None for x in result),'frames':result,
      'limits':['Native UV source correspondence under actual evaluated deformation is verified; final joint cell allocation is not run on these frames.','Two-sided geometric face hits are potential blockers, not a replacement for actual material/culling/hair coverage.','No claim that physical sweep is a validated full0..1pixel allocation sweep.','SourceIDs are from real87 and are never presented as actual107 frames.']}
    (H/'REAL_CORRESPONDENCE109.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps({k:v for k,v in out.items()if k!='frames'}|{'blink':[(r['frame'],r['evaluatedClose'],[e['sameCurrentFacePotentiallyOccludedPoints']for e in r['eyes']])for r in result if r['stage']=='blink']}))
if __name__=='__main__':main()
