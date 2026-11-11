"""Bind the source-only UV edge bend to the existing bounded26 path."""
from pathlib import Path
import hashlib,json,sys
H=Path(__file__).resolve().parent;OLD=H/'native-proof';G=H/'surface27'
sys.path.insert(0,str(H));from prepare_support import replace
sys.path.insert(0,str(H.parent));from prepare_live import compile_cs
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def bind_pigment_material27(host):
 assert '27 historical pigment proof material ABI'not in host,'Material proof already migrated; do not migrate twice'
 fix='''int nativePigmentCount27=checked((int)mesh.GetIndexCount(6)/3);for(int material27=0;material27<proof.Length;material27++){var tag27=proof[material27].primitive;if(tag27.y!=0||tag27.z!=3||tag27.w!=1||tag27.x<=0||tag27.x>nativePigmentCount27)throw new InvalidOperationException("27 historical pigment proof material ABI");proof[material27].primitive=new WholeEye107.I4(tag27.x,3,6,1);}
   '''
 host=replace(host,'proofRows24=proof;ValidateUV24();Proof=',fix+'proofRows24=proof;ValidateUV24();Proof=')
 host=replace(host,'report["nativeCurveInput26"]=new Obj58',
 '''var tagGPU27=new SourcePigment113.Proof24[1];curve.Proof.GetData(tagGPU27,0,0,1);var tag27=tagGPU27[0].primitive;if(tag27.y!=3||tag27.z!=6||tag27.w!=1)throw new InvalidOperationException("27 original pigment material not bound");report["pigmentMaterialBinding27"]=new Obj58{["sourceId"]=sourceId,["frame"]=Time.frameCount,["part"]=tag27.y,["submesh"]=tag27.z,["renderer"]=tag27.w,["actualGPUProofRecord"]=true};
   report["nativeCurveInput26"]=new Obj58''')
 return host
def main():
 assert not(G/'IMPORT_REQUEST.json').exists()and not(G/'phase-run/PHASE_REQUEST.json').exists()
 d=json.loads((G/'UV_SURFACE27.json').read_text());assert not d['unresolved']and d['maxPiecesPerOriginalSegment']==2
 c=(OLD/'NativeProof26.compute').read_text()
 c=replace(c,'StructuredBuffer<CurveSegment106> _Curves106,_NativeCurve26;','StructuredBuffer<CurveSegment106> _Curves106,_NativeCurve26;StructuredBuffer<float4> _NativeBend27;')
 c=replace(c,'float3 world26=lerp(native26.a.xyz,native26.b.xyz,u);',
 '''float3 world26;float4 bend27=_NativeBend27[t];
    if(bend27.w>0&&bend27.w<1)world26=u<bend27.w?lerp(native26.a.xyz,bend27.xyz,u/bend27.w):lerp(bend27.xyz,native26.b.xyz,(u-bend27.w)/(1-bend27.w));
    else world26=lerp(native26.a.xyz,native26.b.xyz,u);''')
 shader=G/'SurfaceCarrier27.compute';shader.write_text(c,encoding='utf-8',newline='\n')
 (G/'phase-run').mkdir(exist_ok=True);(G/'import').mkdir(exist_ok=True)
 host=(OLD/'typed-run/RUN_Capture25.cs.txt').read_text().replace(str(OLD/'typed-run'),str(G/'phase-run')).replace('Assets/EUnityValidation01/NativeProof26/NativeProof26.compute','Assets/EUnityValidation01/SurfaceCarrier27/SurfaceCarrier27.compute')
 a=host.index('public sealed class SourcePigment113:');b=host.index('\npublic sealed class RegionDriver113:',a);block=host[a:b]
 block=replace(block,'struct Point113{','struct Bend27{public bool enabled;public int a,b,c;public Vector3 weights;public float u;public Vector2 uv;}Bend27[] bends27;public GraphicsBuffer NativeBendBuffer27{get;private set;}public Vector4[] NativeBends27{get;private set;}\n struct Point113{')
 block=replace(block,'public long OwnedBytes=>','public long OwnedBytes=>(NativeBendBuffer27==null?0:(long)NativeBendBuffer27.count*NativeBendBuffer27.stride)+')
 load='''NativeBendBuffer27=new GraphicsBuffer(GraphicsBuffer.Target.Structured,count,16);NativeBends27=new Vector4[count];bends27=new Bend27[count];
   var bendBytes27=File.ReadAllBytes(@"BEND_PATH");using(var hash27=SHA256.Create()){var actual27=BitConverter.ToString(hash27.ComputeHash(bendBytes27)).Replace("-","").ToLowerInvariant();if(actual27!="BEND_HASH")throw new InvalidOperationException("27 UV source cache changed");}
   using(var br27=new BinaryReader(new MemoryStream(bendBytes27))){if(br27.ReadString()!="native-uv-bends27/v1"||br27.ReadString()!=topology||br27.ReadString()!="PIGMENT_HASH"||br27.ReadInt32()!=count)throw new InvalidOperationException("27 source bend identity/count");for(int j=0;j<count;j++){int enabled=br27.ReadInt32();var p27=new Bend27{enabled=enabled==1,a=br27.ReadInt32(),b=br27.ReadInt32(),c=br27.ReadInt32(),weights=new Vector3(br27.ReadSingle(),br27.ReadSingle(),br27.ReadSingle()),u=br27.ReadSingle(),uv=new Vector2(br27.ReadSingle(),br27.ReadSingle())};if((enabled!=0&&enabled!=1)||p27.a<0||p27.b<0||p27.c<0||p27.a>=mesh.vertexCount||p27.b>=mesh.vertexCount||p27.c>=mesh.vertexCount||Mathf.Abs(p27.weights.x+p27.weights.y+p27.weights.z-1)>2e-6f||(p27.enabled&&(!(p27.u>0&&p27.u<1)||Mathf.Min(p27.weights.x,p27.weights.y,p27.weights.z)<-2e-6f)))throw new InvalidOperationException("27 source bend ABI/bounds");bends27[j]=p27;}if(br27.BaseStream.Position!=br27.BaseStream.Length)throw new InvalidOperationException("27 source bend trailing data");}
   '''.replace('BEND_PATH',str(G/'UV_BENDS27.bin')).replace('BEND_HASH',d['bendCacheSHA256']).replace('PIGMENT_HASH',d['cacheInputs']['argon23-runtime113/PIGMENT113.bin'])
 block=replace(block,'try{NativeCurve26=', 'try{'+load+'NativeCurve26=')
 block=replace(block,'catch{NativeCurve26?.Dispose();','catch{NativeBendBuffer27?.Dispose();NativeCurve26?.Dispose();')
 block=replace(block,'previousWorld26.w=nextWorld26.w=same26?1:0;',
 '''var bend27=bends27[at];var bendWorld27=new Vector4(0,0,0,-1);if(bend27.enabled){var local27=vertices[bend27.a]*bend27.weights.x+vertices[bend27.b]*bend27.weights.y+vertices[bend27.c]*bend27.weights.z;var world27=model.MultiplyPoint3x4(local27);bendWorld27=new Vector4(world27.x,world27.y,world27.z,bend27.u);}NativeBends27[at]=bendWorld27;previousWorld26.w=nextWorld26.w=(same26||bend27.enabled)?1:0;''')
 block=replace(block,'void ValidateUV24(){mesh.GetUVs(0,uv24);','void ValidateUV24(){mesh.GetUVs(0,uv24);foreach(var bend27 in bends27)if(bend27.enabled){var uv27=uv24[bend27.a]*bend27.weights.x+uv24[bend27.b]*bend27.weights.y+uv24[bend27.c]*bend27.weights.z;if((uv27-bend27.uv).sqrMagnitude>4e-12f)throw new InvalidOperationException("27 bend UV changed; explicit rebuild required");}')
 block=replace(block,'cmd.SetBufferData(NativeCurve26,NativeSegments26);','cmd.SetBufferData(NativeCurve26,NativeSegments26);cmd.SetBufferData(NativeBendBuffer27,NativeBends27);')
 block=replace(block,'Disposed=true;NativeCurve26?.Dispose();','Disposed=true;NativeBendBuffer27?.Dispose();NativeBendBuffer27=null;NativeBends27=null;bends27=null;NativeCurve26?.Dispose();')
 host=host[:a]+block+host[b:]
 host=replace(host,'cmd.SetComputeBufferParam(cs,columnKernel,"_NativeCurve26",curve.NativeCurve26);','cmd.SetComputeBufferParam(cs,columnKernel,"_NativeCurve26",curve.NativeCurve26);cmd.SetComputeBufferParam(cs,columnKernel,"_NativeBend27",curve.NativeBendBuffer27);')
 host=replace(host,'b.UseBuffer(graph.ImportBuffer(Curves.NativeCurve26),AccessFlags.ReadWrite);','b.UseBuffer(graph.ImportBuffer(Curves.NativeBendBuffer27),AccessFlags.ReadWrite);b.UseBuffer(graph.ImportBuffer(Curves.NativeCurve26),AccessFlags.ReadWrite);')
 host=replace(host,'report["nativeCurveInput26"]=new Obj58',
 '''using(var w=new BinaryWriter(new FileStream(Path.Combine(output,"CURVE-bend27.f32"),FileMode.CreateNew))){w.Write(rows.Length);w.Write(16);foreach(var v in curve.NativeBends27){w.Write(v.x);w.Write(v.y);w.Write(v.z);w.Write(v.w);}}
   report["nativeCurveInput26"]=new Obj58''')
 host=bind_pigment_material27(host)
 p=G/'phase-run/RUN_Capture25.cs.txt';p.write_text(host,encoding='utf-8',newline='\n');compile_cs(p)
 (G/'phase-run/GLOBAL_NAMES66.json').write_bytes((OLD/'typed-run/GLOBAL_NAMES66.json').read_bytes())
 imp=(OLD/'RUN_Import25.cs.txt').read_text().replace(str(OLD/'import'),str(G/'import')).replace('Assets/EUnityValidation01/NativeProof26','Assets/EUnityValidation01/SurfaceCarrier27').replace('"NativeProof26"','"SurfaceCarrier27"').replace('/NativeProof26.compute','/SurfaceCarrier27.compute')
 imp=replace(imp,str(OLD/'NativeProof26.compute'),str(shader));imp=replace(imp,sha(OLD/'NativeProof26.compute'),sha(shader))
 ip=G/'RUN_Import25.cs.txt';ip.write_text(imp,encoding='utf-8',newline='\n');compile_cs(ip)
 (G/'relay.py').write_bytes((OLD/'relay.py').read_bytes())
 result={'captureSourceSHA256':sha(p),'importSourceSHA256':sha(ip),'computeSHA256':sha(shader),'CPUCompiled':True,'additionalOwnedGPUBufferBytes':846*16,'addedGPUKernels':0,'addedGPULoops':0,'sourceBVHRaysPerColumn':1,'GPUExecuted':False,'sourceShapeAllocationColourChanged':False}
 (G/'LIVE_PREPARED.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
if __name__=='__main__':main()
