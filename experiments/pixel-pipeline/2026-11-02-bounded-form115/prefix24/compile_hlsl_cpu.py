"""Windows D3DCompile/D3DReflect only. No device/context/driver or Unity API.

Uses the Microsoft-signed System32 compiler already checked by the caller.
Only source->DXBC and bytecode-reflection functions are imported. Includes are
disabled. This process observes its own loaded modules and rejects GPU DLLs.
"""
from pathlib import Path
import ctypes as C, hashlib, json, re, struct
H=Path(__file__).resolve().parent
DLL=Path(r'C:\Windows\System32\d3dcompiler_47.dll')

def modules():
    k=C.WinDLL('kernel32',use_last_error=True);p=C.WinDLL('psapi',use_last_error=True)
    k.GetCurrentProcess.restype=C.c_void_p
    handle=k.GetCurrentProcess();a=(C.c_void_p*2048)();needed=C.c_uint()
    p.EnumProcessModules.argtypes=[C.c_void_p,C.c_void_p,C.c_uint,C.POINTER(C.c_uint)]
    p.GetModuleFileNameExW.argtypes=[C.c_void_p,C.c_void_p,C.c_wchar_p,C.c_uint]
    assert p.EnumProcessModules(handle,a,C.sizeof(a),C.byref(needed))
    assert needed.value<=C.sizeof(a)
    out=[]
    for ptr in a[:needed.value//C.sizeof(C.c_void_p)]:
        buf=C.create_unicode_buffer(32768)
        assert p.GetModuleFileNameExW(handle,ptr,buf,len(buf))
        out.append(buf.value)
    return sorted(out)

def method(ptr,index,restype,*types):
    table=C.cast(ptr,C.POINTER(C.POINTER(C.c_void_p))).contents
    return C.WINFUNCTYPE(restype,C.c_void_p,*types)(table[index])
def release(ptr):
    if ptr:method(ptr,2,C.c_uint)(ptr)
def blob(ptr):
    if not ptr:return b''
    p=method(ptr,3,C.c_void_p)(ptr);n=method(ptr,4,C.c_size_t)(ptr)
    assert n<2*1024*1024
    return C.string_at(p,n)

class GUID(C.Structure):_fields_=[('a',C.c_uint),('b',C.c_ushort),('c',C.c_ushort),('d',C.c_ubyte*8)]
class Binding(C.Structure):
    _fields_=[('Name',C.c_char_p),('Type',C.c_uint),('BindPoint',C.c_uint),('BindCount',C.c_uint),('Flags',C.c_uint),('ReturnType',C.c_uint),('Dimension',C.c_uint),('NumSamples',C.c_uint)]
class CBDesc(C.Structure):_fields_=[('Name',C.c_char_p),('Type',C.c_uint),('Variables',C.c_uint),('Size',C.c_uint),('Flags',C.c_uint)]
class VarDesc(C.Structure):
    _fields_=[('Name',C.c_char_p),('StartOffset',C.c_uint),('Size',C.c_uint),('Flags',C.c_uint),('DefaultValue',C.c_void_p),('StartTexture',C.c_uint),('TextureSize',C.c_uint),('StartSampler',C.c_uint),('SamplerSize',C.c_uint)]

def reflect(dll,code):
    iid=GUID(0x8d536ca1,0x0cca,0x4956,(C.c_ubyte*8)(0xa8,0x37,0x78,0x69,0x63,0x75,0x55,0x84));out=C.c_void_p();buf=C.create_string_buffer(code)
    dll.D3DReflect.argtypes=[C.c_void_p,C.c_size_t,C.POINTER(GUID),C.POINTER(C.c_void_p)];dll.D3DReflect.restype=C.c_long
    assert dll.D3DReflect(buf,len(code),C.byref(iid),C.byref(out))>=0
    rows=[];constants=[]
    try:
        for i in range(128):
            desc=Binding();hr=method(out,6,C.c_long,C.c_uint,C.POINTER(Binding))(out,i,C.byref(desc))
            if hr<0:break
            row={n:int(getattr(desc,n))for n in ['Type','BindPoint','BindCount','Flags','ReturnType','Dimension','NumSamples']};row['Name']=desc.Name.decode();rows.append(row)
            if desc.Type==0:
                cb=method(out,5,C.c_void_p,C.c_char_p)(out,desc.Name);d=CBDesc();assert method(cb,0,C.c_long,C.POINTER(CBDesc))(cb,C.byref(d))>=0
                variables=[]
                for j in range(d.Variables):
                    var=method(cb,1,C.c_void_p,C.c_uint)(cb,j);v=VarDesc();assert method(var,0,C.c_long,C.POINTER(VarDesc))(var,C.byref(v))>=0
                    variables.append({'name':v.Name.decode(),'offset':v.StartOffset,'bytes':v.Size,'flags':v.Flags})
                constants.append({'name':desc.Name.decode(),'bytes':d.Size,'variables':variables})
        else:raise AssertionError('Unexpected binding count')
    finally:release(out)
    return rows,constants

def token_audit(code,allow_arrays=False):
    assert code[:4]==b'DXBC';count=struct.unpack_from('<I',code,28)[0]
    for i in range(count):
        at=struct.unpack_from('<I',code,32+i*4)[0]
        if code[at:at+4]not in[b'SHEX',b'SHDR']:continue
        size=struct.unpack_from('<I',code,at+4)[0];w=struct.unpack_from('<'+'I'*(size//4),code,at+8)
        p=2;ops=[];arrays=[];strides={};threads=None
        while p<len(w):
            op=w[p]&2047;n=w[p+1]if op==53 else(w[p]>>24)&127;assert n and p+n<=len(w)
            if op==105:arrays.append(list(w[p+1:p+n]))
            if op==155:threads=list(w[p+1:p+4])
            if op in[158,162]:strides[('u'if op==158 else't')+str(w[p+2])]=w[p+3]
            ops.append(op);p+=n
        assert threads and (allow_arrays or not arrays)
        return {'instructions':len(ops),'privateArrayDeclarations':arrays,'threads':threads,'structuredStridesBySlot':strides,'loops':ops.count(48)}
    raise AssertionError('No SM5 instruction chunk')

def main():
    identity=json.loads((H/'MODULE.json').read_text());source=(H/'Prefix24.compute').read_bytes();assert hashlib.sha256(source).hexdigest()==identity['sourceSHA256']
    # Unity's entrypoint pragmas are metadata for its importer, not FXC directives.
    compiled_source=re.sub(rb'(?m)^#pragma kernel [^\r\n]+\r?\n',b'',source)
    assert b'#include'not in compiled_source and b'115'not in compiled_source
    before=modules();dll=C.WinDLL(str(DLL),winmode=0x800)
    fn=dll.D3DCompile;fn.argtypes=[C.c_void_p,C.c_size_t,C.c_char_p,C.c_void_p,C.c_void_p,C.c_char_p,C.c_char_p,C.c_uint,C.c_uint,C.POINTER(C.c_void_p),C.POINTER(C.c_void_p)];fn.restype=C.c_long
    data=C.create_string_buffer(compiled_source);rows=[]
    expected=json.loads((H.parent/'HOST_ROUTE24.json').read_text());byname={r['kernel']:r for r in expected['matrix']}
    for entry in identity['entrypoints']:
        code=C.c_void_p();err=C.c_void_p()
        try:
            hr=fn(data,len(compiled_source),b'Prefix24.compute',None,None,entry.encode(),b'cs_5_0',(1<<11)|(1<<15),0,C.byref(code),C.byref(err))
            diagnostics=blob(err).decode('utf-8',errors='replace');(H/(entry+'.diagnostics.txt')).write_text(diagnostics,encoding='utf-8')
            assert hr>=0,(entry,hr,diagnostics)
            assert 'forcing loop'not in diagnostics and 'not natively addressable'not in diagnostics
            binary=blob(code);audit=token_audit(binary);bindings,constants=reflect(dll,binary)
            assert {r['Name']for r in bindings if r['Type']!=0}==set(byname[entry]['resources'])
            assert audit['threads']==[int(x)for x in byname[entry]['threads'].split(',')]
            assert all(r['Type']in[0,6]for r in bindings)
            (H/(entry+'.dxbc')).write_bytes(binary)
            rows.append({'entry':entry,'SHA256':hashlib.sha256(binary).hexdigest(),'bytes':len(binary),'diagnostics':diagnostics,'audit':audit,'bindings':bindings,'constants':constants})
        finally:release(code);release(err)
    after=modules();bad=[p for p in after if re.search(r'(?i)(?:d3d11|d3d12|dxgi|amdxx64|amddxx64|nvwgf2umx|igd10iumd64)\.dll$',p)]
    assert not bad,bad
    output={'compiler':str(DLL),'compilerSHA256':hashlib.sha256(DLL.read_bytes()).hexdigest(),'API':['D3DCompile','D3DReflect','ID3DBlob','ID3D11ShaderReflection'],
            'sourceSHA256':identity['sourceSHA256'],'compiledSourceSHA256':hashlib.sha256(compiled_source).hexdigest(),'target':'cs_5_0','flags':'strictness|optimization3',
            'GPUDeviceCreated':False,'GPUDispatches':0,'UnityCalls':0,'newModules':sorted(set(after)-set(before)),'GPUDriverOrDeviceDLLsLoaded':bad,'kernels':rows,
            'notGPUClearance':True,'reference':'https://learn.microsoft.com/en-us/windows/win32/api/d3dcompiler/nf-d3dcompiler-d3dcompile'}
    (H/'HLSL_COMPILE.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps({'compiled':len(rows),'privateArrays':[len(r['audit']['privateArrayDeclarations'])for r in rows],'UAVs':[sum(b['Type']==6 for b in r['bindings'])for r in rows],'GPUDeviceCreated':False,'GPUDriverDLLs':bad,'warnings':[r['diagnostics']for r in rows]}))

if __name__=='__main__':main()
