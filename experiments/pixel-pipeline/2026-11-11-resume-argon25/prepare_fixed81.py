from pathlib import Path
import json,hashlib
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face81/fixed6'

def main():
 for d in['capture','final','post/final','console','import','build']:(G/d).mkdir(parents=True,exist_ok=True)
 assert not(G/'capture/REQUEST.json').exists()and not(G/'import/REQUEST.json').exists();s=(H/'face81/capture/RUN.cs.txt').read_text().replace('resume-20261111\\face81\\capture','resume-20261111\\face81\\fixed6\\capture').replace('face81-current-curve-motion-','face81-valid-carrier-traced-motion-');start=s.rfind('namespace Unity.AI.Assistant.Agent.Dynamic.Extension.Editor {\npublic sealed partial class SourceOutline40 {');assert start>0;s=s[:start]+(H/'Curve81.cs.txt').read_text()
 a='for(int i81=0;i81<10;i81++)b.UseTexture(graph.ImportTexture(Fields[i81]),AccessFlags.Read);';b='foreach(int i81 in new[]{0,1,2,3,4,5,6,7,8,9,10,11,16,17,18,19,20,21})b.UseTexture(graph.ImportTexture(Fields[i81]),AccessFlags.Read);';assert s.count(a)==1;s=s.replace(a,b)
 a=s.index('int[] atlasSlices={',s.index('void ProduceLite77'));b=s.index('   FrameInfo40["nativeSerial"]',a)
 pack='''int[] core81={9,12,13,14};for(int j=0;j<core81.Length;j++)cmd.CopyTexture(Fields[12].rt,0,0,core81[j]*W77,0,W77,W77,Fields[13].rt,0,0,j*W77,0);cmd.CopyTexture(Fields[15].rt,0,0,0,0,W77,W77,Fields[13].rt,0,0,4*W77,0);for(int j=0;j<10;j++)cmd.CopyTexture(Fields[j].rt,0,0,0,0,W77,W77,Fields[13].rt,0,0,(5+j)*W77,0);int[] trace81={10,11,16,17,18,19,20,21};for(int j=0;j<trace81.Length;j++)cmd.CopyTexture(Fields[trace81[j]].rt,0,0,0,0,W77,W77,Fields[13].rt,0,0,(15+j)*W77,0);
''';s=s[:a]+pack+s[b:];s=s.replace('bottom-left23layers, R77F lossless record','bottom-left23layers CORE5/CURVE10/TRACE8, R77F lossless record').replace('y77*W77*23+5*W77','y77*W77*23+3*W77').replace('y77*W77*23+6*W77','y77*W77*23+4*W77')
 (G/'capture/RUN.cs.txt').write_text(s,encoding='utf-8',newline='\n');compile_unity_language(G/'capture/RUN.cs.txt',G/'build/fixed81.dll')
 for phase in['final','post/final']:
  t=(H/'face81'/phase/'RUN.cs.txt').read_text().replace('resume-20261111\\face81','resume-20261111\\face81\\fixed6');(G/phase/'RUN.cs.txt').write_text(t,encoding='utf-8',newline='\n');compile_unity_language(G/phase/'RUN.cs.txt',G/'build'/('post.dll'if phase.startswith('post')else'pre.dll'))
 (G/'console/ARGS.json').write_text((H/'face81/console/ARGS.json').read_text())
 t=(H/'face81/width-fix/import/RUN.cs.txt').read_text().replace('resume-20261111\\face81\\width-fix\\import','resume-20261111\\face81\\fixed6\\import');(G/'import/RUN.cs.txt').write_text(t,encoding='utf-8',newline='\n');compile_unity_language(G/'import/RUN.cs.txt',G/'build/import.dll');previous=json.loads((H/'face81/width-fix/import/COMPLETE.json').read_text());(G/'import/EXPECTED.json').write_text(json.dumps({'beforeSHA':previous['afterSHA'],'afterSHA':hashlib.sha256((H/'FeatureCurve81.shader').read_bytes()).hexdigest(),'guid':previous['guid']},indent=2));d=json.loads((H/'face81/CPU_PREPARED81.json').read_text());d.update(newRasterCallsPerFrame=8,nearestValidCarrier44Reused=True,sourceEligibilityRawTraces=True,packetLayout='CORE5/CURVE10/TRACE8',maxShaderMRT=3,unityLessEqualDepthState=True);(G/'CPU_PREPARED81.json').write_text(json.dumps(d,indent=2));print(json.dumps(d))
if __name__=='__main__':main()
