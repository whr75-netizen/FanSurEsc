"""Inspect existing113 cache bytes only. No DLL, shader compiler or GPU."""
from pathlib import Path
import hashlib, json, re, struct
from direct_support24 import H

def main():
    report=json.loads((H/'HOST_ROUTE24.json').read_text())
    root=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game\Library\ShaderCache\compute\ForwardEye113c618')
    resources={n for r in report['matrix']for n in r['resources']}
    observed=[]
    for path in root.rglob('*.bin'):
        data=path.read_bytes();at=data.find(b'DXBC')
        if at<0:continue
        names={x.decode()for x in re.findall(rb'_[A-Za-z0-9_]{3,}',data[:at])}&resources
        matches=[r['kernel']for r in report['matrix']if set(r['resources'])==names]
        if not matches:continue
        count=struct.unpack_from('<I',data,at+28)[0]
        for k in range(count):
            start=at+struct.unpack_from('<I',data,at+32+k*4)[0]
            if data[start:start+4]not in[b'SHEX',b'SHDR']:continue
            length=struct.unpack_from('<I',data,start+4)[0];words=struct.unpack_from('<'+'I'*(length//4),data,start+8)
            pc=2;ops=[];arrays=[]
            while pc<len(words):
                code=words[pc]&2047;n=words[pc+1]if code==53 else(words[pc]>>24)&127
                assert n and pc+n<=len(words)
                if code==105:arrays.append(list(words[pc+1:pc+n]))
                ops.append(code);pc+=n
            observed.append({'file':str(path.relative_to(root)),'SHA256':hashlib.sha256(data).hexdigest(),'kernelCandidatesByResourceSignature':matches,
                             'instructionCount':len(ops),'dclIndexableTemp':arrays,'privateArrayDeclarations':len(arrays),'loopInstructions':ops.count(48),
                             'notDriverMachineCodeAttestation':True})
    for name in ['BuildSubsets113','Enumerate113','Reduce113','Write113']:
        rows=[r for r in observed if r['kernelCandidatesByResourceSignature']==[name]]
        assert rows,name
        assert all(r['privateArrayDeclarations']==0 for r in rows),(name,rows)
    output={'schema':'existing113/cache-prefix/v1','newCompilerOrGPUCalls':0,'source':'Existing113 cache, not new24 compilation; kernel matching uses resource signature', 'rows':observed}
    (H/'CACHE_PREFIX24.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps([{'kernels':r['kernelCandidatesByResourceSignature'],'privateArrays':r['privateArrayDeclarations'],'instructions':r['instructionCount']}for r in observed]))

if __name__=='__main__':main()
