"""Carry actual deformed source-curve world points separately from display.
No material/primitive-reference guessing and no GPU execution.
"""
from pathlib import Path
import hashlib,json,sys
H=Path(__file__).resolve().parent;OLD=H/'gate-alpha';G=H/'native-proof';PRE=H.parent
sys.path.insert(0,str(H));from prepare_support import replace
sys.path.insert(0,str(PRE));from prepare_live import compile_cs
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assert not(G/'IMPORT_REQUEST.json').exists()and not(G/'phase-run/PHASE_REQUEST.json').exists()
 (G/'phase-run').mkdir(parents=True,exist_ok=True);(G/'import').mkdir(exist_ok=True)
 c=(OLD/'SharedSource26.compute').read_text()
 c=c.replace('int eye,bool allowShared26)','int eye,bool allowShared26,bool strictSource26)')
 c=replace(c,'((_OwnSkin113[t.source.z-1]&(1u<<eye))!=0||(allowShared26&&(_SharedSkin26[t.source.z-1]&(1u<<eye))!=0))','(!strictSource26&&((_OwnSkin113[t.source.z-1]&(1u<<eye))!=0||(allowShared26&&(_SharedSkin26[t.source.z-1]&(1u<<eye))!=0)))')
 c=replace(c,'(int)round(q.w),allowed26)', '(int)round(q.w),allowed26,false)')
 c=replace(c,'RWStructuredBuffer<ColumnRecord24> _Columns24;','RWStructuredBuffer<ColumnRecord24> _Columns24;RWStructuredBuffer<float4> _ColumnNative26;')
 c=replace(c,'StructuredBuffer<CurveSegment106> _Curves106;','StructuredBuffer<CurveSegment106> _Curves106,_NativeCurve26;')
 c=replace(c,'uint at=tid.x;if(at>=(uint)_CellsSize113.x*2)return;int eye=', 'uint at=tid.x;if(at>=(uint)_CellsSize113.x*2)return;_ColumnNative26[at]=0;int eye=')
 needle='r.midpoint=float4(mid,owner);r.source=float4(uv,primitive,alpha.x);'
 extra='''CurveSegment106 native26=_NativeCurve26[t];
  if(native26.a.w>0&&native26.b.w>0){float3 world26=lerp(native26.a.xyz,native26.b.xyz,u);float4 view26=mul(_View96,float4(world26,1)),clip26=mul(_Projection96,view26);
   if(clip26.w>0&&-view26.z>0&&all(isfinite(world26)))_ColumnNative26[at]=float4((clip26.x/clip26.w*.5+.5)*480,(.5-clip26.y/clip26.w*.5)*272,-view26.z,owner);}
  '''
 c=replace(c,needle,extra+needle)
 c=replace(c,'if(r.midpoint.w>0&&r.source.w>0)r.visibility.xy=TraceExternal24(_ForwardAnchor102.xy+r.midpoint.xy,r.midpoint.z,(int)round(r.midpoint.w),false);',
 '''float4 original26=_ColumnNative26[at];r.visibility.xy=float2(0,1);
 if(r.midpoint.w>0&&r.source.w>0&&original26.z>0&&original26.w==r.midpoint.w){r.midpoint.z=original26.z;r.visibility.xy=TraceExternal24(original26.xy,original26.z,(int)round(original26.w),false,true);}''')
 shader=G/'NativeProof26.compute';shader.write_text(c,encoding='utf-8',newline='\n')
 host=(OLD/'phase-run/RUN_Capture25.cs.txt').read_text().replace(str(OLD/'phase-run'),str(G/'phase-run')).replace('Assets/EUnityValidation01/SharedSource26/SharedSource26.compute','Assets/EUnityValidation01/NativeProof26/NativeProof26.compute')
 a=host.index('public sealed class SourcePigment113:');b=host.index('\npublic sealed class RegionDriver113:',a);block=host[a:b]
 block=replace(block,'public GraphicsBuffer Proof{get;private set;}','public GraphicsBuffer NativeCurve26{get;private set;}public Segment[] NativeSegments26{get;private set;}public GraphicsBuffer Proof{get;private set;}')
 block=replace(block,'public long OwnedBytes=>','public long OwnedBytes=>(NativeCurve26==null?0:(long)NativeCurve26.count*NativeCurve26.stride)+')
 block=replace(block,'try{using(var r=new BinaryReader(File.OpenRead(', 'try{NativeCurve26=new GraphicsBuffer(GraphicsBuffer.Target.Structured,count,32);NativeSegments26=new Segment[count];using(var r=new BinaryReader(File.OpenRead(')
 block=replace(block,'catch{Proof?.Dispose();Buffer?.Dispose();throw;}','catch{NativeCurve26?.Dispose();Proof?.Dispose();Buffer?.Dispose();throw;}')
 block=replace(block,'Vector4 Point(Point113 p){','Vector4 Point(Point113 p,out Vector4 nativeWorld26){')
 block=replace(block,'var world=model.MultiplyPoint3x4(local);','var world=model.MultiplyPoint3x4(local);nativeWorld26=new Vector4(world.x,world.y,world.z,1);')
 block=replace(block,'var previous=Point(curve.points[0]);','Vector4 previousWorld26;var previous=Point(curve.points[0],out previousWorld26);')
 block=replace(block,'var next=Point(curve.points[i]);Segments[at++]=new Segment(previous,next);previous=next;',
  'Vector4 nextWorld26;var next=Point(curve.points[i],out nextWorld26);var pa26=curve.points[i-1];var pb26=curve.points[i];bool same26=(pa26.a==pb26.a||pa26.a==pb26.b||pa26.a==pb26.c)&&(pa26.b==pb26.a||pa26.b==pb26.b||pa26.b==pb26.c)&&(pa26.c==pb26.a||pa26.c==pb26.b||pa26.c==pb26.c);previousWorld26.w=nextWorld26.w=same26?1:0;NativeSegments26[at]=new Segment(previousWorld26,nextWorld26);Segments[at++]=new Segment(previous,next);previous=next;previousWorld26=nextWorld26;')
 block=replace(block,'cmd.SetBufferData(Buffer,Segments);','cmd.SetBufferData(Buffer,Segments);cmd.SetBufferData(NativeCurve26,NativeSegments26);')
 block=replace(block,'Disposed=true;Proof?.Dispose();','Disposed=true;NativeCurve26?.Dispose();NativeCurve26=null;NativeSegments26=null;Proof?.Dispose();')
 host=host[:a]+block+host[b:]
 a=host.index('public sealed class RegionDriver113:');b=host.index('\npublic sealed class HeadHair25',a);block=host[a:b]
 block=replace(block,'exposure,columns24,depth24','exposure,columns24,columnNative26,depth24')
 block=replace(block,'columns24=B(1024,48);','columns24=B(1024,48);columnNative26=B(1024,16);')
 block=replace(block,'Vector2 carrierOrigin,Vector2 sourceAnchor){','Vector2 carrierOrigin,Vector2 sourceAnchor,Matrix4x4 originalView26,Matrix4x4 originalProjection26){')
 block=replace(block,'carrier.ExternalBindings24(cmd,cs,cs.FindKernel("CurveColumns24"));','cmd.SetComputeMatrixParam(cs,"_View96",originalView26);cmd.SetComputeMatrixParam(cs,"_Projection96",originalProjection26);carrier.ExternalBindings24(cmd,cs,cs.FindKernel("CurveColumns24"));')
 phrase='cmd.SetComputeBufferParam(cs,columnKernel,"_Columns24",columns24);cmd.DispatchCompute(cs,columnKernel,'
 assert block.count(phrase)==2
 block=block.replace(phrase,
  'cmd.SetComputeBufferParam(cs,columnKernel,"_Columns24",columns24);cmd.SetComputeBufferParam(cs,columnKernel,"_ColumnNative26",columnNative26);cmd.SetComputeBufferParam(cs,columnKernel,"_NativeCurve26",curve.NativeCurve26);cmd.DispatchCompute(cs,columnKernel,',1)
 # ColumnVisibility has the same old binding phrase but no curve-native input.
 block=replace(block,'cmd.SetComputeBufferParam(cs,columnKernel,"_Columns24",columns24);cmd.DispatchCompute(cs,columnKernel,',
  'cmd.SetComputeBufferParam(cs,columnKernel,"_Columns24",columns24);cmd.SetComputeBufferParam(cs,columnKernel,"_ColumnNative26",columnNative26);cmd.DispatchCompute(cs,columnKernel,')
 host=host[:a]+block+host[b:]
 host=replace(host,'b.UseBuffer(graph.ImportBuffer(Curves.Buffer),AccessFlags.ReadWrite);','b.UseBuffer(graph.ImportBuffer(Curves.NativeCurve26),AccessFlags.ReadWrite);b.UseBuffer(graph.ImportBuffer(Curves.Buffer),AccessFlags.ReadWrite);')
 host=replace(host,'CarrierNative.Bounds96.y),native.Anchor96+new Vector2(native.Bounds96.x,native.Bounds96.y));Region.PrepareCarrier',
  'CarrierNative.Bounds96.y),native.Anchor96+new Vector2(native.Bounds96.x,native.Bounds96.y),data.view,data.projection);Region.PrepareCarrier')
 host=replace(host,'var rows=new ColumnWitness26[count];b.GetData(rows,0,0,count);','JointSlice107("COLUMN-native26",forward102.Region.columnNative26,0,count);JointSlice107("CURVE-native26",forward102.Curves.NativeCurve26,0,forward102.Curves.NativeCurve26.count);var rows=new ColumnWitness26[count];b.GetData(rows,0,0,count);')
 source=G/'phase-run/RUN_Capture25.cs.txt';source.write_text(host,encoding='utf-8',newline='\n');compile_cs(source)
 (G/'phase-run/GLOBAL_NAMES66.json').write_bytes((OLD/'phase-run/GLOBAL_NAMES66.json').read_bytes())
 imp=(OLD/'RUN_Import25.cs.txt').read_text().replace(str(OLD/'import'),str(G/'import')).replace('Assets/EUnityValidation01/SharedSource26','Assets/EUnityValidation01/NativeProof26').replace('"SharedSource26"','"NativeProof26"').replace('/SharedSource26.compute','/NativeProof26.compute')
 imp=replace(imp,str(OLD/'SharedSource26.compute'),str(shader));imp=replace(imp,sha(OLD/'SharedSource26.compute'),sha(shader))
 ip=G/'RUN_Import25.cs.txt';ip.write_text(imp,encoding='utf-8',newline='\n');compile_cs(ip)
 (G/'relay.py').write_bytes((OLD/'relay.py').read_bytes())
 result={'importSourceSHA256':sha(ip),'captureSourceSHA256':sha(source),'computeSHA256':sha(shader),'compiledCPU':True,
  'newKernels':0,'newOwnedBuffers':2,'nativeCurveBytes':846*32,'nativeColumnMaxBytes':1024*16,'newLoops':False,
  'sourceRay':'current deformed PIGMENT113 vertex/barycentric binding; original view/projection; no own/shared skin exemption',
  'crossTriangleSegment':'Unknown, not a fabricated surface point; no extra shared-skin certificate', 'GPUOrUnityExecuted':False}
 (G/'LIVE_PREPARED.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
if __name__=='__main__':main()
