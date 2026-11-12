"""Bounded current-source vertex width; preserve 69 and product77 defaults.

Input: current ordinary source role/primitive/UV -> immutable original vertex
UVs -> native linear green samples -> source barycentric scalar -> explicit
style radius 0..2 -> shared integer grid outside CURRENT actor -> current world
depth gate -> original outline palette. Screen RGB is never a width input.
This is not metre extrusion equality or temporal history. All 24 neighbours are
fixed; no GPU loop, dynamic array, BVH, or EvaluateForm115 code is introduced.
"""
from pathlib import Path
import json,sys,re,ctypes as C,hashlib
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face72'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 for name in ['capture','import','final','shaders','build']:(G/name).mkdir(parents=True,exist_ok=True)
 assert not(G/'capture/REQUEST.json').exists()and not(G/'import/REQUEST.json').exists()
 c=(H/'face69/shaders/SourceNativeHull60.compute').read_text()
 def rep(a,b):
  nonlocal c
  assert c.count(a)==1,(a,c.count(a));c=c.replace(a,b)
 rep('void Source68(', (H/'VertexWidth72.hlsl').read_text()+'\nvoid Source68(')
 rep('int2 origin,int distance2,float4 targetMeta','int2 origin,int distance2,int chebyshev,float4 targetMeta')
 rep('inout float3 inkBest){','inout float3 inkBest,inout float2 widthBest){\n if(chebyshev>_ExteriorRadius72)return;')
 rep(' float4 key=float4(role,selected.w,uv.xy);',' float green72;bool widthValid72=SourceWidth72(role,(int)selected.w-1,uv.xy,green72);\n if(!widthValid72)return;int radius72=(int)floor(_ExteriorRadius72*green72+.5);if(chebyshev>radius72)return;\n float4 key=float4(role,selected.w,uv.xy);')
 rep('keyBest=key;inkBest=ink.rgb;','keyBest=key;inkBest=ink.rgb;widthBest=float2(green72,radius72);')
 rep('out float4 key,out float3 ink){','out float4 key,out float3 ink,out float2 widthTrace){')
 rep('key=0;ink=0;','key=0;ink=0;widthTrace=0;')
 rep('any(local<1)||any(local>=_Size41-1)','_ExteriorRadius72<1||_ExteriorRadius72>2||any(local<2)||any(local>=_Size41-2)')
 a=c.index(' // Eight fixed neighbours');b=c.index(' return key.x>0',a)
 fixed=' // Fixed 5x5 stencil, centre excluded; global radius rejects outer\n // ring before loads. Current source scalar gates candidates before ranking.\n'
 for dy in range(-2,3):
  for dx in range(-2,3):
   if dx or dy:fixed+=f' Source68(local+int2({dx},{dy}),{dx*dx+dy*dy},{max(abs(dx),abs(dy))},meta,world,distanceBest,depthBest,key,ink,widthTrace);\n'
 c=c[:a]+fixed+c[b:]
 rep('float4 key68;float3 ink68;bool selected68=IntegerExterior68(local,cell,meta,world,inside&&finite&&matched,key68,ink68);','float4 key68;float3 ink68;float2 width72;bool selected68=IntegerExterior68(local,cell,meta,world,inside&&finite&&matched,key68,ink68,width72);')
 rep('_OwnerReceipts47[local+int2(4*_Size41.x,0)]=float4(cv62.xyz,0);','_OwnerReceipts47[local+int2(4*_Size41.x,0)]=float4(width72,selected68?1:0,0);')
 rep(' float4 candidateReceipt67;',' float sourceGreen72;bool sourceWidthValid72=SourceWidth72((int)round(originalOwner.x),(int)selectedSource.w-1,originalUV.xy,sourceGreen72);\n _OwnerReceipts47[local+int2(5*_Size41.x,0)]=float4(sourceGreen72,floor(_ExteriorRadius72*sourceGreen72+.5),sourceWidthValid72?1:0,originalOwner.x);\n float4 candidateReceipt67;')
 (G/'shaders/SourceNativeHull60.compute').write_text(c,encoding='utf-8',newline='\n')
 sys.path.insert(0,str(H.parent/'bounded-form115/prefix24'));import compile_hlsl_cpu as api
 dll=C.WinDLL(str(api.DLL),winmode=0x800);fn=dll.D3DCompile;fn.argtypes=[C.c_void_p,C.c_size_t,C.c_char_p,C.c_void_p,C.c_void_p,C.c_char_p,C.c_char_p,C.c_uint,C.c_uint,C.POINTER(C.c_void_p),C.POINTER(C.c_void_p)];fn.restype=C.c_long
 text=re.sub(rb'(?m)^#pragma kernel [^\r\n]+\r?\n',b'',c.encode());buf=C.create_string_buffer(text);code=C.c_void_p();err=C.c_void_p()
 try:
  hr=fn(buf,len(text),b'SourceNativeHull60.compute',None,None,b'SourceNativeHull60',b'cs_5_0',(1<<11)|(1<<15),0,C.byref(code),C.byref(err));assert hr>=0,api.blob(err).decode(errors='replace');audit=api.token_audit(api.blob(code));assert audit['loops']==0 and not audit['privateArrayDeclarations']and audit['instructions']<16000;(G/'build/width72.dxbc').write_bytes(api.blob(code))
 finally:api.release(code);api.release(err)
 s=(H/'face69/capture/RUN.cs.txt').read_text().replace('resume-20261111\\face69\\capture','resume-20261111\\face72\\capture').replace('face69-zero-width-motion-','face72-vertex-width-motion-')
 def sr(a,b):
  nonlocal s
  assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
 sr('readonly SourceZeroWidth69 zero69;','readonly SourceVertexWidth72 width72;readonly SourceZeroWidth69 zero69;')
 sr('Fields[15]=Target(5*QROI.width,QROI.height,uav:true);','Fields[15]=Target(6*QROI.width,QROI.height,uav:true);')
 sr('readonly int[][] rgb;readonly float[] linear;bool disposed;','readonly int[][] rgb;readonly float[] linear;bool disposed;public int MappedRole72=>width72.Role;')
 sr('zero69=new SourceZeroWidth69(Path.GetFullPath(Path.Combine(root,"..","face69")),eye);','zero69=new SourceZeroWidth69(Path.GetFullPath(Path.Combine(root,"..","face69")),eye);width72=new SourceVertexWidth72(Path.GetFullPath(Path.Combine(root,"..","face69")),eye);')
 sr('zero69.Bind(cmd,shader,kernel);','width72.Bind(cmd,shader,kernel);zero69.Bind(cmd,shader,kernel);')
 sr('["zeroWidth69"]=zero69.Info(),','["vertexWidth72"]=width72.Info(),["zeroWidth69"]=zero69.Info(),')
 sr('levels*16+zero69.OwnedBytes','levels*16+zero69.OwnedBytes+width72.OwnedBytes')
 sr('zero69?.Dispose();','width72?.Dispose();zero69?.Dispose();')
 sr('foreach(int c61 in new[]{0,2,3,4,1})','foreach(int c61 in new[]{0,1,2,4,3})')
 sr('c61==1?1:0);if(sourceFlat67','c61>=1&&c61<=3?1:0);cmd.SetComputeIntParam(final41,"_ExteriorRadius72",c61==1?1:2);cmd.SetComputeIntParam(final41,"_UseWidthMap72",c61==3?1:0);if(sourceFlat67')
 sr('["explicitTestWidth"]=1,','["explicitTestWidth"]=new Arr40(0,1,2,2,0),["vertexWidth72Case"]=3,')
 # Do not silently apply this one mapped source's sampler to other materials.
 sr('bool enabled=supported&&mode==1&&width>0&&mix==0;','bool enabled=supported&&mode==1&&width>0&&mix==0;if(enabled&&role!=sourceFlat67.MappedRole72&&(m.IsKeywordEnabled("_MTOON_PARAMETERMAP")||Shader.IsKeywordEnabled("_MTOON_PARAMETERMAP"))&&m.GetTexture("_OutlineWidthTex")&&m.GetTexture("_OutlineWidthTex")!=Texture2D.whiteTexture)throw new InvalidOperationException("72 another mapped source needs its own explicit width binding");')
 s+='\n'+(H/'SourceVertexWidth72.cs.txt').read_text();(G/'capture/RUN.cs.txt').write_text(s,encoding='utf-8',newline='\n');compile_unity_language(G/'capture/RUN.cs.txt',G/'build/width72.dll')
 imp=(H/'face69/import/RUN.cs.txt').read_text().replace('resume-20261111\\face69\\import','resume-20261111\\face72\\import').replace('resume-20261111\\face69\\shaders','resume-20261111\\face72\\shaders');(G/'import/RUN.cs.txt').write_text(imp,encoding='utf-8',newline='\n');compile_unity_language(G/'import/RUN.cs.txt',G/'build/import72.dll');(G/'import/EXPECTED.json').write_text(json.dumps({'beforeSHA':sha(H/'face69/shaders/SourceNativeHull60.compute'),'afterSHA':sha(G/'shaders/SourceNativeHull60.compute'),'guid':'e6f555999930fe84986310c502927d67'},indent=2))
 pre=(H/'face69/final/RUN.cs.txt').read_text().replace('resume-20261111\\face69"','resume-20261111\\face72"');(G/'final/RUN.cs.txt').write_text(pre,encoding='utf-8',newline='\n');compile_unity_language(G/'final/RUN.cs.txt',G/'build/pre72.dll')
 result={'CSharp9Compiled':True,'CPUShaderCompiled':True,'tokenAudit':audit,'newSharedUVTextureBytesUpper':393216,'maxFixedNeighbours':24,'maxWidthGreenTextureSamplesPerThread':72,'maxGroupsPerCaseAt64CellROI':64,'maxCases':5,'computeSHA256':sha(G/'shaders/SourceNativeHull60.compute'),'captureSHA256':sha(G/'capture/RUN.cs.txt'),'GPUExecuted':False,'nativeMetresEquality':False,'runtimeHistoryFeedback':False};(G/'CPU_PREPARED72.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':main()
