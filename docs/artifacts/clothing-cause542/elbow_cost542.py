from pathlib import Path
import json,re,numpy as np,struct
O=Path(__file__).resolve().parent;R=O.parent/'Common540/FullLoop540';s=Path('C:/Users/JG/Documents/work/Fantasy Survival Escape Game/Assets/EUnityValidation01/HeadRegion502/Runtime/HeadRegion502.cs').read_text();cost=float(re.search(r'BoundaryCost\s*=\s*([.\d]+)f',s).group(1))
def region(f):
 b=(R/f'{f:03d}_CLOTH_PART3.bin').read_bytes();x,y,w,h=struct.unpack_from('<4i',b);a=np.frombuffer(b,'<f4',w*h,16).reshape(h,w).astype(float);m=np.frombuffer(b,'?',w*h,16+4*w*h).reshape(h,w).copy();return x,y,a,m
def terms(a,m):
 unary=float(np.where(m,1-a,a).sum());pairs=0
 for dx,dy,weight in [(1,0,.58578644),(0,1,.58578644),(1,1,.29289322),(-1,1,.29289322)]:
  if dx>=0:p=m[:m.shape[0]-dy,:m.shape[1]-dx];q=m[dy:,dx:]
  else:p=m[:m.shape[0]-dy,-dx:];q=m[dy:,:m.shape[1]+dx]
  pairs+=float((p!=q).sum())*cost*weight
 return {'areaError':unary,'boundaryCost':pairs,'total':unary+pairs}
rows=[]
for f in [64,65,66]:
 x,y,a,m=region(f);alt=m.copy();alt[73-y,201-x]=False;alt[74-y,201-x]=False;before=terms(a,m);after=terms(a,alt);rows.append({'frame':f,'actualTwoCells':[bool(m[yy-y,201-x])for yy in[73,74]],'areas':[float(a[yy-y,201-x])for yy in[73,74]],'chosen':before,'withoutLeadingTwoCells':after,'removeMinusChosen':{k:after[k]-before[k]for k in before}})
j={'BoundaryCost':cost,'formula':'sum(selected?1-A:A)+BoundaryCost*(.58578644 cardinal cuts+.29289322 diagonal cuts)','rows':rows,'policyFinding':'The existing area+length objective has no term for the width/progression of a new leading-column tab on a retained larger bend. Correct energy minimization is not a pixel-art design-quality guarantee.'};(O/'ELBOW_COST542.json').write_text(json.dumps(j,indent=2));print(json.dumps(j))
