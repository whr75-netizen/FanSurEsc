"""107 frozen current-source support/mass export. No Unity or colour changes."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
H=Path(__file__).resolve().parent;R=H.parent
sys.path.insert(0,str(R/'forward-eye102'));from analyse102 import load,buffer,components
from analyse_capture68 import plane
sys.path.insert(0,str(R/'live-curve106'));from analyse106 import curve_segments

def joint_arrays(layers,vis):
    a=vis[1:4,...,0].copy();b=vis[1:4,...,1].copy();z=layers[1:4,1,...,0];lo=a.copy();hi=b.copy()
    for p in range(3):
        for q in range(3):
            if p==q:continue
            valid=(z[q]>0)&(b[q]>0);front=valid&(z[q]<z[p]-np.float32(3e-5));tie=valid&(abs(z[q]-z[p])<=np.float32(3e-5))
            lo[p]*=np.where(front|tie,1-b[q],1);hi[p]*=np.where(front,1-a[q],1)
    clo=np.ones(a.shape[1:],np.float32);chi=clo.copy()
    for p in range(3):clo*=1-b[p];chi*=1-a[p]
    allhi=np.concatenate([hi,chi[None]]);dominant=np.array([lo[p]>np.max(allhi[np.arange(4)!=p],axis=0)for p in range(3)])
    return lo,hi,clo,chi,dominant

def load_fields(p):
    m=load(p/'RAW_MANIFEST.json');scale=m.get('jointInputSampleScale107',4)
    if scale==8:
        w,h=m['forward102']['denseSize'];ls=np.zeros((4,5,h,w,4),np.float32);v=np.zeros((4,h,w,4),np.float32)
        for part in [1,2]:ls[part,1]=np.flipud(plane(p/('D-part'+str(part)+'-meta.plane'))[1])
        for ch,n in enumerate(['rgba','meta','rest','uv']):ls[3,ch]=np.flipud(plane(p/('D-lid-'+n+'.plane'))[1])
        v[1:4]=buffer(p/'dense-three-part-visibility.f32').reshape(3,h,w,4)
    else:
        w,h=m['forward102']['canonicalSize'];ls=buffer(p/'canonical-layers.f32').reshape(4,5,h,w,4);v=buffer(p/'canonical-visibility.f32').reshape(4,h,w,4)
    return m,scale,ls,v

def export_packet(p,tag,stage,index,frame):
    m,scale,ls,v=load_fields(p);h,w=ls.shape[2:4]
    lo,hi,clo,chi,dom=joint_arrays(ls,v);cw,ch=w//scale,h//scale;owners=np.rint(ls[1:4,1,...,2]).astype(int)
    def reduce(a):return a.reshape(ch,scale,cw,scale).sum(axis=(1,3),dtype=np.float64)/(scale*scale)
    keys=[(0,0)]+[(o,p)for o in [1,2]for p in [1,4,6]];low=[reduce(clo)];high=[reduce(chi)];support=[np.ones((ch,cw),bool)];pointCounts=[np.zeros((ch,cw),int)]
    for owner,part in keys[1:]:
        i={1:0,4:1,6:2}[part];valid=owners[i]==owner;low.append(reduce(lo[i]*valid));high.append(reduce(hi[i]*valid));ds=dom[i]&valid
        count=ds.reshape(ch,scale,cw,scale).sum(axis=(1,3));pointCounts.append(count);support.append(count>0)
    low=np.array(low);high=np.array(high);support=np.array(support);counts=np.array(pointCounts)
    if (p/'curve-segments106.f32').exists():segments=curve_segments(p/'curve-segments106.f32')
    else:
        source=next(x for x in load(R/'closed-support105/direct/SOURCE_CURVE105.json')if x['sourceId']==m['sourceId']and x['frame']==frame)
        assert source['Close']==100 and all(x['numericMapValidated']for x in source['eyes'])
        segments=np.array([[[*a,0,e['eye']],[*b,0,e['eye']]]for e in source['eyes']for a,b in zip(e['canonicalCurve'],e['canonicalCurve'][1:])],np.float32)
    out=H/'fixtures';out.mkdir(exist_ok=True)
    name=f'{tag}-frame{frame}';np.savez_compressed(out/(name+'.npz'),lower=low,upper=high,support=support,dominantSampleCounts=counts,sourceSegments=segments,keys=keys,
        baselineIdentity=buffer(p/'canonical-identity.f32').reshape(ch,cw,4))
    row={'name':name,'sourceId':m['sourceId'],'stage':stage,'index':index,'frame':frame,'sourcePacket':str(p),'scale':scale,'size':[cw,ch],
      'ownerSupport':{str(o):{str(part):{'candidateCells':int(support[k].sum()),'massInterval':[float(low[k].sum()),float(high[k].sum())],'candidateComponents4':components(support[k]),'fineComponents4':components(dom[{1:0,4:1,6:2}[part]]&(owners[{1:0,4:1,6:2}[part]]==o))}for k,(owner,part)in enumerate(keys)if owner==o}for o in [1,2]},
      'cellUncertainMass':int(np.any(low!=high,axis=0).sum()),'fileSHA256':hashlib.sha256((out/(name+'.npz')).read_bytes()).hexdigest()}
    return row

def main():
    rows=[];s=load(sorted((R/'joint-lid107/capture-final').glob('STATE107-*'))[-1]);assert s['PlayExited']and not s.get('error')
    for e in s['sequencePackets']:rows.append(export_packet(Path(e['output']),'actual107',e['testStage82'],e['stageIndex82'],e['frame']))
    d=R/'closed-support105/direct';s=load(sorted(d.glob('STATE102-*'))[-1]);e=next(e for e in s['sequencePackets']if load(Path(e['output'])/'RAW_MANIFEST.json')['motion82']['requestedClose']==100)
    rows.append(export_packet(Path(e['output']),'closed105',e['testStage82'],e['stageIndex82'],e['frame']))
    (H/'INPUT108.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8');print(json.dumps({'fixtures':len(rows),'focus':[{k:v for k,v in r.items()if k not in ['sourcePacket','fileSHA256']}for r in rows if r['frame']in [103,107,192]or r['name'].startswith('closed105')]}))
if __name__=='__main__':main()
