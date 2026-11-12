"""Exclude proven zero-extrusion triangles; do not invent positive width support."""
from pathlib import Path
import json,struct,io,hashlib,sys,re,ctypes as C
import numpy as np
from PIL import Image
from correspondence68 import read_geometry
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face69'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 for name in ['capture','import','final','shaders','build']:(G/name).mkdir(parents=True,exist_ok=True)
 assert not(G/'capture/REQUEST.json').exists()
 if '--data-only'in sys.argv:assert(G/'import/COMPLETE.json').exists()
 else:assert not(G/'import/REQUEST.json').exists()
 base=json.loads((H/'face68/motion/capture/COMPLETE.json').read_text());info=base['frames'][0]['frameInfo'];src=json.loads((H/'face67/SOURCE_FLAT67.json').read_text());model=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')/src['modelAsset'];assert sha(model)==src['sourceFamily']['source']['modelSHA256']
 with model.open('rb')as f:
  assert struct.unpack('<I',f.read(4))[0]==0x46546c67;f.read(8);size,kind=struct.unpack('<II',f.read(8));assert kind==0x4e4f534a and size<2097152;doc=json.loads(f.read(size));bs,bt=struct.unpack('<II',f.read(8));assert bt==0x004e4942;start=f.tell();mat=src['sourceFamily']['source']['materialId'];tex=doc['materials'][mat]['extensions']['VRMC_materials_mtoon']['outlineWidthMultiplyTexture'];image=doc['images'][doc['textures'][tex['index']]['source']];view=doc['bufferViews'][image['bufferView']];assert view.get('buffer',0)==0 and view['byteLength']<=1048576;f.seek(start+view.get('byteOffset',0));png=f.read(view['byteLength'])
 rgba=np.asarray(Image.open(io.BytesIO(png)).convert('RGBA'));assert np.array_equal(rgba,np.asarray(Image.open(H/'face40/analysis-directed/SOURCE_WIDTH_MASK40.png').convert('RGBA')))
 _,_,_,meshes=read_geometry(H/'face68/motion/capture/all-source-frame102.bin');vertices,ix=meshes[src['rendererOrdinal']];uv=vertices[:,3:5];tri=ix[src['subMesh']];assert np.isfinite(uv).all()and abs(uv).max()<=2
 zero=[];height,width=rgba.shape[:2]
 for u,v in uv:
  # Bound the mathematical centre by adjacent float32 representations. Include
  # both sides when it reaches a texel boundary, rather than an unrelated whole
  # extra texel. D3D fixed-point snapping can hit the interval's integer endpoints
  # with zero weight on the outside tap; it does not invent a positive channel.
  centre=np.array([u,v],np.float32)*np.array([width,height],np.float32)-np.float32(.5)
  lo=np.nextafter(centre,np.float32(-np.inf));hi=np.nextafter(centre,np.float32(np.inf))
  xs=range(int(np.floor(lo[0])),int(np.ceil(hi[0]))+1);ys=range(int(np.floor(lo[1])),int(np.ceil(hi[1]))+1)
  zero.append(all(rgba[height-1-y%height,x%width,1]==0 for y in ys for x in xs))
 flags=np.all(np.asarray(zero)[tri],axis=1);tw=128;th=(len(tri)+tw-1)//tw;raw=np.zeros(tw*th,np.uint8);raw[:len(tri)]=flags*255;raw.tofile(G/'ZERO_TRIANGLES69.r8')
 policy={'modelSHA256':sha(model),'modelAsset':src['modelAsset'],'rendererOrdinal':src['rendererOrdinal'],'subMesh':src['subMesh'],'role':mat+1,'uvSHA256':hashlib.sha256(uv.astype('<f4').tobytes()).hexdigest(),'indexSHA256':hashlib.sha256(tri.astype('<i4').tobytes()).hexdigest(),'flagsSHA256':sha(G/'ZERO_TRIANGLES69.r8'),'count':len(tri),'zeroTriangles':int(flags.sum()),'width':tw,'height':th,'sourceTextureSize':[width,height],'liveTextureImageHash':info['authoredWidth40']['imageHash'],'sourcePNG_SHA256':hashlib.sha256(png).hexdigest(),'positiveOrVariableWidthProven':False,'mechanism':'all three source vertices have all-zero original green throughout adjacent-float32 coordinate footprint; exact zero, no colour threshold','fullPhysicalWidthEquality':False};(G/'ZERO_POLICY69.json').write_text(json.dumps(policy,indent=2))
 if '--data-only'in sys.argv:
  result=json.loads((G/'CPU_PREPARED69.json').read_text());result.update({'flagsSHA256':policy['flagsSHA256'],'zeroTriangles':policy['zeroTriangles'],'dataCorrectedBeforeFirstDispatch':True});(G/'CPU_PREPARED69.json').write_text(json.dumps(result,indent=2));print(json.dumps(result));return
 c=(H/'face68/shaders/SourceNativeHull60.compute').read_text();needle='int _IntegerExterior68;';assert c.count(needle)==1;c=c.replace(needle,'Texture2D<float> _ZeroWidthFlags69;int _ZeroWidthRole69,_ZeroWidthCount69;int2 _ZeroWidthSize69;\n'+needle)
 needle=' if(!valid||targetWorld.x<=0';assert c.count(needle)==1;c=c.replace(needle,' if(role==_ZeroWidthRole69&&valid){int wi69=(int)selected.w-1;if(wi69<0||wi69>=_ZeroWidthCount69)return;int2 wp69=int2(wi69%_ZeroWidthSize69.x,wi69/_ZeroWidthSize69.x);if(_ZeroWidthFlags69.Load(int3(wp69,0))>.5)return;}\n'+needle);(G/'shaders/SourceNativeHull60.compute').write_text(c,encoding='utf-8',newline='\n')
 sys.path.insert(0,str(H.parent/'bounded-form115/prefix24'));import compile_hlsl_cpu as api
 dll=C.WinDLL(str(api.DLL),winmode=0x800);fn=dll.D3DCompile;fn.argtypes=[C.c_void_p,C.c_size_t,C.c_char_p,C.c_void_p,C.c_void_p,C.c_char_p,C.c_char_p,C.c_uint,C.c_uint,C.POINTER(C.c_void_p),C.POINTER(C.c_void_p)];fn.restype=C.c_long
 text=re.sub(rb'(?m)^#pragma kernel [^\r\n]+\r?\n',b'',c.encode());buf=C.create_string_buffer(text);code=C.c_void_p();err=C.c_void_p()
 try:
  hr=fn(buf,len(text),b'SourceNativeHull60.compute',None,None,b'SourceNativeHull60',b'cs_5_0',(1<<11)|(1<<15),0,C.byref(code),C.byref(err));assert hr>=0,api.blob(err).decode(errors='replace');audit=api.token_audit(api.blob(code));assert audit['loops']==0 and not audit['privateArrayDeclarations'];(G/'build/zero69.dxbc').write_bytes(api.blob(code))
 finally:api.release(code);api.release(err)
 s=(H/'face68/motion/capture/RUN.cs.txt').read_text().replace('resume-20261111\\face68\\motion\\capture','resume-20261111\\face69\\capture').replace('face68-integer-exterior-motion-','face69-zero-width-motion-')
 def rep(a,b):
  nonlocal s
  assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
 rep('readonly Json40 spec;public Texture2D regions','readonly SourceZeroWidth69 zero69;readonly Json40 spec;public Texture2D regions')
 rep('  try{\n   regions=new Texture2D','  try{\n   zero69=new SourceZeroWidth69(Path.GetFullPath(Path.Combine(root,"..","face69")),eye);\n   regions=new Texture2D')
 rep('  cmd.SetComputeTextureParam(shader,kernel,"_SourceRegionMask67",regions);','  zero69.Bind(cmd,shader,kernel);cmd.SetComputeTextureParam(shader,kernel,"_SourceRegionMask67",regions);')
 rep('public Obj40 Info()=>new Obj40{["input"]','public Obj40 Info()=>new Obj40{["zeroWidth69"]=zero69.Info(),["input"]')
 rep('["maxOwnedTextureBytes"]=(long)width*height*4+levels*16','["maxOwnedTextureBytes"]=(long)width*height*4+levels*16+zero69.OwnedBytes')
 rep('public void Dispose(){if(disposed)return;if(regions)','public void Dispose(){if(disposed)return;zero69?.Dispose();if(regions)')
 s+='\n'+(H/'SourceZeroWidth69.cs.txt').read_text();(G/'capture/RUN.cs.txt').write_text(s,encoding='utf-8',newline='\n');compile_unity_language(G/'capture/RUN.cs.txt',G/'build/zero69.dll')
 imp=(H/'face68/import/RUN.cs.txt').read_text().replace('resume-20261111\\face68\\import','resume-20261111\\face69\\import').replace('resume-20261111\\face68\\shaders','resume-20261111\\face69\\shaders');(G/'import/RUN.cs.txt').write_text(imp,encoding='utf-8',newline='\n');compile_unity_language(G/'import/RUN.cs.txt',G/'build/import69.dll');(G/'import/EXPECTED.json').write_text(json.dumps({'beforeSHA':sha(H/'face68/shaders/SourceNativeHull60.compute'),'afterSHA':sha(G/'shaders/SourceNativeHull60.compute'),'guid':'e6f555999930fe84986310c502927d67'},indent=2))
 pre=(H/'face68/motion/post/final/RUN.cs.txt').read_text().replace('resume-20261111\\face68\\motion\\post"','resume-20261111\\face69"');(G/'final/RUN.cs.txt').write_text(pre,encoding='utf-8',newline='\n');compile_unity_language(G/'final/RUN.cs.txt',G/'build/pre69.dll')
 result={'CSharp9Compiled':True,'CPUShaderCompiled':True,'tokenAudit':audit,'flagsSHA256':policy['flagsSHA256'],'newSharedTextureBytes':len(raw),'zeroTriangles':policy['zeroTriangles'],'computeSHA256':sha(G/'shaders/SourceNativeHull60.compute'),'captureSHA256':sha(G/'capture/RUN.cs.txt'),'GPUExecuted':False};(G/'CPU_PREPARED69.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':main()
