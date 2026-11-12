"""Connect bounded source-carrier shade history to the existing84 observer.

No RGB history, GPU->CPU selection readback, extra compute kernel or full search.
"""
from pathlib import Path
import json,hashlib,uuid
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face85'
FUNCTION=r'''
 Texture2D<float4> _PreviousAtlas85,_PreviousProjection85;float2 _PreviousOrigin85;int _History85,_PreviousWidth85,_PreviousCount85,_Levels85;
 float4 Candidate85(int2 hp,float4 cls,float4 meta,float4 uv,float4 hu,float4 hm){
  bool valid=meta.y==4&&cls.a>.5&&all(meta==hm)&&all(uv.xy==hu.xy)&&hu.z==cls.x;float4 result=float4(cls.x,cls.x,0,valid?1:0);
  if(!valid||_History85!=1)return result;int primitive=(int)meta.w-1;if(primitive<0||primitive>=_PreviousCount85)return result;
  uint i=3u*(uint)primitive;float4 a=_PreviousProjection85.Load(int3(i&127u,i>>7u,0));i++;float4 b=_PreviousProjection85.Load(int3(i&127u,i>>7u,0));i++;float4 c=_PreviousProjection85.Load(int3(i&127u,i>>7u,0));float2 ab=b.xy-a.xy,ac=c.xy-a.xy,d=uv.xy-a.xy;float det=ab.x*ac.y-ab.y*ac.x;if(det==0||!isfinite(det))return result;float u=(d.x*ac.y-d.y*ac.x)/det,v=(ab.x*d.y-ab.y*d.x)/det;float3 bary=float3(1-u-v,u,v);if(any(bary<0)||any(bary>1))return result;
  float2 before=bary.x*a.zw+bary.y*b.zw+bary.z*c.zw;before.y=272-before.y;if(!all(isfinite(before)))return result;float2 f=frac(before);float uncertainty=32*1.1920928955078125e-7*(1+max(abs(before.x),abs(before.y)));if(any(min(f,1-f)<=uncertainty))return result;
  int2 p=(int2)floor(before)-(int2)_PreviousOrigin85;if(any(p<0)||any(p>=_PreviousWidth85))return result;float4 oldMeta=_PreviousAtlas85.Load(int3(p+int2(9*_PreviousWidth85,0),0)),oldQ=_PreviousAtlas85.Load(int3(p+int2(16*_PreviousWidth85,0),0));if(oldQ.w!=1||any(oldMeta.yzw!=meta.yzw))return result;
  result.y=oldQ.x;float step=1.0/(_Levels85-1),cut=(cls.x+oldQ.x)*.5;bool use=abs(abs(oldQ.x-cls.x)-step)<=1e-6&&abs(cls.y-cut)<=step*.1;if(use){result.x=oldQ.x;result.z=1;}return result;
 }
'''
def main():
 for p in ['build','final','post/final','console','import','capture']:(G/p).mkdir(parents=True,exist_ok=True)
 assert not any((G/p/'REQUEST.json').exists()for p in ['final','import','capture'])
 shader=(H/'SelectedLight84.shader').read_text().replace('EValidation/SelectedLight84','EValidation/ShadeHistory85');shader=shader.replace(' float4 F84(V v):SV_Target{',FUNCTION+'\n float4 F84(V v):SV_Target{');shader=shader.replace('  return added?_Mask96084.Load(int3(n,0)):_Mask48084.Load(int3(n,0));','  if(plane==15)return added?_Mask96084.Load(int3(n,0)):_Mask48084.Load(int3(n,0));return Candidate85(hp,cls,meta,uv,hu,hm);');(H/'ShadeHistory85.shader').write_text(shader,encoding='utf-8',newline='\n')
 cs=(H/'Light84.cs.txt').read_text().replace('SelectedLight84/SelectedLight84.shader','ShadeHistory85/ShadeHistory85.shader');cs=cs.replace('volatile bool invalid81;','volatile bool invalid81;bool previousLease85;');cs=cs.replace('void PrepareCurve81(){','void PrepareCurve81(){previousLease85=false;');cs=cs.replace('["layers"]=16','["layers"]=17,["QHistory85"]=true,["uncertaintyBinRatio85"]=.1,["worldPixel85"]=eye.full.motion.camera.orthographicSize*2/272,["outlineWorldWidth85"]=width,["orthographic85"]=camera.orthographic,["projection85"]=new Arr40(Enumerable.Range(0,16).Select(i=>eye.full.effectiveProjection[i]))')
 needle='   b.UseTexture(graph.ImportTexture(native42.output),AccessFlags.Read);b.SetRenderAttachment';assert cs.count(needle)==1
 history='''   bool history85=ReadyHistory75();p.SetInt("_History85",history85?1:0);p.SetInt("_Levels85",eye.full.faceShadeSteps);p.SetInt("_PreviousCount85",projectionTriangles75);p.SetInt("_PreviousWidth85",W77);p.SetTexture("_PreviousAtlas85",history85?Previous75.Fields[13].rt:Texture2D.blackTexture);p.SetTexture("_PreviousProjection85",history85?Previous75.projection75:projection75);if(history85){b.UseTexture(graph.ImportTexture(Previous75.Fields[13]),AccessFlags.Read);p.SetVector("_PreviousOrigin85",new Vector4(Previous75.QROI.x,272-Previous75.QROI.y-W77,0,0));}
'''
 cs=cs.replace(needle,history+needle);needle='c.cmd.DrawProcedural(Matrix4x4.identity,o.inkStyle39,0,MeshTopology.Triangles,3,1,d.properties);';assert cs.count(needle)==1
 cs=cs.replace(needle,'if(o.Previous75!=null){System.Threading.Interlocked.Increment(ref o.Previous75.Borrowers77);o.previousLease85=true;}'+needle);(H/'Light85.cs.txt').write_text(cs,encoding='utf-8',newline='\n')
 s=(H/'face84/capture/RUN.cs.txt').read_text();start=s.rfind('namespace Unity.AI.Assistant.Agent.Dynamic.Extension.Editor {\npublic sealed partial class SourceOutline40 {');s=s[:start]+cs;s=s.replace('resume-20261111\\face84','resume-20261111\\face85').replace('face84-existing-light-motion-','face85-source-Q-history-motion-').replace('Fields[13]=Target(W77*16,W77);','Fields[13]=Target(W77*17,W77);')
 start=s.index(' void ProduceLite77(');end=s.index('\npublic sealed class StreamHost77',start);block=s[start:end].replace('if(Previous75!=null)System.Threading.Interlocked.Increment(ref Previous75.Borrowers77);historyRecorded75=false;','historyRecorded75=true;').replace('var prior=Previous75;','var prior=previousLease85?Previous75:null;').replace('16*W77*W77*16','17*W77*W77*16').replace('y77*W77*16','y77*W77*17').replace('bottom-left16layers selectedLight84','bottom-left17layers selectedLight84/sourceQhistory85');s=s[:start]+block+s[end:]
 assert 'queued77=true;}historyRecorded75=true;'in s and 'var prior=previousLease85?Previous75:null;'in s
 (G/'capture/RUN.cs.txt').write_text(s,encoding='utf-8',newline='\n');compile_unity_language(G/'capture/RUN.cs.txt',G/'build/capture85.dll')
 for p in ['final','post/final','import']:
  t=(H/'face84'/p/'RUN.cs.txt').read_text().replace('resume-20261111\\face84','resume-20261111\\face85')
  if p=='import':t=t.replace('SelectedLight84','ShadeHistory85')
  (G/p/'RUN.cs.txt').write_text(t,encoding='utf-8',newline='\n');compile_unity_language(G/p/'RUN.cs.txt',G/'build'/(p.replace('/','-')+'85.dll'))
 (G/'console/ARGS.json').write_text((H/'face84/console/ARGS.json').read_text());p=G/'import/EXPECTED.json';expected=json.loads(p.read_text())if p.exists()else{'guid':uuid.uuid4().hex};expected['shaderSHA256']=hashlib.sha256((H/'ShadeHistory85.shader').read_bytes()).hexdigest();p.write_text(json.dumps(expected,indent=2))
 save={'externalCSharp9Compiled':True,'normalFrames':6,'layers':17,'readbackBytes':17*26*26*16,'computeDispatchesAdded':0,'newRasterPasses':1,'history':'same registered UV carrier, prior actual GPU Q atlas; current light budget/validity first','leaseBeforeFirstConsumerDraw':True,'releaseOnlyAfterGPUReadbackCompletionAndWriteACK':True,'projectionGridUncertaintyRejected':True,'RGBHistory':False};(G/'CPU_PREPARED85.json').write_text(json.dumps(save,indent=2));print(json.dumps(save))
if __name__=='__main__':main()
