from pathlib import Path
import json
H=Path(__file__).resolve().parent;G=H/'face78'

def main():
 d=json.loads((G/'ACTUAL_RAYS78.json').read_text());result={k:v for k,v in d.items()if k!='rows'}
 selected=[]
 for space in['encodedRGB','linearRGB']:
  rows=[r for r in d['rows']if r['space']==space]
  for name,eligible in [('rank-deficient',[r for r in rows if not r['uniqueNumericalIntersection']]),('weak-native-component',[r for r in rows if r['connectedSupport']==491]),('small-physical-only',[r for r in rows if r['uniqueNumericalIntersection']and r['unitGamut']and r['allRayParametersAtLeastOne']])]:
   if eligible:
    r=eligible[0].copy();r['sampleSourceXY']=r.pop('sourceRows')[:8];r['exampleKind']=name;selected.append(r)
 result['examples']=selected;result['nativeSourceInput']=json.loads((H/'face28/SOURCE_INPUT28.json').read_text());result['interpretation']={'neitherFlanksNorFittedBaseIsObservedCleanBackground':True,'noUniquePigmentClaimFromLeastSquaresPoint':True,'constantBackgroundContinuumDoesNotProveAllSegmentationImpossible':True,'fixedSigmaOffsetCounterexampleNotAllCurveModels':True,'quantizationIsAStatedPrecisionAssumptionNotAuthoredAAProof':True,'sourceLocalToneAndPigmentContractStillUnresolved':True,'independentRuntimeLightQNotUsedToInferSourceColour':True,'fullFaceOutputNotImplementedByThisAudit':True};(G/'CONTRACT_AUDIT78.json').write_text(json.dumps(result,indent=2));print(json.dumps({'summaryBytes':(G/'CONTRACT_AUDIT78.json').stat().st_size,'compactInputBytes':(G/'INPUT_ROWS78.npz').stat().st_size,'actualGPU':False}))
if __name__=='__main__':main()
