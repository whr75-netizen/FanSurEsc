from pathlib import Path
import sys,json,hashlib
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OLD=ROOT/'live-joint96';OUT=HERE/'capture'
sys.path.insert(0,str(ROOT/'boundary-input69'));from prepare73 import bundle
def main():
    OUT.mkdir(exist_ok=False)
    base=[ROOT/'apply-capture66/Json58Linear66.cs',ROOT/'apply-capture66/SerializedContent66.cs',ROOT/'eye-observer73/CreateOnly73.cs',ROOT/'eye-observer73/NativeSnapshot73.cs']
    deps=base+[ROOT/'uv-features64/GlobalJournal64.cs',ROOT/'uv-features64/CpuSourceCapture64.cs',ROOT/'eye-observer73/EyeReadback73.cs',ROOT/'eye-observer73/UnityEyeBuffer70.cs',ROOT/'eye-continuity77/NativeSource77.cs',ROOT/'final-eye95/MotionScope95.cs',HERE/'MotionScope97.cs',HERE/'MotionScope98.cs',HERE/'GpuTiming98.cs',HERE/'WholeEye96.cs',HERE/'NonEyeUnderlay98.cs',HERE/'NativeRetarget96.cs',HERE/'GraphSources96.cs',HERE/'LiveSurface96.cs',HERE/'LiveGraph96.cs',HERE/'LiveFinal96.cs']
    for mode in ['Read','Compile','Capture','Post','Verify']:
        s=(OLD/'motion'/(mode+'97.cs')).read_text(encoding='utf-8').replace(str(OLD/'motion'),str(OUT)).replace('eye97-','eye98-').replace('STATE97-','STATE98-').replace('TRACE97-','TRACE98-').replace('CURRENT97.json','CURRENT98.json').replace('POST97.json','POST98.json').replace('VERIFY97.json','VERIFY98.json').replace('PRIOR47_CURRENT97.json','PRIOR47_CURRENT98.json').replace('MotionScope97 motion82','MotionScope98 motion82').replace('new MotionScope97(','new MotionScope98(')
        if mode in ['Compile','Capture']:
            s=s.replace('LiveFinal96 final96;','LiveFinal96 final96;GpuTiming98 timing98;')
            s=s.replace('final96=new LiveFinal96(n,retarget89,joint96,current91);','final96=new LiveFinal96(n,retarget89,joint96,current91);timing98=new GpuTiming98();')
            s=s.replace('final96?.Dispose();','timing98?.Dispose();final96?.Dispose();')
            needle='    var engine96=joint96.Source.Engine;'
            addition='''
    foreach(var group98 in new[]{new{n="legacy96-final",a=final96.Legacy98},new{n="actual-world98-",a=final96.World98},new{n="current-non-eye98-",a=current91.NonEye98.Fields}})for(int c98=0;c98<group98.a.Length;c98++){var t98=group98.a[c98];var filename98=group98.n+c98+".plane";CpuSourceCapture64.WriteOwnedPlane(Path.Combine(output,filename98),group98.n.StartsWith("current-non-eye")?Frame(f,"physical-source98",serial):nativeFrame87,t98,new RectInt(0,0,t98.width,t98.height),"98 same-frame exact source underlay/legacy comparison","RGBA, typed source metadata/UV or exact world sample/device depth","raw Float32","raw RT memory");planes.Add(new Obj58{["file"]=filename98,["sourceId"]=sourceId,["frameIndex"]=frameIndex,["renderSerial"]=serial});}
    report["underlay98"]=new Obj58{["frame"]=current91.NonEye98.Frame,["nonEyeDraws"]=current91.NonEye98.Draws,["worldSerial"]=n.worldSerial,["presentSerial"]=n.presentSerial,["worldView"]=M(n.worldView),["worldProjection"]=M(n.worldProjection),["nearFarReversedZ"]=new Arr58(n.gameCamera.nearClipPlane,n.gameCamera.farClipPlane,SystemInfo.usesReversedZBuffer),["profiling"]=timing98.Read(),["sameFrameLegacyAndCandidate"]=true,["product77Unchanged"]=true};
'''
            assert needle in s;s=s.replace(needle,addition+'\n'+needle).replace('Bounded28-sample motion observation budget','Bounded35-sample motion and evaluated Close observation budget')
        p=OUT/(mode+'98.cs');p.write_text(s,encoding='utf-8');bundle((deps if mode in ['Compile','Capture']else base)+[p],OUT/('RUN_'+mode+'98.cs.txt'))
    (OUT/'GLOBAL_NAMES66.json').write_bytes((OLD/'motion/GLOBAL_NAMES66.json').read_bytes());relay=(OLD/'motion/relay97.py').read_text().replace("'Post97','Verify97')","'Post97','Verify97','Read98','Compile98','Capture98','Post98','Verify98','Import98')");(OUT/'relay98.py').write_text(relay,encoding='utf-8')
    imp='''using System;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEditor;
internal class CommandScript:IRunCommand{public void Execute(ExecutionResult result){if(EditorApplication.isPlayingOrWillChangePlaymode||EditorApplication.isCompiling||EditorApplication.isUpdating)throw new InvalidOperationException("Stable Edit only");string root="Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/";foreach(string file in new[]{"WholeEye98.compute","CurrentNonEye98.shader"})AssetDatabase.ImportAsset(root+file,ImportAssetOptions.ForceSynchronousImport);var c=AssetDatabase.LoadAssetAtPath<ComputeShader>(root+"WholeEye98.compute");var s=AssetDatabase.LoadAssetAtPath<Shader>(root+"CurrentNonEye98.shader");if(!c||!s)throw new InvalidOperationException("98 missing shader");var report=new Obj58{["compute"]=new Arr58(ShaderUtil.GetComputeShaderMessages(c).Select(m=>new Obj58{["message"]=m.message,["severity"]=m.severity.ToString(),["line"]=m.line})),["shader"]=new Arr58(ShaderUtil.GetShaderMessages(s).Select(m=>new Obj58{["message"]=m.message,["severity"]=m.severity.ToString(),["line"]=m.line})),["supported"]=s.isSupported,["noCSharpImport"]=true,["playing"]=EditorApplication.isPlaying};CreateOnly73.Text(@"REPORT98",report.ToString());result.Log("98 two isolated shader imports only; no Play or C# domain reload");}}'''.replace('REPORT98',str(OUT/'IMPORT98.json'))
    (OUT/'Import98.cs').write_text(imp,encoding='utf-8');bundle(base+[OUT/'Import98.cs'],OUT/'RUN_Import98.cs.txt')
    print('Prepared Read/Import/Compile/Capture35/Post/Verify98; no Unity execution yet.')
if __name__=='__main__':main()
