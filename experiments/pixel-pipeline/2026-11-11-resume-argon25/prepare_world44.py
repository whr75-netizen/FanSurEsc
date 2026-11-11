from pathlib import Path
import json,hashlib
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face44/world'
def main():
 (G/'capture').mkdir(parents=True,exist_ok=True);(G/'build').mkdir(exist_ok=True);assert not(G/'capture/REQUEST.json').exists();r=json.loads((H/'face44/capture/COMPLETE.json').read_text());assert r['restorationChecksPass']and r['ownedResourcesReleased']and not r['errors']and r['pendingOwners']==0
 s=(H/'face44/capture/RUN.cs.txt').read_text().replace('face44\\capture','face44\\world\\capture').replace('id="face44-nearest-"','id="face44-world-"')
 def rep(a,b):
  nonlocal s
  assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
 rep(' static CommandScript active;SourceOutline40 producer;',' WorldOccluder42 world42;static CommandScript active;SourceOutline40 producer;')
 rep('motion40=new MotionContour40(n,Root);motion40.Start();','world42=new WorldOccluder42(n);motion40=new MotionContour40(n,Root);motion40.Start();')
 rep('cohort[i].EvidenceRoot40=Root;','cohort[i].EvidenceRoot40=Root;cohort[i].BeforePrepare41=world42.Update;cohort[i].WorldProof41=world42.Snapshot;')
 rep(' void Restore(){if(restored)return;',' void Restore(){if(restored)return;world42?.Dispose();if(world42!=null)report["worldFixture41After"]=world42.Snapshot();')
 rep('readonly RTHandle[] Fields=new RTHandle[15]','readonly RTHandle[] Fields=new RTHandle[17]')
 rep('InitFinal41();','InitFinal41();InitLegacy44();')
 rep('ReleaseFinal41();Disposed=true;','ReleaseLegacy44();ReleaseFinal41();Disposed=true;')
 rep('Fields[14]=Target(2*QROI.width,2*QROI.height,uav:true);','Fields[14]=Target(2*QROI.width,2*QROI.height,uav:true);Fields[15]=Target(QROI.width,QROI.height);Fields[16]=Target(QROI.width,QROI.height);')
 rep('b.UseTexture(graph.ImportTexture(Fields[st39+1]),AccessFlags.Write);','b.UseTexture(graph.ImportTexture(Fields[st39+1]),AccessFlags.Write);if(stage==1){b.UseTexture(graph.ImportTexture(Fields[15]),AccessFlags.Write);b.UseTexture(graph.ImportTexture(Fields[16]),AccessFlags.Write);}')
 rep('DrawStyle39(context,stage==1);','DrawStyle39(context,stage==1);if(stage==1)DrawLegacy44(context);')
 rep('foreach(int ni42 in new[]{13,14})','foreach(int ni42 in new[]{13,14,15,16})')
 rep('ni42==13?"nativeBefore42":"nativeAfter42"','ni42==13?"nativeBefore42":ni42==14?"nativeAfter42":ni42==15?"legacyLine44":"legacyProof44"')
 rep('["sourcePoint44"]="orthogonal closest source point to actual SV_Position, clamped to actual finite segment; no hardware t extrapolation; not whole-pixel physical footprint proof",','["sourcePoint44"]="orthogonal closest source point to actual SV_Position, clamped to actual finite segment; no hardware t extrapolation; not whole-pixel physical footprint proof",["pairedLegacy44"]="old/new raster same frame, mesh, viewport, matrices, original width texture and independently cleared identical native depth prepass",')
 helper=(H/'PairedCurve44.cs').read_text();helper=helper[helper.index('namespace Unity.AI.Assistant.Agent.Dynamic.Extension.Editor'):];s+='\n'+helper
 fixture=(H/'WorldOccluder42.cs').read_text();fixture=fixture[fixture.index('namespace Unity.AI.Assistant.Agent.Dynamic.Extension.Editor'):];s+='\n'+fixture;p=G/'capture/RUN.cs.txt';p.write_text(s,encoding='utf-8',newline='\n');compile_unity_language(p,G/'build/world44.dll');(G/'PREPARED_WORLD44.json').write_text(json.dumps({'CPUCompile':True,'captureSHA256':hashlib.sha256(s.encode()).hexdigest(),'newShaderImport':False,'newGPUKernel':False,'fixture':'Same owned world fixture42; nearest-source shader44 and unchanged Native395 consumer42','release':'After native GPU consumers complete and normal Edit return'},indent=2),encoding='utf-8');print('nearest44 world runner compiled, not executed')
if __name__=='__main__':main()
