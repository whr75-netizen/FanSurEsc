"""Geometry-first representative selection prototype; no Unity or RGB averaging.
Output packets keep source chart/UV/baseRGBA/g together from one saved native sample.
"""
from pathlib import Path
import json,time
import numpy as np
from PIL import Image,ImageDraw
import candidate as c
from geometry_edges import Geometry
R=c.R;O=R/'coverage-v3'
def read(name):
 b=(R/'source-export'/(name+'.bin')).read_bytes();w,h=np.frombuffer(b[:8],'<i4');return np.frombuffer(b[8:],'<f4').reshape(h,w,4)[::-1].copy()
def raster(G,scale):
 h,w=40*scale,32*scale;depth=np.full((h,w),np.inf);owner=np.full((h,w),-1,int);triangles=np.full((h,w),-1,int)
 for index,p in enumerate(G.p):
  if not G.valid[index]:continue
  lo=np.maximum(np.ceil(p.min(axis=0)*scale-.5).astype(int),0);hi=np.minimum(np.floor(p.max(axis=0)*scale-.5).astype(int),[w-1,h-1])
  if np.any(hi<lo):continue
  xs=(np.arange(lo[0],hi[0]+1)+.5)/scale;ys=(np.arange(lo[1],hi[1]+1)+.5)/scale;x,y=np.meshgrid(xs,ys);d=np.stack([x,y],-1)-p[0];uv=d@G.inv[index].T;b=np.dstack([1-uv.sum(axis=-1),uv]);valid=b.min(axis=-1)>=-1e-12;z=np.sum(b*G.z[index],axis=-1);tile=depth[lo[1]:hi[1]+1,lo[0]:hi[0]+1];update=valid&(z<tile);tile[update]=z[update];owner[lo[1]:hi[1]+1,lo[0]:hi[0]+1][update]=G.chart[index];triangles[lo[1]:hi[1]+1,lo[0]:hi[0]+1][update]=index
 return owner,triangles,depth
def samples(G):
 uv=read('source960-6');meta=read('source960-5');light=read('light960-3');albedo=read('source960-0');lookup={(int(role),int(primitive)):i for i,(role,primitive) in enumerate(zip(G.role,G.primitive))};rows=[]
 for y,x in np.argwhere((meta[...,1]>=12)&(meta[...,1]<=15)):
  role=int(round(meta[y,x,1]))-1;primitive=int(round(meta[y,x,3]))-1;index=lookup[(role,primitive)];face=G.faces[index];q=G.uv[face];ww=np.linalg.solve((q[1:]-q[0]).T,uv[y,x,:2]-q[0]);bary=np.r_[1-ww.sum(),ww];world=bary@G.world[face];v=G.view@np.r_[world,1];clip=G.proj@v;point=np.array([(clip[0]/clip[3]*.5+.5)*480,(.5-clip[1]/clip[3]*.5)*272])-[204,26]
  if round(light[y,x,3])!=role+1:raise ValueError('saved native g/source role mismatch')
  rows.append({'sampleKind':'native960','fineX':int(x),'fineY':int(y),'chart':int(G.chart[index]),'role':role,'primitive':primitive,'uv':uv[y,x,:2].tolist(),'point':point.tolist(),'g':float(light[y,x,1]),'baseRGBAlinear':albedo[y,x].tolist(),'depth':float(meta[y,x,0])})
 source=json.loads((R/'source-export/bundle/prelight-source.json').read_text());matched=json.loads((R/'geometry-export/SOURCE_MATCH_ROWS.json').read_text())
 for match in matched:
  i=match['i'];cell=source['cells'][i];index=lookup[(cell['materialId'],cell['primitiveId'])];rows.append({'sampleKind':'centre480','fineX':int(i%32)*2+1,'fineY':int(i//32)*2,'chart':int(G.chart[index]),'role':cell['materialId'],'primitive':cell['primitiveId'],'uv':cell['uv'],'point':(np.array([i%32+.5,i//32+.5])+match['screenDelta']).tolist(),'g':cell['g'],'baseRGBAlinear':cell['baseRGBAlinear'],'depth':cell['depthHeadCamera']})
 return rows
def choose(G,owner,scale,sampleRows):
 s,f,mask,g,rgb,n,z=c.load();h,w=mask.shape;sourceCharts=np.load(R/'structure-v2/maps.npz')['sourceCharts'];byChart={}
 for row in sampleRows:byChart.setdefault(row['chart'],[]).append(row)
 packets=[];unknown=[];outChart=np.full(mask.shape,-1,int);coverage=[]
 for y,x in np.argwhere(mask):
  tile=owner[y*scale:(y+1)*scale,x*scale:(x+1)*scale];ids,counts=np.unique(tile[tile>=0],return_counts=True)
  if not len(ids):unknown.append({'cell':[int(x),int(y)],'reason':'no visible hair geometry in original hair cell'});packets.append(None);continue
  # One optimization over measured, locally supported SOURCE PACKETS. This is not
  # "pick an unmeasured surface, then invent/fallback its colour or illumination".
  candidates=[];countsByChart=dict(zip(ids,counts));centroids={}
  for chart in ids:
   points=np.argwhere(tile==chart);centroids[int(chart)]=np.array([x,y])+(points[:,::-1].mean(axis=0)+.5)/scale
   for row in byChart.get(int(chart),[]):
    if np.max(np.abs(np.array(row['point'])-[x+.5,y+.5]))<=.751:
     distance=float(np.sum((np.array(row['point'])-centroids[int(chart)])**2));candidates.append((int(countsByChart[chart]),int(chart)==int(sourceCharts[y,x]),distance,row))
  if not candidates:unknown.append({'cell':[int(x),int(y)],'reason':'no measured source packet supported by local visible geometry'});packets.append(None);continue
  best=max(v[0] for v in candidates);short=[v for v in candidates if v[0]==best];original=[v for v in short if v[1]]
  if original:short=original
  count,_,distance,chosen=min(short,key=lambda v:(v[2],v[3]['sampleKind']!='centre480',v[3]['fineY'],v[3]['fineX']));chart=chosen['chart'];centroid=centroids[chart];outChart[y,x]=chart;unrepresented=[int(v) for v in ids[counts>count]];packets.append({'cell':[int(x),int(y)],'originalChart':int(sourceCharts[y,x]),'selectedChart':chart,'coverage':float(count/(scale*scale)),'hairCoverage':float(len(tile[tile>=0])/(scale*scale)),'centroid':centroid.tolist(),'unrepresentedMoreCoveredCharts':unrepresented,'sample':chosen});coverage.append(float(count/(scale*scale)))
 return packets,unknown,outChart,mask
def main():
 O.mkdir(exist_ok=True);G=Geometry();start=time.perf_counter();allSamples=samples(G);sampleRows=[];excluded=[]
 for row in allSamples:
  hit=G.hit(row['point'])
  if row['chart'] in hit['charts'] and abs(hit['depth']-row['depth'])<=G.tolerance:sampleRows.append(row)
  else:excluded.append(row)
 (O/'PACKET_POOL.json').write_text(json.dumps(sampleRows));(O/'RASTER_BOUNDARY_EXCLUSIONS.json').write_text(json.dumps(excluded,indent=2));owners={};outputs={};details={}
 for scale in [8,16]:
  owner,tri,depth=raster(G,scale);packets,unknown,charts,mask=choose(G,owner,scale,sampleRows);owners[str(scale)]=owner;outputs[str(scale)]=charts;details[str(scale)]={'packets':packets,'unknown':unknown};np.savez_compressed(O/('visibility-'+str(scale)+'.npz'),chart=owner,triangle=tri,depth=depth)
 base=details['16'];s,f,mask,g,rgb,n,z=c.load();sourceCharts=np.load(R/'structure-v2/maps.npz')['sourceCharts'];a=np.zeros((*mask.shape,4),np.uint8);stage=np.full(mask.shape,-1,int)
 for p in base['packets']:
  if not p:continue
  x,y=p['cell'];a[y,x]=np.r_[c.srgb(np.array(p['sample']['baseRGBAlinear'][:3])),255];stage[y,x]=sum(p['sample']['g']>=v for v in f['thresholds'])
 im=Image.new('RGB',(32*12,40*12),(34,37,44));layer=Image.fromarray(a).resize(im.size,Image.Resampling.NEAREST);im.paste(layer,mask=layer);im.save(O/'coverage-source-unlit.png');sourceRGBA=np.dstack([c.srgb(rgb),mask*255]).astype(np.uint8);im=Image.new('RGB',(384,480),(34,37,44));layer=Image.fromarray(sourceRGBA).resize(im.size,Image.Resampling.NEAREST);im.paste(layer,mask=layer);im.save(O/'centre-source-unlit.png');np.savez_compressed(O/'maps.npz',charts=outputs['16'],mask=mask,stage=stage,sourceRGBA=a)
 result={'sourceId':s['sourceId'],'samples':len(sampleRows),'excludedRasterBoundarySamples':len(excluded),'scales':details,'coverage8vs16ChartDifference':int(np.count_nonzero(outputs['8'][mask]!=outputs['16'][mask])),'centreVsCoverageChartChanges':int(np.count_nonzero(outputs['16'][mask]!=sourceCharts[mask])),'remainingUnknown':len(base['unknown']),'unrepresentedMoreCoveredSurfaceCells':sum(bool(p and p['unrepresentedMoreCoveredCharts']) for p in base['packets']),'timeOfflineSeconds':time.perf_counter()-start,'status':'coverage baseline only; shared-curve/feature correction not yet applied','RGBContract':'one saved native packet supplies colour, g, UV, source owner together; no per-channel or cross-owner mixing'};(O/'RESULTS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='scales'}))
if __name__=='__main__':main()
