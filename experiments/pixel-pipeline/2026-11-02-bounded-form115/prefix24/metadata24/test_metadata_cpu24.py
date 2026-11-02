"""Compile exact command units, then execute pure metadata/protocol tests only."""
from pathlib import Path
import sys,json,subprocess,uuid,hashlib
H=Path(__file__).resolve().parent;ROOT=H.parent;sys.path.insert(0,str(ROOT));import compile_cs_cpu as cc
row=next(x for x in json.loads((ROOT/'CS_COMPILE.json').read_text())['compilations']if x['name']=='Stage1MonoReferences');refs=[Path(x[len('/reference:'):])for x in row['arguments']if x.startswith('/reference:')]
compiled=[]
for name in ['ReadMetadataState24.command.cs.txt','ImportMetadata24.command.cs.txt','STAGE1_METADATA24.command.cs.txt']:compiled.append(cc.compile_one(name.split('.')[0],[H/name],refs))
s=(ROOT/'CpuTests24.cs').read_text().replace('Protocol24.Encode=value=>System.Text.Json.JsonSerializer.SerializeToUtf8Bytes(value,value.GetType(),json);','Protocol24.Encode=value=>value is Receipt24?PrefixMetadata24.ReceiptBytes((Receipt24)value):System.Text.Json.JsonSerializer.SerializeToUtf8Bytes(value,value.GetType(),json);').replace('Protocol24.Decode=(bytes,type)=>System.Text.Json.JsonSerializer.Deserialize(bytes,type,json);','Protocol24.Decode=PrefixMetadata24.Decode;')
point='  string temp=Path.Combine'
assert point in s
extra='''  Check("Actual nested case arrays preserved",()=>Assert(c.Globals.Length==74&&c.InputFiles.Length==13));
  Check("Receipt Outputs nested bytes roundtrip",()=>{var r=new Receipt24{ExecutionKind="gpu-prefix",RunId=c.RunId,Stage=1,CaseSha256=CaseLock24.ManifestSha,SourceId=c.SourceId,ShaderSha256=c.ShaderSha256,DispatchCalls=1,Success=true,StateEqual=true,ResourcesReleased=true,BeforeStateSha256="same",AfterStateSha256="same",Outputs=c.InputFiles.Where(x=>x.Stage==1).ToArray()};var bytes=Protocol24.Json(r);var decoded=Protocol24.Parse<Receipt24>(bytes);Assert(decoded.Outputs.Length==2&&decoded.Outputs[0].Sha256==r.Outputs[0].Sha256);Protocol24.CheckReceipt(c,CaseLock24.ManifestSha,1,decoded,"gpu-prefix");Assert(bytes.SequenceEqual(Protocol24.Json(decoded)));});
  Check("Linear reader rejects duplicate and trailing metadata",()=>{MustFail(()=>Json58.Parse("{\\\"x\\\":1,\\\"x\\\":2}"));MustFail(()=>Json58.Parse("{} garbage"));});
  Check("Metadata character budget and required fields",()=>{MustFail(()=>PrefixMetadata24.Decode(new byte[65537],typeof(Case24)));MustFail(()=>PrefixMetadata24.Decode(System.Text.Encoding.UTF8.GetBytes("{}"),typeof(Case24)));});
'''
s=s.replace(point,extra+point)
with(H/'CpuMetadataTests24.cs.txt').open('x',encoding='utf-8',newline='\n')as f:f.write(s)
work=ROOT/'build'/('metadata-cpu-'+uuid.uuid4().hex);work.mkdir()
refs10=Path(r'C:\Program Files\dotnet\packs\Microsoft.NETCore.App.Ref\10.0.13\ref\net10.0')
sources=[ROOT/'Prefix24Protocol.cs',ROOT/'CaseLock24.cs',ROOT/'PrefixMetadata24.cs',H/'Json58Linear24.cs',H/'CpuMetadataTests24.cs.txt']
args=['/nologo','/noconfig','/nostdlib+','/utf8output','/target:exe','/out:'+str(work/'CpuMetadataTests24.dll')]+['/reference:'+str(p)for p in refs10.glob('*.dll')]+[str(p)for p in sources]
proc=subprocess.run([str(cc.DOT),'exec',str(cc.CSC),*args],capture_output=True,text=True,encoding='utf-8');print(proc.stdout+proc.stderr);assert proc.returncode==0
(work/'CpuMetadataTests24.runtimeconfig.json').write_text(json.dumps({'runtimeOptions':{'tfm':'net10.0','framework':{'name':'Microsoft.NETCore.App','version':'10.0.13'}}}))
proc=subprocess.run([str(cc.DOT),str(work/'CpuMetadataTests24.dll')],capture_output=True,text=True,encoding='utf-8');print(proc.stdout+proc.stderr);assert proc.returncode==0
result=json.loads((work/'CPU_TEST_RESULT.json').read_text());assert result['Passed']==21
with(H/'METADATA_CPU24.json').open('x',encoding='utf-8')as f:json.dump({'compilations':compiled,'summary':result,'UnityOrGPUCalls':0,'commands':{p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in H.glob('*.command.cs.txt')}},f,indent=2)
