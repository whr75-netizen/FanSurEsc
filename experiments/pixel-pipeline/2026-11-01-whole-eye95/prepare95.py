from pathlib import Path
import json,sys
HERE=Path(__file__).resolve().parent; ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'boundary-input69')); from prepare73 import bundle
OLD=ROOT/'visibility-backing91'; B=ROOT/'apply-capture66'; O=ROOT/'eye-observer73'; U=ROOT/'uv-features64'

def function(text,signature,new):
    start=text.index(signature); b=text.index('{',start); depth=1; i=b+1
    while depth:depth+=(text[i]=='{')-(text[i]=='}'); i+=1
    return text[:start]+new+text[i:]

def make():
    out=HERE/'capture'; assert not out.exists(); out.mkdir()
    native=(ROOT/'native-feature89/NativeRetarget89.cs').read_text()
    native=native[:native.index(' void Draw(')]
    native=native.replace('using Unity.Collections;','using Unity.Collections;\nusing UnityEngine.Rendering.Universal;\nusing UnityEngine.Rendering.RenderGraphModule;').replace('NativeRetarget89','NativeRetarget95').replace('new Material[4]','new Material[8]')
    native=native.replace('for(int i=0;i<parts.Length;i++){var src=parts[i]==3?eye.skinMaterial:eye.materials[4+parts[i]];var shader=AssetDatabase.LoadAssetAtPath<Shader>(parts[i]==3?SkinAsset:SurfaceAsset);','for(int i=0;i<8;i++){int role=parts[i/2];var src=role==3?eye.skinMaterial:eye.materials[4+role];var shader=AssetDatabase.LoadAssetAtPath<Shader>(role==3?SkinAsset:SurfaceAsset);')
    native=native.replace('"89 owned native source part "+parts[i]','"95 owned native source part "+role+" eye-slot "+(i%2)')
    native=native.replace(' void ReleaseTargets(){',' void ReleaseTargets(){ReleaseWrappers();')
    native+='''
 RTHandle[][] wrappers;RTHandle[] depthWrappers;RTHandle[] controlHandles;RTHandle controlDepth;Material controlMaterial;
 public RenderTexture[] controlFields;public int RenderedFrame{get;private set;}=-1;public int ControlFrame{get;private set;}=-1;
 sealed class Data{public NativeRetarget95 owner;public int part;}
 void ReleaseWrappers(){if(wrappers!=null)foreach(var a in wrappers)foreach(var x in a)x?.Release();if(depthWrappers!=null)foreach(var x in depthWrappers)x?.Release();wrappers=null;depthWrappers=null;}
 void Wrap(){if(wrappers!=null)return;wrappers=layers.Select(a=>a.Select(t=>RTHandles.Alloc(t,transferOwnership:false)).ToArray()).ToArray();depthWrappers=depths.Select(t=>RTHandles.Alloc(t,transferOwnership:false)).ToArray();}
 void ControlTargets(){int w=eye.roi.width*4,h=eye.roi.height*4;if(controlHandles!=null&&controlFields[0].width==w&&controlFields[0].height==h)return;if(controlHandles!=null)foreach(var t in controlHandles)t?.Release();controlDepth?.Release();controlHandles=new RTHandle[5];controlFields=new RenderTexture[5];for(int i=0;i<5;i++){controlHandles[i]=RTHandles.Alloc(w,h,colorFormat:GraphicsFormat.R32G32B32A32_SFloat,filterMode:FilterMode.Point,name:"95 source projected-coordinate control");controlFields[i]=controlHandles[i].rt;}controlDepth=RTHandles.Alloc(w,h,depthBufferBits:DepthBits.Depth32);if(!controlMaterial){var src=eye.materials[10];controlMaterial=new Material(src){shader=AssetDatabase.LoadAssetAtPath<Shader>(SurfaceAsset),hideFlags=HideFlags.DontSave};controlMaterial.shaderKeywords=src.shaderKeywords;}}
 public void RecordGraph(RenderGraph graph,UniversalResourceData resources){
  if(Disposed||!eye||eye.sampleFace!=sourceMesh)throw new InvalidOperationException("95 source/view lifetime changed");
  var f=eye.full;var current=new Vector2[2];var all=new List<Vector2>();for(int i=0;i<2;i++){int owner=Mathf.RoundToInt(eye.centres[i].w);var h=Forward(f.eyeInverse[i]);Vector2 Project(Vector2 p){var q=h*new Vector4(p.x,p.y,1,0);return new Vector2(q.x/q.z,q.y/q.z);}current[i]=Project(anchors[owner]);foreach(var p in f.contours.eyes[i].parent)all.Add(Project(p));}
  var anchor=(current[0]+current[1])*.5f;var min=new Vector2(Mathf.Floor(all.Min(p=>p.x)-anchor.x)-2,Mathf.Floor(all.Min(p=>p.y)-anchor.y)-2);var max=new Vector2(Mathf.Ceil(all.Max(p=>p.x)-anchor.x)+2,Mathf.Ceil(all.Max(p=>p.y)-anchor.y)+2);int w=Mathf.RoundToInt((max.x-min.x)*4),height=Mathf.RoundToInt((max.y-min.y)*4);if(w*height>32768)throw new InvalidOperationException("95 viewport budget");Targets(w,height);Wrap();ControlTargets();var cam=f.motion.camera;var canonical=GL.GetGPUProjectionMatrix(Matrix4x4.Ortho(min.x,max.x,-max.y,-min.y,cam.nearClipPlane,cam.farClipPlane),true);
  screenSign=-1;Bind(controlMaterial,3,0,Vector2.zero,Matrix4x4.identity,1,true);controlMaterial.SetFloat("_ScreenSign89",screenSign);
  for(int part=0;part<4;part++)for(int i=0;i<2;i++){var mat=materials[part*2+i];Bind(mat,part,Mathf.RoundToInt(eye.centres[i].w),anchor,canonical,0,true);mat.SetFloat("_ScreenSign89",screenSign);}
  for(int group=4;group>=0;group--){using var builder=graph.AddUnsafePass<Data>("95 source-local coupled parts with real graph shadows "+group,out var data);data.owner=this;data.part=group;var colours=group==4?controlHandles:wrappers[group];var depth=group==4?controlDepth:depthWrappers[group];foreach(var t in colours)builder.UseTexture(graph.ImportTexture(t),AccessFlags.Write);builder.UseTexture(graph.ImportTexture(depth),AccessFlags.Write);builder.UseAllGlobalTextures(true);if(resources.mainShadowsTexture.IsValid())builder.UseTexture(resources.mainShadowsTexture);if(resources.additionalShadowsTexture.IsValid())builder.UseTexture(resources.additionalShadowsTexture);builder.AllowPassCulling(false);builder.AllowGlobalStateModification(true);builder.SetRenderFunc(static(Data d,UnsafeGraphContext c)=>d.owner.DrawGraph(d.part,c));}
  Arr58 M(Matrix4x4 m)=>new Arr58(Enumerable.Range(0,16).Select(i=>(double)m[i]));Info["anchor"]=new Arr58(anchor.x,anchor.y);Info["bounds"]=new Arr58(min.x,min.y,max.x,max.y);Info["size"]=new Arr58(w,height);Info["canonicalGPUProjection"]=M(canonical);Info["physicalView"]=M(cam.worldToCameraMatrix);Info["headMatrix"]=M(eye.headMatrix);Info["parts"]=new Arr58(parts);Info["sampler"]=4;Info["sourceFrame"]=f.motion.sourceFrame;Info["independentMaterialsPerPartAndEye"]=true;Info["graphContext"]=true;Info["borrowedTextureOwnershipTransferred"]=false;
 }
 void DrawGraph(int part,UnsafeGraphContext context){var cmd=CommandBufferHelpers.GetNativeCommandBuffer(context.cmd);bool control=part==4;var textures=control?controlFields:layers[part];cmd.SetRenderTarget(textures.Select(t=>new RenderTargetIdentifier(t)).ToArray(),control?controlDepth.rt:depths[part]);cmd.ClearRenderTarget(RTClearFlags.All,Color.clear,1,0);cmd.SetViewport(new Rect(0,0,textures[0].width,textures[0].height));var model=eye.full.motion.surface.outputs[1].transform.localToWorldMatrix;if(control){cmd.DrawMesh(sourceMesh,model,controlMaterial,6,0);ControlFrame=Time.frameCount;}else{for(int i=0;i<2;i++)cmd.DrawMesh(sourceMesh,model,materials[part*2+i],parts[part],0);if(part==0)RenderedFrame=Time.frameCount;}}
 public void AssertRendered(){if(RenderedFrame!=Time.frameCount||ControlFrame!=Time.frameCount)throw new InvalidOperationException("95 source graph pass missing; no fallback draw");}
 public void Dispose(){if(Disposed)return;Disposed=true;ReleaseTargets();if(controlHandles!=null)foreach(var t in controlHandles)t?.Release();controlDepth?.Release();if(controlMaterial)UnityEngine.Object.DestroyImmediate(controlMaterial);foreach(var m in materials)if(m)UnityEngine.Object.DestroyImmediate(m);}
}
'''
    (HERE/'NativeRetarget95.cs').write_text(native,encoding='utf-8')
    graph=(OLD/'GraphSources93.cs').read_text().replace('GraphSources93','GraphSources95')
    graph=graph.replace('readonly EyeFeature348 eye;','readonly NativeRetarget95 retarget95;readonly EyeFeature348 eye;').replace('GraphSources95(EyeFeature348 e){eye=e;','GraphSources95(EyeFeature348 e,NativeRetarget95 nativeSource){retarget95=nativeSource;eye=e;')
    old=function(graph,' public override void RecordRenderGraph','PLACEHOLDER')
    start=graph.index(' public override void RecordRenderGraph'); end=graph.index(' void Draw(',start)
    method=graph[start:end].rstrip(); assert method.endswith('}}')
    graph=graph[:start]+method[:-1]+'retarget95.RecordGraph(graph,resources);}\n'+graph[end:]
    (HERE/'GraphSources95.cs').write_text(graph,encoding='utf-8')
    source=(OLD/'capture93b/Capture93B.cs').read_text().replace(str(OLD/'capture93b'),str(out)).replace('NativeRetarget89','NativeRetarget95').replace('GraphSources93','GraphSources95').replace('new GraphSources95(probeEye)','new GraphSources95(probeEye,retarget89)').replace('MotionScope91','MotionScope95').replace('STATE93-','STATE95-').replace('TRACE93-','TRACE95-').replace('eye93b-','eye95-')
    source=function(source,' void CameraEnd89(',''' void CameraEnd89(ScriptableRenderContext context,Camera camera){if(!native||retarget89==null||camera!=native.host.headCamera||renderError89!=null)return;try{current91.AssertRendered();retarget89.AssertRendered();retargetFrame89=Time.frameCount;calibrated89=true;}catch(Exception error){renderError89=error;}}''')
    source=source.replace('   if(previousFrame76>=0&&Time.frameCount!=previousFrame76+1)throw new InvalidOperationException("Observed frames are not consecutive");','   report["conditionalCaptureFrameGap95"]=previousFrame76<0?0:Time.frameCount-previousFrame76;')
    needle='  if(current91==null||current91.RenderedFrame!=Time.frameCount)'
    at=source.index(needle)
    extra='''  for(int ch95=0;ch95<5;ch95++){var t95=retarget89.controlFields[ch95];string file95="projected-control95-"+ch95+".plane";var f95=Frame(f,"physical-control95",serial);CpuSourceCapture64.WriteOwnedPlane(Path.Combine(output,file95),f95,t95,new RectInt(0,0,t95.width,t95.height),"95 graph projected coordinate control","RGBA/meta/rest/UV/shade","linear RGBAFloat","raw RT bottom-left");planes.Add(new Obj58{["file"]=file95,["sourceId"]=sourceId,["viewId"]=f95.viewId,["frameIndex"]=frameIndex,["renderSerial"]=serial,["textureSize"]=new Arr58(t95.width,t95.height),["roiBottomLeft"]=new Arr58(0,0,t95.width,t95.height)});}
'''
    source=source[:at]+extra+source[at:]
    (out/'Capture95.cs').write_text(source,encoding='utf-8')
    compile_source=source.replace(' public void Execute(ExecutionResult result)\n {',' public void Execute(ExecutionResult result)\n {result.Log("95 full source/joint observer compile-only; no Play");return;}\n void Prepared95(ExecutionResult result)\n {',1)
    (out/'Compile95.cs').write_text(compile_source,encoding='utf-8')
    deps=[B/'Json58Linear66.cs',B/'SerializedContent66.cs',U/'GlobalJournal64.cs',U/'CpuSourceCapture64.cs',O/'EyeReadback73.cs',O/'UnityEyeBuffer70.cs',O/'CreateOnly73.cs',O/'NativeSnapshot73.cs',ROOT/'eye-continuity77/NativeSource77.cs',HERE/'NativeRetarget95.cs',HERE/'GraphSources95.cs',HERE/'MotionScope95.cs']
    for mode in ['Compile95','Capture95']:bundle(deps+[out/(mode+'.cs')],out/('RUN_'+mode+'.cs.txt'))
    base=[B/'Json58Linear66.cs',B/'SerializedContent66.cs',O/'CreateOnly73.cs',O/'NativeSnapshot73.cs']
    for mode in ['Read','Post','Verify']:
        text=(ROOT/'visibility-backing94/capture'/(mode+'94.cs')).read_text().replace(str(ROOT/'visibility-backing94/capture'),str(out)).replace('CURRENT94.json','CURRENT95.json').replace('POST94.json','POST95.json').replace('VERIFY94.json','VERIFY95.json').replace('PRIOR47_CURRENT94.json','PRIOR47_CURRENT95.json')
        (out/(mode+'95.cs')).write_text(text,encoding='utf-8');bundle(base+[out/(mode+'95.cs')],out/('RUN_'+mode+'95.cs.txt'))
    relay=(ROOT/'visibility-backing94/capture/relay94.py').read_text().replace("'Verify94')","'Verify94','Read95','Compile95','Capture95','Post95','Verify95')")
    (out/'relay95.py').write_text(relay,encoding='utf-8');(out/'GLOBAL_NAMES66.json').write_bytes((OLD/'capture93b/GLOBAL_NAMES66.json').read_bytes())
    print('Prepared source-local Graph candidate and state-conditioned observer. No imports or execution.')

if __name__=='__main__':make()
