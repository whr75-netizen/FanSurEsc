from pathlib import Path
import json,struct,numpy as np
H=Path(__file__).resolve().parent;G=H/'face40';C=G/'motion/capture'
def geometry(path):
 f=path.open('rb')
 def string():
  n=0;shift=0
  while True:
   b=f.read(1)[0];n|=(b&127)<<shift
   if b<128:break
   shift+=7
  return f.read(n).decode()
 def integer():return struct.unpack('<i',f.read(4))[0]
 assert string()=='face-source-geometry40/v1';sid=string();model=string();frame=integer();n=integer();sm=integer();view=np.frombuffer(f.read(64),'<f4').reshape(4,4,order='F');vp=np.frombuffer(f.read(64),'<f4').reshape(4,4,order='F');dt=np.dtype([('world','<f4',(3,)),('head','<f4',(2,)),('weld','<i4')]);points=np.frombuffer(f.read(n*24),dt).copy();indices=[np.frombuffer(f.read((count:=integer())*4),'<i4').reshape(-1,3).copy()for _ in range(sm)];assert f.read()==b'';f.close();return {'sourceId':sid,'model':model,'frame':frame,'points':points,'indices':indices,'view':view,'vp':vp}
def contour(g):
 a=g['points']['head'].astype(float);w=g['points']['weld'];tri=g['indices'][3];p=a[tri];d=p[:,1]-p[:,0];e=p[:,2]-p[:,0];sign=np.sign(d[:,0]*e[:,1]-d[:,1]*e[:,0]);edges={}
 for ti,t in enumerate(tri):
  for x,y in zip(t,np.roll(t,-1)):
   lo,hi=sorted([int(w[x]),int(w[y])])
   if lo==hi:continue
   key=(lo,hi)
   if key not in edges:edges[key]={'a':int(x),'b':int(y),'triangles':[]}
   edges[key]['triangles'].append(ti)
 selected=[]
 for id,(key,edge)in enumerate(sorted(edges.items()),1):
  t=edge['triangles']
  if len(t)==2 and sign[t[0]]!=sign[t[1]]:selected.append({'id':id,'key':key,**edge})
 return selected
def main():
 r=json.loads((C/'COMPLETE.json').read_text());rows=[];base=None
 for frame in r['frames']:
  n=frame['frame'];g=geometry(C/('geometry-frame'+str(n)+'.bin'));assert g['sourceId']==frame['sourceId'];points=g['points'];head=points['head'].astype(float);sel=contour(g);assert len(sel)==frame['frameInfo']['geometryContour40']['lineSegments'];w=points['weld'];nodes={}
  for e in sel:
   for v in [e['a'],e['b']]:nodes.setdefault(int(w[v]),[]).append(e)
  if base is None:base=head.copy()
  diff=head-base;shift=np.median(diff,axis=0);residual=np.linalg.norm(diff-shift,axis=1);inward=[]
  for node,edges in nodes.items():
   if len(edges)!=2 or any(int(w[e['b']])!=node for e in edges):continue
   endpoint=head[edges[0]['b']];cell=np.floor(endpoint).astype(int);margin=.5-abs(endpoint-(cell+.5)).sum()
   if margin>0:inward.append({'weldVertex':node,'head':endpoint.tolist(),'headCell':cell.tolist(),'strictDiamondInteriorMargin':float(margin),'sourceEdgeIDs':[e['id']for e in edges]})
  rows.append({'frame':n,'sourceId':g['sourceId'],'verifiedLineSegments':len(sel),'medianProjectedTranslationFromFirst':shift.tolist(),'maxResidualAfterTranslation':float(residual.max()),'sourceGraphDegreeCounts':{str(k):sum(len(v)==k for v in nodes.values())for k in sorted({len(v)for v in nodes.values()})},'twoIncomingEdgesAtInteriorDiamond':inward})
 out={'source':'Actual same-sourceId evaluated geometry packets; no guessed rest-pose substitution','reference':'https://learn.microsoft.com/en-us/windows/win32/direct3d11/d3d10-graphics-programming-guide-rasterizer-stage-rules','meaning':'Two incoming independent line segments may fail to exit the joint pixel diamond. This is a projected raster-order risk, not a proof of visibility through self/hair/world occlusion.','rows':rows};(G/'analysis-motion/SOURCE_PATH_TRACE40.json').write_text(json.dumps(out,indent=2),encoding='utf-8',newline='\n');print(json.dumps({'summary':[(p['frame'],p['verifiedLineSegments'],len(p['twoIncomingEdgesAtInteriorDiamond']),p['maxResidualAfterTranslation'])for p in rows]},indent=2))
if __name__=='__main__':main()
