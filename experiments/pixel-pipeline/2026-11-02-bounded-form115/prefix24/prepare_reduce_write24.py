"""Reuse proven state collector; prepare only the approved stage3->stage4 gates."""
from pathlib import Path
import json,sys
H=Path(__file__).resolve().parent;D=H/'reduce-write24';D.mkdir(exist_ok=True)
base=(H/'enumerate24/PRE_STATE.command.cs.txt').read_text()
for phase in ['pre','mid','post']:
 (D/phase).mkdir(exist_ok=True)
 s=base.replace('Root+@"\\enumerate24\\pre"','Root+@"\\reduce-write24\\'+phase+'"').replace('CaseLock24.RunRoot,2);','CaseLock24.RunRoot,3);')
 s=s.replace('Phase="pre"','Phase="'+phase+'"').replace('Read-only Enumerate pre state complete','Read-only ReduceWrite '+phase+' state complete')
 a=s.index('   var shader=AssetDatabase.LoadAssetAtPath<ComputeShader>');b=s.index('   byte[] state=',a)
 if phase=='pre':
  part=s[a:b].replace('Enumerate113','Reduce113')
  part+='   if(!shader.HasKernel("Write113"))throw new IOException("Write missing");uint wx,wy,wz;shader.GetKernelThreadGroupSizes(shader.FindKernel("Write113"),out wx,out wy,out wz);if(wx!=8||wy!=8||wz!=1)throw new IOException("Write group ABI differs");\n'
  s=s[:a]+part+s[b:]
  s=s.replace('KernelGroup=x+","+y+","+z','KernelGroup="Reduce113:64,1,1;Write113:8,8,1"')
 else:
  s=s[:a]+s[b:]
  s=s.replace('||SystemInfo.graphicsDeviceType!=GraphicsDeviceType.Direct3D11','')
  s=s.replace('KernelGroup=x+","+y+","+z','KernelGroup="not queried; state only"').replace('ShaderMessages=messages.Select(m=>m.severity+"|"+m.message).ToArray()','ShaderMessages=new string[0]')
 assert 'shader.Dispatch('not in s and 'AssetDatabase.ImportAsset('not in s
 if phase!='pre':assert 'GetKernelThreadGroupSizes('not in s and 'ShaderUtil.'not in s and 'LoadAssetAtPath<ComputeShader>'not in s
 with(D/(phase.upper()+'_STATE.command.cs.txt')).open('x',encoding='utf-8',newline='\n')as f:f.write(s)
sys.path.insert(0,str(H));import compile_cs_cpu as cc
row=next(x for x in json.loads((H/'CS_COMPILE.json').read_text())['compilations']if x['name']=='Stage1MonoReferences');refs=[Path(x[len('/reference:'):])for x in row['arguments']if x.startswith('/reference:')]
rows=[cc.compile_one('ReduceWrite'+p,[D/(p+'_STATE.command.cs.txt')],refs)for p in ['PRE','MID','POST']]
with(D/'CPU_COLLECTORS24.json').open('x',encoding='utf-8')as f:json.dump(rows,f,indent=2)
