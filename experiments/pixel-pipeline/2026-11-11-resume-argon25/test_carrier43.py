from pathlib import Path
import json,subprocess,shutil,struct,numpy as np,hashlib,sys
from surface_paths34 import native
from trace_contour40 import geometry
H=Path(__file__).resolve().parent;G=H/'face43';G=G/'nearest44'if'--44'in sys.argv else G;B=G/'build';B.mkdir(parents=True,exist_ok=True)
def compile_run(name,source,args=[]):
 refs=Path(r'C:\Program Files\dotnet\packs\Microsoft.NETCore.App.Ref\10.0.13\ref\net10.0');engine=Path(r'C:\Users\15352\Documents\work\6000.5.9f1\Editor\Data\Managed\UnityEngine\UnityEngine.CoreModule.dll');dll=B/(name+'.dll');compiler=r'C:\Program Files\dotnet\sdk\10.0.402\Roslyn\bincore\csc.dll';dotnet=r'C:\Program Files\dotnet\dotnet.exe';rsp=B/(name+'.rsp');values=['/nologo','/nostdlib+','/target:exe','/langversion:9','/utf8output','/out:'+str(dll)]+['/reference:'+str(p)for p in refs.glob('*.dll')]+['/reference:'+str(engine),str(H/'CurveCarrier43.cs'),str(H/source)];rsp.write_text('\n'.join('"'+v+'"'for v in values),encoding='utf-8');r=subprocess.run([dotnet,'exec',compiler,'/noconfig','@'+str(rsp)],capture_output=True,text=True);assert r.returncode==0,r.stdout+r.stderr
 if not(B/engine.name).exists():shutil.copyfile(engine,B/engine.name)
 (B/(name+'.runtimeconfig.json')).write_text(json.dumps({'runtimeOptions':{'tfm':'net10.0','framework':{'name':'Microsoft.NETCore.App','version':'10.0.13'}}}));r=subprocess.run([dotnet,str(dll)]+list(map(str,args)),capture_output=True,text=True);assert r.returncode==0,r.stdout+r.stderr;return json.loads(r.stdout)
def write_string(f,value):
 b=value.encode();n=len(b)
 while n>=128:f.write(bytes([(n&127)|128]));n>>=7
 f.write(bytes([n]));f.write(b)
def main():
 unit=compile_run('tests43','CurveCarrierTests43.cs');(G/'CPU_CARRIER43.json').write_text(json.dumps(unit,indent=2),encoding='utf-8');surface,binding=native();fixture=G/'ACTUAL_INPUT43.bin';i=lambda f,v:f.write(struct.pack('<i',int(v)))
 with fixture.open('wb')as out:
  write_string(out,'curve-carrier43/v1');i(out,binding['rendererOrdinal']);i(out,binding['subMesh']);i(out,len(surface.uv));out.write(surface.uv.astype('<f4').tobytes());i(out,12)
  for case in ['capture','world/capture']:
   c=H/('face44'if'--44'in sys.argv else'face42')/case;r=json.loads((c/'COMPLETE.json').read_text())
   for frame in r['frames']:
    assert frame['frameInfo']['sourceAnchor']['indicesUVVerified'];g=geometry(c/('geometry-frame'+str(frame['frame'])+'.bin'));assert g['sourceId']==frame['sourceId'];p=next(p for p in r['planes']if p['frame']==frame['frame']and p['name']=='atlas40');a=np.fromfile(c/p['file'],dtype='<f4').reshape(p['height'],p['width'],4);w=frame['QROI'][2];stroke,proof=a[:,3*w:4*w],a[:,4*w:5*w];mask=stroke[:,:,3]==1;obs=proof[mask];write_string(out,g['sourceId']);write_string(out,g['model']);i(out,g['frame']);i(out,len(g['points']));out.write(g['points']['world'].astype('<f4').tobytes());tri=g['indices'][binding['subMesh']].astype('<i4');assert np.array_equal(tri,surface.indices);i(out,tri.size);out.write(tri.tobytes());out.write(g['points']['weld'].astype('<i4').tobytes());out.write(g['view'].astype('<f4').flatten(order='F').tobytes());i(out,len(obs))
    for p in obs:i(out,round(p[1]));out.write(struct.pack('<ff',float(p[2]),float(p[0])))
 actual=compile_run('replay43','ReplayCarrier43.cs',[fixture]);actual['sourceHelperSHA256']=hashlib.sha256((H/'CurveCarrier43.cs').read_bytes()).hexdigest();actual['fixtureSHA256']=hashlib.sha256(fixture.read_bytes()).hexdigest();(G/'ACTUAL_CARRIER43.json').write_text(json.dumps(actual,indent=2),encoding='utf-8',newline='\n');print(json.dumps({k:v for k,v in actual.items()if k!='rows'}))
if __name__=='__main__':main()
