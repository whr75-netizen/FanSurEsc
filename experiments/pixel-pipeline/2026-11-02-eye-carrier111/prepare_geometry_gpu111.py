"""Prepare the definite pigment-alpha/carrier separation on an OWNED shader.
Canvas ownership remains a separate unadopted hypothesis. No asset write here.
"""
from pathlib import Path
import sys,json,hashlib
H=Path(__file__).resolve().parent;R=H.parent;G=H/'gpu-carrier';G.mkdir(exist_ok=False);P=R/'joint-lid107';repo=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
sys.path.insert(0,str(R/'boundary-input69'));from prepare73 import bundle
def create(p,s):
    with p.open('x',encoding='utf8',newline='\n')as f:f.write(s)
shader=(repo/'Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/NativeSurface89.shader').read_text(encoding='utf8');shader=shader.replace('Shader "EValidation/NativeSurface89"','Shader "EValidation/NativeCarrier111"');shader=shader.replace('int _Control89,_UseBank89,_SelectedOwner89;','int _Control89,_UseBank89,_SelectedOwner89,_CarrierGeometryOnly111;');needle=' float2 uv=GetMToonGeometry_Uv(v.uv);half4 src='
assert shader.count(needle)==1
shader=shader.replace(needle,''' float2 uv=GetMToonGeometry_Uv(v.uv);
 // Geometry-only carrier metadata. The source pigment supplier is a separate
 // native bank pass. Actual face/hair occluder alpha is still queried normally.
 if(_CarrierGeometryOnly111>0){O333 carrier;carrier.rgba=float4(0,0,0,1);carrier.meta=float4(-mul(_PhysicalView89,float4(v.positionWS,1)).z,round(_Auto245Role)+1,round(v.e202Owner),1);carrier.restPosition=float4(v.restHead348,facing?1:-1);carrier.uv=float4(uv,primitiveID+1,_SupportKind348);carrier.shade=0;return carrier;}
 half4 src=''',1)
create(G/'NativeCarrier111.shader',shader)
s=(H/'NativeCarrier111.cs').read_text().replace('public sealed class NativeCarrier111:','public sealed class NativeGeometryCarrier111:').replace('public NativeCarrier111(','public NativeGeometryCarrier111(').replace('public NativeCarrier111 owner;','public NativeGeometryCarrier111 owner;').replace('NativeSurface89.shader','NativeCarrier111.shader')
s=s.replace('mat.SetInt("_UseBank89",0);','mat.SetInt("_UseBank89",0);mat.SetInt("_CarrierGeometryOnly111",1);');create(G/'NativeGeometryCarrier111.cs',s)
s=(H/'ForwardCanvas111.cs').read_text().replace('ForwardCanvas111','ForwardGeometry111').replace('NativeCarrier111','NativeGeometryCarrier111');create(G/'ForwardGeometry111.cs',s)
for mode in ['Capture','Compile']:
    s=(H/'capture'/(mode+'111.cs')).read_text().replace(str(H/'capture'),str(G)).replace('ForwardCanvas111','ForwardGeometry111').replace('eye111-','eye111geo-').replace('STATE111-','STATE111G-').replace('TRACE111-','TRACE111G-')
    create(G/(mode+'111.cs'),s)
base=[R/'apply-capture66/Json58Linear66.cs',R/'apply-capture66/SerializedContent66.cs',R/'eye-observer73/CreateOnly73.cs',R/'eye-observer73/NativeSnapshot73.cs']
deps=base+[R/'uv-features64/GlobalJournal64.cs',R/'uv-features64/CpuSourceCapture64.cs',R/'eye-observer73/EyeReadback73.cs',R/'eye-observer73/UnityEyeBuffer70.cs',R/'source-palette58/SourcePalette58.cs',R/'renderer-family59/RendererFamily59.cs',R/'layer-zero101/SkinSource101.cs',R/'layer-zero101/LayerZero101.cs',R/'live-underlay98/NativeRetarget96.cs',P/'NativeDense107.cs',G/'NativeGeometryCarrier111.cs',P/'LiveSurface107.cs',H/'WholeEye111.cs',P/'HairDrawScope107.cs',R/'live-curve106/SourceCurves106.cs',G/'ForwardGeometry111.cs',R/'live-curve106/MotionClose106.cs',P/'HoldMorph107.cs',H/'Sequence111.cs']
for mode in ['Compile','Capture']:bundle(deps+[G/(mode+'111.cs')],G/('RUN_'+mode+'111G.cs.txt'))
create(G/'GLOBAL_NAMES66.json',(H/'capture/GLOBAL_NAMES66.json').read_text());wrapper=(H/'capture/relay111.py').read_text();start=wrapper.index('assert mode in (');end=wrapper.index('\n',start);wrapper=wrapper[:start]+"assert mode in ('Import111G','Compile111G','Capture111G','Post111G')"+wrapper[end:];create(G/'relay111g.py',wrapper)
importer='''using System;using System.IO;using System.Linq;using UnityEngine;using UnityEditor;
internal class CommandScript:IRunCommand{public void Execute(ExecutionResult r){
 if(EditorApplication.isPlayingOrWillChangePlaymode||EditorApplication.isCompiling||EditorApplication.isUpdating)throw new InvalidOperationException("Stable Edit required for shader-only import");
 string p="Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/NativeCarrier111.shader";int domain=AppDomain.CurrentDomain.Id;AssetDatabase.ImportAsset(p,ImportAssetOptions.ForceSynchronousImport|ImportAssetOptions.ForceUpdate);var s=AssetDatabase.LoadAssetAtPath<Shader>(p);var errors=s?ShaderUtil.GetShaderMessages(s).Where(m=>m.severity.ToString()=="Error").Select(m=>m.message).ToArray():new[]{"Shader asset unavailable"};
 CreateOnly73.Text(@"OUT",new Obj58{["shader"]=p,["supported"]=s&&s.isSupported,["errors"]=new Arr58(errors),["domainSame"]=AppDomain.CurrentDomain.Id==domain,["playing"]=EditorApplication.isPlaying,["compiling"]=EditorApplication.isCompiling,["CSharpAssetsImported"]=0}.ToString());if(!s||!s.isSupported||errors.Length>0||AppDomain.CurrentDomain.Id!=domain)throw new InvalidOperationException("Geometry carrier shader import failed");r.Log("111 shader-only geometry carrier imported; no Play or default binding changes");}}
'''.replace('OUT',str(G/'IMPORT111G.json'));create(G/'Import111G.cs',importer);bundle([base[0],base[2],G/'Import111G.cs'],G/'RUN_Import111G.cs.txt')
(G/'SHADER_PLAN111.json').write_text(json.dumps({'workspaceShaderSHA256':hashlib.sha256((G/'NativeCarrier111.shader').read_bytes()).hexdigest(),'assetPath':'Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/NativeCarrier111.shader','productShaderReplaced':False,'CSharpAssetsImport':False,'geometryPassRGBIsMetadataOnly':True,'sourceBankRGBAPathUnchanged':True,'occluderAlphaQueryUnchanged':True,'canvasPolicyNotApplied':True},indent=2)+'\n');print('Prepared owned geometry-only shader and external111G bundles; not imported/executed')
