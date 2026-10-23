from pathlib import Path
import ast,json,struct,math,numpy as np
O=Path(__file__).resolve().parent;source=(O.parent/'Cloth527/probe_order529.py').read_text().split('\nactual=[]')[0].replace('1e-9<depth<1','1e-9<depth')
tree=ast.parse(source);funcs=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in['area','returns']];env={'np':np,'math':math};exec(compile(ast.Module(body=funcs,type_ignores=[]),'existing529_geometric_return','exec'),env)
rows=[]
for frame in [64,65,66]:
 raw=(O.parent/f'Common540/FullLoop540/{frame:03d}_CLOTH_PART3.bin').read_bytes();x,y,w,h=struct.unpack_from('<4i',raw);at=16+5*w*h;nr,=struct.unpack_from('<i',raw,at);at+=4;found=[]
 for _ in range(nr):
  n,=struct.unpack_from('<i',raw,at);at+=4;r=np.frombuffer(raw,'<f4',n*2,at).reshape(n,2);at+=8*n
  for q in env['returns'](r):
   if q['axis']==0 and q['sign']==1 and any(199<p[0]<204 and 72<p[1]<76 for p in q['arc']):
    found.append({k:v for k,v in q.items()if k not in['mapping','rule']})
 rows.append({'frame':frame,'unboundedOrderedReturnsAtElbow':found})
(O/'ELBOW_RETURN542.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows))
