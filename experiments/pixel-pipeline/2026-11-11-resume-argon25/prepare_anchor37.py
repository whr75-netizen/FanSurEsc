from pathlib import Path
import hashlib,json,re,sys
import numpy as np
H=Path(__file__).resolve().parent;G=H/'face37';sys.path.insert(0,str(H))
from prepare_review30 import compile_source
from surface_paths34 import native
from review_runtime36 import load
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 G.mkdir(exist_ok=True);(G/'build').mkdir(exist_ok=True);r=json.loads((H/'face36/fix1/capture/COMPLETE.json').read_text());assert r['restorationChecksPass']and r['ownedResourcesReleased'];fr=r['frames'][0];qx,qy,w,h=fr['QROI'];gx,gy=json.loads((H/'face36/WATCH36.json').read_text())['points'][0];x,y=gx-qx,qy+h-1-gy;sample=load(r,fr['frame'],'q9')[y,x];surface,binding=native();tri=int(round(sample[2]))-1;uv=sample[:2].astype(float);b12=surface.inv[tri]@(uv-surface.tri[tri,0]);bary=np.r_[1-b12.sum(),b12];assert bary.min()>=0 and bary.max()<=1
 anchor={'basisSourceId':fr['sourceId'],'sourceModelSHA256':fr['frameInfo']['model'],'meshUVSHA256':binding['meshUVSHA256'],'indexSHA256':binding['indexSHA256'],'rendererOrdinal':binding['rendererOrdinal'],'subMesh':binding['subMesh'],'triangleZeroBased':tri,'corners':surface.indices[tri].tolist(),'barycentric':bary.tolist(),'UV':uv.tolist(),'colourRegionAssigned':False};key=json.dumps({k:anchor[k]for k in ['sourceModelSHA256','rendererOrdinal','subMesh','triangleZeroBased','barycentric']},sort_keys=True);anchor['sourceKey']=hashlib.sha256(key.encode()).hexdigest();(G/'ANCHOR37.json').write_text(json.dumps(anchor,indent=2),encoding='utf-8',newline='\n')
 old=(H/'face36/fix1/capture/RUN.cs.txt').read_text();names=['Json','Obj','Arr','SerializedContent','CreateOnly','NativeSnapshot','GlobalJournal','GridBinding','GridSpace','Submission','ExitCoordinator','PendingViews','QMetaLattice','Projection','ConsumerReads','EditorExitRequest','ReadbackPreflight','SourceOutline','SourceCaptureHost','SourceSequenceHost','FrameInfo','LegacyInputs','ConsumerPending','TargetFrame','RequestFieldReadback','RequestClassificationReadback','FieldExtent'];mapping={n+'36':n+'37'for n in names};code=re.sub(r'\b('+'|'.join(mapping)+r')\b',lambda m:mapping[m[0]],old)
 code=code.replace('face36\\fix1\\capture','face37\\capture').replace('id="face36-"','id="face37-"')
 def rep(a,b):
  nonlocal code
  assert code.count(a)==1,(a,code.count(a));code=code.replace(a,b)
 rep('readonly object failureSync=', 'readonly Json37 anchorDoc37=Json37.Parse(File.ReadAllText(@"'+str(G/'ANCHOR37.json')+'"));public Obj37 Anchor37{get;private set;}\n readonly object failureSync=')
 rep('model=(string)registry["modelSHA256"];','model=(string)registry["modelSHA256"];if(model!=(string)anchorDoc37["sourceModelSHA256"])throw new InvalidOperationException("37 source model invalidated");')
 rep('var normalMatrix=transform.inverse.transpose;','var normalMatrix=transform.inverse.transpose;PrepareAnchor37(mesh,vertices,transform);')
 token=' public override void RecordRenderGraph';assert code.count(token)==1
 method=''' void PrepareAnchor37(UnityEngine.Mesh mesh,Vector3[] vertices,Matrix4x4 transform){
  if(renderer!=(int)anchorDoc37["rendererOrdinal"]||submesh!=(int)anchorDoc37["subMesh"])throw new InvalidOperationException("37 carrier binding mismatch");
  string Hash(byte[] b){using(var h=SHA256.Create())return BitConverter.ToString(h.ComputeHash(b)).Replace("-","").ToLowerInvariant();}
  var indices=mesh.GetIndices(submesh);var ib=new byte[indices.Length*4];Buffer.BlockCopy(indices,0,ib,0,ib.Length);if(Hash(ib)!=(string)anchorDoc37["indexSHA256"])throw new InvalidOperationException("37 source indices invalidated");
  var uv=mesh.uv;var ub=new byte[uv.Length*8];using(var stream=new MemoryStream(ub))using(var writer=new BinaryWriter(stream)){foreach(var a in uv){writer.Write(a.x);writer.Write(a.y);}}if(Hash(ub)!=(string)anchorDoc37["meshUVSHA256"])throw new InvalidOperationException("37 source UV invalidated");
  int t=(int)anchorDoc37["triangleZeroBased"];var corners=anchorDoc37["corners"].Values<int>().ToArray();var b=anchorDoc37["barycentric"].Values<double>().ToArray();if(t<0||3*t+2>=indices.Length)throw new InvalidOperationException("37 source primitive unavailable");var local=new double[3][];var witness=Vector2.zero;
  for(int j=0;j<3;j++){int ix=indices[3*t+j];if(ix!=corners[j]||ix<0||ix>=vertices.Length)throw new InvalidOperationException("37 source primitive changed");var v=vertices[ix];local[j]=new double[]{v.x,v.y,v.z};witness+=uv[ix]*(float)b[j];}
  var expected=anchorDoc37["UV"].Values<double>().ToArray();if(Math.Abs(witness.x-expected[0])>2e-7||Math.Abs(witness.y-expected[1])>2e-7)throw new InvalidOperationException("37 barycentric UV mismatch");
  var world=SourceAnchorMath37.World(local,b,Enumerable.Range(0,16).Select(i=>(double)transform[i]).ToArray());var point=new Vector3((float)world[0],(float)world[1],(float)world[2]);var head=eye.full.Project(point);if(!float.IsFinite(head.x)||!float.IsFinite(head.y))throw new InvalidOperationException("37 source projection unavailable");Anchor37=new Obj37{["sourceKey"]=(string)anchorDoc37["sourceKey"],["actorInstance"]=eye.GetEntityId().ToString(),["camera"]=cameraIdentity,["triangle"]=t,["UV"]=anchorDoc37["UV"],["barycentric"]=anchorDoc37["barycentric"],["world"]=new Arr37(world),["head"]=new Arr37(head.x,head.y),["headPixel"]=new Arr37((int)Math.Floor(head.x),(int)Math.Floor(head.y)),["expectedDepth"]=-(camera.worldToCameraMatrix*new Vector4(point.x,point.y,point.z,1)).z,["indicesUVVerified"]=true};
 }
'''
 code=code.replace(token,method+token)
 rep('["sourceId"]=FrameKey,["frame"]=frame,','["sourceId"]=FrameKey,["frame"]=frame,["sourceAnchor"]=Anchor37,["timeScale"]=Time.timeScale,')
 rep('List<Plane> tasks;','List<Plane> tasks;float runtimeTime37;bool held37;void RestoreHold37(){if(held37){Time.timeScale=runtimeTime37;held37=false;}}')
 rep('cohort=new SourceOutline37[6];','runtimeTime37=Time.timeScale;CreateOnly37.Text(Path.Combine(Root,"POSE_HOLD_BEFORE37.json"),new Obj37{["timeScale"]=runtimeTime37,["sourceFrame"]=n.host.main.motion.sourceFrame,["resetHistoryObserver"]=false,["inputReference"]=InputSystem.settings.GetEntityId().ToString()}.ToString());Time.timeScale=0;held37=true;cohort=new SourceOutline37[6];')
 rep('TargetFrame37=Time.frameCount+1+i;','TargetFrame37=Time.frameCount+2+i;')
 rep('new SourceSequenceHost37(cohort,()=>{},Restore)','new SourceSequenceHost37(cohort,RestoreHold37,Restore)')
 rep('earlyExit.Begin(()=>producer?.StopRecording(),()=>{},','earlyExit.Begin(()=>producer?.StopRecording(),RestoreHold37,')
 start=code.index('if(cohortRead>0){var watch=');end=code.index('report["frameInfo"]=',start)
 code=code[:start]+'''if(cohortRead>0){var point=producer.Anchor37["headPixel"];int lx=(int)point[0]-q.x,ly=q.y+q.height-1-(int)point[1];if(lx<0||ly<0||lx>=q.width||ly>=q.height)throw new InvalidOperationException("37 source anchor outside visible ROI");foreach(int fi in new[]{16,17})tasks.Add(new Plane(true,fi,"q"+fi+"-watch0",8,8){ox=lx*8,oy=ly*8});}'''+code[end:]
 oldABI=set(re.findall(r'"(_[A-Za-z0-9_]+)"',old));assert oldABI<=set(re.findall(r'"(_[A-Za-z0-9_]+)"',code))
 for forbidden in ['EvaluateForm115','BoundRun115','InputSystem.settings=','RenderPose(']:assert forbidden not in code
 source=(H/'SourceAnchor37.cs').read_text();code=source+'\n'+code # move its using into the existing header, before other declarations
 code=code.replace('using System;\n// Pure source-coordinate','// Pure source-coordinate',1)
 # IRunCommand common header must precede the new pure helper declaration.
 header=code[code.index('using System;'):code.index('namespace Unity.AI.Assistant.Agent.Dynamic.Extension.Editor')];code=header+'\n'+code.replace(header,'',1)
 p=G/'capture';p.mkdir(exist_ok=True);assert not(p/'REQUEST.json').exists();(p/'RUN.cs.txt').write_text(code,encoding='utf-8',newline='\n');compile_source([p/'RUN.cs.txt'],G/'build/capture37.dll')
 result={'CPUCompile':'passed','newAssets':0,'newShaderOrKernel':0,'sourceAnchor':anchor,'captureSHA':sha(p/'RUN.cs.txt'),'scalarChanges':'temporary runtime Time.timeScale=0 after ready, restored before normal Exit and after Edit','sourceFrames':6,'sameDefaultShaders36':True};(G/'PREPARED37.json').write_text(json.dumps(result,indent=2),encoding='utf-8',newline='\n');print(json.dumps({k:v for k,v in result.items()if k!='sourceAnchor'}))
if __name__=='__main__':main()
