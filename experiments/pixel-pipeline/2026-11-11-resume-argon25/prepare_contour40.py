from pathlib import Path
import ctypes as C,hashlib,json,re,struct,sys
import numpy as np
H=Path(__file__).resolve().parent;G=H/'face40';R=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');sys.path.insert(0,str(H))
from prepare_review30 import compile_source
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def topology():
 reg=json.loads((H.parent/'renderer-family59/SOURCE_REGISTRY59.json').read_text());raw=(R/reg['modelAsset']).read_bytes();assert hashlib.sha256(raw).hexdigest()==reg['modelSHA256'];chunks={};at=12
 while at<len(raw):n,t=struct.unpack_from('<II',raw,at);at+=8;chunks[t]=raw[at:at+n];at+=n
 d=json.loads(chunks[0x4e4f534a]);blob=chunks[0x004e4942];p=d['meshes'][0]['primitives'][3]
 def accessor(i):
  a=d['accessors'][i];dt=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']]);dim={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];out=np.zeros((a['count'],dim),dt)
  if'bufferView'in a:
   v=d['bufferViews'][a['bufferView']];out[:]=np.ndarray(out.shape,dt,buffer=blob,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',dt.itemsize*dim),dt.itemsize))
  if'sparse'in a:
   s=a['sparse'];v=d['bufferViews'][s['indices']['bufferView']];idt=np.dtype({5121:'u1',5123:'<u2',5125:'<u4'}[s['indices']['componentType']]);ix=np.frombuffer(blob,idt,s['count'],v.get('byteOffset',0)+s['indices'].get('byteOffset',0));v=d['bufferViews'][s['values']['bufferView']];values=np.frombuffer(blob,dt,s['count']*dim,v.get('byteOffset',0)+s['values'].get('byteOffset',0)).reshape(-1,dim);out[ix]=values
  return out
 arrays=[accessor(p['attributes'][k])for k in ['POSITION','JOINTS_0','WEIGHTS_0']]+[accessor(t['POSITION'])for t in p.get('targets',[])if'POSITION'in t];n=len(arrays[0]);assert all(len(a)==n for a in arrays);keys=[b''.join(a[i].tobytes()for a in arrays)for i in range(n)];ids={};weld=[]
 for k in keys:
  if k not in ids:ids[k]=len(ids)
  weld.append(ids[k])
 out={'modelSHA256':reg['modelSHA256'],'rule':'byte-identical rest POSITION + JOINTS_0/WEIGHTS_0 + every morph POSITION; UV excluded; evaluated equality required again at runtime','sourceVertices':n,'groups':len(ids),'positionStreams':len(arrays)-2,'weld':weld};(G/'WELD40.json').write_text(json.dumps(out,separators=(',',':')),encoding='utf-8',newline='\n');return out
def main():
 G.mkdir(exist_ok=True);(G/'build').mkdir(exist_ok=True);(G/'shaders').mkdir(exist_ok=True);w=topology()
 sys.path.insert(0,str(H.parent/'bounded-form115/prefix24'));import compile_hlsl_cpu as api
 dll=C.WinDLL(str(api.DLL),winmode=0x800);fn=dll.D3DCompile;fn.argtypes=[C.c_void_p,C.c_size_t,C.c_char_p,C.c_void_p,C.c_void_p,C.c_char_p,C.c_char_p,C.c_uint,C.c_uint,C.POINTER(C.c_void_p),C.POINTER(C.c_void_p)];fn.restype=C.c_long;raw=(H/'GeoResolve40.compute').read_bytes();blob=C.c_void_p();err=C.c_void_p()
 try:
  hr=fn(raw,len(raw),b'GeoResolve40',None,None,b'ResolveGeometry40',b'cs_5_0',(1<<11)|(1<<15),0,C.byref(blob),C.byref(err));diag=api.blob(err).decode(errors='replace');assert hr>=0,diag;audit=api.token_audit(api.blob(blob));assert audit['threads']==[8,8,1]and not audit['privateArrayDeclarations']and audit['loops']==0
 finally:api.release(blob);api.release(err)
 for name in ['GeoResolve40.compute','GeoContour40.shader']:(G/'shaders'/name).write_bytes((H/name).read_bytes())
 old=(H/'face39/capture/RUN.cs.txt').read_text();names=['Json','Obj','Arr','SerializedContent','CreateOnly','NativeSnapshot','GlobalJournal','GridBinding','GridSpace','Submission','ExitCoordinator','PendingViews','QMetaLattice','Projection','ConsumerReads','EditorExitRequest','ReadbackPreflight','SourceOutline','SourceCaptureHost','SourceSequenceHost','FrameInfo','LegacyInputs','ConsumerPending','TargetFrame','RequestFieldReadback','RequestClassificationReadback','FieldExtent'];m={n+'39':n+'40'for n in names};code=re.sub(r'\b('+'|'.join(m)+r')\b',lambda x:m[x[0]],old).replace('face39\\capture','face40\\capture').replace('id="face39-"','id="face40-"')
 def rep(a,b):
  nonlocal code
  assert code.count(a)==1,(a,code.count(a));code=code.replace(a,b)
 rep('Fields=new RTHandle[12]','Fields=new RTHandle[13]')
 rep('Material inkStyle39;','Material inkStyle39;UnityEngine.Mesh contourMesh40;Contour40.Result contour40;Obj40 motionProof40;public Func<Obj40> MotionProof40;readonly int[] weld40=Json40.Parse(File.ReadAllText(@"'+str(G/'WELD40.json')+'"))["weld"].Values<int>().ToArray();')
 rep('inkStyle39=Clone(originals[renderer][submesh],shader);inkStyle39.SetVector("_SourceOutline29",sourceInk);','var contourShader40=AssetDatabase.LoadAssetAtPath<Shader>("Assets/EUnityValidation01/SourceBoundary40/GeoContour40.shader");if(!contourShader40||!contourShader40.isSupported)throw new InvalidOperationException("40 geometry line shader missing");inkStyle39=new Material(contourShader40){hideFlags=HideFlags.DontSave};contourMesh40=new UnityEngine.Mesh{hideFlags=HideFlags.DontSave,indexFormat=UnityEngine.Rendering.IndexFormat.UInt32};')
 code=code.replace('SourceBoundary39/OutlineResolve39.compute','SourceBoundary40/GeoResolve40.compute').replace('FindKernel("ResolveOutline39")','FindKernel("ResolveGeometry40")')
 rep('styleWidth39=Math.Max(width,camera.orthographicSize*2/272);inkStyle39.SetFloat("_OutlineWidth",styleWidth39);','styleWidth39=width;contour40=Contour40.Build(vertices,mesh.GetIndices(submesh),weld40,transform,f.Project);contourMesh40.Clear();contourMesh40.vertices=contour40.vertices;contourMesh40.uv=contour40.provenance;contourMesh40.SetIndices(contour40.indices,MeshTopology.Lines,0,false);motionProof40=MotionProof40?.Invoke();')
 rep('for(int i=0;i<Fields.Length;i++)Fields[i]=Target(ROI.width*8,ROI.height*8);','for(int i=0;i<8;i++)Fields[i]=Target(ROI.width*8,ROI.height*8);')
 rep('styleDepth39=Target(ROI.width*8,ROI.height*8,true);','')
 rep('QFields[21]=Target(QROI.width,QROI.height,uav:true);','QFields[21]=Target(QROI.width,QROI.height,uav:true);for(int i=8;i<12;i++)Fields[i]=Target(QROI.width,QROI.height);styleDepth39=Target(QROI.width,QROI.height,true);if((long)QROI.width*QROI.height*9*16>262144)throw new InvalidOperationException("40 one-atlas read budget");Fields[12]=Target(QROI.width*9,QROI.height);')
 a=code.index(' void DrawStyle39(');b=code.index(' void DrawQ(',a)
 code=code[:a]+''' void DrawStyle39(UnsafeGraphContext context,bool hair){var cmd=CommandBufferHelpers.GetNativeCommandBuffer(context.cmd);int first=hair?8:10;var p=new MaterialPropertyBlock();p.SetMatrix("_ProbeGPUVP29",qvp);p.SetMatrix("_ProbeView29",view);cmd.SetRenderTarget(new[]{new RenderTargetIdentifier(Fields[first].rt),new RenderTargetIdentifier(Fields[first+1].rt)},styleDepth39.rt);cmd.SetViewport(new Rect(0,0,QROI.width,QROI.height));cmd.ClearRenderTarget(RTClearFlags.All,Color.clear,1,0);for(int r=0;r<meshes.Length;r++){if(!hair&&r==2)continue;for(int sm=0;sm<depthMats[r].Length;sm++)cmd.DrawMesh(meshes[r],matrices[r],depthMats[r][sm],sm,0,p);}p.SetMatrix("_ContourVP40",qvp);p.SetMatrix("_ContourView40",view);p.SetVector("_ContourRGB40",sourceInk);cmd.DrawMesh(contourMesh40,Matrix4x4.identity,inkStyle39,0,0,p);}
'''+code[b:]
 rep('["trialMinimumGridUnits39"]=1,','["geometryContour40"]=new Obj40{["lineSegments"]=contour40.indices.Length/2,["openSourceEdges"]=contour40.openEdges,["nonmanifoldSourceEdges"]=contour40.nonmanifoldEdges,["degenerateProjectedTriangles"]=contour40.degenerateTriangles,["sourceEdges"]=contour40.sourceEdges},["motion40"]=motionProof40,["nativeLineRaster40"]="one logical-grid native GPU line, actual source endpoint depth, no inversion/extrusion or gap fill",')
 rep('foreach(var t in Fields.Concat(QFields.Take(18)))','foreach(var t in Fields.Take(12).Concat(QFields.Take(18)))')
 rep('b.UseTexture(graph.ImportTexture(QFields[18]),AccessFlags.Write);','b.UseTexture(graph.ImportTexture(Fields[12]),AccessFlags.Write);b.UseTexture(graph.ImportTexture(QFields[18]),AccessFlags.Write);')
 start=code.index('cmd.SetComputeTextureParam(outline39,outlineKernel39,"_InkOn39"');end=code.index('submission.StageRecorded(8);',start)
 code=code[:start]+'''cmd.SetComputeTextureParam(outline39,outlineKernel39,"_LineOn40",Fields[8].rt);cmd.SetComputeTextureParam(outline39,outlineKernel39,"_LineOff40",Fields[10].rt);cmd.SetComputeTextureParam(outline39,outlineKernel39,"_Before40",QFields[19].rt);cmd.SetComputeTextureParam(outline39,outlineKernel39,"_After40",QFields[20].rt);cmd.SetComputeTextureParam(outline39,outlineKernel39,"_Meta40",QFields[21].rt);cmd.SetComputeIntParams(outline39,"_Size40",QROI.width,QROI.height);cmd.SetComputeVectorParam(outline39,"_Ink40",sourceInk);cmd.DispatchCompute(outline39,outlineKernel39,(QROI.width+7)/8,(QROI.height+7)/8,1);var pack40=new[]{QFields[19],QFields[20],QFields[21],Fields[8],Fields[9],Fields[10],Fields[11],QFields[7],QFields[9]};for(int i=0;i<pack40.Length;i++)cmd.CopyTexture(pack40[i].rt,0,0,0,0,QROI.width,QROI.height,Fields[12].rt,0,0,QROI.width*i,0);'''+code[end:]
 rep('if(inkStyle39)UnityEngine.Object.DestroyImmediate(inkStyle39);','if(inkStyle39)UnityEngine.Object.DestroyImmediate(inkStyle39);if(contourMesh40)UnityEngine.Object.DestroyImmediate(contourMesh40);')
 # Six consecutive actual native frames; the existing held-pose control is
 # removed only after the normal game-input scope is connected below.
 code=code.replace('producers.Length!=1','producers.Length!=6').replace('cohort=new SourceOutline40[1]','cohort=new SourceOutline40[6]').replace('for(int i=0;i<1;i++){cohort[i]','for(int i=0;i<6;i++){cohort[i]')
 start=code.index('foreach(int i in new[]{6,7,9,11,12,18,19,20,21})');end=code.index('report["frameInfo"]=',start);code=code[:start]+'''var extent=producer.FieldExtent40(false,12);tasks.Add(new Plane(false,12,"atlas40",extent.x,extent.y));'''+code[end:]
 # Start with the same-pose six-frame control. Motion scope is a separate,
 # explicitly prepared test variant after the source contour passes.
 helper=(H/'Contour40.cs').read_text();headerEnd=code.index('namespace Unity.AI.Assistant.Agent.Dynamic.Extension.Editor');helper=helper[helper.index('namespace Unity.AI.Assistant.Agent.Dynamic.Extension.Editor'):];code=code[:headerEnd]+helper+'\n'+code[headerEnd:]
 for bad in ['EvaluateForm115','BoundRun115','InputSystem.settings=','RenderPose(']:assert bad not in code
 c=G/'capture';c.mkdir(exist_ok=True);assert not(c/'REQUEST.json').exists();(c/'RUN.cs.txt').write_text(code,encoding='utf-8',newline='\n');compile_source([c/'RUN.cs.txt'],G/'build/capture40.dll')
 # Reuse the proven shader-only importer and its native preservation checks.
 imp=(H/'face39/import/RUN.cs.txt').read_text();start=imp.index('internal class CommandScript');imp=code[:code.index('internal class CommandScript')]+imp[start:];imp=imp.replace('CreateOnly39','CreateOnly40').replace('Obj39','Obj40').replace('Arr39','Arr40').replace('NativeSnapshot39','NativeSnapshot40').replace('face39\\import','face40\\import').replace('face39\\shaders','face40\\shaders').replace('SourceBoundary39','SourceBoundary40').replace('new[]{"OutlineResolve39.compute"}','new[]{"GeoContour40.shader","GeoResolve40.compute"}').replace('Target+"/OutlineResolve39.compute"','Target+"/GeoResolve40.compute"').replace('FindKernel("ResolveOutline39")','FindKernel("ResolveGeometry40")')
 needle='var checks=NativeSnapshot40.Compare';imp=imp.replace(needle,'var gs40=AssetDatabase.LoadAssetAtPath<Shader>(Target+"/GeoContour40.shader");if(!gs40||!gs40.isSupported)throw new InvalidOperationException("40 line shader unsupported");foreach(var message in ShaderUtil.GetShaderMessages(gs40))if(message.severity.ToString()=="Error")throw new InvalidOperationException(message.message);'+needle)
 i=G/'import';i.mkdir(exist_ok=True)
 if not(i/'REQUEST.json').exists():(i/'RUN.cs.txt').write_text(imp,encoding='utf-8',newline='\n')
 compile_source([i/'RUN.cs.txt'],G/'build/import40.dll');result={'CPUCompile':'passed','weldVertices':w['sourceVertices'],'weldGroups':w['groups'],'allPositionStreams':w['positionStreams'],'computeAudit':audit,'captureSHA256':sha(c/'RUN.cs.txt'),'importSHA256':sha(i/'RUN.cs.txt'),'newShaders':2,'newGPUUnityCalls':0,'arrayOrBVHOr115':False,'atlasBytesCurrentExpected':30*30*9*16,'prototypeNotAdopted':True};(G/'PREPARED40.json').write_text(json.dumps(result,indent=2),encoding='utf-8',newline='\n');print(json.dumps(result))
if __name__=='__main__':main()
