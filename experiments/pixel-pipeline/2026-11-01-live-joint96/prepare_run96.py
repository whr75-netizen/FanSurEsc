from pathlib import Path
import sys,shutil
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'boundary-input69'));from prepare73 import bundle
mode=sys.argv[1];assert mode in ['import','direct','reconstruct'];OUT=HERE/mode;OUT.mkdir(exist_ok=False)
if mode=='import':
    s='''using System;using System.IO;using System.Linq;using UnityEngine;using UnityEditor;
internal class CommandScript:IRunCommand{public void Execute(ExecutionResult result){
if(EditorApplication.isPlayingOrWillChangePlaymode||EditorApplication.isCompiling||EditorApplication.isUpdating)throw new InvalidOperationException("Stable Edit only");
const string path="Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/WholeEye96.compute";
AssetDatabase.ImportAsset(path,ImportAssetOptions.ForceSynchronousImport);var shader=AssetDatabase.LoadAssetAtPath<ComputeShader>(path);if(!shader)throw new InvalidOperationException("Missing compute");var messages=ShaderUtil.GetComputeShaderMessages(shader);var report=new Obj58{["kernels"]=new Arr58(new[]{"CopyAlpha","PackPart","Refit","Query","Select"}.Select(k=>new Obj58{["name"]=k,["found"]=shader.HasKernel(k)})),["errors"]=new Arr58(messages.Select(m=>new Obj58{["severity"]=m.severity.ToString(),["message"]=m.message,["line"]=m.line})),["CSharpDomainReloadRequested"]=false,["playing"]=EditorApplication.isPlaying};CreateOnly73.Text(@"REPORT_PATH96",report.ToString());result.Log("96 single new compute import; no C# import, settings or Play");}}'''.replace('REPORT_PATH96',str(OUT/'IMPORT96.json'))
    name='Import96'
else:
    s=(HERE/'RunFrozen96.cs').read_text().replace('ROOT96',str(HERE)).replace('OUTPUT96',mode+'/gpu-output').replace('REPORT96.json',mode+'/REPORT96.json').replace('COMPLETE96.marker',mode+'/COMPLETE96.marker').replace('DIRECT96','true'if mode=='direct'else'false').replace('DIRECT_DESCRIPTION96','saved exact query coordinates'if mode=='direct'else'GPU reconstructs query from current triangle barycentric and source rest point')
    name='Direct96'if mode=='direct'else'Reconstruct96'
p=OUT/(name+'.cs');p.write_text(s,encoding='utf-8');deps=[ROOT/'apply-capture66/Json58Linear66.cs',ROOT/'eye-observer73/CreateOnly73.cs']
if mode!='import':deps.append(HERE/'WholeEye96.cs')
bundle(deps+[p],OUT/('RUN_'+name+'.cs.txt'))
relay=(ROOT/'final-eye95/capture-scale-correct/relay95.py').read_text().replace("'Verify95B')","'Verify95B','"+name+"')");(OUT/'relay96.py').write_text(relay,encoding='utf-8');print('Prepared '+name+' only; not executed.')
