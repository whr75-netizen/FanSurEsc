from pathlib import Path
import json,sys,numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;sys.path.insert(0,str(ROOT/'native-feature89'))
from analyse89 import packet,geometry,mesh,PARTS,PROJ
from analyse_capture68 import camera
from surface_query90 import ProjectedSurface
def main():
 b=ROOT/'native-feature89';s=json.loads(sorted((b/'capture89f').glob('STATE89*.json'))[-1].read_text());rows=[];alpha=[];skins=[]
 for frame in [135,138,140,141,142]:
  path=Path(next(e['output']for e in s['sequencePackets']if e['frame']==frame));d=packet(path);m=d['m'];layers,physical,check=geometry(d);v,n,uv,tris,world=mesh(path/'eye-evaluated.mesh');cam=camera(path/'source.camera');wv=np.c_[v,np.ones(len(v))]@world.T;skin=ProjectedSurface(wv,uv,tris[3],cam['view'],cam['projection'],[480,272]);lo=np.asarray(m['retarget89']['bounds'][:2]);cx,cy=(np.array([5,0])-lo).astype(int);meta=layers[2][1];sampleIds=[]
  for sy in range(cy*4,cy*4+4):
   for sx in range(cx*4,cx*4+4):
    if meta[sy,sx,0]<=0:continue
    owner=int(round(float(meta[sy,sx,2])));source=np.r_[layers[2][2][sy,sx,:3],1]@PROJ[owner];hits=skin.hits(physical[2,sy,sx]);queryId=f'f{frame}-s{sx}-{sy}'
    for hit in hits:
     hit['queryKey']=queryId+'-skin'+str(hit['primitive'])
     if hit['depth']<meta[sy,sx,0]-3e-5:alpha.append({'id':hit['queryKey'],'uv':hit['uv'],'frame':frame,'primitive':hit['primitive']})
    rx,top,rw,rh=m['eyeFeature']['roiTopLeft'];p=physical[2,sy,sx];xx=int(np.floor((p[0]-rx)*4));yy=rh*4-1-int(np.floor((p[1]-top)*4));nearUV=d['a']['S0-uv'][yy,xx];nearMeta=d['a']['S0-meta'][yy,xx];observed=np.rint(d['a']['S0-uv'][...,2]).astype(int)-1;valid=d['a']['S0-meta'][...,0]>0;signs=skin.sign[np.clip(observed[valid],0,len(skin.tri)-1)];fronts=d['a']['S0-point'][...,3][valid]>0
    row={'id':queryId,'frame':frame,'sourceId':m['sourceId'],'canonicalCellAbsolute':[5,0],'rasterCell':[int(cx),int(cy)],'sample':[sx,sy],'physicalXYTopLeft':p.tolist(),'whiteDepth':float(meta[sy,sx,0]),'whitePrimitive':int(round(float(layers[2][3][sy,sx,2]))),'whiteUV':layers[2][3][sy,sx,:2].tolist(),'sourceBankTexel':np.floor(source).astype(int).tolist(),'owner':owner,'whiteAlpha':float(layers[2][0][sy,sx,3]),'oldNeighbourSkin':{'sampleMemory':[xx,yy],'primitive':int(round(float(nearUV[2]))),'depth':float(nearMeta[0]),'alpha':float(nearMeta[3]),'uv':nearUV[:2].tolist()},'actualRaySkinHits':hits,'observedFrontWinding':np.unique(signs[fronts]).astype(int).tolist(),'candidateColourRGBA':layers[2][0][sy,sx].tolist()};rows.append(row);sampleIds.append(queryId)
  skins.append({'frame':frame,'getterClose':m['eyeFeature']['closeMorphs']['Fcl_EYE_Close'],'eyeVertexDelta':next(x['maxVertexDeltaFromInitialOpenMetres']for x in json.loads((b/'VALIDATION89.json').read_text())['blinkEvaluatedGeometry']if x['frame']==frame),'queries':sampleIds,'matrixWorld':world.tolist(),'cameraView':cam['view'].tolist()})
  if frame==140:
   # Paired actual alpha witnesses for the true3116 primitive, not an inferred label.
   a=d['a'];valid=(a['S0-meta'][...,0]>0)&(np.rint(a['S0-uv'][...,2])==3116)
   for y,x in np.argwhere(valid)[:4]:alpha.append({'id':f'witness140-{x}-{y}','uv':a['S0-uv'][y,x,:2].tolist(),'frame':frame,'primitive':3116,'actualGPUAlpha':float(a['S0-meta'][y,x,3]),'actualGPURGBA':a['S0-rgba'][y,x].tolist()})
 (HERE/'QUERIES90.json').write_text(json.dumps({'status':'stored89 only; exact native geometry query, alpha not yet supplied','fixedSourceFeature':'eye1/role4/bank222,80; canonical cell(5,0)','rows':rows,'frames':skins},indent=2)+'\n');(HERE/'ALPHA_REQUEST90.json').write_text(json.dumps({'queries':alpha,'sourceRendererOrdinal':1,'sourceSubMesh':3,'meshGUID':'43db8c7a3695b164eb6112af020fb082','modelAsset':'Assets/EUnityValidation01/VRoidSampleA144/Inputs/AvatarSample_A.vrm','modelSHA256':'0e2fd0fc90308da3172ecf4e674fdeb4f054ebd617005caa5b997a2ca339cce3','sourceImageSHA256':'0d10d325f6db38fef89de680e3ad83b23034aa502be8ef79d85ae90f2e67d96e'},indent=2)+'\n');print(json.dumps({'whiteQueries':len(rows),'alphaQueries':len(alpha),'frames':[x['frame']for x in skins],'target':next(x for x in rows if x['id']=='f140-s54-21')},indent=2))
if __name__=='__main__':main()
