"""Source-form audit: an unobserved relative pair has no measured error.

110 returned geometric error0 when all source pairs were missing. Combined
with a separate missing-pair cost that made a lost correspondence appear to
have better geometry than an actually measured correspondence. Do not invent
an error or weight for missing geometry. Its explicit coverage penalty remains;
the unmeasured error is None and cannot claim to improve a measured quantity.
This does not prove a globally unique artistic shape.
"""
from identity110 import histogram,conditional_l1,relative_form,nondominated

def rank_source(solutions,cells,transported,available,canonical,expected):
    vectors=[];unmeasured=[]
    for labels in solutions:
        h=histogram(cells,labels,transported);q={str(p):conditional_l1(canonical,h,available,p)for p in [1,4,6]};r=relative_form(cells,labels,transported,expected,available)
        for p in [1,4]:
            keys=[k for k in expected if k[1]==p and k in available]
            if len(keys)<2 or r[f'{p}:missingSourcePairs']==1:r[f'{p}:relativeGeometry']=None
        q.update(r);vectors.append(q);unmeasured.append([k for k,v in r.items()if v is None])
    winners=nondominated(vectors)
    return winners,{'sourceFormDimensions':[{str(k):str(v)if v is not None else None for k,v in q.items()}for q in vectors],'unmeasuredRelativeGeometry':unmeasured,'selectedIndices':winners,'completeInputPoolRequired':True,'missingCorrespondencePenaltyRetained':True,'unknownGeometryNotScoredAsPerfect':True,'historyApplied':False,'immutableBankNotArtistIntentProof':True}
