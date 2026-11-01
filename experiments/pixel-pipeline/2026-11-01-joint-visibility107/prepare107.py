from pathlib import Path
import sys,json,hashlib
H=Path(__file__).resolve().parent;R=H.parent;OLD=R/'live-curve106';D=H/'capture'
sys.path.insert(0,str(R/'boundary-input69'));from prepare73 import bundle

def plans():
    files={}
    def add(name,s):files[str(H/name)]=s
    # External dynamic helpers only. No C# Assets import or product edits.
    whole=(R/'live-underlay98/WholeEye96.cs').read_text(encoding='utf-8').replace('WholeEye96','WholeEye107')
    whole=whole.replace('public GraphicsBuffer World{','public GraphicsBuffer Evidence107{get;private set;} readonly Triangle[] cpuTriangles107;readonly Vector2[] cpuUV107;readonly Vector4[] cpuRest107;readonly MaterialData[] cpuMaterials107;readonly int[] cpuParts107;Vector4[] cpuWorld107;\n public GraphicsBuffer World{')
    whole=whole.replace('Scope=scope;VertexCount=', 'cpuTriangles107=sourceTriangles;cpuUV107=sourceUV;cpuRest107=sourceRest;cpuMaterials107=sourceMaterials;cpuParts107=partMap;cpuWorld107=initialWorld;Scope=scope;VertexCount=')
    whole=whole.replace('Decisions,Witness})Drop(b);','Decisions,Witness,Evidence107})Drop(b);').replace('Layers=B(n*20,16);','Evidence107=B(n*8,16);Layers=B(n*20,16);')
    whole=whole.replace('World.SetData(data);','cpuWorld107=data;World.SetData(data);').replace('Bind("_Visibility96",Visibility);Bind("_Queries96",Queries);','Bind("_Visibility96",Visibility);Bind("_QueryEvidence107",Evidence107);Bind("_Queries96",Queries);')
    evidence='''
 public int PartTriangle107(int part,int primitive)=>cpuParts107[part*PrimitiveStride+primitive-1];
 public Obj58 TriangleEvidence107(int id){var t=cpuTriangles107[id];var vs=new[]{t.v.x,t.v.y,t.v.z};Arr58 V(Vector4 v)=>new Arr58(v.x,v.y,v.z,v.w);var m=cpuMaterials107[t.v.w];return new Obj58{["triangle"]=id,["source"]=new Arr58(t.source.x,t.source.y,t.source.z),["material"]=t.v.w,["world"]=new Arr58(vs.Select(i=>V(cpuWorld107[i]))),["rest"]=new Arr58(vs.Select(i=>V(cpuRest107[i]))),["uv"]=new Arr58(vs.Select(i=>new Arr58(cpuUV107[i].x,cpuUV107[i].y))),["alpha"]=V(m.alphaCullWrap),["atlas"]=V(m.atlas)};}
'''
    whole=whole.replace(' void Check(){',evidence+' void Check(){')
    add('WholeEye107.cs',whole)
    add('LiveSurface107.cs',(R/'live-underlay98/LiveSurface96.cs').read_text(encoding='utf-8').replace('LiveSurface96','LiveSurface107').replace('WholeEye96','WholeEye107'))
    dense=(R/'live-underlay98/NativeRetarget96.cs').read_text(encoding='utf-8').replace('NativeRetarget96','NativeDense107')
    dense=dense.replace('Mathf.RoundToInt((max.x-min.x)*4)','Mathf.RoundToInt((max.x-min.x)*8)').replace('Mathf.RoundToInt((max.y-min.y)*4)','Mathf.RoundToInt((max.y-min.y)*8)').replace('Info["sampler"]=4','Info["sampler"]=8')
    add('NativeDense107.cs',dense)
    forward=(OLD/'ForwardCanvas106.cs').read_text(encoding='utf-8').replace('ForwardCanvas106','ForwardCanvas107').replace('LiveSurface96','LiveSurface107').replace('ForwardEye106.compute','ForwardEye107.compute')
    forward=forward.replace('readonly NativeRetarget96 native;','readonly NativeRetarget96 native;public readonly NativeDense107 DenseNative;public readonly LiveSurface107 DenseSource;')
    forward=forward.replace('public RTHandle[] Fields{','public RTHandle[] LegacyFields{get;private set;}public GraphicsBuffer[] LegacyResults{get;private set;}\n public RTHandle[] Fields{')
    forward=forward.replace('["irisWhiteProtection"]=true','["irisWhiteProtection"]=false,["sameSampleJointVisibility107"]=true,["denseSampler"]=8,["denseSize"]=new Arr58(DenseNative.currentWidth,DenseNative.currentHeight)')
    forward=forward.replace('Curves=new SourceCurves106(e,reg);canvas.AfterCanvas=Record;','Curves=new SourceCurves106(e,reg);DenseNative=new NativeDense107(e,regPath,diag+"-dense107");DenseSource=new LiveSurface107(e,AssetDatabase.LoadAssetAtPath<ComputeShader>("Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/ForwardEye107.compute"),ids,px,py);canvas.AfterCanvas=Record;')
    forward=forward.replace('catch{Curves?.Dispose();','catch{DenseSource?.Dispose();DenseNative?.Dispose();Curves?.Dispose();')
    forward=forward.replace('Fields=new RTHandle[4];BaselineFields=new RTHandle[4];','Fields=new RTHandle[4];BaselineFields=new RTHandle[4];LegacyFields=new RTHandle[4];')
    needle='Fields[i]=RTHandles.Alloc(w,h,colorFormat:'
    pos=forward.index('try{for(int i=0;i<4;i++){')+len('try{for(int i=0;i<4;i++){')
    forward=forward[:pos]+'LegacyFields[i]=RTHandles.Alloc(w,h,colorFormat:UnityEngine.Experimental.Rendering.GraphicsFormat.R32G32B32A32_SFloat,enableRandomWrite:true,filterMode:FilterMode.Point,name:"107 same-input106");'+forward[pos:]
    forward=forward.replace('Results=new GraphicsBuffer[4];try{for(int i=0;i<4;i++)Results[i]=new GraphicsBuffer(GraphicsBuffer.Target.Structured,n,16);}','Results=new GraphicsBuffer[4];LegacyResults=new GraphicsBuffer[4];try{for(int i=0;i<4;i++){Results[i]=new GraphicsBuffer(GraphicsBuffer.Target.Structured,n,16);LegacyResults[i]=new GraphicsBuffer(GraphicsBuffer.Target.Structured,n,16);}}')
    forward=forward.replace('native.RecordGraph(graph,resources);Source.Update();','native.RecordGraph(graph,resources);DenseNative.RecordGraph(graph,resources);DenseSource.Update();DenseSource.Engine.Resize(DenseNative.currentWidth,DenseNative.currentHeight,DenseSource.Scope);Source.Update();')
    forward=forward.replace('foreach(var buffer in engine.Buffers)', 'foreach(var buffer in DenseSource.Engine.Buffers)b.UseBuffer(graph.ImportBuffer(buffer),AccessFlags.ReadWrite);foreach(var a in DenseNative.Handles96)foreach(var t in a)b.UseTexture(graph.ImportTexture(t),AccessFlags.Read);foreach(var buffer in LegacyResults)b.UseBuffer(graph.ImportBuffer(buffer),AccessFlags.ReadWrite);foreach(var buffer in engine.Buffers)')
    forward=forward.replace('Fields.Concat(BaselineFields)','Fields.Concat(BaselineFields).Concat(LegacyFields)')
    forward=forward.replace('var cmd=CommandBufferHelpers.GetNativeCommandBuffer(context.cmd);var e=Source.Engine;','var cmd=CommandBufferHelpers.GetNativeCommandBuffer(context.cmd);for(int p=0;p<4;p++)DenseSource.Engine.Pack(cmd,p,DenseNative.layers[p],true);DenseSource.Engine.Dispatch(cmd,data.view,data.projection,false,0);var e=Source.Engine;')
    # One common binding implementation dispatches the original106 and new107.
    start=forward.index('  Curves.Upload(cmd);');end=forward.index('RenderedFrame=Time.frameCount;',start)
    block=forward[start:end]
    legacy=block.replace('  Curves.Upload(cmd);','').replace('var cs=e.Shader;int k=cs.FindKernel("ApplyCurve106");','var cs=e.Shader;int k=cs.FindKernel(kernel);').replace('Results[i]','targetBuffers[i]').replace('Compose(cmd,Results[0],Results[1],Results[2],Fields);','Compose(cmd,targetBuffers[0],targetBuffers[1],targetBuffers[2],targetFields);')
    forward=forward[:start]+'  Curves.Upload(cmd);Dispatch("ApplyCurve106",LegacyResults,LegacyFields);Dispatch("ResolveCurve107",Results,Fields);\n  void Dispatch(string kernel,GraphicsBuffer[] targetBuffers,RTHandle[] targetFields){'+legacy+'}\n  '+forward[end:]
    forward=forward.replace('Fields=null;BaselineFields=null;','if(LegacyFields!=null)foreach(var f in LegacyFields)f?.Release();Fields=null;BaselineFields=null;LegacyFields=null;')
    forward=forward.replace('Results=null;}','if(LegacyResults!=null)foreach(var b in LegacyResults)b?.Dispose();Results=null;LegacyResults=null;}')
    forward=forward.replace('Curves?.Dispose();Source?.Dispose();native?.Dispose();ReleaseBuffers();','DenseSource?.Dispose();DenseNative?.Dispose();Curves?.Dispose();Source?.Dispose();native?.Dispose();ReleaseBuffers();')
    add('ForwardCanvas107.cs',forward)
    hold=(OLD/'Sequence106.cs').read_text(encoding='utf-8').split('public sealed class Sequence106')[0].replace('HoldClose106','HoldMorph107').replace('readonly float previous;','readonly float previous,desired;').replace('SetBlendShapeWeight(morph,100)','SetBlendShapeWeight(morph,desired)').replace('NativePlayer395 native,string path){n=', 'NativePlayer395 native,string path,float value){desired=value;if(value<0||value>100)throw new ArgumentOutOfRangeException(nameof(value));n=').replace('GetBlendShapeWeight(morph)!=100','GetBlendShapeWeight(morph)!=desired')
    add('HoldMorph107.cs',hold)
    for mode in ['Read','Compile','Capture','Post','Import']:
        s=(OLD/'capture'/(mode+'106.cs')).read_text(encoding='utf-8').replace(str(OLD/'capture'),str(D))
        if mode in ['Compile','Capture']:
            s=s.replace('ForwardCanvas106','ForwardCanvas107').replace('Sequence106','Sequence107').replace('"eye106-"','"eye107-"').replace('STATE106-','STATE107-').replace('TRACE106-','TRACE107-')
            begin=s.index(' void JointBuffer102(');s=s[:begin]+(H/'CaptureFragment107.cs').read_text(encoding='utf-8')+'\n}\n'
        if mode=='Import':s=s.replace('ForwardEye106.compute','ForwardEye107.compute').replace('IMPORT106','IMPORT107')
        add('capture/'+mode+'107.cs',s)
    print(json.dumps(files),flush=True)

def build():
    base=[R/'apply-capture66/Json58Linear66.cs',R/'apply-capture66/SerializedContent66.cs',R/'eye-observer73/CreateOnly73.cs',R/'eye-observer73/NativeSnapshot73.cs']
    deps=base+[R/'uv-features64/GlobalJournal64.cs',R/'uv-features64/CpuSourceCapture64.cs',R/'eye-observer73/EyeReadback73.cs',R/'eye-observer73/UnityEyeBuffer70.cs',R/'source-palette58/SourcePalette58.cs',R/'renderer-family59/RendererFamily59.cs',R/'layer-zero101/SkinSource101.cs',R/'layer-zero101/LayerZero101.cs',R/'live-underlay98/NativeRetarget96.cs',H/'NativeDense107.cs',H/'LiveSurface107.cs',H/'WholeEye107.cs',R/'live-underlay98/MotionScope97.cs',R/'hair-isolation100/HairDrawScope100.cs',OLD/'SourceCurves106.cs',H/'ForwardCanvas107.cs',OLD/'MotionClose106.cs',H/'HoldMorph107.cs',H/'Sequence107.cs']
    for mode in ['Read','Compile','Capture','Post','Import']:
        bundle((deps if mode in ['Compile','Capture']else base)+[D/(mode+'107.cs')],D/('RUN_'+mode+'107.cs.txt'))
    bundle(deps+[D/'Compile107.cs'],D/'RUN_Compile107b.cs.txt')
    bundle(base+[D/'ShaderPost107.cs'],D/'RUN_ShaderPost107.cs.txt')
    bundle(base+[D/'Support107.cs'],D/'RUN_Support107b.cs.txt')
    bundle(base+[D/'Import107b.cs'],D/'RUN_Import107b.cs.txt')
    bundle(base+[D/'Import107c.cs'],D/'RUN_Import107c.cs.txt')
    for mode in ['Read','Capture','Post']:
        bundle((deps if mode=='Capture'else base)+[H/'capture-b'/(mode+'107b.cs')],D/('RUN_'+mode+'107b.cs.txt'))
    (H/'capture-b/GLOBAL_NAMES66.json').write_bytes((OLD/'capture/GLOBAL_NAMES66.json').read_bytes())
    (D/'GLOBAL_NAMES66.json').write_bytes((OLD/'capture/GLOBAL_NAMES66.json').read_bytes())
    wrapper=(OLD/'capture/relay106.py').read_text(encoding='utf-8')
    lines=wrapper.splitlines();ix=next(i for i,s in enumerate(lines)if s.startswith('assert mode in ('));lines[ix]="assert mode in ('Read107','Compile107','Compile107b','Capture107','Post107','Import107','Import107b','Import107c','ShaderPost107','Support107','Support107b','Read107b','Capture107b','Post107b')"
    wrapper='\n'.join(lines)+'\n';begin=wrapper.index('if marker.exists():');end=wrapper.index('connections=[]',begin)
    wrapper=wrapper[:begin]+"assert not marker.exists(),'Previous request exists: inspect outcome; use a new recorded source revision, never overwrite or repeat'\n"+wrapper[end:]
    (D/'relay107.py').write_text(wrapper,encoding='utf-8')
    shader=(OLD/'ForwardEye106.compute').read_text(encoding='utf-8')
    shader='#pragma kernel ResolveCurve107\n'+shader+'\n'+(H/'JointCurve107.hlsl').read_text(encoding='utf-8')
    shader=shader.replace('StructuredBuffer<float4> _Queries96;', 'StructuredBuffer<float4> _Queries96;')
    # Non-mutating occlusion evidence from the existing Query traversal.
    shader='RWStructuredBuffer<float4> _QueryEvidence107;\n'+shader
    shader=shader.replace('_Visibility96[id.x]=0;if(meta.x<=0','_Visibility96[id.x]=0;_QueryEvidence107[id.x*2]=0;_QueryEvidence107[id.x*2+1]=0;if(meta.x<=0')
    shader=shader.replace('trans*=1-abounds.yx;if(trans.y<=0)break;', 'if(abounds.y>0&&(_QueryEvidence107[id.x*2].x==0||zz<_QueryEvidence107[id.x*2].y)){_QueryEvidence107[id.x*2]=float4(nd.z+1,zz,t.verticesMaterial.w+1,abounds.x);_QueryEvidence107[id.x*2+1]=float4(uv,abounds.y,depth);}trans*=1-abounds.yx;if(trans.y<=0)break;')
    assert shader.count('_QueryEvidence107[id.x*2]=0')==1 and shader.count('nd.z+1,zz,t.verticesMaterial.w+1')==1
    (H/'ForwardEye107.compute').write_bytes(shader.encode('utf-8'))
    print('107 external runner and isolated compute prepared, not executed')
if __name__=='__main__':{'plans':plans,'build':build}[sys.argv[1]]()
