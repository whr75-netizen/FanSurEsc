"""Classify the remaining56 native pixels; query the actual same-frame mesh."""
from pathlib import Path
import sys,json,numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'native-feature89'));sys.path.insert(0,str(ROOT/'eye-close90'))
from analyse89 import packet,geometry,visibility,mesh,PARTS
from analyse_capture68 import camera
from surface_query90 import ProjectedSurface

def main():
 old=ROOT/'native-feature89';s=json.loads(sorted((old/'capture89f').glob('STATE89*.json'))[-1].read_text());d=packet(Path(next(e['output']for e in s['sequencePackets']if e['frame']==140)));m=d['m'];expected=np.load(ROOT/'eye-close90/FOCUS_EXPECTED90.npz');selection=expected['owner'];bad=(selection[...,0]>0)&(selection[...,3]<0);h,w=bad.shape;yy,xx=np.mgrid[:h,:w];ref=m['nativeFinalReference89'];bottom=(np.stack([xx+ref['nativeROI'][0]+.5,yy+ref['nativeROI'][1]+.5],-1)-np.asarray(ref['origin']))/ref['scale']-np.asarray(m['trace86']['headJoinOffset'])-np.asarray(m['camera86']['deliveredDelta'][:2]);top=bottom.copy();top[...,1]=272-bottom[...,1];local=np.floor(top-np.asarray(m['retarget89']['anchor'])-np.asarray(m['retarget89']['bounds'][:2])).astype(int);eyes=bad&(selection[...,1]==6);missing=bad&(expected['colour'][...,3]==0);assert eyes.sum()==20 and missing.sum()==36
 cells=np.unique(local[eyes],axis=0);layers,physical,checks=geometry(d);oldVis,unknown=visibility(d,layers,physical);v,n,uv,tris,world=mesh(d['path']/'eye-evaluated.mesh');cam=camera(d['path']/'source.camera');wv=np.c_[v,np.ones(len(v))]@world.T;surfaces={part:ProjectedSurface(wv,uv,tris[part],cam['view'],cam['projection'],[480,272])for part in PARTS};queries=[];alpha=[];rows=[]
 for cx,cy in cells:
  pixels=np.argwhere(eyes&(local[...,0]==cx)&(local[...,1]==cy));detail={'rasterCell':[int(cx),int(cy)],'canonicalCellAbsolute':(np.asarray([cx,cy])+np.asarray(m['retarget89']['bounds'][:2])).astype(int).tolist(),'nativePixelsBottomLeft':pixels[:,::-1].tolist(),'parts':[]}
  for partIndex,part in enumerate(PARTS[1:],1):
   for sy in range(cy*4,cy*4+4):
    for sx in range(cx*4,cx*4+4):
     meta=layers[partIndex][1][sy,sx];rgba=layers[partIndex][0][sy,sx]
     if meta[0]<=0 or rgba[3]<=0:continue
     queryId=f'f140-c{cx}-{cy}-r{part}-s{sx}-{sy}';p=physical[partIndex,sy,sx];hits=[]
     for sourcePart,surface in surfaces.items():
      for hit in surface.hits(p):
       hit['sourcePart']=sourcePart;hit['queryKey']=queryId+'-p'+str(sourcePart)+'-t'+str(hit['primitive']);hits.append(hit)
       if hit['depth']<meta[0]-3e-5:alpha.append({'id':hit['queryKey'],'sourceSubMesh':sourcePart,'uv':hit['uv'],'primitive':hit['primitive'],'actualSourceQuery':p.tolist()})
     query={'id':queryId,'rasterCell':[int(cx),int(cy)],'part':part,'sample':[sx,sy],'actualSourceQuery':p.tolist(),'sourceDepth':float(meta[0]),'candidateAlpha':float(rgba[3]),'oldScalarVisibility':float(oldVis[partIndex,sy,sx]),'oldUnknown':bool(unknown[partIndex,sy,sx]),'hits':sorted(hits,key=lambda h:h['depth'])};queries.append(query)
  rows.append(detail)
 counts={'sourceId':m['sourceId'],'frame':140,'serial':m['mainSerial'],'remainingNativePixels':int(bad.sum()),'missingBackingNativePixels':int(missing.sum()),'unknownEyelineNativePixels':int(eyes.sum()),'eyelineLogicalCells':len(cells),'classification':'36 are missing backing, not visibility decisions.20 are5 native eyeline cells with unknown source visibility.','cells':rows,'geometryQueryCount':len(queries),'frontAlphaQueryCount':len(alpha),'geometryControl':checks,'otherMeshLimitation':'Only this evaluated face mesh is stored. Hair/body S4~S6 metadata are neighbouring samples, not exact source-ray geometry.'}
 (HERE/'CLASSIFICATION91.json').write_text(json.dumps(counts,indent=2)+'\n');(HERE/'QUERIES91.json').write_text(json.dumps({'sourceId':m['sourceId'],'frame':140,'serial':m['mainSerial'],'queries':queries},indent=2)+'\n');(HERE/'ALPHA_REQUEST91.json').write_text(json.dumps({'sourceRendererOrdinal':1,'meshGUID':'43db8c7a3695b164eb6112af020fb082','modelAsset':'Assets/EUnityValidation01/VRoidSampleA144/Inputs/AvatarSample_A.vrm','modelSHA256':'0e2fd0fc90308da3172ecf4e674fdeb4f054ebd617005caa5b997a2ca339cce3','queries':alpha},indent=2)+'\n');np.savez_compressed(HERE/'FROZEN_INPUT91.npz',selection=selection,baseline=expected['baseline'],oldColour=expected['colour'],local=local,missing=missing,eyes=eyes,**{f'rgba{p}':layers[i][0]for i,p in enumerate(PARTS)},**{f'meta{p}':layers[i][1]for i,p in enumerate(PARTS)})
 print(json.dumps({k:v for k,v in counts.items()if k not in ['cells','geometryControl']},indent=2))
if __name__=='__main__':main()
