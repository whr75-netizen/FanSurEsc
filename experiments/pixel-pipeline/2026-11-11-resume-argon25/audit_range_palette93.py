"""Reuse58 targets/92 solver for93 source-range candidate; CPU only.

The per-channel representative envelope cannot justify artistic adoption.
Check that it also survives the existing finite palette contract before any
new runtime connection. No new solver, Unity call or GPU-generated claim.
"""
from pathlib import Path
import json,numpy as np
import audit_palette_constraints92 as audit
H=Path(__file__).resolve().parent;G=H/'face93/range-palette'

def main():
 G.mkdir(exist_ok=True);c=np.load(H/'face93/SOURCE_RANGE_CANDIDATE93.npz');old=np.load(H/'face92/SOURCE_VALUE92.npz');base=np.load(H/'face88/SOURCE_VALUE88.npz');address=c['colourAddress'];edges=np.array(sorted({(int(address[a]),int(address[b]))for a,b in base['orders']}),'<i4');assert(edges[:,0]!=edges[:,1]).all()
 np.savez_compressed(G/'SOURCE_VALUE92.npz',colours=c['colours'],referenceIndices=c['referenceIndices'],colourAddress=address,pairs=old['pairs']);edges.tofile(G/'ORDERS92.i32');audit.H=H;audit.G=G;audit.main();r=json.loads((G/'PALETTE_CONSTRAINTS92.json').read_text());r['candidateSourceAddresses']=len(c['referenceIndices']);r['sourceDistortionMaximumChannelError']=35;r['representativeRangeAloneIsSufficientQualityCriterion']=False;(G/'RANGE_PALETTE93.json').write_text(json.dumps(r,indent=2));print(json.dumps({'candidateAddresses':len(c['referenceIndices']),'same58TargetsAnd92Solver':True,'allLevelsFeasible':r['allLevelsFeasible'],'newGPUExecuted':False,'artAdopted':False}))
if __name__=='__main__':main()
