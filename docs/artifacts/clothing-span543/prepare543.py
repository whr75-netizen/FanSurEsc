from pathlib import Path
import struct,json,ast,math,numpy as np
O=Path(__file__).resolve().parent;O.mkdir(exist_ok=True);R=O.parent/'Common540/FullLoop540'
s=(O.parent/'Cloth527/probe_order529.py').read_text().split('\nactual=[]')[0].replace('1e-9<depth<1','1e-9<depth');t=ast.parse(s);env={'np':np,'math':math};exec(compile(ast.Module(body=[n for n in t.body if isinstance(n,ast.FunctionDef)and n.name in['area','returns']],type_ignores=[]),'existing_return_geometry','exec'),env)
def rings(b,at):
 count,=struct.unpack_from('<i',b,at);at+=4;rs=[]
 for _ in range(count):
  n,=struct.unpack_from('<i',b,at);at+=4;rs.append(np.frombuffer(b,'<f4',2*n,at).reshape(n,2).astype(float));at+=8*n
 return rs,at
def load(name):
 if name.startswith('actual'):
  f=int(name[6:]);b=(R/f'{f:03d}_CLOTH_PART3.bin').read_bytes();x,y,w,h=struct.unpack_from('<4i',b);a=np.frombuffer(b,'<f4',w*h,16).reshape(h,w);m=np.frombuffer(b,'?',w*h,16+4*w*h).reshape(h,w);rs,at=rings(b,16+5*w*h);rs,at=rings(b,at)
 else:
  b=(O.parent/f'Integrate539/MathWholeCS/{name}.bin').read_bytes();rs,at=rings(b,0);x,y,w,h=struct.unpack_from('<4i',b,at);at+=16;a=np.frombuffer(b,'<f4',w*h,at).reshape(h,w);m=np.frombuffer(b,'?',w*h,at+4*w*h).reshape(h,w)
 return x,y,a,m,rs
def group(x,y,a,rs):
 h,w=a.shape;groups=[];details=[]
 def area(px,py):return float(a[py-y,px-x])if x<=px<x+w and y<=py<y+h else 0
 for ring in rs:
  if env['area'](ring)<=0:continue
  for feature in env['returns'](ring):
   if feature['earArea']<=1:continue
   axis,sign=feature['axis'],feature['sign'];arc=np.array(feature['arc']);edge=int(math.floor(arc[:,axis].min())if sign==1 else math.ceil(arc[:,axis].max())-1);start=int(math.floor(arc[:,1-axis].min()));end=int(math.ceil(arc[:,1-axis].max()));best=None
   for v in range(start,end-2):
    cells=[(edge,k)if axis==0 else(k,edge)for k in range(v,v+3)];values=[area(*p)for p in cells]
    if min(values)<=0:continue
    if not all(area(px+(sign if axis==0 else 0),py+(sign if axis==1 else 0))==1 and area(px+(2*sign if axis==0 else 0),py+(2*sign if axis==1 else 0))==1 for px,py in cells):continue
    score=sum(values)
    if best is None or score>best[0]:best=(score,cells)
   if best is None:continue
   indices=[(py-y)*w+px-x for px,py in best[1]]
   if indices in groups:continue
   groups.append(indices);details.append({'axis':axis,'sign':sign,'earArea':feature['earArea'],'cells':best[1],'areaSum':best[0]})
 return groups,details
names=['actual'+str(f)for f in[34,43,44,50,64,65,66]]+[f'thin{r}_{s}'for r in range(4)for s in range(2)];out=O/'Inputs';out.mkdir(exist_ok=True);rows=[]
for name in names:
 x,y,a,m,rs=load(name);g,d=group(x,y,a,rs);h,w=a.shape
 with(out/(name+'.bin')).open('wb')as f:
  f.write(struct.pack('<4i',x,y,w,h));f.write(np.asarray(a,'<f4').tobytes());f.write(struct.pack('<i',len(g)))
  for q in g:f.write(struct.pack('<4i',3,*q))
  f.write(m.tobytes())
 rows.append({'case':name,'origin':[x,y],'size':[w,h],'groups':d})
(O/'INPUTS543.json').write_text(json.dumps(rows,indent=2));print(json.dumps([{'case':r['case'],'groups':len(r['groups'])}for r in rows]))
