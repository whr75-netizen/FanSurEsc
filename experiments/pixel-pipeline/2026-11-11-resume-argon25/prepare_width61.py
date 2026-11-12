"""Four bounded width calibrations on one evaluated frame; no shader changes."""
from pathlib import Path
import json,hashlib
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face61'
def main():
 p=G/'capture';p.mkdir(parents=True,exist_ok=True);assert not(p/'REQUEST.json').exists()
 old=(H/'face60/capture/RUN.cs.txt').read_text();s=old.replace('resume-20261111\\face60\\capture','resume-20261111\\face61\\capture').replace('face60-native-hull-','face61-width-calibration-')
 def rep(a,b):
  nonlocal s
  assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
 rep('readonly RTHandle[] Fields=new RTHandle[20]','readonly RTHandle[] Fields=new RTHandle[27]')
 rep('Fields[18]=Target(QROI.width,QROI.height);Fields[19]=Target(QROI.width,QROI.height);','Fields[18]=Target(QROI.width,QROI.height);Fields[19]=Target(QROI.width,QROI.height);for(int c61=20;c61<26;c61++)Fields[c61]=Target(QROI.width,QROI.height);Fields[26]=Target(8*QROI.width,2*QROI.height);')
 rep('if(stage==1){b.UseTexture(graph.ImportTexture(Fields[18]),AccessFlags.Write);b.UseTexture(graph.ImportTexture(Fields[19]),AccessFlags.Write);}','if(stage==1)foreach(var t61 in Fields.Skip(18).Take(8))b.UseTexture(graph.ImportTexture(t61),AccessFlags.Write);')
 start=s.index(' void DrawHull60(');end=s.index(' void DrawQ(',start)
 s=s[:start]+''' void DrawHull60(UnsafeGraphContext context){
  float maxWidth61=width*32/(eye.full.motion.camera.orthographicSize*2/272);int halo61=Math.Min(Math.Min(ROI.x-QROI.x,ROI.y-QROI.y),Math.Min(QROI.xMax-ROI.xMax,QROI.yMax-ROI.yMax));if(maxWidth61>=halo61)throw new InvalidOperationException("61 calibration extrusion exceeds captured halo; stop");
  var cmd=CommandBufferHelpers.GetNativeCommandBuffer(context.cmd);foreach(int c61 in new[]{0,2,3,1}){float scale61=new[]{0f,1f,8f,32f}[c61];int field61=c61==1?18:c61==0?20:c61==2?22:24;var p=new MaterialPropertyBlock();p.SetMatrix("_ProbeGPUVP29",qvp);p.SetMatrix("_ProbeView29",view);p.SetVector("_SourceOutline29",sourceInk);p.SetFloat("_OutlineWidth",width*scale61);cmd.SetRenderTarget(new[]{new RenderTargetIdentifier(Fields[field61].rt),new RenderTargetIdentifier(Fields[field61+1].rt)},styleDepth39.rt);cmd.SetViewport(new Rect(0,0,QROI.width,QROI.height));cmd.ClearRenderTarget(RTClearFlags.All,Color.clear,1,0);if(scale61<=0)continue;for(int r=0;r<meshes.Length;r++)for(int sm=0;sm<depthMats[r].Length;sm++)cmd.DrawMesh(meshes[r],matrices[r],depthMats[r][sm],sm,0,p);cmd.DrawMesh(meshes[renderer],matrices[renderer],hull60,submesh,1,p);}
 }
'''+s[end:]
 # Graph declares every source read and the copied native output atlas.
 rep('new[]{Fields[18],Fields[19],native42.output','Fields.Skip(18).Take(8).Concat(new[]{native42.output')
 rep('eye.intrinsic,eye.visible,eye.domain,eye.supportMeta})b.UseTexture','eye.intrinsic,eye.visible,eye.domain,eye.supportMeta}))b.UseTexture')
 rep('new[]{Fields[12],Fields[13],Fields[14],Fields[15],Fields[16],Fields[17]}','new[]{Fields[12],Fields[13],Fields[14],Fields[15],Fields[16],Fields[17],Fields[26]}')
 a='cmd.DispatchCompute(final41,finalKernel41,(QROI.width+7)/8,(QROI.height+7)/8,1);'
 b='''foreach(int c61 in new[]{0,2,3,1}){int field61=c61==1?18:c61==0?20:c61==2?22:24;T("_Line41",Fields[field61]);T("_Proof41",Fields[field61+1]);cmd.DispatchCompute(final41,finalKernel41,(QROI.width+7)/8,(QROI.height+7)/8,1);cmd.CopyTexture(Fields[14].rt,0,0,0,0,2*QROI.width,2*QROI.height,Fields[26].rt,0,0,c61*2*QROI.width,0);}'''
 rep(a,b)
 needle='report["frameInfo"]=producer.FrameInfo40;'
 more='''foreach(int c61 in new[]{20,21,22,23,24,25,26}){var ex61=producer.FieldExtent40(false,c61);tasks.Add(new Plane(false,c61,c61==26?"widthCompositeAtlas61":"widthCaseField"+c61,ex61.x,ex61.y));}'''
 rep(needle,more+needle)
 rep('["forcedOneCellMinimum60"]=false','["forcedOneCellMinimum60"]=false,["widthCalibration61"]=new Obj40{["scales"]=new Arr40(0,1,8,32),["defaultScale"]=1,["changedOriginalMaterial"]=false,["scope"]="owned draw MaterialPropertyBlock._OutlineWidth only",["sameEvaluatedFrame"]=frame,["finalBuffersRestoredToDefaultCase"]=true,["artPolicyAdopted"]=false}')
 assert 'EvaluateForm115'not in s and'BoundRun115'not in s
 (p/'RUN.cs.txt').write_text(s,encoding='utf-8',newline='\n');build=G/'build';build.mkdir(exist_ok=True);compile_unity_language(p/'RUN.cs.txt',build/'width61.dll')
 data={'fullExternalCSharp9Compiled':True,'scales':[0,1,8,32],'plannedSourceFrames':1,'additionalShaders':0,'additionalBuffers':0,'totalNativeHullTriangles':3*4232,'totalNativeHullDepthTriangles':3*29542,'totalNativeHullTrianglesIncludingDepth':3*(4232+29542),'finalKernelDispatches':4,'threadsPerDispatchAt28x28':1024,'shaderLoops':0,'extraRTsOver60':7,'extraRTBytesAt28x28':6*28*28*16+224*56*16,'haloExtrusionGuard':True,'originalMaterialChanged':False,'defaultSourceScale':1,'artPolicyAdopted':False,'GPUExecuted':False,'captureSHA256':hashlib.sha256(s.encode()).hexdigest()};(G/'CPU_PREPARED61.json').write_text(json.dumps(data,indent=2),encoding='utf-8');print(json.dumps(data))
if __name__=='__main__':main()
