"""Reuse the acknowledged93/94 lifecycle, changing only the observation packet.

One readback and the existing24-plane byte limit. No new product/compute path,
no additional callback, no borrowed RT release and no automatic next run.
"""
from pathlib import Path
import json,sys
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent
def prepare(name,count):
 G=H/'face95'/name
 for d in ['build','capture','final','post/final','console']:(G/d).mkdir(parents=True,exist_ok=True)
 assert not any((G/d/'REQUEST.json').exists()for d in ['capture','final'])
 source=H/'face94/held480/capture/RUN.cs.txt';s=source.read_text()
 def once(a,b):
  nonlocal s
  assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
 s=s.replace('resume-20261111\\face94\\held480\\capture','resume-20261111\\face95\\'+name+'\\capture').replace('face94-fixed-union-held480-','face95-raw2x-'+name+'-')
 once('["plannedSourceFrames"]=480','["plannedSourceFrames"]='+str(count))
 once('motion40.FirstTarget,480,24,()=>{int at94=Time.frameCount-motion40.FirstTarget;if(at94==0)CaptureUnion94("baseline");if(at94==479)CaptureUnion94("final");return motion40.Snapshot();}','motion40.FirstTarget,'+str(count)+',24,motion40.Snapshot')
 s=s.replace('EditorApplication.timeSinceStartup-started>420','EditorApplication.timeSinceStartup-started>120').replace('94 measured480-frame420s CPU-IO observation limit','95 bounded source observation120s CPU-IO limit')
 once('InitCurve81();InitRibbon93();','InitCurve81();InitRibbon93();InitFootprint95();')
 once('RecordCurve81(graph);RecordRibbon93(graph);','RecordCurve81(graph);RecordRibbon93(graph);RecordFootprint95(graph);')
 once('b.UseTexture(graph.ImportTexture(readbackPack93),AccessFlags.Write);','b.UseTexture(graph.ImportTexture(readbackPack93),AccessFlags.Read);')
 a=s.index('var columns93=new[]{');b=s.index('lock(sync77){queued77=true;}',a);s=s[:a]+s[b:]
 once('RGBAFloat32 bottom-left24layers packedRibbon93 BASE16+CURVE8, R77F lossless record','RGBAFloat32 bottom-left24layers SourceFootprint95 rawWORLD4+DEPTH4+META4+UV4+RECEIPTS8')
 once('FrameInfo40["worldSerial"]=native42.worldSerial;','FrameInfo40["worldSerial"]=native42.worldSerial;FinalizeFootprint95();')
 a=s.index('int actorCount77=0,faceCount77=0;');b=s.index('for(int yy=0;',a)
 s=s[:a]+'int actorCount77=0,faceCount77=0;for(int y77=0;y77<W77;y77++)for(int x77=0;x77<W77;x77++){bool actor95=false;for(int sample95=0;sample95<4;sample95++){int i95=16*(y77*W77*24+(8+sample95)*W77+x77);actor95|=BitConverter.ToSingle(bytes,i95)>0&&BitConverter.ToSingle(bytes,i95+4)>0;}if(actor95)actorCount77++;int address95=16*(y77*W77*24+17*W77+x77);if(BitConverter.ToSingle(bytes,address95+12)==1&&BitConverter.ToSingle(bytes,address95)>0)faceCount77++;}'+s[b:]
 once('yy*W77*24+15*W77+xx','yy*W77*24+17*W77+xx')
 once('void ReleaseRibbon93(){','void ReleaseRibbon93(){ReleaseFootprint95();')
 s+='\n'+(H/'Footprint95.cs.txt').read_text()
 assert 'EvaluateForm115'not in s and 'BoundRun115'not in s and s.count('cmd.RequestAsyncReadback(readbackPack93.rt')==1
 (G/'capture/RUN.cs.txt').write_text(s,encoding='utf-8',newline='\n');compile_unity_language(G/'capture/RUN.cs.txt',G/'build/capture95.dll')
 for d in ['final','post/final']:
  t=(H/'face94/held480'/d/'RUN.cs.txt').read_text().replace('resume-20261111\\face94\\held480','resume-20261111\\face95\\'+name)
  (G/d/'RUN.cs.txt').write_text(t,encoding='utf-8',newline='\n');compile_unity_language(G/d/'RUN.cs.txt',G/'build'/(d.replace('/','-')+'95.dll'))
 (G/'console/ARGS.json').write_bytes((H/'face94/held480/console/ARGS.json').read_bytes())
 out={'CPUCompiled':True,'plannedFrames':count,'packetBytes':259584,'oneExistingCallback':True,'sameGPUCompletionIOACKExitGate':True,'newShaderPasses':1,'shaderLoops':0,'newComputeDispatches':0,'GPUExecuted':False};(G/'CPU_PREPARED95.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
def main():
 if '--import'in sys.argv:
  G=H/'face95';(G/'import').mkdir(parents=True,exist_ok=True);assert not(G/'import/REQUEST.json').exists();s=(H/'face93/import/RUN.cs.txt').read_text().replace('resume-20261111\\face93\\import','resume-20261111\\face95\\import').replace('ProjectedRibbon93','SourceFootprint95');(G/'import/RUN.cs.txt').write_text(s,encoding='utf-8',newline='\n');compile_unity_language(G/'import/RUN.cs.txt',G/'build/import95.dll');proof=json.loads((G/'CPU_SHADER95.json').read_text());(G/'import/EXPECTED.json').write_text(json.dumps({'shaderSHA256':proof['shaderSHA256'],'UnityGeneratesMeta':True},indent=2));return
 name=sys.argv[1];prepare(name,1 if name=='one' else 64)
if __name__=='__main__':main()
