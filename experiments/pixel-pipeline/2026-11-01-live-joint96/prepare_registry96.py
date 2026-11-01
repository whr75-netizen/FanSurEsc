from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;OUT=HERE/'registry';OUT.mkdir(exist_ok=False)
s='''using System;
using System.IO;
using System.Linq;
using System.Text;
using System.Security.Cryptography;
using UnityEngine;
using UnityEditor;
internal class CommandScript:IRunCommand{
static UnityEngine.Object Ref(UnityEngine.Object target,string field){using(var so=new SerializedObject(target)){var p=so.FindProperty(field);if(p==null)throw new InvalidOperationException(field);return p.objectReferenceValue;}}
public void Execute(ExecutionResult result){if(EditorApplication.isPlayingOrWillChangePlaymode||EditorApplication.isCompiling)throw new InvalidOperationException("Stable Edit only");var report=new Obj58();var importer=AssetImporter.GetAtPath("ProjectSettings/ProjectSettings.asset");string text=importer?EditorJsonUtility.ToJson(importer):null;report["importerAvailable"]=importer?true:false;report["importerId"]=importer?importer.GetEntityId().ToString():null;report["importerJSON"]=text;report["originalJSON"]=File.ReadAllText(@"SNAP96");report["sameContent"]=text==File.ReadAllText(@"SNAP96");report["settingsWrites"]=0;report["assetImports"]=0;
var boot=Resources.FindObjectsOfTypeAll<MonoBehaviour>().Single(b=>b&&b.gameObject.scene.IsValid()&&b.GetType().Name=="GameplayShellBootstrap");var n=(Ref(boot,"shellPrefab")as Component).GetComponentsInChildren<MonoBehaviour>(true).Single(b=>b&&b.GetType().Name=="NativePlayer395");var source=Ref(Ref(Ref(Ref(n,"host"),"main"),"motion"),"surface");var rows=new Arr58();using(var so=new SerializedObject(source)){var src=so.FindProperty("source");for(int slot=0;slot<src.arraySize;slot++){var r=src.GetArrayElementAtIndex(slot).objectReferenceValue as SkinnedMeshRenderer;for(int sm=0;sm<r.sharedMaterials.Length;sm++){var m=r.sharedMaterials[sm];var t=m.GetTexture("_MainTex")as Texture2D;rows.Add(new Obj58{["slot"]=slot,["subMesh"]=sm,["materialId"]=m.GetEntityId().ToString(),["material"]=m.name,["texture"]=t?t.name:null,["textureId"]=t?t.GetEntityId().ToString():null,["width"]=t?t.width:0,["height"]=t?t.height:0,["factorAlpha"]=m.GetColor("_Color").a,["alphaTest"]=m.IsKeywordEnabled("_ALPHATEST_ON"),["alphaBlend"]=m.IsKeywordEnabled("_ALPHABLEND_ON"),["cutoff"]=m.GetFloat("_Cutoff"),["cull"]=m.GetFloat("_M_CullMode"),["wrapU"]=t?t.wrapModeU.ToString():null,["wrapV"]=t?t.wrapModeV.ToString():null});}}}report["sourceMaterials"]=rows;CreateOnly73.Text(@"OUT96",report.ToString());result.Log("96 read existing importer and immutable source-material registry; no reimport/settings writes");}}'''.replace('SNAP96',str(HERE/'capture/native-before-40.json')).replace('OUT96',str(OUT/'REGISTRY96.json'))
(OUT/'Registry96.cs').write_text(s,encoding='utf-8');sys.path.insert(0,str(ROOT/'boundary-input69'));from prepare73 import bundle
bundle([ROOT/'apply-capture66/Json58Linear66.cs',ROOT/'eye-observer73/CreateOnly73.cs',OUT/'Registry96.cs'],OUT/'RUN_Registry96.cs.txt');relay=(ROOT/'final-eye95/capture-scale-correct/relay95.py').read_text().replace("'Verify95B')","'Verify95B','Registry96')");(OUT/'relay96.py').write_text(relay,encoding='utf-8')
