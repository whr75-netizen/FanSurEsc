"""Force archived same-source inputs; no Unity, registry59 or host texture path."""
import os,json
os.environ['PIXEL111_FROZEN_INPUTS']='1'
from geometry111 import H,packet_list,load
from ray111 import NativeAlpha,FaceRay
from analyse111 import validate,source_fields,source_components,bank_data
from io109 import joint_arrays
def main():
    rows=[]
    for kind in['original','geometry']:
        _,paths=packet_list(kind)
        for p in [paths[3],paths[10]]:
            c=load(p);a=NativeAlpha(c);proof=validate(c,a,FaceRay(c,a));assert proof['maxCPUvsGPUVisibilityIntervalDifference']==0;m,ls,v=source_fields(p);lo,*_=joint_arrays(ls,v);bank,groups=bank_data()
            for owner in[1,2]:
                _,_,ids,errors=source_components(c,ls,lo,owner,bank,groups);assert not errors and all(v['sourceKeyUnique']for v in ids)
            rows.append({'kind':kind,'sourceId':c['sourceId'],'frame':c['frame'],'GPUWitnesses':proof['sampledGPUCarrierQueryChecks'],'maxIntervalDifference':0})
    (H/'FROZEN_REPLAY111.json').write_text(json.dumps({'archivedPacketsRecomputed':rows,'actualNewUnityCalls':0,'hostTexturePathsUsed':False},indent=2)+'\n');print(json.dumps(rows))
if __name__=='__main__':main()
