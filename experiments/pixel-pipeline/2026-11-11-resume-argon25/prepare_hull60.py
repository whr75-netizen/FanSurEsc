"""Replace forced one-cell silhouette by the actual authored MToon hull, privately."""
from pathlib import Path
import hashlib,json,difflib
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face60'
def main():
 for name in['capture','shaders','build','import']:(G/name).mkdir(parents=True,exist_ok=True)
 assert not(G/'capture/REQUEST.json').exists()and not(G/'import/REQUEST.json').exists()
 # Same installed MToon vertex and alpha implementation as the existing29 pass.
 shader=(H/'face29/physical-fix/SourceOutline29.shader').read_text().replace('EValidation/SourceBoundary29','EValidation/SourceNativeHull60').replace('Name "SourceOutline29"','Name "SourceNativeHull60"')
 a='Out29 Outline29(Varyings v){float a=Alpha29(v);Out29 o;o.colour=float4(_SourceOutline29.rgb,a);o.meta=float4(-mul(_ProbeView29,float4(v.positionWS,1)).z,v.uv,1);return o;}'
 b='Out29 Outline29(Varyings v,uint primitive:SV_PrimitiveID){float a=Alpha29(v);Out29 o;o.colour=float4(_SourceOutline29.rgb,a);o.meta=float4(-mul(_ProbeView29,float4(v.positionWS,1)).z,v.uv,primitive+1);return o;}'
 assert shader.count(a)==1;shader=shader.replace(a,b);(G/'shaders/SourceNativeHull60.shader').write_text(shader,encoding='utf-8',newline='\n')
 compute=(H/'SourceDomain49.compute').read_text().replace('SourceDomain49','SourceNativeHull60')
 a='bool source=stroke.a==1&&all(stroke.rgb==_Ink41.rgb)&&proof.x>0&&proof.y>0&&proof.w>0;'
 b='bool source=stroke.a==1&&all(stroke.rgb==_Ink41.rgb)&&proof.x>0&&all(proof.yz>=0)&&all(proof.yz<=1)&&proof.w>=1&&proof.w==round(proof.w)&&proof.w<=_RegisteredTriangleCount48;'
 assert compute.count(a)==1;compute=compute.replace(a,b).replace('use?float4(1,proof.y,_OwnerScope45,proof.z)','use?float4(6,proof.w,proof.y,proof.z)')
 assert 'float4(6,proof.w,proof.y,proof.z)'in compute and'for('not in compute and'while('not in compute
 (G/'shaders/SourceNativeHull60.compute').write_text(compute,encoding='utf-8',newline='\n')
 old=(H/'face58/capture/RUN.cs.txt').read_text();s=old.replace('resume-20261111\\face58\\capture','resume-20261111\\face60\\capture').replace('face58-authored-width-','face60-native-hull-')
 def rep(a,b):
  nonlocal s
  assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
 # Current material is the authoritative source. Preserve frozen metadata as a
 # comparison only; do not fix a colour disagreement with a tolerance.
 guard='if(widthMaterial40.GetFloat("_OutlineWidth")!=width||widthMaterial40.GetFloat("_OutlineLightingMix")!=0||widthMaterial40.GetColor("_OutlineColor").r!=sourceInk.x||widthMaterial40.GetColor("_OutlineColor").g!=sourceInk.y||widthMaterial40.GetColor("_OutlineColor").b!=sourceInk.z)throw new InvalidOperationException("58 live source outline settings differ from provenance; no historical override accepted");'
 rep(guard,'')
 needle='originals=e.full.motion.surface.source.Select(v=>v.sharedMaterials).ToArray();qOriginals=e.full.legacySignalsMats.ToArray();'
 live='''var material60=originals[renderer][submesh];if(QualitySettings.activeColorSpace!=UnityEngine.ColorSpace.Linear||!material60.HasProperty("_OutlineWidthMode")||material60.GetFloat("_OutlineWidthMode")!=1||material60.GetFloat("_OutlineLightingMix")!=0)throw new InvalidOperationException("60 requires declared Linear/world-outline/unlit source mode");var colour60=material60.GetColor("_OutlineColor").linear;width=material60.GetFloat("_OutlineWidth");sourceInk=new Vector4(colour60.r,colour60.g,colour60.b,1);if(!float.IsFinite(width)||width<0||!float.IsFinite(sourceInk.x)||!float.IsFinite(sourceInk.y)||!float.IsFinite(sourceInk.z))throw new InvalidOperationException("60 finite live source required");'''
 rep(needle,needle+live)
 rep('readonly RTHandle[] Fields=new RTHandle[18]','Material hull60;readonly RTHandle[] Fields=new RTHandle[20]')
 rep('readonly Material[][] originals,depthMats;','Json40 registeredTopology60;readonly Material[][] originals,depthMats;')
 registryLine=next(x for x in s.splitlines()if 'var registry='in x and 'registryPath'in x)
 rep(registryLine,registryLine+'\n   registeredTopology60=registry;')
 rep('if(normals.Length!=vertices.Length)throw new InvalidOperationException("31 native normals missing");','foreach(var row60 in registeredTopology60["bindings"]){int rr60=(int)row60["rendererOrdinal"],sm60=(int)row60["subMesh"],n60=(int)row60["triangleCount"];if(rr60<0||rr60>=meshes.Length||sm60<0||sm60>=meshes[rr60].subMeshCount||n60<0||(long)meshes[rr60].GetIndexCount(sm60)!=3L*n60)throw new InvalidOperationException("60 registered triangle workload changed; no draw submitted");}if(normals.Length!=vertices.Length)throw new InvalidOperationException("31 native normals missing");')
 rep('Fields[17]=Target(4*QROI.width,QROI.height);','Fields[17]=Target(4*QROI.width,QROI.height);Fields[18]=Target(QROI.width,QROI.height);Fields[19]=Target(QROI.width,QROI.height);')
 needle='if(pigment.FindPass("SourcePigment29")!=2)'
 add='var shaderHull60=AssetDatabase.LoadAssetAtPath<Shader>("Assets/EUnityValidation01/SourceBoundary60/SourceNativeHull60.shader");if(!shaderHull60||!shaderHull60.isSupported)throw new InvalidOperationException("60 native hull shader unavailable");hull60=Clone(originals[renderer][submesh],shaderHull60);if(hull60.FindPass("SourceNativeHull60")!=1)throw new InvalidOperationException("60 native hull pass ABI");'
 rep(needle,add+needle)
 rep('if(inkStyle39)UnityEngine.Object.DestroyImmediate(inkStyle39);','if(inkStyle39)UnityEngine.Object.DestroyImmediate(inkStyle39);if(hull60)UnityEngine.Object.DestroyImmediate(hull60);')
 rep('DrawSource(context,stage==1);DrawStyle39(context,stage==1);','DrawSource(context,stage==1);DrawStyle39(context,stage==1);if(stage==1)DrawHull60(context);')
 needle='int st39=stage==1?8:10;'
 rep(needle,'if(stage==1){b.UseTexture(graph.ImportTexture(Fields[18]),AccessFlags.Write);b.UseTexture(graph.ImportTexture(Fields[19]),AccessFlags.Write);}'+needle)
 needle=' void DrawQ(UnsafeGraphContext context)'
 method=''' void DrawHull60(UnsafeGraphContext context){var cmd=CommandBufferHelpers.GetNativeCommandBuffer(context.cmd);var p=new MaterialPropertyBlock();p.SetMatrix("_ProbeGPUVP29",qvp);p.SetMatrix("_ProbeView29",view);p.SetVector("_SourceOutline29",sourceInk);cmd.SetRenderTarget(new[]{new RenderTargetIdentifier(Fields[18].rt),new RenderTargetIdentifier(Fields[19].rt)},styleDepth39.rt);cmd.SetViewport(new Rect(0,0,QROI.width,QROI.height));cmd.ClearRenderTarget(RTClearFlags.All,Color.clear,1,0);for(int r=0;r<meshes.Length;r++)for(int sm=0;sm<depthMats[r].Length;sm++)cmd.DrawMesh(meshes[r],matrices[r],depthMats[r][sm],sm,0,p);cmd.DrawMesh(meshes[renderer],matrices[renderer],hull60,submesh,1,p);}
'''
 rep(needle,method+needle)
 s=s.replace('SourceBoundary49/SourceDomain49.compute','SourceBoundary60/SourceNativeHull60.compute').replace('FindKernel("SourceDomain49")','FindKernel("SourceNativeHull60")')
 rep('new[]{Fields[8],Fields[9],native42.output','new[]{Fields[18],Fields[19],native42.output')
 rep('T("_Line41",Fields[8]);T("_Proof41",Fields[9]);','T("_Line41",Fields[18]);T("_Proof41",Fields[19]);')
 needle='report["frameInfo"]=producer.FrameInfo40;'
 rep(needle,'foreach(int h60 in new[]{18,19}){var ex60=producer.FieldExtent40(false,h60);tasks.Add(new Plane(false,h60,h60==18?"nativeLogicalHull60":"nativeLogicalHullProof60",ex60.x,ex60.y));}'+needle)
 rep('["liveOutlineWidthAndColourMatchFrozen"]=true','["liveOutlineWidthAndColourMatchFrozen"]=false,["liveMaterialSourceAuthoritative60"]=true')
 rep('["sourceOutlineRGB39"]=new Arr40(sourceInk.x,sourceInk.y,sourceInk.z)','["sourceOutlineRGB39"]=new Arr40(sourceInk.x,sourceInk.y,sourceInk.z),["sourceColour60"]=new Obj40{["materialInstance"]=originals[renderer][submesh].GetEntityId().ToString(),["materialAsset"]=AssetDatabase.GetAssetPath(originals[renderer][submesh]),["property"]="_OutlineColor",["storedSpace"]="sRGB per installed UniVRM importer",["storedRGB"]=new Arr40(originals[renderer][submesh].GetColor("_OutlineColor").r,originals[renderer][submesh].GetColor("_OutlineColor").g,originals[renderer][submesh].GetColor("_OutlineColor").b),["renderSpace"]="Linear via Color.linear; actual current material is authoritative",["frozenSourceColourUsed"]=false},["finalOutline60"]="Actual MToon evaluated world extrusion, width texture and alpha at logical grid. SourceCurve44 remains reference panels3/4 only; final payload is primitive+UV, not edge+t"')
 rep('["ownerKind"]="SourceCurve"','["ownerKind"]="NativeAuthoredOutlinePrimitive60"')
 rep('["productionHistoryWrites"]=false','["productionHistoryWrites"]=false,["nativeHull60"]="kind6=(native face submesh primitive+1,source UV); actual evaluated MToon world extrusion/alpha/depth; not a source curve t or fabricated point",["forcedOneCellMinimum60"]=false')
 assert 'EvaluateForm115'not in s and'BoundRun115'not in s
 (G/'capture/RUN.cs.txt').write_text(s,encoding='utf-8',newline='\n');compile_unity_language(G/'capture/RUN.cs.txt',G/'build/hull60.dll')
 # Reuse the proven shader-only import command; no C# Assets or full Refresh.
 imp=(H/'face49/import/RUN.cs.txt').read_text().replace('face49\\import','face60\\import').replace('face49\\shaders','face60\\shaders').replace('SourceBoundary49','SourceBoundary60')
 imp=imp.replace('var names=new[]{"SourceDomain49.compute"};','var names=new[]{"SourceNativeHull60.shader","SourceNativeHull60.compute"};').replace('"/SourceDomain49.compute"','"/SourceNativeHull60.compute"').replace('FindKernel("SourceDomain49")','FindKernel("SourceNativeHull60")')
 needle='var checks=NativeSnapshot40.Compare(Root,before);'
 extra='var hs60=AssetDatabase.LoadAssetAtPath<Shader>(Target+"/SourceNativeHull60.shader");if(!hs60||!hs60.isSupported)throw new InvalidOperationException("60 shader unsupported");foreach(var m in ShaderUtil.GetShaderMessages(hs60))if(m.severity.ToString()=="Error")throw new InvalidOperationException(m.message);'
 assert imp.count(needle)==1;imp=imp.replace(needle,extra+needle)
 (G/'import/RUN.cs.txt').write_text(imp,encoding='utf-8',newline='\n');compile_unity_language(G/'import/RUN.cs.txt',G/'build/import60.dll')
 registry=json.loads((H.parent/'renderer-family59/SOURCE_REGISTRY59.json').read_text());depthTriangles=sum(v['triangleCount']for v in registry['bindings'])
 result={'fullExternalCSharp9Compiled':True,'shaderOnlyImportPrepared':True,'plannedSourceFrames':1,'additionalOutlineDrawTriangles':4232,'additionalDepthDrawTriangles':depthTriangles,'totalAdditionalDrawTriangles':depthTriangles+4232,'runtimeIndexCountsMustMatchRegistry':True,'additionalLogicalRTs':2,'computeThreadsAt28x28ROI':1024,'computeLoops':0,'newBuffers':0,'readbackMaxBytesPerRequest':262144,'sourceColour':'live material stored sRGB converted to linear, no frozen RGB or tolerance','sourceOwner':'native submesh primitive+1 and source UV; separate kind6','minimumOneCellForced':False,'GPUExecuted':False,'captureSHA256':hashlib.sha256(s.encode()).hexdigest()};(G/'CPU_PREPARED60.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
if __name__=='__main__':main()
