from pathlib import Path
import array,ast,base64,collections,json,math,struct,sys,zipfile
R=Path(__file__).resolve().parent;sys.path.insert(0,str(R.parent/'colour-family'))
from pngio import read,write,zoom
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
B=Path(r'C:\Users\15352\Documents\Codex\2026-10-27\task-2\render-fix21\author33\feature34')
v3=load(R.parent/'palette-v3/BINDINGS.json');edges=load(R.parent/'palette-v3/EDGES.json')['preserve']['appearanceBoundaryRGBMerged'];source=load(B/'source-export/bundle/prelight-source.json');baseline=load(R.parent/'colour-family/NATIVE_ROW_MODE_BASELINES.json')['rows'];rows={(r['materialId'],r['y']):r['L']for r in baseline}
textures={m['materialId']:(*read(R.parent/'model-source'/f"image-{m['imageId']}.png"),m['imageId'])for m in source['materials']if m['materialId']in[11,12,13]}
def npz(path):
 out={}
 with zipfile.ZipFile(path)as z:
  for fn in z.namelist():
   raw=z.read(fn);n=struct.unpack_from('<H',raw,8)[0];h=ast.literal_eval(raw[10:10+n].decode());code={'<i8':'q','<f8':'d','|b1':'b'}[h['descr']];v=array.array(code);v.frombytes(raw[10+n:]);out[fn[:-4]]=(h['shape'],v)
 return out
fields=npz(B/'shared-v5/NATIVE_FEATURE_FIELDS.npz');valid=fields['valid'][1];base=fields['base'][1];chart=fields['charts'][1];app=fields['colour'][1];uncertain=fields['uncertain'][1];residual=fields['residual'][1]
def enc(v):return round(255*(12.92*v if v<=.0031308 else 1.055*v**(1/2.4)-.055))
rgba=bytearray(b'\x20\x23\x29\xff'*(512*640))
for i in range(512*640):
 if valid[i]:rgba[i*4:i*4+3]=bytes(enc(v)for v in base[i*3:i*3+3])
write(R/'native-visible-source.png',512,640,rgba)
def patch(mid,uv,size):
 w,h,raw,im=textures[mid];x=int((uv[0]%1)*w);y=int(((1-uv[1])%1)*h);half=size//2
 out=b''.join(raw[(((y+dy)%h)*w+(x+dx)%w)*4:(((y+dy)%h)*w+(x+dx)%w)*4+4]for dy in range(-half,half)for dx in range(-half,half))
 return out,{'imageId':im,'centerTexel':[x,y],'patchSize':size}
def crop(raw,w,x0,y0,x1,y1):return b''.join(raw[(y*w+x0)*4:(y*w+x1)*4]for y in range(y0,y1))
audit=[]
for k,e in enumerate(edges):
 entry={'id':k,**e,'endpoints':[]}
 for side,xy in zip(['a','b'],[e['a'],e['b']]):
  q=v3['variants']['preserve']['rows'][xy[1]*32+xy[0]];s=q['sample'];raw,origin=patch(s['materialId'],s['uv'],96);write(R/f'edge{k}-{side}-uv-native.png',96,96,raw);write(R/f'edge{k}-{side}-uv-4x.png',384,384,zoom(raw,96,96,4))
  x,y=xy;stats={};N=16
  for cellname,(cx,cy)in [('cell',(x,y)),('sameChartNear',(x,y))]:
   ids=[yy*512+xx for yy in range(max(0,cy*16-(16 if cellname=='sameChartNear'else 0)),min(640,(cy+1)*16+(16 if cellname=='sameChartNear'else 0)))for xx in range(max(0,cx*16-(16 if cellname=='sameChartNear'else 0)),min(512,(cx+1)*16+(16 if cellname=='sameChartNear'else 0)))if valid[yy*512+xx]and not uncertain[yy*512+xx]and chart[yy*512+xx]==chart[(y*16+8)*512+x*16+8]]
   counts=collections.Counter(app[i]for i in ids);rs=sorted(residual[i]for i in ids if app[i]==q['appearance']);stats[cellname]={'samples':len(ids),'appearanceCounts':dict(counts),'sameAppearanceResidualRange':[rs[0],rs[-1]]if rs else None}
  entry['endpoints'].append({'side':side,'cell':xy,**q,'rawSourceRGB8':[enc(v)for v in s['baseRGBAlinear'][:3]],'nativePatch':origin,'footprint':stats})
 x0=max(0,min(e['a'][0],e['b'][0])-2);y0=max(0,min(e['a'][1],e['b'][1])-2);x1=min(32,max(e['a'][0],e['b'][0])+3);y1=min(40,max(e['a'][1],e['b'][1])+3)
 raw=crop(rgba,512,x0*16,y0*16,x1*16,y1*16);write(R/f'edge{k}-projected-native.png',(x1-x0)*16,(y1-y0)*16,raw)
 entry['projectedPatchLogicalBounds']=[x0,y0,x1,y1];audit.append(entry)
(R/'NINE_NATIVE_AUDIT.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
html='<!doctype html><meta charset="utf-8"><style>body{background:#222;color:white;font:14px sans-serif}img{image-rendering:pixelated}section{display:flex;gap:20px;margin:30px}article{width:300px}</style><h1>9 native evidence pairs</h1>'
for e in audit:
 html+=f'<h2>{e["id"]}: {e["a"]}/{e["b"]} source ΔL {e["sourceGapL"]:.6f}</h2><section><article><img src="edge{e["id"]}-projected-native.png" width="256"><p>projected native texture</p></article>'
 for q in e['endpoints']:html+=f'<article><img src="edge{e["id"]}-{q["side"]}-uv-4x.png" width="256"><p>{q["sample"]["materialId"]} UV{q["sample"]["uv"]}<br>source{q["rawSourceRGB8"]} A{q["appearance"]} Q{q["shadeK"]}</p></article>'
 html+='</section>'
(R/'AUDIT.html').write_text(html,encoding='utf-8');print('9 native patches ready')
