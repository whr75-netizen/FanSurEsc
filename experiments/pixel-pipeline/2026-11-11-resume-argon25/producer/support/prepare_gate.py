"""Prepare shared-skin witness transport on existing113; CPU compilation only."""
from pathlib import Path
import hashlib,json,re,sys
H=Path(__file__).resolve().parent;G=H/'gate';G.mkdir(exist_ok=True);PRE=H.parent
sys.path.insert(0,str(H));from prepare_support import replace
sys.path.insert(0,str(PRE));from prepare_live import compile_cs

def main():
 assert not(G/'IMPORT_REQUEST.json').exists()and not(G/'phase-run/PHASE_REQUEST.json').exists(),'Submitted code is immutable'
 cache=H/'SHARED_SOURCE_MASK26.json';j=json.loads(cache.read_text());assert j['requiresSameFrameSourceCertificate']
 c=(PRE/'ForwardEye113_HeadHair25.compute').read_text()
 c=replace(c,'StructuredBuffer<uint> _OwnSkin113;','StructuredBuffer<uint> _OwnSkin113,_SharedSkin26;')
 c=c.replace('TraceExternal24(float2 queryPoint,float depth,int eye)','TraceExternal24(float2 queryPoint,float depth,int eye,bool allowShared26)')
 c=replace(c,'if((_OwnSkin113[t.source.z-1]&(1u<<eye))!=0&&depth-zz<=SocketLimit24(eye))continue;',
   'if(((_OwnSkin113[t.source.z-1]&(1u<<eye))!=0||(allowShared26&&(_SharedSkin26[t.source.z-1]&(1u<<eye))!=0))&&depth-zz<=SocketLimit24(eye))continue;')
 c=replace(c,'TraceExternal24(_ForwardAnchor102.xy+r.midpoint.xy,r.midpoint.z,(int)round(r.midpoint.w))',
   'TraceExternal24(_ForwardAnchor102.xy+r.midpoint.xy,r.midpoint.z,(int)round(r.midpoint.w),false)')
 # The additional mask is never used to produce source visibility. Certificates
 # identify the same source sample used for selected colour/depth; negative
 # values identify a source curve column. They are not whole-area visibility.
 c=replace(c,'float4 mass=0,ci=0,cw=0;','float3 witness26=0;float4 mass=0,ci=0,cw=0;')
 c=replace(c,'depth.x=SL113(1,1,at).x;','depth.x=SL113(1,1,at).x;float2 sv26=_SrcVisibility113[_SourceSize113.x*_SourceSize113.y+at].xy;witness26.x=all(sv26==1)?at+1:0;')
 c=replace(c,'depth.y=SL113(2,1,at).x;','depth.y=SL113(2,1,at).x;float2 sv26=_SrcVisibility113[2*_SourceSize113.x*_SourceSize113.y+at].xy;witness26.y=all(sv26==1)?at+1:0;')
 c=replace(c,'lid=float4(_LidPalette113[owner==_CurveEyeIds106.x?0:1].rgb,m.x);','lid=float4(_LidPalette113[owner==_CurveEyeIds106.x?0:1].rgb,m.x);witness26.z=all(v.xy==1)?at+1:0;')
 c=replace(c,'if(chosen<0&&boundary.source.w>0&&boundary.visibility.x>0&&boundary.visibility.x==boundary.visibility.y)lid=float4(_LidPalette113[owner==_CurveEyeIds106.x?0:1].rgb,boundary.midpoint.z);',
   'if(chosen<0&&boundary.source.w>0&&boundary.visibility.x>0&&boundary.visibility.x==boundary.visibility.y){lid=float4(_LidPalette113[owner==_CurveEyeIds106.x?0:1].rgb,boundary.midpoint.z);witness26.z=all(boundary.visibility.xy==1)?-((owner==_CurveEyeIds106.x?0:1)*_CellsSize113.x+p.x+1):0;}')
 c=replace(c,'_Cells113[cell*7+6]=0;','_Cells113[cell*7+6]=float4(witness26,26);')
 c=replace(c,'if(q.z>0&&q.w>0)v.xy=TraceExternal24(q.xy,q.z,(int)round(q.w));',
 '''if(q.z>0&&q.w>0){int pixel=sample/16;int2 p=int2(pixel%_ForwardROI102.z,pixel/_ForwardROI102.z);
  float2 centre=float2(_ForwardROI102.x+p.x+.5,272-(_ForwardROI102.y+p.y+.5));int2 cell=(int2)floor(centre-_ForwardAnchor102.xy);bool allowed26=false;
  if(all(cell>=0)&&all(cell<_CellsSize113)){int at=cell.y*_CellsSize113.x+cell.x;float4 id=_ReadIdentity96[at],cert=C113(at,6);int role=(int)round(id.x),owner=(int)round(id.y);float witness=role==1?cert.x:role==4?cert.y:role==6?cert.z:0;allowed26=cert.w==26&&owner==(int)round(q.w)&&witness!=0;}
  v.xy=TraceExternal24(q.xy,q.z,(int)round(q.w),allowed26);}''')
 compute=G/'SharedSkin26.compute';compute.write_text(c,encoding='utf-8',newline='\n')
 host=(H/'phase-run/RUN_Capture25.cs.txt').read_text();run=G/'phase-run';run.mkdir(exist_ok=True)
 host=host.replace(str(H/'phase-run'),str(run)).replace('Assets/EUnityValidation01/HeadHair25/ForwardEye113_HeadHair25.compute','Assets/EUnityValidation01/SharedSkin26/SharedSkin26.compute')
 a=host.index('public sealed class RegionDriver113:');b=host.index('\npublic sealed class HeadHair25',a);block=host[a:b]
 block=replace(block,'keys,own,cells,','keys,own,shared26,cells,')
 needle='own=B(mask.Length,4);own.SetData(mask);'
 extra='''var cacheBytes26=File.ReadAllBytes(CACHE_PATH);using(var hash26=SHA256.Create())if(BitConverter.ToString(hash26.ComputeHash(cacheBytes26)).Replace("-","").ToLowerInvariant()!=CACHE_SHA)throw new InvalidOperationException("26 reviewed source cache changed");var extra26=Json58.Parse(System.Text.Encoding.UTF8.GetString(cacheBytes26));if((string)extra26["sourceTopology"]!=topology||extra26["additionalBits"].Count!=mask.Length)throw new InvalidOperationException("26 source-affiliation cache identity mismatch");var mask26=extra26["additionalBits"].Select(v=>(uint)(int)v).ToArray();shared26=B(mask26.Length,4);shared26.SetData(mask26);'''.replace('CACHE_PATH','@"'+str(cache)+'"').replace('CACHE_SHA',json.dumps(hashlib.sha256(cache.read_bytes()).hexdigest()))
 block=replace(block,needle,needle+extra)
 needle='cmd.SetComputeBufferParam(cs,k,"_OwnSkin113",own);cmd.SetComputeBufferParam(cs,k,"_AssignedDepth24",depth24);'
 extra='cmd.SetComputeBufferParam(cs,k,"_SharedSkin26",shared26);cmd.SetComputeBufferParam(cs,k,"_Cells113",cells);cmd.SetComputeBufferParam(cs,k,"_ReadIdentity96",result[1]);'
 block=replace(block,needle,'cmd.SetComputeBufferParam(cs,k,"_OwnSkin113",own);'+extra+'cmd.SetComputeBufferParam(cs,k,"_AssignedDepth24",depth24);')
 host=host[:a]+block+host[b:]
 host=replace(host,'MotionScope97 motion82;','MotionClose106 motion82;')
 host=replace(host,'motion82=new MotionScope97(n,output);','motion82=new MotionClose106(n,output);')
 host=replace(host,'public string Stage=>"evaluated-blink106";','public bool CaptureThis=>true;public string Stage=>"evaluated-blink106";')
 host=replace(host,'static readonly float[] Values={0,25,50,75,100,75,50,25,0};','static readonly float[] Values={0,75,100,0};')
 host=replace(host,'if(captured76>=2)','if(captured76>=4)')
 for bad in ['EvaluateForm115','BoundRun115','Shader.SetGlobalBuffer(','SaveAssets(','ClearDirty(']:assert bad not in host
 assert not re.search(r'InputSystem\.settings\s*=(?!=)',host)
 source=run/'RUN_Capture25.cs.txt';source.write_text(host,encoding='utf-8',newline='\n');compile_cs(source)
 (run/'GLOBAL_NAMES66.json').write_bytes((H/'phase-run/GLOBAL_NAMES66.json').read_bytes())
 result={'computeSHA256':hashlib.sha256(compute.read_bytes()).hexdigest(),'captureSourceSHA256':hashlib.sha256(source.read_bytes()).hexdigest(),
  'cacheSHA256':hashlib.sha256(cache.read_bytes()).hexdigest(),'CSharpCPUCompiled':True,'sharedMaskBytes':4*j['primitiveCount'],
  'newComputeKernels':0,'sourceVisibilityUsesAdditionalMask':False,'GPUOrUnityExecuted':False,
  'remaining':'HLSL CPU compile/reflection, source cache binding validation and bounded import/runtime before any adoption'}
 (G/'PREPARED_GATE26.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
if __name__=='__main__':main()
