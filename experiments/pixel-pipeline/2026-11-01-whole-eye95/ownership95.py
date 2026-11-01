"""Attach existing source eye identity; no semantic detection or material names."""
from pathlib import Path
import json,sys
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
sys.path.insert(0,str(ROOT/'native-feature89'));from analyse89 import packet,geometry,REST

def main():
    state=json.loads(sorted((HERE/'capture-scale-correct').glob('STATE95B*'))[-1].read_text());by={e['frame']:e for e in state['sequencePackets']};data=json.loads((HERE/'QUERIES_SKIN_FOCUS95.json').read_text());count=0
    for frame in data['frames']:
        d=packet(Path(by[frame['frame']]['output']));layers,_,_=geometry(d);centres=np.asarray(d['m']['eyeFeature']['centres']);distance=((REST[:,None]-centres[None,:,:3])**2).sum(2);owners=centres[np.argmin(distance,axis=1),3]
        for q in frame['queries']:
            p=q['partIndex'];x,y=q['sample'];q['eyeOwner']=int(round(float(layers[p][1][y,x,2])))
            assert q['eyeOwner']in centres[:,3]
            for hit in q['hits']:
                if hit['rendererSlot']!=1:continue
                own=float(np.asarray(hit['barycentric'])@owners[hit['vertices']]);hit['eyeOwner']=int(np.floor(own+.5))
                if hit['sourceSubMesh']in [1,2,4,6]and hit['eyeOwner']==q['eyeOwner']:count+=1
    data['ownershipContract']={'sourceDefinition':'EyeFeature348.Initialise UV7: nearest native model-eye centre, barycentric interpolation and round','newEyeParts':[1,4,6],'replacedOriginalEyeParts':[1,2,4,6],'highlight2':'Iris template already supplies its authored colour; original highlight material is replaced with the same owning eye','alwaysExternal':['face skin3 including actual lid','brow5','other eye','hair and body'],'sameFeatureOriginalHits':count}
    (HERE/'QUERIES_OWNED95.json').write_text(json.dumps(data,indent=2)+'\n');print(json.dumps(data['ownershipContract'],indent=2))

if __name__=='__main__':main()
