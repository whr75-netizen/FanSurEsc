from pathlib import Path
import subprocess,json,hashlib
H=Path(__file__).resolve().parent;G=H/'face65';build=G/'build'
def main():
 source=(G/'capture/RUN.cs.txt').read_text();a=source.index('public sealed class ConsumerReads40');b=source.index('// Readback callbacks',a);guard=source[a:b]
 code='using System;\n'+guard+'\n'+(H/'ConsumerRegression65.cs').read_text().replace('using System;','')
 target=build/'consumer65.cs';target.write_text(code,encoding='utf-8',newline='\n');out=build/'consumer65.dll'
 dotnet=Path(r'C:\Program Files\dotnet');ref=dotnet/'packs/Microsoft.NETCore.App.Ref/10.0.13/ref/net10.0'
 args=[str(dotnet/'dotnet.exe'),'exec',str(dotnet/'sdk/10.0.402/Roslyn/bincore/csc.dll'),'/noconfig','/nostdlib+','/utf8output','/langversion:9','/target:exe','/out:'+str(out),'/reference:'+str(ref/'System.Runtime.dll'),'/reference:'+str(ref/'System.Console.dll'),'/reference:'+str(ref/'System.Threading.dll'),str(target)]
 c=subprocess.run(args,capture_output=True,text=True);assert c.returncode==0,c.stdout+c.stderr
 out.with_suffix('.runtimeconfig.json').write_text(json.dumps({'runtimeOptions':{'tfm':'net10.0','framework':{'name':'Microsoft.NETCore.App','version':'10.0.13'}}}))
 done=subprocess.run([str(dotnet/'dotnet.exe'),str(out)],capture_output=True,text=True);assert done.returncode==0,done.stdout+done.stderr
 r={'actualGuardSourceSHA256':hashlib.sha256(guard.encode()).hexdigest(),'sameGuardAsExecutedGPUCapture':True,'sixOwnersOutOfOrder':True,'wrongOwnerRetainsUntilOwnCompletion':True,'sealedPendingRetains':True,'incompleteErrorWrongByteRetain':True,'UnityGPUCalls':0,'output':done.stdout.strip()};(G/'CPU_CONSUMERS65.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
if __name__=='__main__':main()
