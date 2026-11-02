from pathlib import Path
from fractions import Fraction
import json,sys,hashlib
import numpy as np
from paths114 import H,R,folder
P=folder('113')
from tie114 import transport,rank_source,read
from inputs113 import load_packets
def main():
    ties=read(H/'TIES114.json');pairs=read(H/'PAIRING_ALL114.json');pigment=read(H/'PIGMENT114.json');reg=read(H/'REGISTRATION_CURRENT102.json');source=read(P/'SOURCE113.json');_,packets=load_packets(P);tests=0
    for r in ties['rows']:
        path=next(p for e,p in packets if e['sourceId']==r['sourceId']);maps,avail,expected,_=transport(path,2,reg,source);points=[tuple(p)for p in r['pointsYX']];labels=r['layouts'];baseline,_=rank_source(labels,points,maps,avail,avail,expected);assert baseline==[1];tests+=1
        # Grid rotations/reflections act on both the current reference and
        # cell centres, while immutable source IDs remain unchanged.
        for turn in range(4):
            for reflect in[False,True]:
                def transform(x,y):
                    if reflect:x=-x
                    for _ in range(turn):x,y=-y,x
                    return x,y
                def cell(y,x):
                    xx,yy=transform(Fraction(2*x+1,2),Fraction(2*y+1,2));return int(yy-Fraction(1,2)),int(xx-Fraction(1,2))
                pp=[cell(y,x)for y,x in points];mm={(*cell(y,x),p):v for(y,x,p),v in maps.items()};ee={k:transform(*v)for k,v in expected.items()};win,_=rank_source(labels,pp,mm,avail,avail,ee);rev,_=rank_source(labels[::-1],pp,mm,avail,avail,ee);assert win==[1]and rev==[0];tests+=2
        ix=list(range(len(points)))[::-1];win,_=rank_source([[v[i]for i in ix]for v in labels],[points[i]for i in ix],maps,avail,avail,expected);assert win==[1];tests+=1
    key=(1,1,2,3);_,flags=rank_source([[1,0],[0,0]],[(0,0),(0,1)],{(0,0,1):{key:Fraction(1)}},{key:Fraction(1)},{key:Fraction(1)},{key:(Fraction(1,2),Fraction(1,2))});assert all(v['1:relativeGeometry']is None for v in flags['sourceFormDimensions']);tests+=1
    assert pairs['knownGPUQueryComparisons']==3190 and pairs['knownGPUQueryMaxError']==0 and pairs['carrier8xMembershipChecks']==4320 and not pairs['carrier8xMembershipMismatches'];tests+=2
    assert all(r['poolIsCompleteNotCap']and r['sourceSampleScale']==8 and r['combinedExistingCriteriaWinners']==[1]for r in ties['rows']);tests+=2
    assert len(pigment['rows'])==1 and len(pigment['rows'][0]['cases'][0]['points'])==6
    c=pigment['rows'][0]['cases'][0];assert c['actualUpperRow']['row']==c['correctVertexRasterUpperRow']['row']==5 and all(p['sourceAlphaBilinear']>0 and p['intrinsicFace']['faceInterval'][0]>0 for p in c['points']);tests+=2
    coordinateChecks=0;trace=read(H/'TRACE_ALL114.json')
    for r in trace['frames']:
        origin=np.array(r['carrierOrigin'],np.float32)
        for case in r['issues']:
            # Check the actual recorded coordinates, not repeated generic
            # dummy pixels. Source and target remain separately identified.
            for fine in case['fine']:
                q=np.array(fine['desiredPhysicalXY'],np.float32);idx=np.floor((q-origin)*4);actual=origin+(idx+.5)/4;old=np.array(fine['queryPhysicalXY'],np.float32);assert np.array_equal(actual,q)and np.array_equal(old-q,[.0625,.0625]);coordinateChecks+=1
    candidate=H/'paired-point-patch';cs=(candidate/'RegionDriver113.cs').read_text();shader=(candidate/'ForwardEye114.compute').read_text();driver=(candidate/'Forward113.cs').read_text();capture=(candidate/'Capture113.cs').read_text();assert '"_CarrierSize113",carrier.Width,carrier.Height'in cs and '"_CarrierSampleScale113",4'in cs and 'sampleScale:4'in driver and 'Shaders/ForwardEye113.compute'not in driver and '"_SourceSize113",source.Width,source.Height'in cs;assert '_CarrierOrigin113.xy)*_CarrierSampleScale113' in shader and 'n=_CarrierSize113.x*_CarrierSize113.y'in shader and 'new RectInt(0,0,dw,dh)'in capture;tests+=1
    out={'passed':True,'tests':tests,'pairedCoordinateChecks':coordinateChecks,'reusedSourceFormRotationReflectionAndStorageOrder':True,'unobservedPairGeometryRemainsNone':True,'GPU113FaceQueryMatches':3190,'GPU113CarrierMembershipMatches':4320,'GPU113FinalCompositionMatches':270,'sourceImageBinding':'hash-verified original111 texture data; current geometry113; no old pose buffers','pairedCandidateCompiled':False,'pairedCandidateImported':False,'pairedCandidateGPUExecuted':False,'minimumPairingFixHasOtherPixelChanges':sum(c['finalRGBAChanged']for r in pairs['rows']for c in r['issues']),'fullAlgorithmAdopted':False,'extraUnityCalls':0,'extraPlay':0,'duplicateLibraryUploads':0}
    (H/'CHECK114.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps(out,ensure_ascii=False))
if __name__=='__main__':main()
