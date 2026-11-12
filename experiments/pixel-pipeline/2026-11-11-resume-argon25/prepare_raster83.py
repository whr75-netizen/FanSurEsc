"""Reuse native alpha/depth rasterisation in the feature's own placement frame.

The old cell-representative primitive is retained as a diagnostic, not visibility
evidence for a different point. No BVH, loop kernel, shared state or new manager.
"""
from pathlib import Path
import json,hashlib,sys
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;fix='--fix1'in sys.argv;G=H/('face83/fix1'if fix else'face83')

def main():
 for part in ['build','final','post/final','import','capture','console']:(G/part).mkdir(parents=True,exist_ok=True)
 assert not any((G/p/'REQUEST.json').exists()for p in ['final','import','capture'])
 shader=(H/'FeatureCurve81.shader').read_text().replace('EValidation/FeatureCurve81','EValidation/FeatureCurve83')
 shader=shader.replace('int _Role81,_Triangles81,_TraceMode81;','int _Role81,_Triangles81,_TraceMode81,_RasterSource81;')
 needle='float z=proof.x+_DepthOffset81;';assert shader.count(needle)==1
 shader=shader.replace(needle,'// Coverage was already tested against current original mesh/alpha depth\n // in this exact raw or joint source raster frame, including hair.\n if(_RasterSource81==1)source=projection.z>=1&&projection.w>=1&&projection.z<=_Triangles81&&projection.w<=_Triangles81;\n '+needle)
 (H/'FeatureCurve83.shader').write_text(shader,encoding='utf-8',newline='\n')
 cs=(H/'Curve81.cs.txt').read_text();cs=cs.replace('p.SetMatrix("_ContourVP40",translated);','p.SetMatrix("_ContourVP40",translated);p.SetMatrix("_ProbeGPUVP29",translated);p.SetMatrix("_ProbeView29",view);')
 cs=cs.replace('void InitCurve81(){','void InitCurve81(){var depthShader83=AssetDatabase.LoadAssetAtPath<Shader>("Assets/EUnityValidation01/SourceBoundary33/SourceOutline33.shader");if(!depthShader83||!depthShader83.isSupported)throw new InvalidOperationException("83 native depth shader missing");for(int rr=0;rr<originals.Length;rr++){depthMats[rr]=new Material[originals[rr].Length];for(int sm=0;sm<originals[rr].Length;sm++)depthMats[rr][sm]=Clone(originals[rr][sm],depthShader83);}')
 needle='c.cmd.DrawMesh(o.contourMesh40,Matrix4x4.identity,o.inkStyle39,0,0,p.properties);';assert cs.count(needle)==1
 cs=cs.replace(needle,'for(int rr=0;rr<o.meshes.Length;rr++)for(int sm=0;sm<o.depthMats[rr].Length;sm++)c.cmd.DrawMesh(o.meshes[rr],o.matrices[rr],o.depthMats[rr][sm],sm,0,p.properties);'+needle)
 cs=cs.replace('p.SetInt("_TraceMode81",trace81);','p.SetInt("_TraceMode81",trace81);p.SetInt("_RasterSource81",1);')
 needle='void PrepareCurve81(){';assert cs.count(needle)==1
 cs=cs.replace(needle,needle+'\n  long tris83=meshes.Sum(m=>Enumerable.Range(0,m.subMeshCount).Sum(s=>(long)m.GetIndexCount(s)/3));if(tris83>65536||originals.Sum(v=>v.Length)>16)throw new InvalidOperationException("83 source raster budget");foreach(var row in depthMats)foreach(var m in row)if(!m||m.FindPass("SourceDepth29")!=0)throw new InvalidOperationException("83 native alpha/depth pass ABI changed");\n')
 cs=cs.replace('["sourceEligibilityTraces"]=true','["sourceEligibilityTraces"]=true,["sourceVisibility83"]="current evaluated original meshes, alpha/cull/ZWrite, same source raster frame before exterior/world composition",["sourceTriangles83"]=tris83,["sourceDraws83"]=originals.Sum(v=>v.Length)')
 (H/'Curve83.cs.txt').write_text(cs,encoding='utf-8',newline='\n')
 source=(H/'face81/fixed6/capture/RUN.cs.txt').read_text();start=source.rfind('namespace Unity.AI.Assistant.Agent.Dynamic.Extension.Editor {\npublic sealed partial class SourceOutline40 {');assert start>0
 source=source[:start]+cs;source=source.replace('resume-20261111\\face81\\fixed6','resume-20261111\\'+str(G.relative_to(H))).replace('face81-valid-carrier-traced-motion-','face83-source-raster-motion-')
 needle='  ReadbackPreflight40.RequireCapabilities();try{Fields[12]=Target(W77*16,W77,uav:true);';assert source.count(needle)==1;source=source.replace(needle,'  depthMats=new Material[originals.Length][];'+needle)
 (G/'capture/RUN.cs.txt').write_text(source,encoding='utf-8',newline='\n');compile_unity_language(G/'capture/RUN.cs.txt',G/'build/capture83.dll')
 for phase in (['final','post/final']if fix else['final','post/final','import']):
  source=(H/'face81/fixed6'/phase/'RUN.cs.txt').read_text().replace('resume-20261111\\face81\\fixed6','resume-20261111\\'+str(G.relative_to(H)))
  if phase=='import':source=source.replace('\\FeatureCurve81.shader"','\\FeatureCurve83.shader"')
  (G/phase/'RUN.cs.txt').write_text(source,encoding='utf-8',newline='\n');compile_unity_language(G/phase/'RUN.cs.txt',G/'build'/(phase.replace('/','-')+'83.dll'))
 (G/'console/ARGS.json').write_text((H/'face81/fixed6/console/ARGS.json').read_text())
 previous=json.loads((H/'face81/fixed6/import/COMPLETE.json').read_text());(G/'import/EXPECTED.json').write_text(json.dumps({'beforeSHA':previous['afterSHA'],'afterSHA':hashlib.sha256((H/'FeatureCurve83.shader').read_bytes()).hexdigest(),'guid':previous['guid']},indent=2))
 (G/'CPU_PREPARED83.json').write_text(json.dumps({'externalCSharp9Compiled':True,'frames':6,'oldComputeThreads':1024,'readbackBytes':248768,'newShaderLoops':0,'rasterPasses':8,'maxMRT':3,'extraSourceDrawsPerFrameMaximum':32,'sourceTrianglesMaximumPerDrawSet':65536,'noNewDepthOffset':True,'oldRepresentativeGateRetainedAsDiagnosticOnly':True,'sourceAndDestinationVisibilitySeparated':True,'fullFootprintOrVariableWidthClaimed':False},indent=2));print('83 source raster / native alpha-depth ABI CPU compiled; no Unity or GPU executed')
if __name__=='__main__':main()
