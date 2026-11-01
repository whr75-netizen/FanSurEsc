from pathlib import Path
import json,sys,numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;sys.path.insert(0,str(ROOT/'native-feature89'))
from analyse89 import packet,geometry,visibility,joint,PARTS,rgb8
from surface_query90 import visibility_bounds,choose_joint_bounds

def actual_alpha_bounds(source):
 props=source['source'];assert props['mipmapCount']==1 and props['filter']=='Bilinear'and props['anisoLevel']<=1;assert props['factorAlpha']==1 and props['alphaTestKeyword']and props['cutoff']==.5
 result={}
 for row in source['queries']:
  if row['minAcrossMipCorners']==row['maxAcrossMipCorners']==1:result[row['id']]=[1.,1.]
  elif row['maxAcrossMipCorners']<props['cutoff']:result[row['id']]=[0.,0.]
  elif row['minAcrossMipCorners']>=props['cutoff']:result[row['id']]=[1.,1.]
  # Otherwise alpha-to-coverage derivatives may matter: leave unknown.
 return result

def main():
 query=json.loads((HERE/'QUERIES90.json').read_text());source=json.loads((HERE/'ALPHA_SOURCE90.json').read_text());assert source['success']and all(source['unchanged'].values());bounds=actual_alpha_bounds(source);old=ROOT/'native-feature89';state=json.loads(sorted((old/'capture89f').glob('STATE89*.json'))[-1].read_text());summary=[];trace=[];images=[]
 for frame in query['frames']:
  f=frame['frame'];path=Path(next(e['output']for e in state['sequencePackets']if e['frame']==f));d=packet(path);layers,physical,geo=geometry(d);vis,unknown=visibility(d,layers,physical);fixed=vis.copy();loCell=np.asarray(d['m']['retarget89']['bounds'][:2]);cx,cy=(np.array([5,0])-loCell).astype(int);lo=vis.copy();hi=vis.copy();lo[unknown]=0
  for q in query['rows']:
   if q['frame']!=f:continue
   proof=visibility_bounds(q['actualRaySkinHits'],q['whiteDepth'],bounds,cull_back=False);sx,sy=q['sample'];before=float(vis[2,sy,sx]);entry={'id':q['id'],'sample':q['sample'],'sourceBankTexel':q['sourceBankTexel'],'oldScalarVisibility':before,'skinVisibilityBounds':[proof['lower'],proof['upper']],'oldUnknown':bool(unknown[2,sy,sx]),'occluders':proof['hits']}
   if proof['upper']==0:fixed[2,sy,sx]=0;lo[2,sy,sx]=hi[2,sy,sx]=0;entry['reason']='actual opaque source triangle blocks ray; independent of Close getter'
   else:
    # Do not declare other unobserved occluders transparent, nor auto-open.
    lo[2,sy,sx]*=proof['lower'];hi[2,sy,sx]*=proof['upper'];entry['reason']='remaining non-skin uncertainty retained'
   trace.append(entry)
  oldColour,oldId,oldDetails,_=joint(layers,vis,False);newColour,newId,newDetails,_=joint(layers,fixed,False);sl=(slice(cy*4,cy*4+4),slice(cx*4,cx*4+4));rgba=np.stack([layers[p][0][sl][...,3].reshape(16)for p in [1,2,3]]);depth=np.stack([layers[p][1][sl][...,0].reshape(16)for p in [1,2,3]]);depth=np.where(depth>0,depth,np.inf);lower=np.stack([lo[p][sl].reshape(16)for p in [1,2,3]])*rgba;upper=np.stack([hi[p][sl].reshape(16)for p in [1,2,3]])*rgba;decision=choose_joint_bounds(lower,upper,depth,[1,4,6]);whiteBounds=decision['massBounds']['4'];row={'frame':f,'getterClose':frame['getterClose'],'evaluatedVertexDelta':frame['eyeVertexDelta'],'cellAbsolute':[5,0],'rasterCell':[int(cx),int(cy)],'oldChosenRole':int(oldId[cy,cx,0]),'oldMass':float(oldId[cy,cx,2]),'scalarCandidateAfterExactSkinRole':int(newId[cy,cx,0]),'robustDecision':decision,'whiteDefinitelyNotWinner':4 not in decision['possibleLabels'],'sourceWhiteRGBUnchanged':True,'stateGetterUsedByAlgorithm':False};summary.append(row)
  np.savez_compressed(HERE/f'focused-frame{f}.npz',oldColour=oldColour,oldIdentity=oldId,correctedColour=newColour,correctedIdentity=newId,whiteLower=lower[1],whiteUpper=upper[1])
 assert next(r for r in summary if r['frame']==140)['oldChosenRole']==4
 assert all(next(r for r in summary if r['frame']==f)['robustDecision']['massBounds']['4'][1]==0 for f in [140,141])
 assert all(next(r for r in summary if r['frame']==f)['whiteDefinitelyNotWinner']for f in [140,141])
 assert any(next(r for r in summary if r['frame']==f)['robustDecision']['massBounds']['4'][1]>0 for f in [135,142])
 target=next(q for q in query['rows']if q['id']=='f140-s54-21');t=next(q for q in trace if q['id']==target['id']);assert t['skinVisibilityBounds']==[0,0]and t['oldUnknown'];report={'status':'CLOSED_SCLERA_COUNTEREXAMPLE_RESOLVED_OFFLINE_NOT_PRODUCT_INTEGRATED','target':target,'targetCorrection':t,'frames':summary,'trace':trace,'alphaEvidence':{'queries':len(source['queries']),'GetPixelCalls':source['pixelGetterCalls'],'actualSourceMips':source['source']['mipmapCount'],'actualAlphaMode':source['source']['alphaMode'],'sourceModeReturnsOpaqueAfterPassedMask':True,'sourceTextureSource':'configured actual source material, public CPU getters; immutable model hash verified','noNewCapture':True},'pipelineFailure':'Nearest4x neighbour triangle3120 missed the real ray intersection3116; unknown was then treated as clear by the scalar joint allocator. The final89 validity mask already rejected this output, but the internal role remained white.','fix':'Query actual stored source triangles at the feature ray, preserve unknown as an interval, and prevent LUT emission until a winner is known. No Close conditional or forced sclera alpha edit.','limits':['Only the fixed cell(5,0) and its5 recorded states are corrected here. No whole89 candidate re-tuning or adoption.','Remaining native-lid/other-layer uncertainty and the colour for any vacated pixel remain independent.','No full movement or whole-eye production success claim.']};(HERE/'CLOSE_RESULT90.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'target':target['id'],'frames':summary,'alphaQueries':len(source['queries'])},indent=2))
if __name__=='__main__':main()
