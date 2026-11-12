"""Source-local GPU owner history; fixed current candidates, no colour cache.

Reuse previous actual producer's immutable GPU atlas. Every cohort owner stays
alive until ALL producer/consumer ACKs, so no previous atlas/pose is reused or
released while a later producer may read it. Warm frame uses a distinct bound
texture and disabled history, never an SRV/UAV alias of the output atlas.
"""
from pathlib import Path
import ctypes as C,json,sys,re,hashlib
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face75'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 for d in['capture','import','final','post/final','console','shaders','build']:(G/d).mkdir(parents=True,exist_ok=True)
 assert not(G/'capture/REQUEST.json').exists()and not(G/'import/REQUEST.json').exists()
 c=(H/'face73/shaders/SourceNativeHull60.compute').read_text()
 def rep(a,b):
  nonlocal c
  assert c.count(a)==1,(a,c.count(a));c=c.replace(a,b)
 rep('void Source68(', (H/'History75.hlsl').read_text()+'\nvoid Source68(')
 rep('inout float2 widthBest){','inout float2 widthBest,inout float historyBest,int2 targetQ){')
 rep(' float4 key=float4(role,selected.w,uv.xy);',' float history75=CurrentHistory75(role,(int)selected.w-1,uv.xy,oq,targetQ)?1:0;\n float4 key=float4(role,selected.w,uv.xy);')
 rep('owner.z==depthBest&&lex','owner.z==depthBest&&(history75>historyBest||(history75==historyBest&&lex))')
 rep('widthBest=float2(green72,radius72);','widthBest=float2(green72,radius72);historyBest=history75;')
 rep('out float2 widthTrace){','out float2 widthTrace,out float historyTrace){')
 rep('widthTrace=0;','widthTrace=0;historyTrace=0;')
 c=c.replace('key,ink,widthTrace);','key,ink,widthTrace,historyTrace,local+_HeadTextureOrigin41+_JoinOffset41);')
 rep('float2 width72;bool selected68=','float2 width72;float history75;bool selected68=')
 rep('key68,ink68,width72);','key68,ink68,width72,history75);')
 rep('float4(width72,selected68?1:0,0);','float4(width72,selected68?1:0,history75);')
 (G/'shaders/SourceNativeHull60.compute').write_text(c,encoding='utf-8',newline='\n')
 sys.path.insert(0,str(H.parent/'bounded-form115/prefix24'));import compile_hlsl_cpu as api
 dll=C.WinDLL(str(api.DLL),winmode=0x800);fn=dll.D3DCompile;fn.argtypes=[C.c_void_p,C.c_size_t,C.c_char_p,C.c_void_p,C.c_void_p,C.c_char_p,C.c_char_p,C.c_uint,C.c_uint,C.POINTER(C.c_void_p),C.POINTER(C.c_void_p)];fn.restype=C.c_long
 text=re.sub(rb'(?m)^#pragma kernel [^\r\n]+\r?\n',b'',c.encode());buf=C.create_string_buffer(text);code=C.c_void_p();err=C.c_void_p()
 try:
  hr=fn(buf,len(text),b'SourceNativeHull60.compute',None,None,b'SourceNativeHull60',b'cs_5_0',(1<<11)|(1<<15),0,C.byref(code),C.byref(err));assert hr>=0,api.blob(err).decode(errors='replace');audit=api.token_audit(api.blob(code));assert audit['loops']==0 and not audit['privateArrayDeclarations']and audit['instructions']<24000;(G/'build/history75.dxbc').write_bytes(api.blob(code))
 finally:api.release(code);api.release(err)
 s=(H/'face73/capture/RUN.cs.txt').read_text().replace('resume-20261111\\face73\\capture','resume-20261111\\face75\\capture').replace('face73-source-halo-motion-','face75-source-owner-history-')
 def sr(a,b):
  nonlocal s
  assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
 sr('frame=Time.frameCount;FrameKey=','frame=Time.frameCount;PrepareHistory75();FrameKey=')
 sr('ReleaseFinal41();Disposed=true;','ReleaseFinal41();ReleaseHistory75();Disposed=true;')
 sr('cohort[i].TargetFrame40=','cohort[i].Previous75=i>0?cohort[i-1]:null;cohort[i].TargetFrame40=')
 # Extend only the existing final pass resource declaration, never a hidden
 # global binding. Previous atlas is immutable until the whole cohort drains.
 sr('d.owner=this;foreach(var t in Fields.Skip(18).Take(8)', 'd.owner=this;if(Previous75!=null)b.UseTexture(graph.ImportTexture(Previous75.Fields[12]),AccessFlags.Read);foreach(var t in Fields.Skip(18).Take(8)')
 sr('cmd.SetComputeIntParam(final41,"_UseWidthMap72",c61==3?1:0);','cmd.SetComputeIntParam(final41,"_UseWidthMap72",c61>=2&&c61<=3?1:0);BindHistory75(cmd,c61==3);')
 sr('int field49=0;foreach(var src49','historyRecorded75=true;FrameInfo40["runtimeHistory75"]=new Obj40{["previousActualFrame"]=Previous75==null?-1:Previous75.CapturedFrame,["previousSourceId"]=Previous75==null?"warm":Previous75.FrameKey,["currentMappedRole"]=sourceFlat67.MappedRole72,["poseTextureBytes"]=(long)projection75.width*projection75.height*16,["readPreviousGPUOwnerAtlas"]=Previous75!=null,["noRGBHistory"]=true,["historyOnlyBreaksEqualCurrentGeometryTies"]=true,["currentVisibilityAndOcclusionFirst"]=true,["allOwnersRetainedUntilAllACK"]=true};int field49=0;foreach(var src49')
 s+='\n'+(H/'History75.cs.txt').read_text();(G/'capture/RUN.cs.txt').write_text(s,encoding='utf-8',newline='\n');compile_unity_language(G/'capture/RUN.cs.txt',G/'build/history75.dll')
 imp=(H/'face73/import/RUN.cs.txt').read_text().replace('resume-20261111\\face73\\import','resume-20261111\\face75\\import').replace('resume-20261111\\face73\\shaders','resume-20261111\\face75\\shaders');(G/'import/RUN.cs.txt').write_text(imp,encoding='utf-8',newline='\n');compile_unity_language(G/'import/RUN.cs.txt',G/'build/import75.dll');(G/'import/EXPECTED.json').write_text(json.dumps({'beforeSHA':sha(H/'face73/shaders/SourceNativeHull60.compute'),'afterSHA':sha(G/'shaders/SourceNativeHull60.compute'),'guid':'e6f555999930fe84986310c502927d67'},indent=2))
 for mode in['final','post/final']:
  ss=(H/('face73/'+mode+'/RUN.cs.txt')).read_text().replace('resume-20261111\\face73','resume-20261111\\face75');(G/mode/'RUN.cs.txt').write_text(ss,encoding='utf-8',newline='\n');compile_unity_language(G/mode/'RUN.cs.txt',G/'build'/('post75.dll'if mode.startswith('post')else'pre75.dll'))
 (G/'console/ARGS.json').write_text((H/'face73/console/ARGS.json').read_text())
 result={'CSharp9Compiled':True,'CPUShaderCompiled':True,'tokenAudit':audit,'computeSHA256':sha(G/'shaders/SourceNativeHull60.compute'),'captureSHA256':sha(G/'capture/RUN.cs.txt'),'GPUExecuted':False,'maxFixedNeighbours':24,'noNewHistoryRT':True,'projectionTextureBytesPerFrame':204800,'faceCarrierHistoryOnly':True,'noCPUReadbackForSelection':True,'noRGBHistory':True,'sixFrameRetentionNotLongTermRing':True,'allOwnersKeptUntilAllGPUAndReadbackACK':True,'product77Changed':False};(G/'CPU_PREPARED75.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':main()
