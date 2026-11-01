"""Workspace-only provenance checks; frozen check108 is the portable verifier."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
from export108 import H,R,load_fields,joint_arrays
sys.path.insert(0,str(R/'joint-lid107'));from joint_reference107 import contributions

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    rows=json.loads((H/'INPUT108.json').read_text());known={x['file']:x['sha256']for x in json.loads((R/'joint-lid107/RAW107_INDEX.json').read_text())};raw=[];checks=0;rng=np.random.default_rng(108)
    for row in rows:
        p=Path(row['sourcePacket']);d=np.load(H/'fixtures'/(row['name']+'.npz'));m,scale,ls,v=load_fields(p);assert m['sourceId']==row['sourceId'];lo,hi,clo,chi,dom=joint_arrays(ls,v)
        h,w=lo.shape[1:];ch,cw=h//scale,w//scale
        reduce=lambda x:x.reshape(ch,scale,cw,scale).sum((1,3),dtype=np.float64)/(scale*scale)
        assert np.array_equal(d['lower'][0],reduce(clo))and np.array_equal(d['upper'][0],reduce(chi))
        for k,(owner,part)in enumerate(d['keys'][1:],1):
            j={1:0,4:1,6:2}[int(part)];mask=np.rint(ls[j+1,1,...,2])==owner
            assert np.array_equal(d['lower'][k],reduce(lo[j]*mask))and np.array_equal(d['upper'][k],reduce(hi[j]*mask))
            assert np.array_equal(d['dominantSampleCounts'][k],(dom[j]&mask).reshape(ch,scale,cw,scale).sum((1,3)))
        for _ in range(16):
            y=int(rng.integers(h));x=int(rng.integers(w));a,b=contributions(ls,v,y,x)
            assert np.array_equal(a,np.r_[lo[:,y,x],clo[y,x]])and np.array_equal(b,np.r_[hi[:,y,x],chi[y,x]]);checks+=1
        names=['RAW_MANIFEST.json','canonical-identity.f32']+(['dense-three-part-visibility.f32','D-part1-meta.plane','D-part2-meta.plane','D-lid-rgba.plane','D-lid-meta.plane','D-lid-rest.plane','D-lid-uv.plane','curve-segments106.f32']if scale==8 else['canonical-layers.f32','canonical-visibility.f32'])
        for n in names:
            f=p/n;q={'fixture':row['name'],'file':n,'sourceId':row['sourceId'],'bytes':f.stat().st_size,'sha256':sha(f)}
            if row['name'].startswith('actual107'):
                expected=known[f"final54/frame{row['frame']}/{n}"];assert q['sha256']==expected;q['matches107CommittedRawIndex']=True
            raw.append(q)
    sourceCurve=R/'closed-support105/direct/SOURCE_CURVE105.json'
    out={'fixtures':len(rows),'rawFileHashes':raw,'independentFloat32JointContributionChecks':checks,'closed105CurveSHA256':sha(sourceCurve),'noMixedSourceIds':True,'noUnityCalls':True}
    (H/'PROVENANCE108.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in out.items()if k!='rawFileHashes'}|{'rawFiles':len(raw)}))
if __name__=='__main__':main()
