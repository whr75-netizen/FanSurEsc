"""Generate review-only runtime source variants. No Unity/import/compiler/GPU."""
from pathlib import Path
import difflib,hashlib,json,re,struct,sys
H=Path(__file__).resolve().parent;B=H.parent;R=B.parent;P=R/'argon23-runtime113'
sys.path.insert(0,str(B));from host_audit24 import functions
from geometry24 import affiliation
def replace(s,a,b):
    assert s.count(a)==1,(a[:120],s.count(a));return s.replace(a,b)
def save(name,s,original=None):
    (H/name).write_bytes(s.encode('utf-8'))
    if original is not None:
        (H/(name+'.patch')).write_text(''.join(difflib.unified_diff(original.splitlines(True),s.splitlines(True),fromfile='113/'+name,tofile='runtime24/'+name)),encoding='utf-8')
def binary_string(s):
    b=s.encode();n=len(b);out=bytearray()
    while n>=128:out.append((n&127)|128);n>>=7
    return bytes(out)+bytes([n])+b
def shader():
    original=(B/'ForwardEye113_Direct24.compute').read_text();s=original;f=functions(s)
    # Copy the existing face traversal. No new cost/ranking/BVH architecture.
    q=f['Query']['source'];loop=q[q.index(' float2 trans=1;'):q.index(' Mat96 candidate=')]
    loop=loop.replace('depth-zz<=_SocketLimit113','depth-zz<=SocketLimit24(eye)')
    loop=loop.replace('_ExposeOwn113!=0&&','')
    loop=re.sub(r'if\(abounds.y>0&&\(_QueryEvidence107.*?\}trans\*=', 'trans*=',loop)
    assert '_QueryEvidence107'not in loop and 'id.x'not in loop
    trace='float2 TraceExternal24(float2 queryPoint,float depth,int eye){\n'+loop+'\nreturn overflow?float2(0,1):trans;\n}\n'
    declarations,body=(H/'Geometry24.hlsl').read_text().split('float SocketLimit24',1)
    declarations+='float SocketLimit24(int eye);\nfloat2 TraceExternal24(float2 queryPoint,float depth,int eye);\n'
    first=s.index('[numthreads(8,8,1)]void PackWorld98')
    s=s[:first]+declarations+s[first:]
    s=replace(s,'int _ExposeOwn113; float _SocketLimit113;','int _ExposeOwn113; float2 _SocketLimit113;')
    s=replace(s,'depth-zz<=_SocketLimit113','depth-zz<=SocketLimit24(eye)')
    # Original Query remains source sampling. Native carrier holes are handled
    # only AFTER assignment, by the rewritten carrier/compose functions.
    for name in ['CarrierQueries113','ComposeRegion113']:
        text=f[name]['source'];start=s.index(text);attr=s.rfind('[numthreads(',0,start)
        assert s[attr:start].endswith(']');s=s[:attr]+s[start+len(text):]
    old=f['PrepareCells113']['source'];keep=old[:old.index(' int boundaryOwner=')]
    tail='''
 int boundaryOwner=0,row=0;ColumnRecord24 boundary;boundary.midpoint=0;boundary.source=0;boundary.visibility=0;
 for(int i=0;i<2;i++){ColumnRecord24 c=_Columns24[i*_CellsSize113.x+p.x];if(c.midpoint.w>0&&p.y==(int)floor(c.visibility.z)){if(boundaryOwner!=0)errors|=8;boundaryOwner=(int)round(c.midpoint.w);row=(int)floor(c.visibility.z);boundary=c;}}
 int policy=1;if(boundaryOwner>0){owner=boundaryOwner;policy=2;}else if(owner>0){int eye=owner==_CurveEyeIds106.x?0:1;ColumnRecord24 c=_Columns24[eye*_CellsSize113.x+p.x];if(c.midpoint.w>0){row=(int)floor(c.visibility.z);policy=p.y<row?-1:1;}}
 float4 lid=0;float best=3.402823e38;int chosen=-1;
 if(policy==2){for(int y=0;y<8;y++)for(int x=0;x<8;x++){int at=(p.y*8+y)*_SourceSize113.x+p.x*8+x;float4 v=_SrcVisibility113[3*_SourceSize113.x*_SourceSize113.y+at],m=SL113(3,1,at);if(round(m.z)!=owner||v.x<=0||v.x!=v.y)continue;float d=length((float2(p*8+int2(x,y))+.5)/8-boundary.midpoint.xy);if(d<best){best=d;chosen=at;lid=float4(_LidPalette113[owner==_CurveEyeIds106.x?0:1].rgb,m.x);}}
  if(chosen<0&&boundary.source.w>0&&boundary.visibility.x>0&&boundary.visibility.x==boundary.visibility.y)lid=float4(_LidPalette113[owner==_CurveEyeIds106.x?0:1].rgb,boundary.midpoint.z);
 }
 _Cells113[cell*7]=mass;_Cells113[cell*7+1]=ci;_Cells113[cell*7+2]=cw;_Cells113[cell*7+3]=float4(owner,depth,row);_Cells113[cell*7+4]=lid;_Cells113[cell*7+5]=float4(policy,chosen+1,errors,chosen<0&&lid.w>0?24:0);_Cells113[cell*7+6]=0;_CellTags113[cell]=tags;
}'''
    s=replace(s,old,keep+tail)
    # Equivalent fixed-three-role arithmetic, without dynamic vector l-values.
    weight='''void Weight113(int at,out float3 lo,out float3 hi){
 int n=_SourceSize113.x*_SourceSize113.y;float4 a=_SrcVisibility113[n+at],b=_SrcVisibility113[2*n+at],c=_SrcVisibility113[3*n+at];
 float za=SL113(1,1,at).x,zb=SL113(2,1,at).x,zc=SL113(3,1,at).x;
 float2 aa=a.xy,bb=b.xy,cc=c.xy;
 if(zb>0&&b.y>0){if(zb<za-3e-5)aa*=1-b.yx;else if(abs(zb-za)<=3e-5)aa.x*=1-b.y;}
 if(zc>0&&c.y>0){if(zc<za-3e-5)aa*=1-c.yx;else if(abs(zc-za)<=3e-5)aa.x*=1-c.y;}
 if(za>0&&a.y>0){if(za<zb-3e-5)bb*=1-a.yx;else if(abs(za-zb)<=3e-5)bb.x*=1-a.y;}
 if(zc>0&&c.y>0){if(zc<zb-3e-5)bb*=1-c.yx;else if(abs(zc-zb)<=3e-5)bb.x*=1-c.y;}
 if(za>0&&a.y>0){if(za<zc-3e-5)cc*=1-a.yx;else if(abs(za-zc)<=3e-5)cc.x*=1-a.y;}
 if(zb>0&&b.y>0){if(zb<zc-3e-5)cc*=1-b.yx;else if(abs(zb-zc)<=3e-5)cc.x*=1-b.y;}
 lo=float3(aa.x,bb.x,cc.x);hi=float3(aa.y,bb.y,cc.y);
}'''
    s=replace(s,f['Weight113']['source'],weight)
    s+='\n'+trace+'\nfloat SocketLimit24'+body
    s='#pragma kernel CurveColumns24\n#pragma kernel ColumnVisibility24\n#pragma kernel AssignedVisibility24\n'+s
    for banned in ['115','EvaluateForm','BoundRun','Down115','Up115']:assert banned not in s
    before=functions(original);after=functions(s)
    for name in ['BuildSubsets113','Enumerate113','Reduce113','Write113']:assert before[name]['source']==after[name]['source']
    save('ForwardEye113_Geometry24.compute',s,original)

def source_pigment():
    original=(P/'SourcePigmentStream113.cs').read_text();s=original
    s=replace(s,'readonly int[] ids;','readonly int[][] ring24;readonly int[] ids;')
    s=replace(s,'readonly int[][] ring24;','readonly int[][] ring24;readonly List<Vector2> uv24=new List<Vector2>();Proof24[] proofRows24;')
    s=replace(s,'public GraphicsBuffer Buffer{get;private set;}', 'public struct Proof24{public Vector4 uv;public WholeEye107.I4 primitive;}\n public GraphicsBuffer Proof{get;private set;}public Vector4 SocketDiameters{get;private set;}public Vector4 RingDepthRanges{get;private set;}public GraphicsBuffer Buffer{get;private set;}')
    s=replace(s,'public long OwnedBytes=>Buffer==null?0:(long)Buffer.count*Buffer.stride;','public long OwnedBytes=>(Buffer==null?0:(long)Buffer.count*Buffer.stride)+(Proof==null?0:(long)Proof.count*Proof.stride);')
    s=replace(s,'Buffer=new GraphicsBuffer(GraphicsBuffer.Target.Structured,count,32);','''Buffer=new GraphicsBuffer(GraphicsBuffer.Target.Structured,count,32);
  try{using(var r=new BinaryReader(File.OpenRead(@"'''+str(H/'GEOMETRY_BINDINGS24.bin')+'''"))){if(r.ReadString()!="geometry-bindings24/v1"||r.ReadString()!=topology)throw new InvalidOperationException("24 immutable source topology");var textureSHA=r.ReadString();if(textureSHA.Length!=64)throw new InvalidOperationException("24 texture provenance");if(r.ReadInt32()!=2)throw new InvalidOperationException("24 ring identities");ring24=new int[2][];for(int i=0;i<2;i++){if(r.ReadInt32()!=ids[i])throw new InvalidOperationException("24 ring owner");int n=r.ReadInt32();if(n<3||n>128)throw new InvalidOperationException("24 ring bound");ring24[i]=new int[n];for(int j=0;j<n;j++){int v=r.ReadInt32();if(v<0||v>=mesh.vertexCount)throw new InvalidOperationException("24 ring index");ring24[i][j]=v;}}
   if(r.ReadInt32()!=count)throw new InvalidOperationException("24 proof count");var proof=new Proof24[count];for(int i=0;i<count;i++)proof[i]=new Proof24{uv=new Vector4(r.ReadSingle(),r.ReadSingle(),r.ReadSingle(),r.ReadSingle()),primitive=new WholeEye107.I4(r.ReadInt32(),r.ReadInt32(),r.ReadInt32(),r.ReadInt32())};
   if(r.BaseStream.Position!=r.BaseStream.Length)throw new InvalidOperationException("24 trailing bytes");var uvs=new List<Vector2>();mesh.GetUVs(0,uvs);int atProof=0;foreach(var curve in curves)for(int i=0;i<curve.points.Length-1;i++){Vector2 U(Point113 p)=>uvs[p.a]*p.weights.x+uvs[p.b]*p.weights.y+uvs[p.c]*p.weights.z;var a=U(curve.points[i]);var b=U(curve.points[i+1]);var q=proof[atProof++].uv;if((a-new Vector2(q.x,q.y)).sqrMagnitude>4e-12f||(b-new Vector2(q.z,q.w)).sqrMagnitude>4e-12f)throw new InvalidOperationException("24 source UV mapping changed");}
   proofRows24=proof;ValidateUV24();Proof=new GraphicsBuffer(GraphicsBuffer.Target.Structured,count,32);Proof.SetData(proof);
  }}catch{Proof?.Dispose();Buffer?.Dispose();throw;}''')
    s=replace(s,'var physical=camera.worldToCameraMatrix;int at=0;', '''var physical=camera.worldToCameraMatrix;
  var diameter=Vector4.zero;var depthRange=Vector4.zero;for(int i=0;i<2;i++){float d=0,lo=Single.PositiveInfinity,hi=Single.NegativeInfinity;foreach(int a in ring24[i]){var pa=model.MultiplyPoint3x4(vertices[a]);float z=-physical.MultiplyPoint3x4(pa).z;lo=Mathf.Min(lo,z);hi=Mathf.Max(hi,z);foreach(int b in ring24[i])d=Mathf.Max(d,(pa-model.MultiplyPoint3x4(vertices[b])).magnitude);}if(!(d>0)||Single.IsInfinity(d)||!(lo>0)||hi<lo)throw new InvalidOperationException("24 evaluated ring invalid");diameter[i]=d;depthRange[i*2]=lo;depthRange[i*2+1]=hi;}SocketDiameters=diameter;RingDepthRanges=depthRange;int at=0;''')
    s=replace(s,'mesh.GetVertices(vertices);','ValidateUV24();mesh.GetVertices(vertices);')
    validation='''void ValidateUV24(){mesh.GetUVs(0,uv24);if(uv24.Count!=mesh.vertexCount)throw new InvalidOperationException("24 source UV count changed");int at=0;foreach(var curve in curves)for(int i=0;i<curve.points.Length-1;i++){Vector2 U(Point113 p)=>uv24[p.a]*p.weights.x+uv24[p.b]*p.weights.y+uv24[p.c]*p.weights.z;var a=U(curve.points[i]);var b=U(curve.points[i+1]);var q=proofRows24[at++].uv;if((a-new Vector2(q.x,q.y)).sqrMagnitude>4e-12f||(b-new Vector2(q.z,q.w)).sqrMagnitude>4e-12f)throw new InvalidOperationException("24 source UV content changed; explicit cache rebuild required");}}
 public void Upload'''
    s=replace(s,'public void Upload',validation)
    s=replace(s,'Buffer?.Dispose();Buffer=null;','Proof?.Dispose();Proof=null;proofRows24=null;uv24.Clear();Buffer?.Dispose();Buffer=null;')
    save('SourcePigment113_Geometry24.cs',s,original)
    cache=json.loads((R/'pigment-carrier109/NATIVE_CACHE109.json').read_text());rings=affiliation()['rings']
    data=binary_string('geometry-bindings24/v1')+binary_string(cache['sourceTopologySHA256'])+binary_string(cache['textureSHA256'])+struct.pack('<i',2)
    for owner in [1,2]:
        a=rings[str(owner)]['sourceVertices'];data+=struct.pack('<ii',owner,len(a))+struct.pack('<'+'i'*len(a),*a)
    proofs=[]
    for curve in cache['curves']:
        for a,b in zip(curve['points'],curve['points'][1:]):
            assert not a.get('unresolved') and not b.get('unresolved')
            # Existing WholeEye107 slots are skin0/iris1/white2/lid3; native
            # source tags are renderer1/submesh3 for this immutable source.
            proofs.append(struct.pack('<4f4i',*a['sourceUV'],*b['sourceUV'],a['primitive'],0,3,1))
    data+=struct.pack('<i',len(proofs))+b''.join(proofs);(H/'GEOMETRY_BINDINGS24.bin').write_bytes(data)

def engine():
    original=(R/'joint-lid107/WholeEye107.cs').read_text();s=original
    # Reuse exactly the old Refit prefix; do not call its Query/Select afterward.
    start=s.index('  Check();',s.index('public void Dispatch('));end=s.index('  k=Shader.FindKernel("Query")',start)
    prefix=s[start:end].replace('directQueries?1:0','0').replace('coldTie','0')
    prefix=prefix.replace('cmd.BeginSample("WholeEye107 BVH visibility and joint selection");','')
    method='''
 public void RefitOnly24(CommandBuffer cmd,Matrix4x4 view,Matrix4x4 projection){
'''+prefix+'''
 }
 public void ExternalBindings24(CommandBuffer cmd,ComputeShader cs,int k){
  Check();if(alphaSources==null||alphaSources.Any(t=>!t))throw new InvalidOperationException("24 borrowed alpha source invalidated");void Bind(string n,GraphicsBuffer b)=>cmd.SetComputeBufferParam(cs,k,n,b);
  Bind("_Triangles96",triangles);Bind("_Materials96",materials);Bind("_World96",World);Bind("_UV96",uv);Bind("_PartTriangles96",parts);Bind("_Nodes96",nodes);Bind("_Boxes96",boxes);
  for(int i=0;i<32;i++)cmd.SetComputeTextureParam(cs,k,"_SourceAlpha96_"+i,i<alphaSources.Length?alphaSources[i]:Texture2D.whiteTexture);
  cmd.SetComputeIntParam(cs,"_FacePrimitiveStride96",PrimitiveStride);
 }
'''
    s=replace(s,' public void SetAlphaSources(',method+' public void SetAlphaSources(')
    save('WholeEye107_Geometry24.cs',s,original)

def driver():
    original=(P/'RegionDriver113.cs').read_text();s=original
    s=replace(s,'subsets,exposure;','subsets,exposure,columns24,depth24,visibility24;')
    s=replace(s,'exposure=B(1024,16);','exposure=B(1024,16);columns24=B(1024,48);depth24=B(512*16,16);visibility24=B(512*16,16);')
    s=replace(s,'e.Shader.SetFloat("_SocketLimit113",.012f);','')
    a=s.index(' public void PrepareCarrier(');b=s.index(' public void Draw(',a)
    s=s[:a]+''' public void Limits24(CommandBuffer cmd,SourcePigment113 curve,params WholeEye107[] engines){if(curve.UpdatedFrame!=Time.frameCount)throw new InvalidOperationException("24 current evaluated rings required");foreach(var e in engines){cmd.SetComputeVectorParam(e.Shader,"_SocketLimit113",curve.SocketDiameters);cmd.SetComputeVectorParam(e.Shader,"_RingDepth24",curve.RingDepthRanges);cmd.SetComputeIntParams(e.Shader,"_CurveEyeIds106",curve.EyeId(0),curve.EyeId(1));}}
 public void PrepareCarrier(CommandBuffer cmd,WholeEye107 carrier,WholeEye107 target,GraphicsBuffer[] result,Vector2 origin,Vector2 anchor,Matrix4x4 view,Matrix4x4 projection){
  if(eye.roi.width<1||eye.roi.height<1||eye.roi.width*eye.roi.height>512)throw new InvalidOperationException("24 assigned16 ROI budget");var cs=target.Shader;int k=cs.FindKernel("CarrierQueries113");carrier.ExternalBindings24(cmd,cs,k);cmd.SetComputeMatrixParam(cs,"_View96",view);cmd.SetComputeMatrixParam(cs,"_Projection96",projection);
  cmd.SetComputeIntParams(cs,"_SourceSize113",carrier.Width,carrier.Height);cmd.SetComputeIntParams(cs,"_CellsSize113",target.Width/4,target.Height/4);cmd.SetComputeIntParam(cs,"_PhysicalCount24",eye.roi.width*eye.roi.height);
  cmd.SetComputeIntParams(cs,"_ForwardROI102",eye.roi.x,272-eye.roi.y-eye.roi.height,eye.roi.width,eye.roi.height);cmd.SetComputeVectorParam(cs,"_ForwardAnchor102",new Vector4(anchor.x,anchor.y,0,0));cmd.SetComputeVectorParam(cs,"_CarrierOrigin113",new Vector4(origin.x,origin.y,0,0));
  cmd.SetComputeBufferParam(cs,k,"_SrcLayers113",carrier.Layers);cmd.SetComputeBufferParam(cs,k,"_ReadIdentity96",result[1]);cmd.SetComputeBufferParam(cs,k,"_ReadDecision96",result[2]);cmd.SetComputeBufferParam(cs,k,"_AssignedDepth24",depth24);cmd.SetComputeBufferParam(cs,k,"_AssignedVisibility24",visibility24);cmd.DispatchCompute(cs,k,(eye.roi.width*eye.roi.height*16+63)/64,1,1);
  k=cs.FindKernel("AssignedVisibility24");carrier.ExternalBindings24(cmd,cs,k);cmd.SetComputeBufferParam(cs,k,"_OwnSkin113",own);cmd.SetComputeBufferParam(cs,k,"_AssignedDepth24",depth24);cmd.SetComputeBufferParam(cs,k,"_AssignedVisibility24",visibility24);cmd.DispatchCompute(cs,k,(eye.roi.width*eye.roi.height*16+63)/64,1,1);
 }
'''+s[b:]
    s=replace(s,'GraphicsBuffer[] output,Vector2 carrierOrigin){','GraphicsBuffer[] output,Vector2 carrierOrigin,Vector2 sourceAnchor){')
    s=replace(s,'cmd.SetComputeVectorParam(cs,"_CarrierOrigin113",new Vector4(carrierOrigin.x,carrierOrigin.y,0,0));', '''cmd.SetComputeVectorParam(cs,"_CarrierOrigin113",new Vector4(carrierOrigin.x,carrierOrigin.y,0,0));cmd.SetComputeVectorParam(cs,"_ForwardAnchor102",new Vector4(sourceAnchor.x,sourceAnchor.y,0,0));
 carrier.ExternalBindings24(cmd,cs,cs.FindKernel("CurveColumns24"));int columnKernel=cs.FindKernel("CurveColumns24");cmd.SetComputeBufferParam(cs,columnKernel,"_Curves106",curve.Buffer);cmd.SetComputeBufferParam(cs,columnKernel,"_CurveProof24",curve.Proof);cmd.SetComputeBufferParam(cs,columnKernel,"_Columns24",columns24);cmd.DispatchCompute(cs,columnKernel,(w*2+63)/64,1,1);
 columnKernel=cs.FindKernel("ColumnVisibility24");carrier.ExternalBindings24(cmd,cs,columnKernel);cmd.SetComputeBufferParam(cs,columnKernel,"_OwnSkin113",own);cmd.SetComputeBufferParam(cs,columnKernel,"_Columns24",columns24);cmd.DispatchCompute(cs,columnKernel,(w*2+63)/64,1,1);
 cmd.SetComputeBufferParam(cs,cs.FindKernel("PrepareCells113"),"_Columns24",columns24);''')
    s=replace(s,'cmd.SetComputeBufferParam(cs,k,"_CarrierVisibility113",carrier.Visibility);cmd.SetComputeBufferParam(cs,k,"_CarrierLayers113",carrier.Layers);','cmd.SetComputeBufferParam(cs,k,"_AssignedDepth24",depth24);cmd.SetComputeBufferParam(cs,k,"_AssignedVisibility24",visibility24);')
    s=s.replace('["nativeOwnSocketMetres"]=.012,','["nativeOwnSocketMetres"]="evaluated per-eye ring diameter",')
    save('RegionDriver113_Geometry24.cs',s,original)

def forward():
    original=(P/'Forward113.cs').read_text();s=original
    s=s.replace('Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/ForwardEye113.compute','Assets/EUnityValidation01/Direct24Geometry/ForwardEye113_Geometry24.compute')
    s=replace(s,'Compose(cmd,e.Colour,e.Identity,e.Decisions,BaselineFields);','')
    s=replace(s,'Curves.Upload(cmd);Dispatch("ApplyCurve106",LegacyResults,LegacyFields);','Curves.Upload(cmd);')
    start=s.index('  void Dispatch(string kernel,');end=s.index('  RenderedFrame=Time.frameCount;',start);s=s[:start]+s[end:]
    s=replace(s,'["baseline102SameInputs"]=true,','["baseline102SameInputs"]=false,["legacyControlOutputsWritten24"]=false,')
    s=replace(s,'Region.PrepareCarrier(cmd,CarrierSource.Engine,CarrierNative.Anchor96+new Vector2(CarrierNative.Bounds96.x,CarrierNative.Bounds96.y));CarrierSource.Engine.Dispatch(cmd,data.view,data.projection,true,0);','CarrierSource.Engine.RefitOnly24(cmd,data.view,data.projection);')
    s=replace(s,'for(int p=0;p<4;p++)DenseSource.Engine.Pack(cmd,p,DenseNative.layers[p],true);','Region.Limits24(cmd,Curves,Source.Engine,DenseSource.Engine,CarrierSource.Engine);for(int p=0;p<4;p++)DenseSource.Engine.Pack(cmd,p,DenseNative.layers[p],true);')
    s=replace(s,'ComposeRegion113(cmd);','Region.PrepareCarrier(cmd,CarrierSource.Engine,e,Results,CarrierNative.Anchor96+new Vector2(CarrierNative.Bounds96.x,CarrierNative.Bounds96.y),native.Anchor96+new Vector2(native.Bounds96.x,native.Bounds96.y),data.view,data.projection);ComposeRegion113(cmd);')
    s=replace(s,'Region.Draw(cmd,e,DenseSource.Engine,CarrierSource.Engine,Curves,Results,CarrierNative.Anchor96+new Vector2(CarrierNative.Bounds96.x,CarrierNative.Bounds96.y));','Region.Draw(cmd,e,DenseSource.Engine,CarrierSource.Engine,Curves,Results,CarrierNative.Anchor96+new Vector2(CarrierNative.Bounds96.x,CarrierNative.Bounds96.y),native.Anchor96+new Vector2(native.Bounds96.x,native.Bounds96.y));')
    s=replace(s,'b.UseBuffer(graph.ImportBuffer(Curves.Buffer),AccessFlags.ReadWrite);','b.UseBuffer(graph.ImportBuffer(Curves.Buffer),AccessFlags.ReadWrite);b.UseBuffer(graph.ImportBuffer(Curves.Proof),AccessFlags.Read);')
    # Geometry trace runs on target shader with the carrier BVH but view matrices
    # are already set by Source.Engine.Dispatch in exactly this graph pass.
    save('Forward113_Geometry24.cs',s,original)

def main():
    shader();source_pigment();engine();driver();forward()
    rows={p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in H.iterdir()if p.suffix in ['.cs','.compute','.bin','.hlsl']}
    (H/'PREPARED_RUNTIME24.json').write_text(json.dumps({'files':rows,'GPUOrUnityCalls':0,'AssetsImported':False,'ProductApplied':False,'fourAllocatorBodiesPreserved':True,'unexecutedCandidate':True},indent=2)+'\n')
    print(json.dumps(rows,indent=2))
if __name__=='__main__':main()
