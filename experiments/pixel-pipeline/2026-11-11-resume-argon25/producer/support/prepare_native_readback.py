"""Fix only bounded observation; preserve the completed failed run unchanged."""
from pathlib import Path
import hashlib,json,sys
H=Path(__file__).resolve().parent;G=H/'native-proof';RUN=G/'readback-run'
sys.path.insert(0,str(H));from prepare_support import replace
sys.path.insert(0,str(H.parent));from prepare_live import compile_cs
def main():
 global RUN
 typed='--typed'in sys.argv
 if typed:RUN=G/'typed-run'
 assert not(RUN/'PHASE_REQUEST.json').exists()
 state=json.loads(next((G/'phase-run').glob('STATE113-*-finished.json')).read_text())
 assert state['PlayExited']and state['motionRestoration82']['allRestored']and not state.get('restorationError')
 assert '107 bounded source readback'in state['error']
 unknown=[v for v in state['nativeComparisons72']if v['equal']is not True]
 assert unknown==[{'equal':None,'path':'ProjectSettings/ProjectSettings.asset','status':'Unavailable','type':'UnityEditor.AssetImporter'}],unknown
 # This clean importer is not PlayerSettings; its lifetime was also unavailable
 # in the earlier ROI run. Do not call this unavailable native identity restored.
 RUN.mkdir(exist_ok=True)
 s=(G/'phase-run/RUN_Capture25.cs.txt').read_text().replace(str(G/'phase-run'),str(RUN))
 old='JointSlice107("CURVE-native26",forward102.Curves.NativeCurve26,0,forward102.Curves.NativeCurve26.count);'
 if typed:
  s=replace(s,old,'CaptureNativeCurveInput26();')
  method='''void CaptureNativeCurveInput26(){
   var curve=forward102.Curves;var rows=curve.NativeSegments26;
   if(curve.UpdatedFrame!=Time.frameCount||rows==null||rows.Length<1||rows.Length>1024||curve.NativeCurve26.stride!=32||rows.Length!=curve.NativeCurve26.count)throw new InvalidOperationException("26 native curve input ABI/frame bound");
   using(var w=new BinaryWriter(new FileStream(Path.Combine(output,"CURVE-native26.f32"),FileMode.CreateNew))){w.Write(rows.Length);w.Write(32);foreach(var r in rows){w.Write(r.a.x);w.Write(r.a.y);w.Write(r.a.z);w.Write(r.a.w);w.Write(r.b.x);w.Write(r.b.y);w.Write(r.b.z);w.Write(r.b.w);}}
   report["nativeCurveInput26"]=new Obj58{["sourceId"]=sourceId,["frame"]=Time.frameCount,["count"]=rows.Length,["stride"]=32,["source"]="Exact current CPU array submitted to NativeCurve26; column query is separate GPU readback"};
  }
  '''
  s=replace(s,'void CaptureColumns26(){',method+'void CaptureColumns26(){')
  assert 'JointSlice107("CURVE-native26'not in s and 'curve.NativeCurve26.stride!=32'in s
 else:
  s=replace(s,old,'JointSlice107("CURVE-native26a",forward102.Curves.NativeCurve26,0,512);JointSlice107("CURVE-native26b",forward102.Curves.NativeCurve26,512,forward102.Curves.NativeCurve26.count-512);')
 p=RUN/'RUN_Capture25.cs.txt';p.write_text(s,encoding='utf-8',newline='\n');compile_cs(p)
 (RUN/'GLOBAL_NAMES66.json').write_bytes((G/'phase-run/GLOBAL_NAMES66.json').read_bytes())
 relay=(G/'relay.py').read_text().replace("assert mode in ['import','phase']","assert mode in ['phase']")
 relay=replace(relay,"root=H if mode=='import'else H/'phase-run'","root=H/"+repr(RUN.name))
 metadata='TYPED_PREPARED.json'if typed else'READBACK_PREPARED.json'
 relay=replace(relay,"contract=load(H/'LIVE_PREPARED.json')","contract=load(H/"+repr(metadata)+")")
 (G/('relay_typed.py'if typed else'relay_readback.py')).write_text(relay,encoding='utf-8',newline='\n')
 result={'captureSourceSHA256':hashlib.sha256(p.read_bytes()).hexdigest(),'compiledCPU':True,'shaderChanged':False,'newImport':False,'GPUExecuted':False,'curveInputCPURecordBytes':846*32 if typed else None,'GPUColumnReadbackBytes':36*16,'originalFailurePreserved':True,'unavailableNativeComparison':unknown,'fixesFailure':'Original readback helper accepts only stride16, not stride32. CPU upload array serialized with exact stride32; GPU query remains bounded stride16.'if typed else None}
 (G/metadata).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
if __name__=='__main__':main()
