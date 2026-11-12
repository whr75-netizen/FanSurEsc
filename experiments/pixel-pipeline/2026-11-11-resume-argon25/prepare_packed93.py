"""Fix only observation packing: preserve262144B request/codec caps.

The RGB/history atlas stays22planes. Observe16 identity/RGB planes +8 curve
planes in one24plane259584B request. No shader or geometry change from93.
"""
from pathlib import Path
import json
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face93/packed1'
BASE=[0,1,2,3,4,5,6,7,8,9,11,13,14,16,19,20]
def main():
 for d in ['build','capture','final','post/final','console']:(G/d).mkdir(parents=True,exist_ok=True)
 assert not any((G/d/'REQUEST.json').exists()for d in ['capture','final']);s=(H/'face93/capture/RUN.cs.txt').read_text();marker='namespace Unity.AI.Assistant.Agent.Dynamic.Extension.Editor {\npublic sealed partial class SourceOutline40 {\n readonly RTHandle[] ribbonFields93';pos=s.rfind(marker);assert pos>0;s=s[:pos]+(H/'Ribbon93.cs.txt').read_text();s=s.replace('resume-20261111\\face93\\capture','resume-20261111\\face93\\packed1\\capture').replace('face93-native-ribbon-','face93-packed-native-ribbon-').replace('Fields[13]=Target(W77*34,W77);','Fields[13]=Target(W77*22,W77);').replace('34*W77*W77*16','24*W77*W77*16').replace('y77*W77*34','y77*W77*24').replace('yy*W77*34','yy*W77*24').replace('["layers"]=34','["layers"]=24').replace('bottom-left34layers sourceValue89/currentQ-and-historyQ','bottom-left24layers packedRibbon93 BASE16+CURVE8').replace('["maxReadbackBytes"]=367744','["maxReadbackBytes"]=259584');s=s.replace('yy*W77*24+20*W77+xx','yy*W77*24+15*W77+xx')
 old='for(int i93=0;i93<12;i93++)cmd.CopyTexture(ribbonFields93[i93].rt,0,0,0,0,W77,W77,Fields[13].rt,0,0,(22+i93)*W77,0);';new='var columns93=new[]{'+','.join(map(str,BASE))+'};for(int i93=0;i93<16;i93++)cmd.CopyTexture(Fields[13].rt,0,0,columns93[i93]*W77,0,W77,W77,readbackPack93.rt,0,0,i93*W77,0);for(int i93=0;i93<8;i93++)cmd.CopyTexture(ribbonFields93[4+i93].rt,0,0,0,0,W77,W77,readbackPack93.rt,0,0,(16+i93)*W77,0);';assert s.count(old)==1;s=s.replace(old,new)
 old='foreach(var t93 in ribbonFields93)b.UseTexture(graph.ImportTexture(t93),AccessFlags.Read);';assert s.count(old)==1;s=s.replace(old,old+'b.UseTexture(graph.ImportTexture(readbackPack93),AccessFlags.Write);');old='cmd.RequestAsyncReadback(Fields[13].rt,0,r=>{';assert s.count(old)==1;s=s.replace(old,'cmd.RequestAsyncReadback(readbackPack93.rt,0,r=>{');assert 'bytes.Length>262144'in s and 'n>262144'not in s and 'Fields[13]=Target(W77*22,W77);'in s and 'EvaluateForm115'not in s and 'BoundRun115'not in s
 (G/'capture/RUN.cs.txt').write_text(s,encoding='utf-8',newline='\n');compile_unity_language(G/'capture/RUN.cs.txt',G/'build/packed93.dll')
 for mode in ['final','post/final']:
  t=(H/'face93'/mode/'RUN.cs.txt').read_text().replace('resume-20261111\\face93','resume-20261111\\face93\\packed1');(G/mode/'RUN.cs.txt').write_text(t,encoding='utf-8',newline='\n');compile_unity_language(G/mode/'RUN.cs.txt',G/'build'/(mode.replace('/','-')+'93.dll'))
 (G/'console/ARGS.json').write_text((H/'face93/console/ARGS.json').read_text());d={'externalCSharp9Compiled':True,'readbackBytes':24*26*26*16,'existingRequestAndCodecCap':262144,'mainHistoryAtlasLayersUnchanged':22,'packedBaseColumns':BASE,'packedRibbonColumns':list(range(4,12)),'sourceIdentityAndCurrentRGBProofRetained':True,'originalPointSourceColourProbeNotIncluded':True,'rawRibbonGeometryProofNotIncluded':True,'geometryAndShaderUnchanged':True,'newGPUExecuted':False};(G/'CPU_PREPARED93.json').write_text(json.dumps(d,indent=2));print(json.dumps(d))
if __name__=='__main__':main()
