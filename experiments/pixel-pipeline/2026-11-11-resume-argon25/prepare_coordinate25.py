"""Prepare one isolated common-footprint candidate, never import/dispatch it."""
from pathlib import Path
import hashlib,json
import numpy as np

H=Path(__file__).resolve().parent
BASE=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game\Assets\EUnityValidation01\Direct24Carrier\ForwardEye113_Geometry24.compute')
def xy(roi,p,si):return np.array([roi[0]+p[0]+(si%4+.5)/4,272-(roi[1]+p[1]+(si//4+.5)/4)],np.float32)
def shift(roi,p,anchor):
    centre=xy(roi,p,0)+np.array([.375,-.375],np.float32)
    cell=np.floor(centre-anchor).astype(int)
    delta=centre-(anchor+cell.astype(np.float32)+np.float32(.5))
    return np.rint(np.array([-delta[0],delta[1]],np.float32)*np.float32(4)).astype(int)
def main():
    raw=BASE.read_bytes();base=raw.decode('utf-8-sig').replace('\r\n','\n')
    old='float2 Destination24(int2 p,int si){uint x=(uint)si%4u,y=(uint)si/4u;return float2(_ForwardROI102.x+p.x+(x+.5)/4,272-(_ForwardROI102.y+p.y+(y+.5)/4));}'
    assert base.count(old)==1
    helper=(H/'HeadFootprint25.hlsl').read_text(encoding='utf-8')
    candidate=base.replace(old,helper)
    old='for(int y=0;y<4;y++)for(int x=0;x<4;x++){int i=y*4+x;float4 h=_HairMeta102.Load(int3(p*4+int2(x,y),0)),v=_HairRGBA102.Load(int3(p*4+int2(x,y),0));if(h.x<=0||h.w<=0||v.a<=0)continue;'
    assert candidate.count(old)==1
    new='''for(int y=0;y<4;y++)for(int x=0;x<4;x++){int i=y*4+x;
  int2 hairPos=p*4+int2(x,y)+(chosenPart>0?HeadShift25(p):int2(0,0));
  // Missing capture is unknown coverage, never a clamped edge or transparency.
  if(any(hairPos<0)||any(hairPos>=_ForwardROI102.zw*4)){if(chosenPart>0)hairHi+=1;continue;}
  float4 h=_HairMeta102.Load(int3(hairPos,0)),v=_HairRGBA102.Load(int3(hairPos,0));if(h.x<=0||h.w<=0||v.a<=0)continue;'''
    candidate=candidate.replace(old,new)
    assert 'EvaluateForm115' not in candidate and 'BoundRun115'not in candidate
    assert candidate.count('#pragma kernel')==base.count('#pragma kernel')
    assert candidate.count('Destination24(p,si)')==base.count('Destination24(p,si)')
    assert 'all(q.xy==Destination24(p,i))'in candidate and 'if(any(hairPos<0)'in candidate
    candidate='\n'.join(line.rstrip()for line in candidate.splitlines()).rstrip()+'\n'
    out=H/'ForwardEye113_Footprint25.compute';out.write_text(candidate,encoding='utf-8',newline='\n')
    # Algebraic equality on exact quarter-pixel addresses: depth/face producer,
    # source carrier lookup, final comparison and hair fetch share one location.
    checks=0
    for anchor in [np.array([10+x,20+y],np.float32)for x in [0,.125,.25,.5,.875]for y in [0,.125,.5,.875]]:
        roi=np.array([7,200,12,12]);p=np.array([4,5]);delta=shift(roi,p,anchor)
        for si in range(16):
            query=xy(roi,p,si)+np.array([delta[0],-delta[1]],np.float32)*np.float32(.25)
            hair=p*4+np.array([si%4,si//4])+delta
            fromHair=np.array([roi[0]+(hair[0]+.5)/4,272-(roi[1]+(hair[1]+.5)/4)],np.float32)
            assert np.array_equal(query,fromHair);checks+=1
    report={'base':str(BASE),'baseSHA256':hashlib.sha256(raw).hexdigest(),'candidateSHA256':hashlib.sha256(out.read_bytes()).hexdigest(),
        'cpuCoordinatePairsExact':checks,'newKernels':0,'newBuffers':0,'newDispatches':0,'UnityGPUCalls':0,
        'kernelCount':candidate.count('#pragma kernel'),'skinMaskChanged':False,'bankOrPaletteChanged':False,
        'missingCapturedHairCoverage':'unknown, not clamped or transparent','runtimeApplied':False,
        'limits':['No corrected visibility/depth or final RGB has been rendered/validated.',
            'This uses a common nearest4x footprint for depth AND hair; exact continuous anchor minus snapDelta is approximated by at most 1/8 pixel, rather than mixing continuous depth with rounded hair.',
            'Close75 shared-skin rule1B source-unoccluded gating must be connected before expanding any live skin mask.',
            'No fixed cell-size/shape, bilateral symmetry or section3 art thresholds adopted.']}
    (H/'COORDINATE25.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
    print(json.dumps({'coordinatePairsExact':checks,'kernelCountUnchanged':True,'UnityGPUCalls':0,'runtimeApplied':False}))
if __name__=='__main__':main()
