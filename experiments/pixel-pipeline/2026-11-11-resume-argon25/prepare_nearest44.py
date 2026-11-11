from pathlib import Path
import json,hashlib
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face44'
def main():
 for n in ['build','capture','import','shaders','final','console']:(G/n).mkdir(parents=True,exist_ok=True)
 assert not(G/'capture/REQUEST.json').exists()and not(G/'import/REQUEST.json').exists()
 r=json.loads((H/'face42/world/capture/COMPLETE.json').read_text());assert r['restorationChecksPass']and r['ownedResourcesReleased']and r['pendingOwners']==0 and not r['errors']
 s=(H/'face42/capture/RUN.cs.txt').read_text().replace('face42\\capture','face44\\capture').replace('id="face42-native-"','id="face44-nearest-"')
 def rep(a,b):
  nonlocal s
  assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
 rep('SourceBoundary40Authored/GeoContour40Authored.shader','SourceBoundary44/GeoContour44.shader')
 rep('contourMesh40.SetUVs(1,contour40.sourceVertexIndices.Select(i=>sourceUV40[i]).ToList());','contourMesh40.SetUVs(1,contour40.sourceVertexIndices.Select(i=>sourceUV40[i]).ToList());var cp44=ContourPayload44.Build(contour40,sourceUV40);contourMesh40.SetUVs(2,cp44.a.ToList());contourMesh40.SetUVs(3,cp44.b.ToList());contourMesh40.SetUVs(4,cp44.uv.ToList());')
 rep('p.SetVector("_ContourRGB40",sourceInk);','p.SetVector("_ContourRGB40",sourceInk);p.SetVector("_ContourSize44",new Vector4(QROI.width,QROI.height,0,0));')
 rep('if(!camera.orthographic)throw new NotSupportedException("39 orthographic trial required");','if(!camera.orthographic||SystemInfo.graphicsDeviceType!=GraphicsDeviceType.Direct3D11)throw new NotSupportedException("44 currently validates orthographic D3D11 only");')
 rep('["nativeLineRaster40"]="one logical-grid native GPU line, actual source endpoint depth, no inversion/extrusion or gap fill",','["nativeLineRaster40"]="same native line coverage; nearest valid source segment t for depth/width/provenance, explicit SV_Depth",["sourcePoint44"]="orthogonal closest source point to actual SV_Position, clamped to actual finite segment; no hardware t extrapolation; not whole-pixel physical footprint proof",')
 s+='\n'+(H/'ContourPayload44.cs').read_text().replace('using System;using UnityEngine;','')
 p=G/'capture/RUN.cs.txt';p.write_text(s,encoding='utf-8',newline='\n');compile_unity_language(p,G/'build/nearest44.dll')
 original=(H/'face42/import/RUN.cs.txt').read_text();prefix,body=original.split('internal class CommandScript',1);body=body.replace('face42\\import','face44\\import').replace('face42\\shaders','face44\\shaders').replace('SourceBoundary42','SourceBoundary44').replace('new[]{"ContourNative42.compute"}','new[]{"GeoContour44.shader"}')
 # Retain the already validated compute ABI check; import only the new raster shader.
 body=body.replace('Target+"/ContourNative42.compute"','"Assets/EUnityValidation01/SourceBoundary42/ContourNative42.compute"');token='var checks=NativeSnapshot40.Compare';assert body.count(token)==1;body=body.replace(token,'var gs44=AssetDatabase.LoadAssetAtPath<Shader>(Target+"/GeoContour44.shader");if(!gs44||!gs44.isSupported)throw new InvalidOperationException("44 raster shader unavailable");foreach(var m44 in ShaderUtil.GetShaderMessages(gs44))if(m44.severity.ToString()=="Error")throw new InvalidOperationException(m44.message);'+token)
 p=G/'import/RUN.cs.txt';p.write_text(prefix+'internal class CommandScript'+body,encoding='utf-8',newline='\n');compile_unity_language(p,G/'build/import44.dll');(G/'shaders/GeoContour44.shader').write_bytes((H/'GeoContour44.shader').read_bytes());(G/'PREPARED44.json').write_text(json.dumps({'CPU_CSharp9':True,'UnityOrGPUExecuted':False,'newComputeKernel':False,'extraRTs':0,'newShader':1,'captureSHA256':hashlib.sha256(s.encode()).hexdigest(),'repair':'Actual finite source endpoints and UVs; nointerpolation endpoint payload; closest projected source point; depth and width reconstructed from that valid point; explicit device depth','remaining':'Does not certify full pixel footprint/visibility or final owner/history/colour-region policy'},indent=2),encoding='utf-8');print('nearest44 external runner compiled; GPU not executed')
if __name__=='__main__':main()
