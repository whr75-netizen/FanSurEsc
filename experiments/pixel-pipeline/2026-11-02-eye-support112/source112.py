"""Read original source topology/morph semantics. No Unity or asset writes."""
from pathlib import Path
import hashlib, itertools, json, struct, sys
import numpy as np

HERE=Path(__file__).resolve().parent
P111=HERE.parent/'aperture-runtime111'
if not P111.exists():P111=HERE.parent/'2026-11-02-eye-carrier111'
sys.path.insert(0,str(P111))
from geometry111 import packet_list,load,read

MODEL=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game\Assets\EUnityValidation01\VRoidSampleA144\Inputs\AvatarSample_A.vrm')
MODEL_HASH='0e2fd0fc90308da3172ecf4e674fdeb4f054ebd617005caa5b997a2ca339cce3'

class Source:
    def __init__(self):
        fixture=HERE/'SOURCE112.json'
        if fixture.exists():
            meta=json.loads(fixture.read_text(encoding='utf8'))
            assert meta['modelSHA256']==MODEL_HASH
            raw=HERE/meta['arrays'];assert hashlib.sha256(raw.read_bytes()).hexdigest()==meta['arraysSHA256']
            self.g=meta['sourceSubset'];self.frozen=np.load(raw);self.cache={}
            return
        data=MODEL.read_bytes()
        assert hashlib.sha256(data).hexdigest()==MODEL_HASH
        magic,version,length=struct.unpack_from('<III',data)
        assert magic==0x46546c67 and version==2 and length==len(data)
        self.chunks={};p=12
        while p<len(data):
            n,t=struct.unpack_from('<II',data,p);p+=8
            assert p+n<=len(data);self.chunks[t]=data[p:p+n];p+=n
        self.g=json.loads(self.chunks[0x4e4f534a]);self.blob=self.chunks[0x004e4942]
        self.cache={}

    def accessor(self,i):
        if i in self.cache:return self.cache[i].copy()
        if hasattr(self,'frozen'):return self.frozen['a'+str(i)].copy()
        a=self.g['accessors'][i];components={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
        dtype=np.dtype({5120:'i1',5121:'u1',5122:'<i2',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']]);count=a['count']
        out=np.zeros((count,components),dtype)
        if 'bufferView'in a:
            v=self.g['bufferViews'][a['bufferView']];assert v.get('buffer',0)==0
            offset=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',components*dtype.itemsize)
            assert stride>=components*dtype.itemsize
            out=np.ndarray((count,components),dtype,buffer=self.blob,offset=offset,strides=(stride,dtype.itemsize)).copy()
        if 'sparse'in a:
            s=a['sparse'];q=s['indices'];v=self.g['bufferViews'][q['bufferView']];dt=np.dtype({5121:'u1',5123:'<u2',5125:'<u4'}[q['componentType']]);ids=np.frombuffer(self.blob,dt,s['count'],v.get('byteOffset',0)+q.get('byteOffset',0));q=s['values'];v=self.g['bufferViews'][q['bufferView']];values=np.frombuffer(self.blob,dtype,s['count']*components,v.get('byteOffset',0)+q.get('byteOffset',0)).reshape(-1,components);assert np.all(ids<count);out[ids]=values
        assert not a.get('normalized',False),'no silent normalized attribute conversion'
        self.cache[i]=out;return out.copy()

    def freeze(self):
        if hasattr(self,'frozen'):return
        binding,node,mesh=self.binding();presets=self.g['extensions']['VRMC_vrm']['expressions']['preset']
        semantic={k:v for k,v in presets.items()if k in ['blink','blinkLeft','blinkRight']}
        ids=set()
        for p in mesh['primitives']:
            ids.update([p['attributes']['POSITION'],p['attributes']['TEXCOORD_0'],p['indices']])
            for value in semantic.values():
                for b in value['morphTargetBinds']:ids.add(p['targets'][b['index']]['POSITION'])
        out=HERE/'SOURCE112.npz';assert not out.exists()
        np.savez_compressed(out,**{'a'+str(i):self.accessor(i)for i in sorted(ids)})
        nodes=[{}for _ in self.g['nodes']];nodes[binding['node']]=node
        data={'modelSHA256':MODEL_HASH,'arrays':out.name,'arraysSHA256':hashlib.sha256(out.read_bytes()).hexdigest(),'sourceSubset':{'extensions':{'VRMC_vrm':{'expressions':{'preset':semantic}}},'nodes':nodes,'meshes':[mesh],'accessorProvenance':{str(i):self.g['accessors'][i]for i in sorted(ids)}},'sourceOriginalUnchanged':True,'noTexturesOrSourceGeometryModified':True}
        (HERE/'SOURCE112.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf8')

    def binding(self):
        vrm=self.g['extensions']['VRMC_vrm'];blink=vrm['expressions']['preset']['blink']['morphTargetBinds']
        assert len(blink)==1 and blink[0]['weight']==1
        binding=blink[0];node=self.g['nodes'][binding['node']];mesh=self.g['meshes'][node['mesh']]
        return binding,node,mesh

    def map_to_capture(self,c):
        binding,node,mesh=self.binding();solutions=[]
        for permutation in itertools.permutations(range(3)):
            offsets=[];maxuv=0
            for sm,primitive in enumerate(mesh['primitives']):
                rows=np.where((c['sources'][:,0]==1)&(c['sources'][:,1]==sm))[0]
                original=self.accessor(primitive['indices']).reshape(-1,3)[:,permutation]
                assert len(rows)==len(original)
                # Actual primitive index is a per-submesh 1-based identity.
                assert np.array_equal(c['sources'][rows,2],np.arange(1,len(rows)+1))
                delta=c['triangles'][rows,:3].astype(np.int64)-original.astype(np.int64)
                offsets.extend(np.unique(delta).tolist())
            if len(set(offsets))==1:solutions.append((permutation,offsets[0]))
        assert len(solutions)==1,solutions
        permutation,offset=solutions[0];uv=self.accessor(mesh['primitives'][0]['attributes']['TEXCOORD_0']).astype(float)
        actual=c['uv'][offset:offset+len(uv)];errors={'same':float(abs(actual-uv).max()),'flipV':float(abs(actual-np.c_[uv[:,0],1-uv[:,1]]).max())};assert min(errors.values())<2e-7
        positions=self.accessor(mesh['primitives'][0]['attributes']['POSITION'])
        delta=self.accessor(mesh['primitives'][0]['targets'][binding['index']]['POSITION'])
        assert len(positions)==len(delta)==len(uv)
        reg=read(c['path'].parent/'REGISTRATION_CURRENT102.json')
        rings={}
        for owner in sorted({v['owner']for v in reg['measurements']}):
            points=sorted([v for v in reg['measurements']if v['owner']==owner],key=lambda v:v['ringIndex']);assert [v['ringIndex']for v in points]==list(range(len(points)))
            rings[owner]=np.array([v['vertex']for v in points],int)
        return {'binding':binding,'node':node['name'],'mesh':node['mesh'],'faceVertexOffset':int(offset),'permutation':list(permutation),'uvErrors':errors,'positions':positions,'delta':delta,'uv':uv,'rings':rings,'meshData':mesh}

def main():
    source=Source();_,paths=packet_list();c=load(paths[0]);m=source.map_to_capture(c)
    moving=np.any(m['delta']!=0,axis=1)
    out={k:v for k,v in m.items()if k not in ['positions','delta','uv','rings','meshData']}
    out.update({'sourceModelHash':MODEL_HASH,'sourceId':c['sourceId'],'vertexCount':len(moving),'movingCount':int(moving.sum()),'movingRings':{str(k):{'length':len(r),'moving':int(moving[r].sum()),'deltaNormMinMax':list(map(float,[np.linalg.norm(m['delta'][r],axis=1).min(),np.linalg.norm(m['delta'][r],axis=1).max()]))}for k,r in m['rings'].items()}})
    print(json.dumps(out,indent=2))

if __name__=='__main__':main()
