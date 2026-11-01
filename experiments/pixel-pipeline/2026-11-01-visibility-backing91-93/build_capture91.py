from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OLD=ROOT/'native-feature89/capture89f';OUT=HERE/'capture91'
sys.path.insert(0,str(ROOT/'boundary-input69'));from prepare73 import bundle
s=(OLD/'Capture89F.cs').read_text().replace(str(OLD),str(OUT)).replace('MotionScope89','MotionScope91').replace('STATE89-','STATE91-').replace('TRACE89-','TRACE91-').replace('eye89-','eye91-')
s=s.replace(' NativeRetarget89 retarget89;', ' NativeRetarget89 retarget89;CurrentRasters91 current91;')
s=s.replace('RenderPipelineManager.endCameraRendering+=CameraEnd89;', 'current91=new CurrentRasters91(probeEye);RenderPipelineManager.endCameraRendering+=CameraEnd89;')
s=s.replace('retarget89.Render();retargetFrame89=Time.frameCount;', 'retarget89.Render();current91.Render();retargetFrame89=Time.frameCount;')
s=s.replace('retarget89?.Dispose();report["retargetDisposed89"]', 'current91?.Dispose();report["current91Disposed"]=current91==null||current91.Disposed;retarget89?.Dispose();report["retargetDisposed89"]')
needle='  var sky=';at=s.index(needle)
extra='''  if(current91==null||current91.RenderedFrame!=Time.frameCount)throw new InvalidOperationException("91 current-source diagnostic frame mismatch");report["currentSources91"]=current91.Info;var currentFrame91=Frame(f,"physical-source91",serial);for(int group91=0;group91<current91.fields.Length;group91++)for(int field91=0;field91<current91.fields[group91].Length;field91++){var texture91=current91.fields[group91][field91];string file91="current91-g"+group91+"-"+field91+".plane";var rect91=new RectInt(0,0,texture91.width,texture91.height);CpuSourceCapture64.WriteOwnedPlane(Path.Combine(output,file91),currentFrame91,texture91,rect91,"91 isolated current evaluated source mesh, no cached backing","RGBA/meta/rest/UV; S3 shade/normalWS/SH/lit-available","linear RGBAFloat; direct original source material","raw RT memory; scale recorded per group");planes.Add(new Obj58{["file"]=file91,["sourceId"]=sourceId,["viewId"]="physical-source91",["frameIndex"]=frameIndex,["renderSerial"]=serial,["textureSize"]=new Arr58(texture91.width,texture91.height),["roiBottomLeft"]=new Arr58(0,0,texture91.width,texture91.height),["producer"]="91 owned current-source probe"});report["largestOwnedReadbackBytes"]=Math.Max((long)report["largestOwnedReadbackBytes"],texture91.width*texture91.height*16L);}
'''
s=s[:at]+extra+s[at:]
s=s.replace('Coupled native/authored source geometry/material observer; product77 remains active','91 current evaluated backing and same-ray normal/SH/light totals; product77 unchanged')
# Do not lengthen any existing timeout. Eight normal frames only, no virtual input.
(OUT/'Capture91.cs').write_text(s,encoding='utf-8')
compile=s.replace(' public void Execute(ExecutionResult result)\n {',' public void Execute(ExecutionResult result)\n {result.Log("91 full observer compile-only; no Play");return;}\n void Prepared91(ExecutionResult result)\n {',1)
assert 'void Prepared91'in compile
(OUT/'Compile91.cs').write_text(compile,encoding='utf-8')
B=ROOT/'apply-capture66';O=ROOT/'eye-observer73';U=ROOT/'uv-features64'
deps=[B/'Json58Linear66.cs',B/'SerializedContent66.cs',U/'GlobalJournal64.cs',U/'CpuSourceCapture64.cs',O/'EyeReadback73.cs',O/'UnityEyeBuffer70.cs',O/'CreateOnly73.cs',O/'NativeSnapshot73.cs',ROOT/'eye-continuity77/NativeSource77.cs',ROOT/'native-feature89/NativeRetarget89.cs',HERE/'CurrentRasters91.cs',HERE/'MotionScope91.cs']
for mode in ['Compile91','Capture91']:bundle(deps+[OUT/(mode+'.cs')],OUT/('RUN_'+mode+'.cs.txt'))
print('Prepared8 normal Close/reopen frames, no InputSettings writes/device injection. No execution.')
