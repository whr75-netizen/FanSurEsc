from pathlib import Path
import json,struct,sys,hashlib
import numpy as np
from PIL import Image,ImageDraw
W=Path(__file__).parent;R=W/(sys.argv[1]if len(sys.argv)>1 else 'Walk511')
j=json.loads((R/'ANALYSIS511.json').read_text());rows=j['rows'];records={}
def rd(n):
 b=(R/(n+'.bin')).read_bytes();w,h,_,_=struct.unpack_from('<4i',b);return np.frombuffer(b,'<f4',offset=16).reshape(h,w,4)
for r in rows:
 p=f"{r['capture']:03d}";b=(R/(p+'_areas.bin')).read_bytes();x,y,w,h=struct.unpack_from('<4i',b);a=np.zeros((272,480),float);a[y:y+h,x:x+w]=np.frombuffer(b,'<f4',offset=16).reshape(h,w)
 records[r['target']]={'row':r,'p':p,'area':a,'mask':rd(p+'_MASK')[:,:,1]>.5,'baseMeta':rd(p+'_BASE_META'),'meta':rd(p+'_ALT_META'),'baseColour':rd(p+'_BASE_FINAL'),'colour':rd(p+'_ALT_FINAL'),'curves':json.loads((R/(p+'_curves.json')).read_text())['curves']}
 for key in ['baseMeta','meta']:
  local=np.zeros((272,480,4),np.float32);ox,oy=r['pose']['offset'];yy,xx=np.indices((272,480));mx=xx+ox;my=yy-oy;ok=(mx>=0)&(mx<480)&(my>=0)&(my<272);local[ok]=records[r['target']][key][my[ok],mx[ok]];records[r['target']][key+'Local']=local
events=[]
visibleEvents=[]
for i,d in records.items():
 if i-1 not in records or i+1 not in records:continue
 mask=d['mask'];prev=records[i-1];nxt=records[i+1];aba=(prev['mask']==nxt['mask'])&(prev['mask']!=mask)
 for y,x in np.argwhere(aba):
  steps=[]
  for n in [i-1,i,i+1]:
   z=records[n];ox,oy=z['row']['pose']['offset'];v=z['meta'][y-oy,x+ox];weight=0
   for dx,dy,w in [(1,0,.58578644),(-1,0,.58578644),(0,1,.58578644),(0,-1,.58578644),(1,1,.29289322),(-1,1,.29289322),(1,-1,.29289322),(-1,-1,.29289322)]:
    if 0<=x+dx<480 and 0<=y+dy<272:weight+=.14*w*(1-2*int(z['mask'][y+dy,x+dx]))
   steps.append({'target':n,'continuousArea':z['area'][y,x],'selected':bool(z['mask'][y,x]),'role':int(round(float(v[1]))),'primitivePlusOne':int(round(float(v[3]))),'deltaFillVsEmptyGivenCurrentNeighbours':float(1-2*z['area'][y,x]+weight)})
  events.append({'target':i,'headXY':[int(x),int(y)],'steps':steps,'classification':'AREA_AND_NEIGHBOURS_OBSERVATION_NOT_AUTOMATIC_ERROR'})
 for key,tag in [('baseMetaLocal','original'),('metaLocal','candidate')]:
  a,b,c=[records[n][key]for n in [i-1,i,i+1]];ha=(a[:,:,0]>0)&(a[:,:,1]>=12);hb=(b[:,:,0]>0)&(b[:,:,1]>=12);hc=(c[:,:,0]>0)&(c[:,:,1]>=12);v=(ha==hc)&(ha!=hb)
  for y,x in np.argwhere(v):visibleEvents.append({'target':i,'version':tag,'headXY':[int(x),int(y)],'roles':[int(round(float(z[y,x,1])))for z in [a,b,c]],'classification':'FINAL_VISIBLE_ROLE_ABA_OBSERVATION; continuity/occlusion must be interpreted, not counted as automatic errors'})
known=[]
for event,xy,targets in [('area-input .0250',[None,None],[1,2,3]),('neighbour .8750',[224,58],[69,70,71]),('historic disconnected .6875',[235,42],[54,55,56])]:
 if xy[0] is None:continue
 x,y=xy;steps=[]
 for n in targets:
  if n not in records:continue
  z=records[n];ox,oy=z['row']['pose']['offset'];my,mx=y-oy,x+ox;steps.append({'target':n,'area':z['area'][y,x],'mask':bool(z['mask'][y,x]),'originalRole':int(round(float(z['baseMeta'][my,mx,1]))),'candidateRole':int(round(float(z['meta'][my,mx,1])))})
 known.append({'event':event,'headXY':xy,'steps':steps})
# The proof view is only nearest-neighbour magnification of captured final PNGs.
sheet=Image.new('RGB',(512,len(rows)*246),'#202020');draw=ImageDraw.Draw(sheet);colourDifferences=[]
for line,r in enumerate(rows):
 d=records[r['target']];ox,oy=r['pose']['offset'];box=(2*(197+ox),2*(27-oy),2*(239+ox),2*(65-oy))
 for k,tag in enumerate(['BASE','ALT']):
  im=Image.open(R/(d['p']+'_'+tag+'.png')).convert('RGB').crop(box).resize((252,228),Image.Resampling.NEAREST);sheet.paste(im,(k*256,line*246+18))
 draw.text((3,line*246+2),f"{r['target']/80:.4f} CURRENT ORIGINAL | AUTO511 (3x integer display)",fill='white')
 for role,coords in r['sameSurfaceColourDifferenceYX'].items():
  for y,x in coords:
   rawdiff=float(np.max(abs(d['colour'][y,x,:3]-d['baseColour'][y,x,:3])));a=Image.open(R/(d['p']+'_BASE.png'));b=Image.open(R/(d['p']+'_ALT.png'));pa=np.array(a)[2*y:2*y+2,2*x:2*x+2,:3];pb=np.array(b)[2*y:2*y+2,2*x:2*x+2,:3]
   colourDifferences.append({'target':r['target'],'semantic':role,'mainXY':[x,y],'linearRGBMaxDelta':rawdiff,'pngMaxByteDelta':int(np.max(abs(pa.astype(int)-pb.astype(int)))),'samePrimitive':bool(d['meta'][y,x,3]==d['baseMeta'][y,x,3]),'note':'same source primitive; UV tolerance is 1e-5, not identical sample coordinates'})
sheet.save(R/'HEAD_CONTACT511.png')
for group in range((len(rows)+3)//4):sheet.crop((0,group*4*246,512,min((group+1)*4,len(rows))*246)).save(R/f'HEAD_GROUP511_{group}.png')
cost={key:{'min':min(r['runtime'][key]for r in rows),'median':float(np.median([r['runtime'][key]for r in rows])),'max':max(r['runtime'][key]for r in rows)}for key in ['curveMs','areaMs','binsAndVisibilityMs','packetAndUploadMs']}
cost.update({key:{'min':min(r['cost'][key]for r in rows),'median':float(np.median([r['cost'][key]for r in rows])),'max':max(r['cost'][key]for r in rows)}for key in ['baseOriginalRenderMs','auto511RenderMs']})
out={'scope':'16 actual pairs in four adjacent Walk intervals; no full loop','events':events,'finalVisibleRoleABA':visibleEvents,'knownEvents':known,'originalLayerABA':j['events'],'sameSourceSurfaceColourDifferences':colourDifferences,'cost':cost,'maxUncertainAlphaTests':max(r['runtime']['alphaUncertainTests']for r in rows),'curveCrossingsByTarget':{str(r['target']):r['runtime']['curveCrossings']for r in rows},'headContact':str(R/'HEAD_CONTACT511.png'),'gifSHA256':hashlib.sha256(Path(j['gif']['path']).read_bytes()).hexdigest(),'note':'Positive-winding curve graph is continuous form input; selected binary regions retain current joint area/perimeter cost. Classification requires visual/continuous-boundary evidence; no error count from raw differences.'}
(R/'REVIEW511.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items()if k not in ['events','sameSourceSurfaceColourDifferences']}));print(json.dumps({'ABAevents':events,'sameSourceColourSummary':{'count':len(colourDifferences),'maxLinearDelta':max((x['linearRGBMaxDelta']for x in colourDifferences),default=0),'maxPNGByteDelta':max((x['pngMaxByteDelta']for x in colourDifferences),default=0)}}))
details=[]
for d in sorted(colourDifferences,key=lambda q:q['linearRGBMaxDelta'],reverse=True)[:5]:
 z=records[d['target']];p=z['p'];x,y=d['mainXY'];ox,oy=z['row']['pose']['offset'];hx,hy=x-ox,y+oy;item={'change':d,'headXY':[hx,hy],'buffers':{}}
 for k in ['FINAL','META','UV','OWNER']:
  item['buffers'][k]={tag:rd(p+'_'+tag+'_'+k)[y,x].tolist()for tag in ['BASE','ALT']}
 item['packet']=[q for q in json.loads((R/(p+'_packets.json')).read_text())['packets']if q['x']==hx and q['y']==hy]
 details.append(item)
(R/'COLOUR_DETAILS511.json').write_text(json.dumps(details,indent=2)+'\n');print(json.dumps({'largestColourChanges':details}))
