import numpy as np
from analyse89 import rgb8
def trace(z,a,bank):
 out=[];rgba=bank['TemplateRGBA'];roles=bank['TemplateRole']
 for y,x in np.argwhere(np.isin(z[:,:,1,0],[2,5,7])):
  q=z[y,x];pig=q[7];role=int(round(q[1,0]));c=q[0];control=q[14];row={'eyeROIxy':[int(x),int(y)],'encodedRole':role,'RGBA':c.tolist(),'RGB8':rgb8(c[:3]).tolist(),'control':control.tolist(),'pigmentProvenance':pig.tolist(),'pre348ColourExact':bool(np.array_equal(c,a['eye-prior295'][y,x]))}
  if pig[3]==1:
   tx,ty=int(pig[0]),271-int(pig[1]);bc=rgba[ty,tx,:3];br=roles[ty,tx];row.update({'colourSource':'prefab-bound original Template216 atlas, not the representative native S1/S2 visibility sample','bankTextureXYBottomLeft':[tx,ty],'bankRGB8':bc.tolist(),'bankRole':br.tolist(),'RGB8EqualsSourceBank':bool(np.array_equal(rgb8(c[:3]),bc))})
  elif pig[3]==2:
   uv=a['S3-uv'];valid=a['S3-meta'][...,0]>0;hit=valid&np.all(uv[...,:2]==pig[:2],axis=-1);candidates=[]
   for sy,sx in np.argwhere(hit):
    raw=a['S3-rgba'][sy,sx];sh=a['S3-shade'][sy,sx];err=float(np.max(abs(raw[:3]*sh[2]-c[:3])));candidates.append({'sampleXY':[int(sx),int(sy)],'rawRGBA':raw.tolist(),'shade':sh.tolist(),'sourceTimesShadeMaxFloatError':err,'literalRGBEquals':bool(np.array_equal(raw[:3],c[:3]))})
   row.update({'colourSource':'native lid UV; control.z=1 retains pre348 composition; otherwise Evaluate selects nearest-cell/max-alpha S3 colour then multiplies shade.z','sameUVS3Candidates':candidates,'sameUVExactTimesShade':any(k['sourceTimesShadeMaxFloatError']==0 for k in candidates)})
  else:row['colourSource']='unresolved producer; not guessed from representative visibility sample'
  out.append(row)
 return out
