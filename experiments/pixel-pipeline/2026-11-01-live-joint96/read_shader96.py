from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OUT=HERE/'shader-read';OUT.mkdir(exist_ok=False)
s='''using System;
using System.Linq;
using UnityEngine;
using UnityEditor;
internal class CommandScript:IRunCommand{public void Execute(ExecutionResult result){var shader=AssetDatabase.LoadAssetAtPath<ComputeShader>("Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/WholeEye96.compute");var a=ShaderUtil.GetComputeShaderMessages(shader);CreateOnly73.Text(@"OUT96",new Obj58{["device"]=SystemInfo.graphicsDeviceType.ToString(),["shaderLevel"]=SystemInfo.graphicsShaderLevel,["messages"]=new Arr58(a.Select(x=>new Obj58{["message"]=x.message,["line"]=x.line,["file"]=x.file,["severity"]=x.severity.ToString()})),["Edit"]=!EditorApplication.isPlaying}.ToString());result.Log("96 read shader compilation diagnostics only");}}'''.replace('OUT96',str(OUT/'MESSAGES96.json'))
(OUT/'ReadShader96.cs').write_text(s,encoding='utf-8');sys.path.insert(0,str(ROOT/'boundary-input69'));from prepare73 import bundle
bundle([ROOT/'apply-capture66/Json58Linear66.cs',ROOT/'eye-observer73/CreateOnly73.cs',OUT/'ReadShader96.cs'],OUT/'RUN_ReadShader96.cs.txt');relay=(ROOT/'final-eye95/capture-scale-correct/relay95.py').read_text().replace("'Verify95B')","'Verify95B','ReadShader96')");(OUT/'relay96.py').write_text(relay,encoding='utf-8')
