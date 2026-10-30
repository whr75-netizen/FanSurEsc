"""Analytic hair-geometry visibility along frozen adjacent-cell segments.
Uses matched evaluated vertices, all double-sided opaque hair triangles, no GPU.
Does not extrapolate just the two endpoint triangles or equate shading normals to planes.
"""
from pathlib import Path
import json,math,hashlib
import numpy as np
from PIL import Image,ImageDraw
import candidate as c
R=c.R;O=R/'geometry-export'
class Geometry:
 def __init__(self):
  self.source=json.loads((R/'source-export/bundle/prelight-source.json').read_text());self.frame=json.loads((R/'source-export/bundle/frame-source-data.json').read_text());cap=json.loads((R/'source-export/CAPTURE.json').read_text());self.view=np.array(cap['view']).reshape(4,4,order='F');self.proj=np.array(cap['projection']).reshape(4,4,order='F');d=np.load(O/'EVALUATED.npz');self.world=d['worldVertices'];self.uv=d['uv'];v=np.c_[self.world,np.ones(len(self.world))]@self.view.T;q=v@self.proj.T;self.xy=np.c_[(q[:,0]/q[:,3]*.5+.5)*480,(.5-q[:,1]/q[:,3]*.5)*272]-[204,26];self.depth=-v[:,2];top=np.load(R/'SOURCE_TOPOLOGY.npz');faces=[];role=[];primitive=[];chart=[]
  for r in range(11,15):
   for i,t in enumerate(d['triangles'+str(r)]):faces.append(t);role.append(r);primitive.append(i);chart.append(r*10000+int(top['welded'+str(r)][i]))
  self.faces=np.array(faces);self.role=np.array(role);self.primitive=np.array(primitive);self.chart=np.array(chart);self.p=self.xy[self.faces];self.z=self.depth[self.faces];self.origin=self.p[:,0];a=self.p[:,1]-self.origin;b=self.p[:,2]-self.origin;det=a[:,0]*b[:,1]-a[:,1]*b[:,0];self.valid=np.abs(det)>np.finfo(float).eps*np.maximum(np.sum(a*a,axis=1)+np.sum(b*b,axis=1),1);self.inv=np.zeros((len(det),2,2));self.inv[self.valid,0,0]=b[self.valid,1]/det[self.valid];self.inv[self.valid,0,1]=-b[self.valid,0]/det[self.valid];self.inv[self.valid,1,0]=-a[self.valid,1]/det[self.valid];self.inv[self.valid,1,1]=a[self.valid,0]/det[self.valid];self.tolerance=float(np.max(np.spacing(self.depth.astype(np.float32)))*8)
 def bary(self,p):
  x=np.einsum('nij,nj->ni',self.inv,np.asarray(p)-self.origin);return np.c_[1-x.sum(axis=1),x]
 def hit(self,p):
  b=self.bary(p);valid=self.valid&(b.min(axis=1)>=-2e-12);z=np.sum(b*self.z,axis=1);ix=np.flatnonzero(valid)
  if not len(ix):return {'charts':[],'depth':None,'triangles':[]}
  zz=z[ix].min();front=ix[z[ix]<=zz+self.tolerance];return {'charts':sorted(int(v) for v in np.unique(self.chart[front])),'depth':float(zz),'triangles':[int(i) for i in front]}
 def envelope(self,A,B):
  ba=self.bary(A);bb=self.bary(B);delta=bb-ba;lo=np.zeros(len(ba));hi=np.ones(len(ba));valid=self.valid.copy()
  for j in range(3):
   rising=delta[:,j]>0;falling=delta[:,j]<0;zero=~(rising|falling);lo[rising]=np.maximum(lo[rising],-ba[rising,j]/delta[rising,j]);hi[falling]=np.minimum(hi[falling],-ba[falling,j]/delta[falling,j]);valid[zero&(ba[:,j]<0)]=False
  ix=np.flatnonzero(valid&(hi>lo)&(hi>0)&(lo<1));lo=np.maximum(lo[ix],0);hi=np.minimum(hi[ix],1);start=np.sum(ba[ix]*self.z[ix],axis=1);slope=np.sum(delta[ix]*self.z[ix],axis=1);points=[0.,1.,*lo.tolist(),*hi.tolist()]
  for i in range(len(ix)):
   for j in range(i+1,len(ix)):
    den=slope[i]-slope[j]
    if den==0:continue
    # Include the numerical tie band's two boundaries as well as exact order exchange.
    for difference in [0.,-self.tolerance,self.tolerance]:
     t=(start[j]-start[i]+difference)/den
     if max(lo[i],lo[j])<t<min(hi[i],hi[j]):points.append(float(t))
  points=sorted(set(points));runs=[]
  for a,b in zip(points,points[1:]):
   if b-a<=1e-11:continue
   t=(a+b)*.5;active=np.flatnonzero((lo<t)&(hi>t));ids=[];frontTriangles=[];depth=None
   if len(active):
    depths=start[active]+t*slope[active];depth=depths.min();front=active[depths<=depth+self.tolerance];ids=sorted(int(v) for v in np.unique(self.chart[ix[front]]));frontTriangles=sorted(int(v) for v in ix[front])
   if runs and runs[-1]['triangles']==frontTriangles:runs[-1]['end']=float(b)
   else:runs.append({'start':float(a),'end':float(b),'charts':ids,'triangles':frontTriangles})
  events=[]
  for left,right in zip(runs,runs[1:]):
   t=(left['end']+right['start'])*.5
   def limit(run):
    mid=(run['start']+run['end'])*.5;active=np.flatnonzero((lo<mid)&(hi>mid))
    if not len(active):return None
    depths=start[active]+mid*slope[active];front=active[depths<=depths.min()+self.tolerance];return float(np.min(start[front]+t*slope[front]))
   za,zb=limit(left),limit(right);jump=None if za is None or zb is None else abs(zb-za);common=set(left['charts'])&set(right['charts'])
   kind='uncovered hair projection interval' if za is None or zb is None else 'resolved front/back depth step' if jump>self.tolerance else 'same-chart transition' if common else 'depth-continuous ownership exchange or numerically tied overlap'
   events.append({'t':float(t),'beforeCharts':left['charts'],'afterCharts':right['charts'],'depthLeft':za,'depthRight':zb,'depthJump':jump,'sameChart':bool(common),'kind':kind})
  kinds={e['kind'] for e in events};singleOwners={r['charts'][0] for r in runs if len(r['charts'])==1};category='projected uncovered hair gap' if any(not r['charts'] for r in runs) else 'front/back occlusion' if 'resolved front/back depth step' in kinds else 'depth-continuous ownership change' if len(singleOwners)>1 else 'depth-tied chart overlap' if any(len(r['charts'])>1 for r in runs) else 'same front source chart throughout'
  return {'category':category,'runs':runs,'events':events,'intersectingTriangles':len(ix),'analyticBreakpoints':len(points),'multipleSubpixelOwners':len({q for r in runs for q in r['charts']})>2}
def main():
 G=Geometry();s,f,m,g,rgb,n,z=c.load();old=json.loads((R/'structure-v2/EDGE_ABLATION.json').read_text());receipt=json.loads((O/'RECEIPT.json').read_text());prior=json.loads((R/'source-export/CAPTURE.json').read_text());rows=[];mismatches=[];depthErrors=[];projected={row['i']:np.array([row['i']%32+.5,row['i']//32+.5])+row['screenDelta'] for row in json.loads((O/'SOURCE_MATCH_ROWS.json').read_text())};top=np.load(R/'SOURCE_TOPOLOGY.npz')
 for i,cell in enumerate(s['cells']):
  if not cell:continue
  x,y=i%32,i//32;hit=G.hit(projected[i]);expected=cell['materialId']*10000+int(top['welded'+str(cell['materialId'])][cell['primitiveId']]);err=None if hit['depth'] is None else abs(hit['depth']-cell['depthHeadCamera']);depthErrors.append(err or 0)
  if expected not in hit['charts'] or err is None or err>G.tolerance:mismatches.append({'cell':[x,y],'expectedChart':expected,'expectedDepth':cell['depthHeadCamera'],'hit':hit,'depthError':err})
 if mismatches:raise RuntimeError('CPU endpoint visibility not matched; inspect instead of adopting: '+json.dumps(mismatches[:5]))
 allRows=[]
 for edge in old:
  a=projected[edge['a'][1]*32+edge['a'][0]];b=projected[edge['b'][1]*32+edge['b'][0]];env=G.envelope(a,b);rows.append({**edge,'queryA':a.tolist(),'queryB':b.tolist(),'oldUnknown':edge['visibility'].startswith('unknown'),'evaluatedGeometry':env})
 allRows=rows;rows=[row for row in allRows if not row['sameSourceChart']]
 categories={key:sum(row['evaluatedGeometry']['category']==key for row in rows) for key in sorted({row['evaluatedGeometry']['category'] for row in rows})};oldUnknown={key:sum(row['oldUnknown'] and row['evaluatedGeometry']['category']==key for row in rows) for key in categories}
 binding={'parentSourceId':s['sourceId'],'captureUTC':receipt['utc'],'parentCaptureUTC':s['timestampUTC'],'sameCaptureTimeOrFrameCounter':False,'bindingKind':'reproduced evaluated geometry matched against frozen source samples','queryCoordinates':'actual saved source UV barycentric point projected through the original camera; not silently equated to the unsnapped ideal cell centre','bonesExact':receipt['bones']==prior['bonesA'],'vertexCount':len(G.world),'CPUBytes':(O/'EVALUATED_HAIR.bin').stat().st_size,'worldPositionBytes':len(G.world)*12,'screenMatchRows':'SOURCE_MATCH_ROWS.json','all368EndpointFrontChartAndDepthMatched':not mismatches,'maxEndpointDepthError':max(depthErrors),'depthClassificationFloatBound':G.tolerance,'doubleSided':True,'alphaEvidence':'all original hair textures alpha255, original factor alpha1 and glTF doubleSided true; hair-only visibility, not unseen face/body geometry','evaluatedBinarySHA256':hashlib.sha256((O/'EVALUATED_HAIR.bin').read_bytes()).hexdigest(),'vertexSource':'existing transient CurrentSurface330 BakeMesh output; no original source mesh setters','explicitRenderCalls':receipt['explicitRenders'],'readbacks':receipt['readbacks'],'runtimePoseRestored':receipt['runtimeRestored']};(O/'GEOMETRY_BINDING.json').write_text(json.dumps(binding,indent=2));(O/'EDGE_CLASSIFICATION.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2));(O/'EDGE_CLASSIFICATION_ALL.json').write_text(json.dumps(allRows,ensure_ascii=False,indent=2));summary={'sourceId':s['sourceId'],'allInternalHairEdges':len(allRows),'sameChartSelfOcclusionEdges':sum(row['sameSourceChart'] and row['evaluatedGeometry']['category']=='front/back occlusion' for row in allRows),'crossChartEdges':len(rows),'formerlyUnknownEdges':sum(row['oldUnknown'] for row in rows),'categoriesAll':categories,'categoriesFormerlyUnknown':oldUnknown,'multipleSubpixelSurfaceEdges':sum(row['evaluatedGeometry']['multipleSubpixelOwners'] for row in rows),'remainingMissingTrianglePlanes':0,'scope':'exact evaluated hair-vs-hair geometry between the original shader source points of adjacent cells; outer semantic mask fixed, face/body between cells not rendered/exported'};(O/'SUMMARY.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary));visual(rows,G,f)
def visual(rows,G,f):
 size=(512,640);base=np.asarray(Image.open(R/'structure-v2/source-unlit-1x.png').convert('RGBA'));im=Image.new('RGB',size,(30,33,40));layer=Image.fromarray(base).resize(size,Image.Resampling.NEAREST);im.paste(layer,mask=layer);draw=ImageDraw.Draw(im);colours={'front/back occlusion':(255,80,120),'projected uncovered hair gap':(255,195,40),'depth-continuous ownership change':(50,220,200),'depth-tied chart overlap':(170,120,245),'same front source chart throughout':(130,150,160)}
 for row in rows:
  a,b=np.array(row['a']),np.array(row['b']);mid=(a+b+1)*8;d=(b-a)*7;t=np.array([-d[1],d[0]]);draw.line([tuple(mid-t),tuple(mid+t)],fill=colours[row['evaluatedGeometry']['category']],width=2)
 im.save(O/'evaluated-visibility.png')
if __name__=='__main__':main()
