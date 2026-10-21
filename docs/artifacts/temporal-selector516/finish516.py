from pathlib import Path
import json,math,collections,hashlib,zipfile
import numpy as np
import active516 as G,select516 as C
D=G.OUTPUT;R=G.INPUT;W=G.ROOT
review=json.loads((D/'REVIEW516.json').read_text());failure=json.loads((D/'FAILURE516.json').read_text());support=json.loads((D/'SUPPORT516.json').read_text())

# Check a stationary state against every admissible one-cell move. This is one
# frozen-input objective audit, not a new solve, loop or capture.
sel=C.Selector(80,None,1.);chosen=np.load(D/'eta-1.0/080.npy');desc={}
for e in G.boundary(chosen):
    d=sel.describe(C.key(e));assert d is not None;desc[C.key(e)]=d
gg=C.groups(desc);sel.mask=chosen.copy();sel.desc=desc;sel.groupEdges={}
for k,d in desc.items():sel.groupEdges.setdefault(C.channel(d),{})[k]=d
sel.groupSpans=gg;sel.previous={'spans':gg,'active':sel.active,'rings':sel.rings,'signature':sel.signature};sel.costs={ch:sel.cost(ch,ss)for ch,ss in gg.items()};moves=[]
bx,by,w,h=sel.bounds
for y in range(by+1,by+h-1):
    for x in range(bx+1,bx+w-1):
        p=sel.proposal(x,y)
        if p is not None:moves.append({k:p[k]for k in ['xy','deltaSpatial','deltaTemporal','deltaObjective']})
moves.sort(key=lambda p:p['deltaObjective'])
freeze={'allAdmissibleOneCellMoves':len(moves),'minimumObjectiveDelta':moves[0]['deltaObjective'],'bestMoves':moves[:5],'oneCellLocalFixedPoint':moves[0]['deltaObjective']>=-1e-9,'noRepeatedFrameWasSolved':True}

def profile(m):
    cols=np.any(m,axis=0);xx=np.flatnonzero(cols);top=np.zeros(m.shape[1]);bottom=np.zeros_like(top)
    for x in xx:ys=np.flatnonzero(m[:,x]);top[x]=ys.min();bottom[x]=ys.max()+1
    ys,xs=np.where(m)
    return cols,top,bottom,[int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)]
base=[G.read_mask(i)for i in range(81)];profiles=[]
for eta in [.5,1.,2.]:
    rows=[]
    for i in range(81):
        a,at,ab,abox=profile(base[i]);b,bt,bb,bbox=profile(np.load(D/('eta-'+str(eta))/f'{i:03d}.npy'));common=a&b;dd=(bb-ab)[common]
        rows.append({'target':i,'bottomEnvelopeMaxDownCells':float(dd.max(initial=0)),'bottomEnvelopeMaxUpCells':float(dd.min(initial=0)),'topEnvelopeMaxAbsoluteCells':float(abs((bt-at)[common]).max(initial=0)),'bboxDelta':[v-u for u,v in zip(abox,bbox)],'changedBottomColumns':int((dd!=0).sum()),'columnsBornOrRemoved':int((a!=b).sum())})
    profiles.append({'eta':eta,'maxBottomDown':max(r['bottomEnvelopeMaxDownCells']for r in rows),'maxBottomUp':min(r['bottomEnvelopeMaxUpCells']for r in rows),'maxTopChange':max(r['topEnvelopeMaxAbsoluteCells']for r in rows),'maxChangedBottomColumns':max(r['changedBottomColumns']for r in rows),'rows':rows,'limit':'Column envelope measures geometric tip/lower boundary movement; it does not identify artist-intended individual strands or make every merged micro-gap a defect.'})

# Preserve all state masks without large uncompressed full-grid duplication.
etas=[.5,1.,2.];sequences=np.array([[np.load(D/('eta-'+str(eta))/f'{i:03d}.npy')for i in range(81)]for eta in etas])
np.savez_compressed(D/'ALL_REGION_SEQUENCES516.npz',etas=np.array(etas),masks=sequences,timestamps=np.array([json.loads((R/f'{i:03d}_ALT_projection.json').read_text())['gameTime']for i in range(81)]))
archive=D/'ALL_SELECTOR_TRACES516.zip'
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6)as z:
    for eta in etas:
        for p in sorted((D/('eta-'+str(eta))).glob('*.json')):z.write(p,arcname=p.relative_to(D).as_posix())
out={'decision':'REJECTED_OFFLINE_PROTOTYPE; NO_UNITY_INTEGRATION','sensitivity':review['sensitivity'],'sourceCorrespondenceFailure':{'sameRegionControlSlideTemporalCost':failure['unchangedRegionTangentialReparameterization']['rawTemporalCost'],'expected':0,'storedUnchangedEdgeRelabels':len(failure['storedUnchangedEdgeChannelRelabels']),'adjacentActiveRelabels':sum(r['adjacentSourceSegments']and r['bothCurrentSegmentsActive']for r in failure['storedUnchangedEdgeChannelRelabels']),'qualification':'Relabel counts are not certified individual animation defects. The exact unchanged-region synthetic counterexample establishes the implementation invariant failure.'},'historyCostFailure':{'frozenEndpoint':{k:v for k,v in failure['frozenEndpointCounterexample'].items()if k not in ['operatorTraceRecover','individualCorrections']},'stationaryAllMoves':freeze,'qualification':'A positive one-frame recovery barrier can retain a higher-spatial-cost drawing at stationary geometry. It is not a visual claim that the static raster is automatically the right artwork.'},'novelPacketSupport':{k:v for k,v in support.items()if k not in['rows','limits']},'headEnvelopeProfiles':profiles,'physicalOcclusionLabelCorrection':'119 NO_CURRENT_VISIBLE_SPAN audit entries mean selected span absent from its source-segment channel; they do not certify119 physical occlusions or actual visibility resets. The span cost itself uses common active intervals, not this diagnostic label.','allFramesPreserved':{'compressedMasks':str(D/'ALL_REGION_SEQUENCES516.npz'),'shape':list(sequences.shape),'originalSourceFrames':81,'loopSamples':80,'normalDurationMs':1333,'diagnostic':review['allFramesDiagnostic'],'actualNewCandidateFullBodyRendered':False},'runtimeShaderChanged':False,'actualNewUnityCalls':0,'experimentDefaultOFF':True,'separateUnresolved':['hair colour11','paired body colour1','native world inputs','packet/quad upload212ms'],'nextMinimalContracts':['First repair geometric active-arc correspondence: allow tangential reparameterization and continue across arbitrary control-point segment boundaries; do not reset on absence of a selected pixel span. Require unchanged-region slide cost0 plus rigid motion/visibility/merge-split counterexamples. Keep spatial cost and coefficient fixed while testing this correction.','Then replace one-step switching-barrier semantics inside the same selector with a time-defined cumulative shape-evidence comparison between geometrically valid designs. Persistent fidelity gain must eventually outweigh a finite edit cost; test the frozen endpoint. Candidate-history/committed-output consistency must be explicit. Do not append a hold timer, RGB filter or blanket history decay layer.','No coefficient choice, new rendering or basic activation before correspondence and stationary-state counterexamples pass.']}
(D/'FINAL516.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({'decision':out['decision'],'sourceFailure':out['sourceCorrespondenceFailure'],'freeze':freeze,'support':out['novelPacketSupport'],'headEnvelope':[{'eta':r['eta'],'maxDown':r['maxBottomDown'],'maxUp':r['maxBottomUp'],'topMax':r['maxTopChange'],'changedColumnsMax':r['maxChangedBottomColumns']}for r in profiles],'archiveBytes':archive.stat().st_size,'sequenceBytes':(D/'ALL_REGION_SEQUENCES516.npz').stat().st_size},ensure_ascii=False))
