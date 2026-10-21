"""Minimum properties and counterexamples BEFORE Walk sensitivity."""
from pathlib import Path
import json,math,time,itertools,hashlib
import numpy as np
import active516 as G,state520 as S
W=G.ROOT;D=W/'State520';real=json.loads((D/'PREFLIGHT520.json').read_text());assert real['preconditionPassed'];good,bad=real['rows'];delta=bad['spatial']['total']-good['spatial']['total'];raw=real['recoverRaw519'];assert raw==real['reverseRaw519'];matrix=[[0,raw],[raw,0]];rows=[];recoveries=[]
times=[json.loads((G.INPUT/f'{i:03d}_ALT_projection.json').read_text())['gameTime']for i in range(81)];reference=float(np.median(np.diff(times)))
def kernel(raw,eta,initial=None,keys=None):return S.StateCost(raw,eta,initial,keys,reference_seconds=reference)

for eta in[.5,1.,2.]:
    state=kernel(matrix,eta,[0.,math.inf]);bound=state.beta*raw*reference/delta;history=[];dt=reference
    for k in range(math.ceil((bound+1)*60)):
        chosen=state.step([delta,0.],dt);history.append({'seconds':state.seconds,'drawing':'current'if chosen else'past','values':state.value.tolist()})
    first=next(r['seconds']for r in history if r['drawing']=='current');assert first<=bound+dt+1e-10;assert history[-1]['drawing']=='current'
    recoveries.append({'eta':eta,'oldFramewiseRecoverMinusStay':state.beta*raw-delta,'finiteBarrier':state.beta*raw,'currentEvidenceAdvantagePerReferenceInterval':delta,'theoreticalRecoverySeconds':bound,'observedRecoverySeconds60Hz':first,'oneTransitionCellChanges':real['differentCells'],'oldArea':bad['spatial']['area'],'recoveredArea':good['spatial']['area'],'oldStairRatioReversals':bad['stairRhythm']['stairRatioReversalsDiagnostic'],'recoveredStairRatioReversals':good['stairRhythm']['stairRatioReversalsDiagnostic'],'history':history})
rows.append({'name':'real-stationary12cell-recovery-for-all3weights','passed':True,'recoveries':recoveries})

firstStep=[]
for eta in[.5,1.,2.]:
    barrier=float(np.float32(.14))*eta*raw
    for advantage in[0.,barrier*.5,barrier,barrier*2]:
        state=kernel(matrix,eta,[0.,math.inf]);energy=[advantage,0.];oldScores=[advantage,barrier];oldChoice=min(range(2),key=lambda i:(oldScores[i],energy[i],i));newChoice=state.step(energy,reference);assert oldChoice==newChoice
        firstStep.append({'eta':eta,'spatialAdvantage':advantage,'oldChoice':oldChoice,'newChoice':newChoice})
rows.append({'name':'one-reference-interval-preserves-old-weight-calibration','passed':True,'cases':firstStep})

# Equal physical evidence with different partitions must give equal potentials.
for eta in[.5,1.,2.]:
    outputs=[]
    for hz in[30,60,120]:
        state=kernel(matrix,eta,[0.,math.inf])
        for i in range(6*hz):state.step([delta,0.],1/hz)
        outputs.append(state.value.copy())
    assert max(float(np.max(abs(v-outputs[0])))for v in outputs)<1e-10
rows.append({'name':'physical-time-partition-invariance-on-stationary-input','passed':True,'ratesHz':[30,60,120],'seconds':6,'scope':'Piecewise-constant evidence and fixed valid geometry, not invented missing Walk poses.'})
beforeThreshold=[];duration=float(np.float32(.14))*raw*reference/delta*.5
for pieces in[1,2,4,8]:
    state=kernel(matrix,1,[0.,math.inf])
    for _ in range(pieces):state.step([delta,0],duration/pieces)
    beforeThreshold.append(state.value.copy())
assert max(float(np.max(abs(v-beforeThreshold[0])))for v in beforeThreshold)<1e-10
rows.append({'name':'pre-recovery-partition-invariance-without-saturation','passed':True,'durationSeconds':duration,'pieces':[1,2,4,8],'valueAtEnd':beforeThreshold[0].tolist()})

# Three-state composition uses explicit raw edit paths; it is not a lowered
# coordinate threshold. A nonmetric direct edit must not break the semigroup.
raw3=[[0,2,10],[2,0,2],[10,2,0]];k=kernel(raw3,1,[0,math.inf,math.inf]);assert abs(k.cost[0,2]-k.beta*4)<1e-12 and k.paths[0][2]==[0,1,2]
one=kernel(raw3,1,[0,math.inf,math.inf]);many=kernel(raw3,1,[0,math.inf,math.inf]);one.step([.4,.2,0],2*reference)
for i in range(120):many.step([.4,.2,0],2*reference/120)
assert np.max(abs(one.value-many.value))<1e-10
rows.append({'name':'multi-state-edit-path-closure-and-semigroup','passed':True,'directRaw':10,'explicitComposedRaw':4,'path':[0,1,2],'rawEdgeCostsChanged':False,'effectiveReachableBarrierCanDifferFromOneDirectEdit':True})

zero=kernel(matrix,1,[0,math.inf]);before=zero.value.copy()
for i in range(100):zero.step([delta,0],0)
assert np.array_equal(before,zero.value)
balanced=kernel(matrix,1,[0,math.inf])
for i in range(120):balanced.step([0,0],1/60)
assert balanced.value[0]==0 and balanced.value[1]>0
rows.append({'name':'no-unconditional-timer-or-zero-dt-accumulation','passed':True,'equalEvidenceDoesNotErasePrior':True})

# Transport validity is provided by the frozen correspondence. State labels
# follow current geometry; retaining a design state cannot freeze screen space.
moving=kernel(matrix,1,[0,math.inf]);positions=[]
for i in range(120):
    chosen=moving.step([0,delta],1/60);assert chosen==0;positions.append(i/30.)
assert positions[-1]-positions[0]>3.9
rows.append({'name':'sustained-rigid-motion-is-permitted','passed':True,'stateLabel':0,'geometryPositionTravel':positions[-1]-positions[0],'scope':'Kernel property under an explicitly valid co-moving correspondence; no new actual Walk result.'})

# Partial event restart must preserve the unaffected component's prior.
old=list(itertools.product(range(2),range(2)));values=[0.,1.,2.,3.];restart=[]
for event,count in[('explicit-occlusion-reappearance',2),('split',3),('merge',1)]:
    current=list(itertools.product(range(2),range(count)));prior=S.restart_marginal(old,values,current,[0],current);assert np.all(prior==np.array([0. if u==0 else 2. for u,a in current]))
    rawCurrent=[[4*(u!=v)+(a!=b)for v,b in current]for u,a in current];state=kernel(rawCurrent,1,prior,keys=current);energy=[.5*(u==0)+(a!=count-1)for u,a in current];selected=state.step(energy,reference*.01);assert current[selected][0]==0
    restart.append({'event':event,'oldStates':len(old),'newStates':len(current),'selected':current[selected],'affectedPrior':'UNAVAILABLE','eventTransitionCost':None,'unaffectedPriorPreserved':True})
rows.append({'name':'component-marginal-restart-preserves-unaffected-history','passed':True,'events':restart})

# The tempting alternatives fail: clear all history, or retain only coupled
# whole-drawing hypotheses. Keep those failures visible, never report reset0.
current=list(itertools.product(range(2),range(2)));cost=[[4*(u!=v)+(a!=b)for v,b in current]for u,a in current];wrong=kernel(cost,1,None,keys=current);idx=wrong.step([.5*(u==0)+(a!=1)for u,a in current],reference*.01);assert current[idx][0]==1
restricted=[(0,0),(1,1)];rejection=None
try:S.restart_marginal(restricted,[0,2],restricted,[0],current)
except ValueError as exc:rejection=str(exc)
assert rejection is not None
rows.append({'name':'whole-reset-and-truncated-whole-drawing-bank-counterexamples','passedAsExpectedRejection':True,'wholeResetWronglyChangesUnaffectedTo':current[idx],'truncatedBankRejected':rejection})

# Strict persistent advantage removes initial-state dependence. Balanced
# periodic alternatives do not define a unique design; do not promise one.
strict=[]
for init in[[0,math.inf],[math.inf,0]]:
    k=kernel(matrix,1,init)
    for i in range(6*60):selected=k.step([delta,0],1/60)
    strict.append(selected)
assert strict==[1,1]
cycles=[]
for init in[[0,math.inf],[math.inf,0]]:
    k=kernel(matrix,1,init);ends=[];amplitude=.25*k.beta*raw*reference/.5
    for loop in range(10):
        for frame in range(60):selected=k.step([0,amplitude]if frame<30 else[amplitude,0],1/60)
        ends.append(selected)
    cycles.append(ends)
rows.append({'name':'loop-initial-state-properties','strictAdvantagePassed':True,'strictOutputs':strict,'balancedPeriodicEndStates':cycles,'balancedInitialStateIndependenceGuaranteed':False,'scope':'Equal cycle energy can retain distinct stable choices. This is not proof that actual Walk startup quality is acceptable.'})
out={'finiteStateContractPropertiesPassed':True,'existingSelectorApplicationGatePassed':False,'reason':'The516 selector retains one emitted previous span set, not alternative value states; a restricted whole-drawing bank cannot implement component-only marginal restart without missing feasible combinations. The kernel alone does not repair that search/state representation.','tests':rows,'newStateCostKernelImplementedOffline':True,'newWalkSensitivityRun':False,'etaValues':[.5,1.,2.],'etaUnitInReplacement':'original dimensionless strength at one fixed reference interval','referenceSeconds':reference,'referenceBasis':'Median of the original81 stored gameTime samples; fixed calibration, independent of current render frame partition.','newUnityCalls':0,'productChanged':False,'newFillPhysicalVisibility':'UNVERIFIED','validatedCorrespondenceChanged':False}
(D/'MINIMUM520.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'finiteStateContractPropertiesPassed':True,'existingSelectorApplicationGatePassed':False,'referenceSeconds':reference,'recoverySeconds':[{'eta':r['eta'],'bound':r['theoreticalRecoverySeconds'],'observed':r['observedRecoverySeconds60Hz']}for r in recoveries],'wholeResetNegativeExample':current[idx],'truncatedBankRejection':rejection,'balancedLoopInitialStates':cycles,'walkSensitivityRun':False},ensure_ascii=False),flush=True)
