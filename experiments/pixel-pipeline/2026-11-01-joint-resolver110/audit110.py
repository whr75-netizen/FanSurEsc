"""Stage/curve/count audit. Reuses completed packets and solves only."""
import json,gzip,math,hashlib,ast
from pathlib import Path
import numpy as np
from stored110 import H,P108,P109
from resolver110 import constraints,feasible
def read(p):return json.loads(p.read_text(encoding='utf8'))
def layouts(q):
    return {tuple((tuple(c),p)for c,p in zip(q['cells'],q['solutions'][i])if p)for i in q.get('selectedIndicesWithinEnumeratedOptima',[])}
def covered_length(points,cells):
    covered=total=0.
    for a,b in zip(points,points[1:]):
        a=np.array(a);d=np.array(b)-a;length=float(np.linalg.norm(d));total+=length;intervals=[]
        for y,x in cells:
            low=0.;high=1.
            for axis,start in [(0,x),(1,y)]:
                if d[axis]==0:
                    if not start<=a[axis]<=start+1:low=1.;high=0.;break
                else:
                    t0=(start-a[axis])/d[axis];t1=(start+1-a[axis])/d[axis];low=max(low,min(t0,t1));high=min(high,max(t0,t1))
            if high>=low:intervals.append((low,high))
        end=0.;fraction=0.
        for a,b in sorted(intervals):
            if b>end:fraction+=max(0,b-max(end,a));end=b
        covered+=length*fraction
    return {'totalPolylineLengthPixels':total,'missedPolylineLengthPixels':max(0,total-covered),'missedFraction':max(0,(total-covered)/total)if total else None,'exactPiecewiseLinearIntervalsNotSampledMidpoints':True}

def main():
    root=[read(p)for p in sorted(H.glob('*-result.json'))];(H/'RESULTS110.json').write_text(json.dumps(root,indent=2)+'\n',encoding='utf8');new=read(H/'separated/RESULTS110.json');lookup={(r['metadata']['sourceId'],r['owner']):r for r in new};by={(r['metadata']['frame'],r['owner']):r for r in new if not r['metadata']['sourceId'].startswith('eye105')};old={(r['metadata']['frame'],r['owner']):r for r in root if r['metadata']['reconstructedGeometry']};reg=[]
    for owner in [1,2]:
        a,b,c=[by[(f,owner)]for f in [204,207,210]];assert layouts(a)==layouts(b)==layouts(c)
        reg.append({'owner':owner,'hairOnOffRestoredCanonicalLayoutsExactlyEqual':True,'conditionalChoices':len(layouts(a)),'ONfullyMaskedCells':sorted({sum(v['fullyMaskedAtRecordedSamples']for v in x)for x in a['exposureForConditionalChoices']}),'OFFfullyMaskedCells':sorted({sum(v['fullyMaskedAtRecordedSamples']for v in x)for x in b['exposureForConditionalChoices']})})
        assert layouts(by[(99,owner)])==layouts(by[(115,owner)])
    closed=[q for q in new if q['metadata']['Close']==1]
    assert all(all(p not in [1,2]for p in v)for q in closed for v in q.get('solutions',[]))
    side=by[(192,1)];assert all(v['fullyMaskedAtRecordedSamples']for x in side['exposureForConditionalChoices']for v in x)
    overlap=[]
    for frame in sorted({q['metadata']['frame']for q in new if q['metadata']['reconstructedGeometry']}):
        a,b=by[(frame,1)],by[(frame,2)];common=set(map(tuple,a['cells']))&set(map(tuple,b['cells']))
        if common:overlap.append({'frame':frame,'cellsYX':sorted(common)})
    sourceMismatch=sum(q.get('sourceIdentity',{}).get('bankSourceCheck',{}).get('bankRGB8Mismatch',0)for q in new)
    assert sourceMismatch==0
    base=read(P108/'RESULTS108.json');curves=[]
    for owner in [1,2]:
        prefix='closed105-frame104-eye'+str(owner)
        with gzip.open(H/(prefix+'-footprint.json.gz'),'rt',encoding='utf8')as f:d=json.load(f)
        q=read(H/'separated'/(prefix+'-result.json'));r=base['closed105-frame104']['noCurve'][str(owner)];points=d['reference']['nativeCurvePoints'];oldL=[tuple(v)for v,p in zip(r['points'],r['massFirst']['labels'])if p==3];newL=[[tuple(v)for v,p in zip(q['cells'],q['solutions'][i])if p==3]for i in q['selectedIndicesWithinEnumeratedOptima']]
        curves.append({'sourceId':q['metadata']['sourceId'],'owner':owner,'old108MassFirstCells':len(oldL),'old108ActualPigmentCurveError':covered_length(points,oldL),'newConditionalCases':[{'cells':len(v),'curveError':covered_length(points,v)}for v in newL],'notFinalHairVisibleCurveOrArtSuccess':True})
    phase=[]
    for owner in [1,2]:phase.append({'owner':owner,'frames':[121,125,129],'hairGatedErrorPixels':[old[(f,owner)]['errorPixels']for f in [121,125,129]],'separatedErrorPixels':[by[(f,owner)]['errorPixels']for f in [121,125,129]],'selectedLayoutsNotProvenInvariant':layouts(by[(121,owner)])!=layouts(by[(125,owner)]),'actualContinuousFinalRGBStabilityClaimed':False})
    minimum=by[(103,1)];index=minimum['cells'].index([4,12]);focus=sorted({minimum['solutions'][i][index]for i in minimum['selectedIndicesWithinEnumeratedOptima']})
    check=read(H/'CHECK110.json');recon=read(H/'RECONSTRUCTION110.json');summary={'status':'offline-unadopted-prototype-with-proven-stage-correction','states':len(new),'capturedInputStates':19,'independent105ClosedInputs':1,'newUnityCalls':0,'newGPUDispatches':0,'productApplied':False,
       'minimum107Frame103Canonical12_4ConditionalLabels':focus,'irisWhiteAtEvaluatedFullClose':0,'hairOnOff':reg,'reopenConditionalLayoutsMatch':True,'twoEyeCarrierOverlapsInTestedStates':overlap,'sourceBankRGB8Mismatches':sourceMismatch,
       'phaseStageAblation':phase,'same105CurveComparison':curves,'side192LatentLidCells':3,'side192RecordedSampleExposure':0,
       'reconstructed107GeometryMaxCanonicalPixels':max(x['maxCanonicalPixels']or 0 for f in recon['frames']for x in f['independentSamples']),
       'reconstructed107GeometryMaxDepthMetres':max(x['maxDepth']or 0 for f in recon['frames']for x in f['independentSamples']),
       'reconstructionIsNotDirectSameFrameMesh':True,'completeOptimumEnumerationStates':sum(q.get('enumerationComplete',False)for q in new),
       'conditionalWitnessLimit':64,'countPlateauExact':read(H/'COUNT_RANGE110.json')['cases'][0]['feasibleCountsAtSameOptimum'],
       'remaining':['An equal geometric optimum permits source iris1..5 cells in F99 eye1. Source-key histogram alone is not shape.','Relative source-key geometry keeps explicit tradeoffs, not an arbitrary unique selection.','64 bounded witnesses are not the complete Pareto frontier. Count-range feasibility proves omitted budgets exist.','Per-S4 surface/alpha bounds do not define an unobserved continuous hair visibility field.','Final RGB/palette/outline and runtime temporal controller are not implemented by this prototype.']}
    (H/'SUMMARY110.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf8')
    code={}
    for path in sorted(H.glob('*.py')):
        tree=ast.parse(path.read_text(encoding='utf8'));code[path.name]=[{'function':n.name,'line':n.lineno}for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))]
    (H/'CODE_INDEX110.json').write_text(json.dumps(code,indent=2)+'\n',encoding='utf8');print(json.dumps(summary))
if __name__=='__main__':main()
