"""Reuse77 external runner/lifetimes; CPU compile only, no Unity call here."""
from pathlib import Path
import json,re,ctypes as C,sys
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face81'

def main():
 for d in['capture','final','post/final','console','import','build']:(G/d).mkdir(parents=True,exist_ok=True)
 assert not(G/'capture/REQUEST.json').exists()
 if(G/'import/REQUEST.json').exists():assert(G/'import/COMPLETE.json').exists()
 s=(H/'face77/loop120/capture/RUN.cs.txt').read_text().replace('resume-20261111\\face77\\loop120','resume-20261111\\face81').replace('face77-bounded-runtime-stream-','face81-current-curve-motion-')
 def rep(a,b):
  nonlocal s
  assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
 rep('bool started,disposed;int loopPhase77;int direction;','bool started,disposed,turned;int direction;')
 rep('void AfterFrame(ScriptableRenderContext context,Camera[] cameras){if(Time.frameCount<FirstTarget)return;int phase=(Time.frameCount-FirstTarget+1)/8;if(phase!=loopPhase77){Queue(direction+2*phase);loopPhase77=phase;}}','void AfterFrame(ScriptableRenderContext context,Camera[] cameras){if(!turned&&Time.frameCount>=FirstTarget+2){Queue(direction+2);turned=true;}}')
 rep('var expected=D[(direction+2*Math.Max(0,index/8)+8)%8];','var expected=D[((index<3?direction:direction+2)+8)%8];')
 rep('["stage"]="bounded-loop-side-"+(Math.Max(0,index/8)%4),','["stage"]=index<3?"walk":"turn",')
 rep('motion40.FirstTarget,120,1,','motion40.FirstTarget,6,1,');rep('["plannedSourceFrames"]=120,','["plannedSourceFrames"]=6,')
 rep('const int W77=35;','const int W77=26;');s=s.replace('W77*13','W77*23').replace('13*W77*W77*16','23*W77*W77*16').replace('bottom-left13layers','bottom-left23layers').replace('y77*W77*13','y77*W77*23').replace('["maxReadbackBytes"]=254800','["maxReadbackBytes"]=248768')
 rep('x1-x0>29||y1-y0>29','x1-x0>22||y1-y0>22')
 rep('InitFinal41();if(slot77==0)','InitFinal41();InitCurve81();if(slot77==0)')
 rep('lock(sync77){reserved77=false;queued77=false;done77=false;written77=false;Receipt77=null;}','PrepareCurve81();lock(sync77){reserved77=false;queued77=false;done77=false;written77=false;Receipt77=null;}')
 rep('lock(sync77){reserved77=true;}\n  using(var b=','lock(sync77){reserved77=true;}RecordCurve81(graph);\n  using(var b=')
 rep('d.owner=this;foreach(var t in new[]{native42.output','d.owner=this;for(int i81=0;i81<10;i81++)b.UseTexture(graph.ImportTexture(Fields[i81]),AccessFlags.Read);foreach(var t in new[]{native42.output')
 needle='cmd.CopyTexture(Fields[15].rt,0,0,5*W77,0,W77,W77,Fields[13].rt,0,0,12*W77,0);';rep(needle,needle+'for(int i81=0;i81<10;i81++)cmd.CopyTexture(Fields[i81].rt,0,0,0,0,W77,W77,Fields[13].rt,0,0,(13+i81)*W77,0);')
 rep('Received77?.Invoke(receipt);','Received77?.Invoke(receipt);if(invalid81)Fail(new InvalidOperationException("81 current source renderer ordering invalid; readback completed, stop"));')
 # Save actual producer inputs for sourceId/frame/edge provenance checks.
 source=(H/'Curve81.cs.txt').read_text();needle='invalid81=false;';assert source.count(needle)==1
 s+='\n'+source;rep('public void Execute(ExecutionResult result){','public void Execute(ExecutionResult result){if(SystemInfo.supportedRenderTargetCount<3)throw new InvalidOperationException("81 requires3 MRT before any state change");var shader81=AssetDatabase.LoadAssetAtPath<Shader>("Assets/EUnityValidation01/FeatureCurve81/FeatureCurve81.shader");if(!shader81||ShaderUtil.ShaderHasError(shader81))throw new InvalidOperationException("81 shader absent/error before state change");')
 (G/'capture/RUN.cs.txt').write_text(s,encoding='utf-8',newline='\n');compile_unity_language(G/'capture/RUN.cs.txt',G/'build/curve81.dll')
 for phase in['final','post/final']:
  ss=(H/'face77/loop120'/phase/'RUN.cs.txt').read_text().replace('resume-20261111\\face77\\loop120','resume-20261111\\face81');p=G/phase/'RUN.cs.txt'
  if p.exists():assert p.read_text()==ss
  else:p.write_text(ss,encoding='utf-8',newline='\n')
  compile_unity_language(p,G/'build'/('post81.dll'if phase.startswith('post')else'pre81.dll'))
 (G/'console/ARGS.json').write_text((H/'face77/loop120/console/ARGS.json').read_text());result={'externalCSharp9Compiled':True,'normalFrames':6,'sameFrameRawAndJoint':True,'readbackBytes':248768,'oldComputeThreads':1024,'newRasterCallsPerFrame':4,'sourceSegmentCap':1024,'MRTCount':3,'sourceFaceCount':4232,'newGPUExecuted':False,'minimalAliasedCurveNotGeneralVariableWidth':True,'sampleGateNotFullFootprintAlpha':True};(G/'CPU_PREPARED81.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':main()
