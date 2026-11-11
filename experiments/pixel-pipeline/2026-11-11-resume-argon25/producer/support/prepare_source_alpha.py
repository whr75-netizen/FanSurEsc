"""Correct witness units: Query outputs intrinsic alpha * transmittance.
Preserve the actually tested gate candidate; prepare a separate minimal fix.
"""
from pathlib import Path
import hashlib,json,sys
H=Path(__file__).resolve().parent;OLD=H/'gate';G=H/'gate-alpha';PRE=H.parent
sys.path.insert(0,str(H));from prepare_support import replace
sys.path.insert(0,str(PRE));from prepare_live import compile_cs
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 check='--check-only'in sys.argv
 if not check:
  assert not(G/'IMPORT_REQUEST.json').exists()and not(G/'phase-run/PHASE_REQUEST.json').exists()
  (G/'phase-run').mkdir(parents=True,exist_ok=True);(G/'import').mkdir(exist_ok=True)
 s=(OLD/'SharedSkin26.compute').read_text()
 for part,axis in [(1,'x'),(2,'y')]:
  s=replace(s,f'witness26.{axis}=all(sv26==1)?at+1:0;',f'witness26.{axis}=SL113({part},0,at).a>0&&all(sv26==SL113({part},0,at).a)?at+1:0;')
 s=replace(s,'witness26.z=all(v.xy==1)?at+1:0;','witness26.z=SL113(3,0,at).a>0&&all(v.xy==SL113(3,0,at).a)?at+1:0;')
 cs=G/'SharedSource26.compute'
 if check:assert cs.read_text()==s
 else:cs.write_text(s,encoding='utf-8',newline='\n')
 host=(OLD/'phase-run/RUN_Capture25.cs.txt').read_text().replace(str(OLD/'phase-run'),str(G/'phase-run')).replace('Assets/EUnityValidation01/SharedSkin26/SharedSkin26.compute','Assets/EUnityValidation01/SharedSource26/SharedSource26.compute')
 columns=''' struct ColumnWitness26{public Vector4 midpoint,source,visibility;}
 void CaptureColumns26(){
  int count=forward102.Source.Engine.Width/4*2;var b=forward102.Region.columns24;
  if(b.stride!=48||count<=0||count>b.count||count*48>65536)throw new InvalidOperationException("26 bounded source-column witness readback");
  var rows=new ColumnWitness26[count];b.GetData(rows,0,0,count);
  using(var w=new BinaryWriter(new FileStream(Path.Combine(output,"SOURCE-columns26.f32"),FileMode.CreateNew))){w.Write(count);w.Write(48);foreach(var row in rows)foreach(var v in new[]{row.midpoint,row.source,row.visibility}){w.Write(v.x);w.Write(v.y);w.Write(v.z);w.Write(v.w);}}
  report["sourceWitnessColumns26"]=new Obj58{["sameFrame"]=Time.frameCount,["count"]=count,["stride"]=48,["sourceId"]=sourceId,["source"]=forward102.Source.Scope};
 }
'''
 host=replace(host,' void CaptureFull113(NativePlayer395 n,CpuSourceCapture64.Frame hf,EyeFeature348 e){',columns+' void CaptureFull113(NativePlayer395 n,CpuSourceCapture64.Frame hf,EyeFeature348 e){\n  CaptureColumns26();')
 source=G/'phase-run/RUN_Capture25.cs.txt'
 if check:assert source.read_text()==host
 else:
  source.write_text(host,encoding='utf-8',newline='\n');compile_cs(source)
  (G/'phase-run/GLOBAL_NAMES66.json').write_bytes((OLD/'phase-run/GLOBAL_NAMES66.json').read_bytes())
 imp=(OLD/'RUN_Import25.cs.txt').read_text().replace(str(OLD/'import'),str(G/'import'))
 imp=imp.replace('Assets/EUnityValidation01/SharedSkin26','Assets/EUnityValidation01/SharedSource26').replace('"SharedSkin26"','"SharedSource26"').replace('/SharedSkin26.compute','/SharedSource26.compute')
 imp=replace(imp,str(OLD/'SharedSkin26.compute'),str(cs));imp=replace(imp,sha(OLD/'SharedSkin26.compute'),sha(cs))
 ip=G/'RUN_Import25.cs.txt'
 if check:
  assert ip.read_text()==imp
  receipt=json.loads((G/'LIVE_PREPARED.json').read_text());assert receipt['captureSourceSHA256']==sha(source)and receipt['computeSHA256']==sha(cs)
  print(json.dumps({'executedSourceMatchesGenerator':True,'computeAndImportMatch':True,'UnityGPUCalls':0}));return
 ip.write_text(imp,encoding='utf-8',newline='\n');compile_cs(ip)
 (G/'relay.py').write_bytes((OLD/'relay.py').read_bytes())
 record={'importSourceSHA256':sha(ip),'captureSourceSHA256':sha(source),'computeSHA256':sha(cs),
  'cacheSHA256':sha(H/'SHARED_SOURCE_MASK26.json'),'compiledCPU':True,'newAssets':1,'newKernels':0,'actualFramesBound':4,
  'units':'source weighted visibility equals same source intrinsic alpha>0; column trace uses raw transmittance1',
  'noAlphaOrColourModified':True,'boundedSourceColumnWitnesses':True,'GPUOrUnityExecuted':False}
 (G/'LIVE_PREPARED.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');print(json.dumps(record))
if __name__=='__main__':main()
