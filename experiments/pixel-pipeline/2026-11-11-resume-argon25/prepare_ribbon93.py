"""Connect bounded native-width ribbon to existing92 live colour/history.

One initial normal frame. Private shader-only import, no C# Assets/default edit.
"""
from pathlib import Path
import json,hashlib
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face93'
def main():
 for d in ['build','capture','import','console']:(G/d).mkdir(parents=True,exist_ok=True)
 assert not any((G/d/'REQUEST.json').exists()for d in ['capture','import']);proof=json.loads((G/'CPU_SHADER93.json').read_text());assert proof['shaderSHA256']==hashlib.sha256((H/'ProjectedRibbon93.shader').read_bytes()).hexdigest()
 s=(H/'face92/gpu/capture/RUN.cs.txt').read_text().replace('resume-20261111\\face92\\gpu\\capture','resume-20261111\\face93\\capture').replace('face92-native-contrast-palette-','face93-native-ribbon-').replace('motion40.FirstTarget,6,1,motion40.Snapshot','motion40.FirstTarget,1,1,motion40.Snapshot').replace('["plannedSourceFrames"]=6','["plannedSourceFrames"]=1')
 def once(a,b):
  nonlocal s
  assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
 once('InitCurve81();if(slot77==0)','InitCurve81();InitRibbon93();if(slot77==0)')
 once('PrepareCurve81();lock(sync77)','PrepareCurve81();PrepareRibbon93();lock(sync77)')
 once('lock(sync77){reserved77=true;}RecordCurve81(graph);','lock(sync77){reserved77=true;}RecordCurve81(graph);RecordRibbon93(graph);')
 once('if(inkStyle39)UnityEngine.Object.DestroyImmediate(inkStyle39);','ReleaseRibbon93();if(inkStyle39)UnityEngine.Object.DestroyImmediate(inkStyle39);')
 # Previous-atlas lookups address the same first22 planes. Only append owned
 # ribbon results after both GPU raster variants and their colour composition.
 s=s.replace('Fields[13]=Target(W77*22,W77);','Fields[13]=Target(W77*34,W77);').replace('22*W77*W77*16','34*W77*W77*16').replace('y77*W77*22','y77*W77*34').replace('yy*W77*22','yy*W77*34').replace('bottom-left22layers','bottom-left34layers').replace('["layers"]=22','["layers"]=34').replace('["maxReadbackBytes"]=248768','["maxReadbackBytes"]=367744')
 needle='using(var b=graph.AddUnsafePass<Data>("77 bounded current native owner-history observation"';a=s.index(needle);b=s.index('b.AllowPassCulling(false);',a);block=s[a:b];assert 'Fields[12],Fields[13],Fields[14]'in block and 'AccessFlags.ReadWrite'in block;block=block.replace('d.owner=this;','d.owner=this;foreach(var t93 in ribbonFields93)b.UseTexture(graph.ImportTexture(t93),AccessFlags.Read);');s=s[:a]+block+s[b:]
 once('var cmd=CommandBufferHelpers.GetNativeCommandBuffer(context.cmd);lock(sync77){queued77=true;}','var cmd=CommandBufferHelpers.GetNativeCommandBuffer(context.cmd);for(int i93=0;i93<12;i93++)cmd.CopyTexture(ribbonFields93[i93].rt,0,0,0,0,W77,W77,Fields[13].rt,0,0,(22+i93)*W77,0);lock(sync77){queued77=true;}')
 once('public void Execute(ExecutionResult result){','public void Execute(ExecutionResult result){var sr93=AssetDatabase.LoadAssetAtPath<Shader>("Assets/EUnityValidation01/ProjectedRibbon93/ProjectedRibbon93.shader");if(!sr93||ShaderUtil.ShaderHasError(sr93)||!sr93.isSupported||SystemInfo.supportedRenderTargetCount<4)throw new InvalidOperationException("93 shader/4MRT preflight before state change");')
 s+='\n'+(H/'Ribbon93.cs.txt').read_text();assert 'EvaluateForm115'not in s and 'BoundRun115'not in s;assert 'Fields[13]=Target(W77*34,W77);'in s
 (G/'capture/RUN.cs.txt').write_text(s,encoding='utf-8',newline='\n');compile_unity_language(G/'capture/RUN.cs.txt',G/'build/ribbon93.dll')
 t=(H/'face91/import/RUN.cs.txt').read_text().replace('resume-20261111\\face91\\import','resume-20261111\\face93\\import').replace('SourceValue91','ProjectedRibbon93');(G/'import/RUN.cs.txt').write_text(t,encoding='utf-8',newline='\n');compile_unity_language(G/'import/RUN.cs.txt',G/'build/import93.dll');(G/'import/EXPECTED.json').write_text(json.dumps({'shaderSHA256':proof['shaderSHA256'],'UnityGeneratesMeta':True},indent=2))
 result={'externalCSharp9Compiled':True,'initialFrames':1,'layers':34,'readbackBytes':34*26*26*16,'newComputeDispatches':0,'newRasterPasses':4,'maxMRT':4,'maxRibbonBBoxPixelsPerVariant':8192,'maxSourceTrianglesPerSet':65536,'maxSourceDrawsPerSet':16,'sharedHistoryAndPalette92Unchanged':True,'fullDisplacedFootprintVisibilityProven':False,'GPUExecuted':False};(G/'CPU_PREPARED93.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':main()
