"""Bounded fine source-light observation using the proven33 MRT path."""
from pathlib import Path
import hashlib,json,re,sys
H=Path(__file__).resolve().parent;G=H/'face35';sys.path.insert(0,str(H))
from prepare_review30 import compile_source
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 G.mkdir(exist_ok=True);(G/'build').mkdir(exist_ok=True);(G/'shaders').mkdir(exist_ok=True)
 shader=(H/'face33/shaders/QMeta33.shader').read_text().replace('EValidation/QMeta33','EValidation/FineSourceLight35').replace('v.pos.xy+=_QMetaRasterOrigin31.xy;','v.pos.xy=v.pos.xy/8+_QMetaRasterOrigin31.xy;')
 assert shader.count('v.pos.xy=v.pos.xy/8+')==1;(G/'shaders/FineSourceLight35.shader').write_text(shader,encoding='utf-8',newline='\n')
 old=(H/'face34/capture/RUN.cs.txt').read_text();code=re.sub(r'\b[A-Za-z_]\w*34\b',lambda m:m[0][:-2]+'35',old)
 def rep(a,b):
  nonlocal code
  assert code.count(a)==1,(a,code.count(a));code=code.replace(a,b)
 rep('QFields=new RTHandle[13]','QFields=new RTHandle[18]')
 rep('RTHandle depth,qDepth;','RTHandle depth,qDepth,fineDepth;Material[] fineMats;')
 rep('for(int i=0;i<qMats.Length;i++)qMats[i]=Clone(qOriginals[i],qShader);','for(int i=0;i<qMats.Length;i++)qMats[i]=Clone(qOriginals[i],qShader);var fineShader=AssetDatabase.LoadAssetAtPath<Shader>("Assets/EUnityValidation01/SourceBoundary35/FineSourceLight35.shader");if(!fineShader||!fineShader.isSupported)throw new InvalidOperationException("35 fine source-light variant unavailable");fineMats=qOriginals.Select(m=>Clone(m,fineShader)).ToArray();')
 rep('qDepth=Target(QROI.width,QROI.height,true);','qDepth=Target(QROI.width,QROI.height,true);for(int i=13;i<18;i++)QFields[i]=Target(QROI.width*8,QROI.height*8);fineDepth=Target(QROI.width*8,QROI.height*8,true);')
 rep('b.UseTexture(graph.ImportTexture(qDepth),AccessFlags.Write);','b.UseTexture(graph.ImportTexture(qDepth),AccessFlags.Write);b.UseTexture(graph.ImportTexture(fineDepth),AccessFlags.Write);')
 rep('new[]{Classification,depth,qDepth}','new[]{Classification,depth,qDepth,fineDepth}')
 rep('cmd.DrawMesh(meshes[r],matrices[r],qMats[k++],sm,0,p);','cmd.DrawMesh(meshes[r],matrices[r],qMats[k++],sm,0,p);\n  cmd.SetRenderTarget(QFields.Skip(13).Select(t=>new RenderTargetIdentifier(t.rt)).ToArray(),fineDepth.rt);cmd.SetViewport(new Rect(0,0,QROI.width*8,QROI.height*8));cmd.ClearRenderTarget(RTClearFlags.All,Color.clear,1,0);k=0;for(int r=0;r<meshes.Length;r++)for(int sm=0;sm<depthMats[r].Length;sm++)cmd.DrawMesh(meshes[r],matrices[r],fineMats[k++],sm,0,p);')
 rep('if(qMats!=null)foreach(var m in qMats)if(m)UnityEngine.Object.DestroyImmediate(m);','if(qMats!=null)foreach(var m in qMats)if(m)UnityEngine.Object.DestroyImmediate(m);if(fineMats!=null)foreach(var m in fineMats)if(m)UnityEngine.Object.DestroyImmediate(m);')
 rep('new[]{0,1,2,3,4,6}','new[]{0,2}')
 rep('foreach(int i in new[]{0,3,4,5,6,7,8,9,10,11,12})tasks.Add(new Plane(true,i,"q"+i,q.width,q.height));','foreach(int i in new[]{0,3,4,5,6,7,8,9,10,11,12,16,17})tasks.Add(new Plane(true,i,"q"+i,q.width*(i>=13?8:1),q.height*(i>=13?8:1)));')
 rep('face33/import/COMPLETE.json','face35/import/COMPLETE.json')
 # Record that fine light is a same-frame native material sample; screen-space
 # positions retain head logical units despite the8x viewport.
 rep('["legacyInputs"]=','["fineSourceLightScale"]=8,["fineSVPositionContract"]="raster.xy/8+headROIOrigin",["legacyInputs"]=')
 p=G/'capture';p.mkdir(exist_ok=True);assert not(p/'REQUEST.json').exists();(p/'RUN.cs.txt').write_text(code,encoding='utf-8',newline='\n');compile_source([p/'RUN.cs.txt'],G/'build/capture35.dll')
 shared=code[:code.rfind('namespace Unity.AI.Assistant.Agent.Dynamic.Extension.Editor {\ninternal class CommandScript')]
 imp=(H/'Import33.cs.txt').read_text().replace('face33\\import','face35\\import').replace('face33\\shaders','face35\\shaders').replace('SourceBoundary33','SourceBoundary35').replace('Json33','Json35').replace('Obj33','Obj35').replace('Arr33','Arr35').replace('NativeSnapshot33','NativeSnapshot35').replace('CreateOnly33','CreateOnly35')
 imp=imp.replace('new[]{"SourceOutline33.shader","QMeta33.shader","LineClass33.compute"}','new[]{"FineSourceLight35.shader"}')
 start=imp.index('   var compute=');end=imp.index('   var checks=',start);imp=imp[:start]+imp[end:];imp=imp.replace('Object.ReferenceEquals','System.Object.ReferenceEquals')
 p=G/'import';p.mkdir(exist_ok=True);(p/'RUN.cs.txt').write_text(shared+'\n'+imp,encoding='utf-8',newline='\n');compile_source([p/'RUN.cs.txt'],G/'build/import35.dll')
 plan={'basis':'actual33/34 executed pipeline','newShaderSHA':sha(G/'shaders/FineSourceLight35.shader'),'captureSHA':sha(G/'capture/RUN.cs.txt'),'importSHA':sha(G/'import/RUN.cs.txt'),'CPUCompile':'passed','fineGrid':[224,232],'fineMRTs':5,'computeUnchanged':True,'noNewComputeKernel':True,'SVPositionScale':8,'reconstruction':'Direct source lighting at fine surface samples, not RGB blur or interpolation of coarse Q.','output':'Fine continuous/Q/role/depth input; no forced final palette/outline activation.'};(G/'PREPARED35.json').write_text(json.dumps(plan,indent=2),encoding='utf-8',newline='\n');print(json.dumps(plan))
if __name__=='__main__':main()
