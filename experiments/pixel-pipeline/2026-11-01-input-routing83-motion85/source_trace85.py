from pathlib import Path
import json,sys,numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
from validate_motion85 import packet,rgb8
sys.path.insert(0,str(ROOT/'eye-continuity77'));from source_candidate77 import components
native=np.load(ROOT/'whole-eye52/SOURCE_SURFACES52.npz');state=json.loads(sorted((HERE/'motion85').glob('STATE85*'))[-1].read_text());data=[];pigments=[]
for entry in state['sequencePackets']:
 d=packet(Path(entry['output']));data.append(d);a=d['arrays'];e=d['manifest']['eyeFeature'];parts,labels=components(native['native_xyz_head'],native['native_role6_tri'],e['centres'],e['axesY']);rx,ry,rw,rh=d['eyeROI'];rec=d['records'];sm=a['S3-meta'];uv=a['S3-uv'];rgba=a['S3-rgba'];shade=a['S3-shade'];primitive=np.rint(uv[...,2]).astype(int)-1
 for yy,xx in np.argwhere(rec[...,14,3]==77):
  r=rec[yy,xx];sid=int(round(float(r[3,1])));k=int(round(float(r[3,3])));sx=xx*4+(k&3);sy=yy*4+(k>>2);component=labels[primitive[sy,sx]];candidates=[]
  for cy,cx in np.argwhere((sm[...,0]>0)&(sm[...,3]>0)&(np.rint(sm[...,2])==sid)&(primitive>=0)):
   if labels[primitive[cy,cx]]!=component:continue
   cellDistance=(cx//4-xx)**2+(cy//4-yy)**2;distance=(cx+.5-(xx*4+(k%4)+.5))**2+(cy+.5-(yy*4+(k//4)+.5))**2;candidates.append((cellDistance,-float(rgba[cy,cx,3]),distance,int(cy),int(cx)))
  _,_,_,cy,cx=min(candidates);expected=rgba[cy,cx,:3]*shade[cy,cx,2];error=float(np.max(abs(expected-r[0,:3])));assert error<1e-6 and np.array_equal(rgb8(expected),rgb8(r[0,:3]));assert np.max(abs(r[7,:2]-uv[cy,cx,:2]))<1e-6 and np.array_equal(r[7,2:],[6,2])
  pigments.append({'frame':entry['frame'],'xyTopLeft':[int(xx+rx),int(271-yy-ry)],'eye':sid,'sourceSampleXY':[cx,cy],'primitive':int(primitive[cy,cx])+1,'sourceUV':uv[cy,cx,:2].tolist(),'sourceLinearRGB':rgba[cy,cx,:3].tolist(),'shadeZ':float(shade[cy,cx,2]),'outputRGB8':rgb8(r[0,:3]).tolist(),'maxLinearError':error,'sourceComponent':int(component)})
phaseExamples=[];first=data[0]
for d in data[1:6]:
 a,b=first['arrays']['head-final'],d['arrays']['head-final'];delta=abs(rgb8(a[...,:3]).astype(int)-rgb8(b[...,:3]).astype(int));rank=np.max(delta,-1);coords=np.argwhere(rank>0)
 if not len(coords):continue
 yy,xx=max(coords,key=lambda p:rank[p[0],p[1]]);x,y,w,h=d['roi'];xy=[int(xx+x),int(271-yy-y)];row={'fromFrame':first['identity']['frameIndex'],'toFrame':d['identity']['frameIndex'],'xyTopLeft':xy,'RGB8before':rgb8(a[yy,xx,:3]).tolist(),'RGB8after':rgb8(b[yy,xx,:3]).tolist(),'maxRGB8ChannelDelta':int(rank[yy,xx])}
 for name,v in [('before',first),('after',d)]:
  row[name]={'headOwner':v['arrays']['head-owner'][yy,xx].tolist(),'pre348RGBA':v['baseline'][yy,xx,0].tolist(),'pre348Owner':v['baseline'][yy,xx,1].tolist(),'pre348Meta':v['baseline'][yy,xx,2].tolist(),'pre348UV':v['baseline'][yy,xx,3].tolist(),'finalEqualsPre348':bool(np.array_equal(v['arrays']['head-final'][yy,xx],v['baseline'][yy,xx,0]))}
 phaseExamples.append(row)
out={'newNativeSourcePixelsChecked':len(pigments),'allNewNativeRGB8MatchActualS3TimesShadeZ':True,'pigments':pigments,'phaseColourExamples':phaseExamples,'limits':['The measured native colour formula matches captured source samples and default render branch; shader view-mode flag was not explicitly exported.','Existing head colour differences shown here precede348 when finalEqualsPre348=true; this does not identify the earlier colour-selection root cause.','Phase display span is near zero because the camera follows; no full subpixel sweep claimed.']};(HERE/'SOURCE_TRACE85.json').write_bytes((json.dumps(out,indent=2)+'\n').encode());print(json.dumps({'nativeColoursChecked':len(pigments),'phaseExamples':[(x['fromFrame'],x['toFrame'],x['xyTopLeft'],x['maxRGB8ChannelDelta'],x['before']['finalEqualsPre348'],x['after']['finalEqualsPre348'])for x in phaseExamples]},indent=2))
