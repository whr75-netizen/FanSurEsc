from pathlib import Path
import json,hashlib,uuid
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face84'
def main():
 for phase in ['build','final','post/final','console','import','capture']:(G/phase).mkdir(parents=True,exist_ok=True)
 assert not any((G/p/'REQUEST.json').exists()for p in ['final','import','capture'])
 s=(H/'face83/fix1/capture/RUN.cs.txt').read_text();a=s.rfind('namespace Unity.AI.Assistant.Agent.Dynamic.Extension.Editor {\npublic sealed partial class SourceOutline40 {');assert a>0;s=s[:a]+(H/'Light84.cs.txt').read_text();s=s.replace('resume-20261111\\face83\\fix1','resume-20261111\\face84').replace('face83-source-raster-motion-','face84-existing-light-motion-')
 s=s.replace('Fields[13]=Target(W77*23,W77);','Fields[13]=Target(W77*16,W77);')
 a=s.index('using(var b=graph.AddUnsafePass<Data>("77 bounded current native owner-history observation"');b=s.index('b.AllowPassCulling(false);',a);s=s[:a]+s[a:b].replace('foreach(int i81 in new[]{0,1,2,3,4,5,6,7,8,9,10,11,16,17,18,19,20,21})b.UseTexture(graph.ImportTexture(Fields[i81]),AccessFlags.Read);','')+s[b:]
 a=s.index('   var cmd=CommandBufferHelpers.GetNativeCommandBuffer(context.cmd);void T(string n,RTHandle t)=>',s.index(' void ProduceLite77('));b=s.index('   FrameInfo40["nativeSerial"]',a)
 s=s[:a]+'''   var cmd=CommandBufferHelpers.GetNativeCommandBuffer(context.cmd);lock(sync77){queued77=true;}if(Previous75!=null)System.Threading.Interlocked.Increment(ref Previous75.Borrowers77);historyRecorded75=false;
'''+s[b:]
 # This bounded observer now reads the already drawn atlas; never executes75.
 a=s.index(' void ProduceLite77(');b=s.index('\npublic sealed class StreamHost77',a);block=s[a:b].replace('23*W77*W77*16','16*W77*W77*16').replace('y77*W77*23','y77*W77*16').replace('bottom-left23layers CORE5/CURVE10/TRACE8','bottom-left16layers selectedLight84');s=s[:a]+block+s[b:]
 (G/'capture/RUN.cs.txt').write_text(s,encoding='utf-8',newline='\n');compile_unity_language(G/'capture/RUN.cs.txt',G/'build/capture84.dll')
 for phase in ['final','post/final']:
  t=(H/'face83/fix1'/phase/'RUN.cs.txt').read_text().replace('resume-20261111\\face83\\fix1','resume-20261111\\face84');(G/phase/'RUN.cs.txt').write_text(t,encoding='utf-8',newline='\n');compile_unity_language(G/phase/'RUN.cs.txt',G/'build'/(phase.replace('/','-')+'84.dll'))
 (G/'console/ARGS.json').write_text((H/'face83/fix1/console/ARGS.json').read_text())
 t=(H/'face81/import/RUN.cs.txt').read_text().replace('resume-20261111\\face81\\import','resume-20261111\\face84\\import').replace('FeatureCurve81','SelectedLight84');(G/'import/RUN.cs.txt').write_text(t,encoding='utf-8',newline='\n');compile_unity_language(G/'import/RUN.cs.txt',G/'build/import84.dll')
 p=G/'import/EXPECTED.json'
 expected=json.loads(p.read_text())if p.exists()else{'guid':uuid.uuid4().hex};expected['shaderSHA256']=hashlib.sha256((H/'SelectedLight84.shader').read_bytes()).hexdigest();p.write_text(json.dumps(expected,indent=2))
 d={'externalCSharp9Compiled':True,'normalFrames':6,'atlasLayers':16,'readbackBytes':16*26*26*16,'newComputeDispatches':0,'newRasterPasses':1,'sameExistingProducerNoLightReevaluation':True,'strictAddressUVSourceIdentityNoUnknownRepair':True,'maxGeometryBytesPerFrame':262144};(G/'CPU_PREPARED84.json').write_text(json.dumps(d,indent=2));print(json.dumps(d))
if __name__=='__main__':main()
