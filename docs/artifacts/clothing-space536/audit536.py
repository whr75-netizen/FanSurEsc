"""Contract audit + decomposition of existing535 results; no new metric fit.

Do not manufacture a complete spatial score when its required inputs differ.
"""
from pathlib import Path
import hashlib, json, math

O=Path(__file__).resolve().parent
R=O.parent/'Feature535'
j=json.loads((R/'METRIC_AUDIT535.json').read_text())
g=json.loads((R/'GATE535.json').read_text())
normals=[]
for q in j['rows']:
    if not q['case'].startswith('thin'):continue
    base=q['alternatives']['baseline']
    filtered=base['eq3HeightEligibility']['rows']
    raw=base['unfilteredReferenceDiagnostic']['rows']
    terms=[]
    for a,b in zip(filtered,raw):
        if a['costRange'][0]<=0:continue
        assert len(a['nearbyReference'])==0 and len(b['nearbyReference'])==1
        e=a['output'];ref=b['nearbyReference'][0]
        assert ref['height']==.75 and ref['width']==3 and e['width']==3
        assert b['costRange']==[0,0]
        terms.append({'outputPosition':e['position'],'referencePosition':ref['position'],
            'axis':e['axis'],'polarity':e['kind'],
            'distanceBeforeEligibility':math.dist(e['position'],ref['position']),
            'withinRadius2BeforeEligibility':True,'referenceHeight':ref['height'],
            'referenceRemovedByEligibility':True,'outputWidth':e['width'],
            'costWithEligibility':a['costRange'][0], 'costWithoutEligibility':0})
    assert len(terms)==3 and math.isclose(sum(x['costWithEligibility']for x in terms),1)
    omitted=next(a for a in g['normalEndOmissionCounterexamples']if a['case']==q['case'])
    assert omitted['newScore']==[1/11,1/11]
    normals.append({'case':q['case'],'terms':terms,'preservedCost':1,'bothEndsOmittedCost':1/11,
                    'radiusSearchFailure':False,'explicitDeletedReferenceExtremumTermPresent':False})
assert len(normals)==8
causal={'status':'535_PROXY_MECHANISM_DECOMPOSED_NOT_PAPER_RESULT',
    'primaryMechanism':'Eligibility removed shallow reference extrema even though radius search would match them.',
    'secondaryMechanism':'Eq3-style sum is over output extrema; deleting them removes terms. No separate lost-reference-end charge exists in that term.',
    'wholeObjectiveOmissions':['orientation Eq1','location/weighted stroke coverage Eq2','span staircase Eq4'],
    'exactnessMismatch':['region cell edges instead of AppendixA pixel-centre/span feature lines',
                        'feature-list eligibility instead of reference pixel perturbation'],
    'normalCases':normals,'newMetricEvaluations':0,'newUnityCalls':0,'newCaptures':0}
(O/'CAUSAL_DECOMPOSITION536.json').write_text(json.dumps(causal,indent=2),encoding='utf-8')
spec={'scope':'spatial-only specification, no scorer/selector implemented',
    'sourceURL':'https://yongliangyang.net/docs/pixelAnim_pg16.pdf',
    'spatialObjective':'Espace = Eso + 0.5*Esc + Eqs + 0.5*Eqj',
    'weightsOrigin':'paper Algorithm1 spatial weights, fixed; temporal term excluded by task; not claimed optimal for region masks',
    'terms':[
      {'name':'Eso','paper':'Eq1 / Fig4','definition':'sum of areas between turning functions of matching oriented polylines, arc-length parameterized',
       'requires':['same reference/output line identity, orientation and line start/end','AppendixA output pixel-path vectorization','fixed unrasterized deformed reference'],
       'current':'region contours available; pixel-centre line paths and closed-loop phase correspondence absent', 'equivalent':False},
      {'name':'Esc','paper':'Eq2 / Fig5','definition':'per-line average of output-pixel penalties 1-ci, using weighted overlap with fixed high-resolution warped source feature-line footprint',
       'requires':['10x source pixel-art feature-line footprint warped before low-resolution rasterization','Manhattan boundary weights and per-pixel normalization','ordered output line pixels and paper ci<0.5 handling'],
       'current':'filled-region area A is available; it is not weighted stroke ci; original pixel-line footprint/warp is absent', 'equivalent':False},
      {'name':'Eqs','paper':'Eq3 / Fig7','definition':'output extrema compared to nearby reference extrema; width difference over width sum for matched, inverse width for unmatched',
       'requires':['same vectorized feature-line representation','reference extremum filtering by specified pixel perturbation','width band .5, reference height1, experimental correspondence radius2 in logical pixels'],
       'current':'535 uses region-edge extrema and list culling, not the exact reference perturbation/line representation', 'equivalent':False},
      {'name':'Eqj','paper':'Eq4 / Fig8','definition':'nonmonotone consecutive span-triplet count per line, normalized by initial line span count',
       'requires':['ordered pixels grouped into spans inside extremum-separated sub-polylines','fixed initial span-count denominator','same line/junction and pixel-vectorization rules'],
       'current':'no paper centreline/span graph or fixed initial line span denominator; region perimeter is not this quantity', 'equivalent':False}],
    'sharedInputs':{'referenceDuringCandidateEvaluation':'immutable and independent of FitArea/selected mask',
                    'withinPoseLineCorrespondence':'required','crossPoseTemporalMatching':'not required by this spatial-only comparison',
                    'closedLoops':'need an explicit common anchor/orientation/phase rule, not independently minimum screen coordinates',
                    'regionFillAuthority':'existing common Gate retained, but it does not supply missing line/stroke inputs'},
    'currentSelector':{'path':'Assets/EUnityValidation01/HeadRegion502/Runtime/HeadRegion502.cs:207',
        'inputs':'float cell fill areas + width + height','energy':'area unary + pairwise boundary length',
        'hasPaperLineTerms':False,'canAddFourIndependentPerPixelWeightsAndRemainEquivalent':False},
    'replacementContract':'Boundary choice before selected mask must receive a fixed reference plus candidate line/band/region correspondence. FitArea can generate candidates, but cannot replace the reference. Downstream fill/outline/gates must consume the same chosen closed region.',
    'caseMatrix':[{'case':q['case'],'fullSpatialScore':None,'status':'UNDEFINED_INPUT_REPRESENTATION_NOT_EQUIVALENT'}for q in j['rows']],
    'minimumMissingAdapter':'Define one common boundary-centreline/outline-band-to-fill contract and matching per-pose pixel line graph; a band synthesized from mesh distance would be an explicit region-method adaptation, not the paper warped artist-line input.',
    'newEngineRequiredProved':False,'reasonNotImplemented':'Exact paper inputs are unavailable; choosing a different stroke/anchor/topology policy is a method change, not completing omitted arithmetic.',
    'paperKnownLimitsRelevant':'paper does not model all relationships between nearby feature lines; part occlusion/topology change are outside its demonstrated formulation. This does not prevent per-pose spatial evaluation once valid inputs exist.'}
(O/'SPATIAL_CONTRACT536.json').write_text(json.dumps(spec,indent=2),encoding='utf-8')
summary={'status':'FULL_SPATIAL_SCORE_NOT_DEFINED_ON_CURRENT_REGION_INPUTS',
    'allSpatialTermsSpecifiedTogether':True,'paperEquivalentImplementationVerified':False,
    'fullObjectiveValuesComputed':False,'newMetricEvaluations':0,'newUnityCalls':0,'newCaptures':0,'newProductCode':False,
    '535Cause':'deliberate reference eligibility exclusion + output-only extremum terms, with other spatial terms missing; not a radius-search failure',
    '535NotExactPaperEq3':True,'spatialWeights':[1,.5,1,.5],'weightsTuned':False,
    'missing':['pixel-centre feature-line/region-band correspondence','warped source feature-line footprint for Eq2','fixed initial span graph and valid closed-loop alignment'],
    'noNewOptimizerOrEngine':True,'runtimeCandidateOFF':True,
    'sourceVisualRead':'web original text read; local PDF download returned HTTP403, no bypass/retry; no local figure image read claimed',
    'noFullPaperSuccessOrFailureVerdict':True}
(O/'SUMMARY536.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
inputs=[{'path':str(R/n),'sha256':hashlib.sha256((R/n).read_bytes()).hexdigest()}for n in ['METRIC_AUDIT535.json','GATE535.json','compare535.py']]
(O/'INPUTS536.json').write_text(json.dumps(inputs,indent=2),encoding='utf-8')
print(json.dumps({'status':summary['status'],'normalCasesDecomposed':len(normals),'termContributions':normals[0]['terms'],
                  'spatialObjective':spec['spatialObjective'],'equivalentTerms':sum(x['equivalent']for x in spec['terms']),
                  'newMetricEvaluations':0,'newUnityCalls':0,'newCaptures':0}))
