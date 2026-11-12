"""Compile exact current union source with a tiny CPU-only vector stub.

No Unity DLL initialization, Editor call, D3D device or GPU compile/dispatch.
This isolates exact predicates from source orientation; not gameplay proof.
"""
from pathlib import Path
import subprocess,json,hashlib,sys
H=Path(__file__).resolve().parent;G=H/'face94';R=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
def main():
 G.mkdir(exist_ok=True);source=R/'Assets/EUnityValidation01/ClothRegion524/Runtime/ClosedRegion524.cs';p=G/'ClosedRegion.before.cs'
 if p.exists():raw=p.read_bytes()
 else:raw=source.read_bytes();p.write_bytes(raw)
 expected=G/'PATCH_TARGETS94.json'
 if expected.exists():assert hashlib.sha256(raw).hexdigest()==json.loads(expected.read_text())['ClosedRegion524.cs']['beforeSHA']
 trace='--trace'in sys.argv
 if trace:p=G/'ClosedRegion.trace94.cs'
 ref=Path(r'C:\Windows\Microsoft.NET\Framework64\v4.0.30319');exe=G/('winding94-trace.exe'if trace else'winding94.exe');args=[r'C:\Program Files\dotnet\dotnet.exe','exec',r'C:\Program Files\dotnet\sdk\10.0.402\Roslyn\bincore\csc.dll','/noconfig','/nostdlib','/langversion:9','/target:exe','/out:'+str(exe),*[str('/r:'+str(ref/(n+'.dll')))for n in ['mscorlib','System','System.Core','System.Numerics']],str(p),str(H/'WindingTests94.cs')];q=subprocess.run(args,capture_output=True);assert q.returncode==0,q.stdout.decode('utf-8',errors='replace')+q.stderr.decode('utf-8',errors='replace');inp=Path(sys.argv[sys.argv.index('--input')+1]).resolve()if'--input'in sys.argv else None;q=subprocess.run([str(exe),str(G)]+([str(inp)]if inp else[]),capture_output=True);r={'CPUOnly':True,'sourceSHA256':hashlib.sha256(raw).hexdigest(),'traceOnlyErrorMessageChanged':trace,'input':str(inp)if inp else None,'exitCode':q.returncode,'output':q.stdout.decode('utf-8',errors='replace')+q.stderr.decode('utf-8',errors='replace'),'actualGameplayReproduced':bool(inp and b'INPUT_FAIL'in q.stdout),'newUnityOrGPUExecuted':False};out=G/('CPU_'+inp.stem+('_TRACE'if trace else'')+'.json'if inp else'CPU_WINDING94.json');out.write_text(json.dumps(r,indent=2));print(json.dumps(r));assert q.returncode in [0,2]
if __name__=='__main__':main()
