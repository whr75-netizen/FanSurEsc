"""Exercise the exact embedded runtime encoder at the declared payload size."""
from pathlib import Path
import subprocess,os,json,numpy as np
from frame_bytes77 import decode
H=Path(__file__).resolve().parent;G=H/'face93/packed1'
def main():
 s=(G/'capture/RUN.cs.txt').read_text();a=s.index('public static class FrameBytes77');b=s.index('\nnamespace Unity.AI.Assistant.Agent.Dynamic.Extension.Editor',a);code=s[a:b];assert 'bytes.Length>262144'in code;test='using System;using System.IO;'+code+'\npublic static class Main93 {public static void Main(string[] args){try{File.WriteAllBytes(args[1],FrameBytes77.Encode(File.ReadAllBytes(args[0])));}catch(ArgumentException e){Console.Error.WriteLine(e.Message);Environment.ExitCode=3;}}}';build=G/'build';build.mkdir(exist_ok=True);(build/'codec93.cs').write_text(test);csc=Path(os.environ.get('WINDIR',r'C:\Windows'))/'Microsoft.NET/Framework64/v4.0.30319/csc.exe';exe=build/'codec93.exe';r=subprocess.run([r'C:\Program Files\dotnet\dotnet.exe','exec',r'C:\Program Files\dotnet\sdk\10.0.402\Roslyn\bincore\csc.dll','/noconfig','/nostdlib+','/langversion:9','/target:exe','/optimize+','/r:'+str(csc.parent/'mscorlib.dll'),'/out:'+str(exe),str(build/'codec93.cs')],capture_output=True);assert r.returncode==0,(r.stdout+r.stderr).decode('utf-8',errors='replace');checks=0
 for n in [16,237952,259584,262144]:
  for repeated in [True,False]:
   raw=bytes(n)if repeated else np.arange(n//4,dtype='<u4').tobytes();(build/'input.bin').write_bytes(raw);r=subprocess.run([str(exe),str(build/'input.bin'),str(build/'output.r77')],capture_output=True);assert r.returncode==0 and decode((build/'output.r77').read_bytes(),n)==raw;checks+=1
 (build/'input.bin').write_bytes(bytes(262160));r=subprocess.run([str(exe),str(build/'input.bin'),str(build/'output.r77')],capture_output=True);assert r.returncode==3 and b'77 bounded RGBAFloat32 bytes'in r.stderr;checks+=1;d={'CPUChecks':checks,'actualEmbeddedRuntimeEncoderCompiled':True,'declared24PlaneRGBAFloatBytes':259584,'old262144ByteCapUnchanged':True,'PythonDecodeExactForRawAndRepeatedModes':True,'overBudgetStillRejected':True,'newGPUExecuted':False};(G/'CPU_CODEC93.json').write_text(json.dumps(d,indent=2));print(json.dumps(d))
if __name__=='__main__':main()
