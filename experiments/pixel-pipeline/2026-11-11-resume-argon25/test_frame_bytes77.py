from pathlib import Path
import json,subprocess,hashlib,struct,datetime,numpy as np
from frame_bytes77 import decode
H=Path(__file__).resolve().parent;G=H/'face77';F=Path(r'C:\Windows\Microsoft.NET\Framework64\v4.0.30319')
def main():
 build=G/'byte-test';build.mkdir(exist_ok=True);exe=build/'FrameBytes77.exe';rsp=build/'compile.rsp';args=['/nologo','/utf8output','/langversion:9','/target:exe','/nostdlib+','/out:'+str(exe)]+['/r:'+str(F/n)for n in['mscorlib.dll','System.dll','System.Core.dll']]+[str(H/'FrameBytes77.cs'),str(H/'FrameBytesTests77.cs')];rsp.write_text('\n'.join('"'+v+'"'for v in args));r=subprocess.run([r'C:\Program Files\dotnet\dotnet.exe','exec',r'C:\Program Files\dotnet\sdk\10.0.402\Roslyn\bincore\csc.dll','/noconfig','@'+str(rsp)],capture_output=True,text=True,encoding='utf-8');assert r.returncode==0,r.stdout+r.stderr
 root=build/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%f');root.mkdir();rng=np.random.default_rng(77);cases=[bytes(16),bytes(248832),rng.integers(0,256,248832,np.uint8).tobytes(),b'a'*32+b'b'*16+b'c'*48]+[rng.integers(0,256,n*16,np.uint8).tobytes()for n in[2,3,5,7,31,128]];invoke=[str(exe)]
 for i,data in enumerate(cases):a=root/(str(i)+'.raw');a.write_bytes(data);invoke.extend([str(a),str(root/(str(i)+'.r77'))])
 subprocess.run(invoke,check=True,capture_output=True);tests=0;modes=[]
 for i,original in enumerate(cases):
  encoded=(root/(str(i)+'.r77')).read_bytes();assert decode(encoded,len(original))==original;assert len(encoded)<=len(original)+12;modes.append(struct.unpack_from('<I',encoded,4)[0]);tests+=1
  for bad in[encoded[:-1],encoded+b'x',encoded[:8]+struct.pack('<I',0x7fffffff)+encoded[12:]]:
   try:decode(bad,len(original))
   except ValueError:tests+=1
   else:raise AssertionError('malformed record accepted')
 assert modes[1]==1 and modes[2]==0;tests+=1
 result={'CPUChecks':tests,'actualCSharpEncoderCompiledAndExecuted':True,'roundtripCases':len(cases),'rawFallbackAndRLEBothCovered':True,'truncationTrailingOverflowRejected':True,'noExtraAssembliesBeyondExistingSystem':True,'GPUCalls':0,'sourceSHA256':hashlib.sha256((H/'FrameBytes77.cs').read_bytes()).hexdigest()};(G/'CPU_BYTES77.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':main()
