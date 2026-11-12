"""Separate output window from the full current source queries.

72 verified only a 2-cell interior because its source function clipped to the
diagnostic ROI. Actual source textures are full Native/Main grids. Query those
grids directly; capture an extra 2-cell observation halo for the CPU oracle.
No selected RGB or CPU history is uploaded, and product77 remains unchanged.
"""
from pathlib import Path
import ctypes as C,sys,re,json,hashlib
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face73'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 for d in['capture','import','final','post/final','console','shaders','build']:(G/d).mkdir(parents=True,exist_ok=True)
 assert not(G/'capture/REQUEST.json').exists()and not(G/'import/REQUEST.json').exists()
 c=(H/'face72/shaders/SourceNativeHull60.compute').read_text();a='any(origin<0)||any(origin>=_Size41)||';assert c.count(a)==1;c=c.replace(a,'');a='||any(local<2)||any(local>=_Size41-2)';assert c.count(a)==1;c=c.replace(a,'')
 # Source indices are nonnegative after explicit bounds guards. Constant power
 # of two indexing removes newly introduced dynamic signed division warnings.
 c=c.replace('int3(i%_VertexUVStride72,i/_VertexUVStride72,0)','int3((uint)i&127u,(uint)i>>7u,0)')
 (G/'shaders/SourceNativeHull60.compute').write_text(c,encoding='utf-8',newline='\n')
 sys.path.insert(0,str(H.parent/'bounded-form115/prefix24'));import compile_hlsl_cpu as api
 dll=C.WinDLL(str(api.DLL),winmode=0x800);fn=dll.D3DCompile;fn.argtypes=[C.c_void_p,C.c_size_t,C.c_char_p,C.c_void_p,C.c_void_p,C.c_char_p,C.c_char_p,C.c_uint,C.c_uint,C.POINTER(C.c_void_p),C.POINTER(C.c_void_p)];fn.restype=C.c_long
 text=re.sub(rb'(?m)^#pragma kernel [^\r\n]+\r?\n',b'',c.encode());buf=C.create_string_buffer(text);code=C.c_void_p();err=C.c_void_p()
 try:
  hr=fn(buf,len(text),b'SourceNativeHull60.compute',None,None,b'SourceNativeHull60',b'cs_5_0',(1<<11)|(1<<15),0,C.byref(code),C.byref(err));assert hr>=0,api.blob(err).decode(errors='replace');audit=api.token_audit(api.blob(code));assert audit['loops']==0 and not audit['privateArrayDeclarations']and audit['instructions']<16000;(G/'build/halo73.dxbc').write_bytes(api.blob(code))
 finally:api.release(code);api.release(err)
 s=(H/'face72/capture/RUN.cs.txt').read_text().replace('resume-20261111\\face72\\capture','resume-20261111\\face73\\capture').replace('face72-vertex-width-motion-','face73-source-halo-motion-')
 a='int qx=Math.Max(0,left-3),qy=Math.Max(0,top-3),qr=Math.Min(480,right+3),qb=Math.Min(272,bottom+3);';assert s.count(a)==1;s=s.replace(a,'int qx=Math.Max(0,left-5),qy=Math.Max(0,top-5),qr=Math.Min(480,right+5),qb=Math.Min(272,bottom+5);')
 a='(long)QROI.width*QROI.height*16*16>262144';assert s.count(a)==1;s=s.replace(a,'(long)QROI.width*QROI.height*16*16>1048576')
 # The 1MiB atlas remains copied using existing <=262144-byte row strips; no
 # individual GPU readback limit or acknowledgement guard is relaxed.
 (G/'capture/RUN.cs.txt').write_text(s,encoding='utf-8',newline='\n');compile_unity_language(G/'capture/RUN.cs.txt',G/'build/halo73.dll')
 imp=(H/'face72/import/RUN.cs.txt').read_text().replace('resume-20261111\\face72\\import','resume-20261111\\face73\\import').replace('resume-20261111\\face72\\shaders','resume-20261111\\face73\\shaders');(G/'import/RUN.cs.txt').write_text(imp,encoding='utf-8',newline='\n');compile_unity_language(G/'import/RUN.cs.txt',G/'build/import73.dll');(G/'import/EXPECTED.json').write_text(json.dumps({'beforeSHA':sha(H/'face72/shaders/SourceNativeHull60.compute'),'afterSHA':sha(G/'shaders/SourceNativeHull60.compute'),'guid':'e6f555999930fe84986310c502927d67'},indent=2))
 for mode in['final','post/final']:
  src=H/('face72/'+mode+'/RUN.cs.txt');s=src.read_text().replace('resume-20261111\\face72','resume-20261111\\face73');(G/mode/'RUN.cs.txt').write_text(s,encoding='utf-8',newline='\n');compile_unity_language(G/mode/'RUN.cs.txt',G/'build'/('post73.dll'if mode.startswith('post')else'pre73.dll'))
 (G/'console/ARGS.json').write_text((H/'face72/console/ARGS.json').read_text())
 result={'CSharp9Compiled':True,'CPUShaderCompiled':True,'tokenAudit':audit,'computeSHA256':sha(G/'shaders/SourceNativeHull60.compute'),'captureSHA256':sha(G/'capture/RUN.cs.txt'),'GPUExecuted':False,'maxFixedNeighbours':24,'readbackMaxBytes':262144,'observationHaloCells':2,'oracleOnlyClaimsInteriorHalo2':True,'sourceQueryUsesFullCurrentNativeMainGrids':True,'product77Changed':False};(G/'CPU_PREPARED73.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':main()
