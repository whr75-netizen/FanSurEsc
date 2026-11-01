"""Conditional source-ID history among EXACTLY equivalent108 allocations.

This is not adoption of108's incomplete shape objective. It tests whether an
existing source-domain cache can distinguish its concrete tied layouts. The
20-cell authored SOURCE bank remains immutable; a previous raster is NEVER
promoted to canonical form. Current eligibility/occlusion is evaluated first.
Only source-bank iris/white histories are ranked here, not a full native-lid
history controller. No RGB or screen-coordinate distance enters the score.
"""
from pathlib import Path
from fractions import Fraction
import json,sys,itertools
import numpy as np
from native109 import H,R,read,static,sha
from io109 import buffer,joint_arrays,ZipNode

def source_histograms(row,bank,projection,packet_override=None):
    p=packet_override if packet_override is not None else Path(row['sourcePacket'])
    if packet_override is None and not p.exists():
        archive=R/'2026-11-01-joint-visibility107/RAW107.zip';p=ZipNode(archive,f'final54/frame{row["frame"]}')
    m=read(p/'RAW_MANIFEST.json');assert m['sourceId']==row['sourceId'];w,h=m['forward102']['canonicalSize'];a=buffer(p/'canonical-layers.f32').reshape(4,5,h,w,4);v=buffer(p/'canonical-visibility.f32').reshape(4,h,w,4);lo,hi,*_=joint_arrays(a,v)
    cells={};available={};unknown=0;colourMismatch=0;examined=0;decodeError=0.
    for part,index in [(1,1),(4,2)]:
        for y,x in np.argwhere(lo[index-1]>0):
            owner=round(float(a[index,1,y,x,2]));rest=np.r_[a[index,2,y,x,:3],np.float32(1)].astype(np.float32);q=rest@projection[owner];k=np.floor(q).astype(int);key=(owner,part,int(k[0]),int(k[1]));examined+=1
            if key not in bank:unknown+=1;continue
            # Bank shader supplies an exact existing linear RGB; source IDs
            # must also reproduce its palette, not merely nearest colour.
            encoded=np.array(bank[key],float)/255;linear=np.where(encoded<=.04045,encoded/12.92,((encoded+.055)/1.055)**2.4)
            decodeError=max(decodeError,float(np.max(abs(a[index,0,y,x,:3]-linear))))
            actual=a[index,0,y,x,:3];encodedActual=np.where(actual<=.0031308,actual*12.92,1.055*np.maximum(actual,0)**(1/2.4)-.055)
            if not np.array_equal(np.rint(encodedActual*255).astype(int),bank[key]):colourMismatch+=1
            weight=Fraction(float(lo[index-1,y,x]))/16;cell=(owner,int(y)//4,int(x)//4,part);cells.setdefault(cell,{})[key]=cells.setdefault(cell,{}).get(key,Fraction(0))+weight;available[key]=available.get(key,Fraction(0))+weight
    return cells,available,{'examined':examined,'unresolvedSourceKeys':unknown,'bankRGB8Mismatch':colourMismatch,'maxGPUFloatVsAnalyticSRGBDecode':decodeError,'sampleScale':4,'primary108SampleScale':row['scale']}

def layout_hist(q,labels,owner,cells):
    hist={}
    for(y,x),part in zip(q['points'],labels):
        if part not in [1,2]:continue
        for key,value in cells.get((owner,y,x,1 if part==1 else 4),{}).items():hist[key]=hist.get(key,Fraction(0))+value
    return hist

def source_score(previous,current,available):
    """L1 between conditional source-key distributions, AFTER visibility gate.
    No information stays unresolved, not a fabricated temporal preference.
    """
    score=Fraction(0);informative=[]
    for part in [1,4]:
        a={k:v for k,v in previous.items()if k[1]==part and available.get(k,0)>0};b={k:v for k,v in current.items()if k[1]==part and available.get(k,0)>0};sa=sum(a.values());sb=sum(b.values())
        if not sa or not sb:continue
        score+=sum(abs(a.get(k,0)/sa-b.get(k,0)/sb)for k in a.keys()|b.keys());informative.append(part)
    return score,informative

def part_scores(previous,current,available):
    out={}
    for part in [1,4]:
        a={k:v for k,v in previous.items()if k[1]==part and available.get(k,0)>0};b={k:v for k,v in current.items()if k[1]==part and available.get(k,0)>0};sa=sum(a.values());sb=sum(b.values())
        out[part]=sum(abs(a.get(k,0)/sa-b.get(k,0)/sb)for k in a.keys()|b.keys())if sa and sb else None
    return out

def pareto_indices(vectors):
    common=[p for p in [1,4]if all(v[p]is not None for v in vectors)]
    return {i for i,a in enumerate(vectors)if not any(all(b[p]<=a[p]for p in common)and any(b[p]<a[p]for p in common)for j,b in enumerate(vectors)if i!=j)}

def canonical_rank(candidates,source,cells,available,owner,q):
    # Each immutable authored bank cell has its ORIGINAL unit source area.
    # This is not a count requirement for the destination raster.
    canonical={tuple([x['owner'],x['part'],x['x'],x['y']]):Fraction(1)for x in source}
    vectors=[part_scores(canonical,layout_hist(q,c,owner,cells),available)for c in candidates]
    return sorted(pareto_indices(vectors)),[{str(p):str(v)if v is not None else None for p,v in a.items()}for a in vectors]

def rank(candidates,prior,cells,available,owner,q):
    h=[layout_hist(q,x,owner,cells)for x in candidates]
    if not prior:return list(range(len(candidates))),h,{'historyAvailable':False,'initialMultipleSolutionsRemain':len(candidates)>1}
    scores=[];vectors=[]
    for previous in prior:
        scores.append([source_score(previous,current,available)[0]for current in h])
        vectors.append([part_scores(previous,current,available)for current in h])
    winners=[]
    for v in vectors:winners.append(pareto_indices(v))
    # A unique previous branch may resolve a tie. Several prior branches must
    # AGREE, otherwise retain their union instead of choosing the first one.
    chosen=set.union(*winners)
    return sorted(chosen),[h[i]for i in sorted(chosen)],{'historyAvailable':True,'priorBranches':len(prior),'chosenIndices':sorted(chosen),'exactScores':[[str(v)for v in s]for s in scores],
       'partVectorsDecideNotWeightedSum':[[{str(p):str(v)if v is not None else None for p,v in a.items()}for a in vv]for vv in vectors],'priorBranchesAgree':all(x==winners[0]for x in winners)}

def transform_check(q,candidates,prior,cells,available,owner):
    base,_,flags=rank(candidates,prior,cells,available,owner,q);checks=0
    # Full labelled problem and observed source-carrier cells transform
    # together. This checks selection, not a tautology on an unused position.
    for f in [lambda y,x:(x,-y),lambda y,x:(-y,-x),lambda y,x:(y,-x),lambda y,x:(-x,y)]:
        points=[f(*p)for p in q['points']];transformed={(o,*f(y,x),p):v for(o,y,x,p),v in cells.items()};qq=q|{'points':points}
        win,_,info=rank(candidates,prior,transformed,available,owner,qq);assert win==base and info.get('exactScores')==flags.get('exactScores');checks+=1
        rev,_,_=rank(candidates[::-1],prior,transformed,available,owner,qq);assert {tuple(candidates[i])for i in base}=={tuple(candidates[::-1][i])for i in rev};checks+=1
    # Reorder all cell/label storage independently of geometry.
    ix=list(range(len(q['points'])))[::-1];qq=q|{'points':[q['points'][i]for i in ix]};cc=[[x[i]for i in ix]for x in candidates]
    win,_,info=rank(cc,prior,cells,available,owner,qq);assert win==base and info.get('exactScores')==flags.get('exactScores');checks+=1
    return checks

def tests():
    a={(2,1,4,8):Fraction(1)};b={(2,1,5,8):Fraction(1)};available=a|b
    assert source_score(a,a,available)[0]==0 and source_score(a,b,available)[0]==2
    # Actual occlusion makes a previous source key unavailable; it cannot be
    # brought back by history. Absence is not assigned an arbitrary ghost.
    assert source_score(a,b,b)[0]==0
    # Relocation/rotation/reflection/continuous world motion do not enter a
    # source-ID score. Keep source identity fixed while changing all positions.
    for t in np.linspace(0,1,21):
        for f in [lambda x,y:(x+t,y-t),lambda x,y:(-y+t,x+t),lambda x,y:(-x-t,y+t)]:
            moved=f(4.2,8.3);assert moved and source_score(a,a,available)[0]==0
    # Candidate ordering does not decide winners.
    q={'points':[(0,0),(0,1)]};cells={(2,0,0,1):a,(2,0,1,1):b};candidates=[[1,0],[0,1]]
    win,_,_=rank(candidates,[a],cells,available,2,q);rev,_,_=rank(candidates[::-1],[a],cells,available,2,q);assert candidates[win[0]]==candidates[::-1][rev[0]]
    initial,_,flags=rank(candidates,[],cells,available,2,q);assert initial==[0,1]and flags['initialMultipleSolutionsRemain']
    both,_,flags=rank(candidates,[a,b],cells,available,2,q);assert both==[0,1]and not flags['priorBranchesAgree']
    assert pareto_indices([{1:Fraction(0),4:Fraction(1)},{1:Fraction(1),4:Fraction(0)}])=={0,1}
    checks=transform_check(q,candidates,[a],cells,available,2)
    return {'sourceScoreContinuousCoordinateInvarianceChecks':63,'fullProblemRotationReflectionOrderChecks':checks,'candidateOrderInvariant':True,'initialAndConflictingHistoryRemainMultiple':True,'occlusionBeforeHistory':True,'notAnEndToEndPhaseRasterTest':True}

def main():
    source=read(static('SOURCE_FIXTURE88.json',R/'feature-layer88/SOURCE_FIXTURE88.json'));bank={(x['owner'],x['part'],x['x'],x['y']):source['paletteRGB8'][x['palette']]for x in source['source']};reg=read(static('REGISTRATION89.json',R/'native-feature89/REGISTRATION89.json'));projection={e['eye']:np.asarray(e['nativeToAuthoredProjection'],np.float32)for e in reg['eyes']};related=R/'joint-model108'if(R/'joint-model108').exists()else R/'2026-11-01-joint-objective108';rows=read(related/'INPUT108.json');base=read(related/'RESULTS108.json');prior={1:[],2:[]};previousFrame={1:None,2:None};out=[];scope=None;metamorphic=0
    fixture=[];bankSignature=sha(static('SOURCE_FIXTURE88.json',R/'feature-layer88/SOURCE_FIXTURE88.json'))
    for row in sorted((x for x in rows if x['name'].startswith('actual107')),key=lambda r:r['frame']):
        pp=Path(row['sourcePacket'])
        if not pp.exists():pp=ZipNode(R/'2026-11-01-joint-visibility107/RAW107.zip',f'final54/frame{row["frame"]}')
        m=read(pp/'RAW_MANIFEST.json');currentScope=(m['forward102']['scope'],bankSignature)
        if currentScope!=scope:prior={1:[],2:[]};previousFrame={1:None,2:None};scope=currentScope
        cells,available,check=source_histograms(row,bank,projection);assert check['unresolvedSourceKeys']==0 and check['bankRGB8Mismatch']==0;entries=[]
        for owner in [1,2]:
            q=base[row['name']]['noCurve'][str(owner)]
            if 'massFirst'not in q:entries.append({'owner':owner,'status':q['status'],'historyCannotCreateUnsupportedParts':True});continue
            candidates=q['massFirstDistinctWitnesses'];winners,hist,flags=rank(candidates,prior[owner],cells,available,owner,q)
            entry={'owner':owner,'candidatesBefore':len(candidates),'candidatesAfter':len(winners),'candidateOrderIndependentSelection':winners,'previousCapturedFrame':previousFrame[owner],
               'frameGap':row['frame']-previousFrame[owner]if previousFrame[owner]else None,'notNecessarilyAdjacentFrames':True,**flags}
            if len(candidates)>1:
                intrinsic,iv=canonical_rank(candidates,source['source'],cells,available,owner,q);entry['immutableSourceFormNondominatedIndices']=intrinsic;entry['immutableSourceFormPartVectors']=iv;entry['sourceFormAlreadyDistinguishesThisCase']=len(intrinsic)==1
                entry['differences']=[{'pointsYX':q['points'],'labels':c}for c in candidates];metamorphic+=transform_check(q,candidates,prior[owner],cells,available,owner)
                encode=lambda hist:[{'key':list(k),'weight':str(v)}for k,v in sorted(hist.items())]
                fixture.append({'frame':row['frame'],'sourceId':row['sourceId'],'owner':owner,'q':{'points':q['points']},'candidates':candidates,'prior':[encode(x)for x in prior[owner]],
                    'cells':[{'cell':list(k),'histogram':encode(v)}for k,v in cells.items()if k[0]==owner],'available':encode(available),'expectedWinners':winners,'expectedExactScores':flags['exactScores'],'expectedCanonicalWinners':intrinsic,'expectedCanonicalPartVectors':iv})
            entries.append(entry)
            # Assignment history is separate from immutable canonical source
            # cache. Occlusion may retain latent identities, never render them.
            active=[h for h in hist if h]
            if active:prior[owner]=active;previousFrame[owner]=row['frame']
        out.append({'frame':row['frame'],'sourceId':row['sourceId'],'stage':row['stage'],'sourceKeyCheck':check,'currentlyVisibleSourceBankKeys':{str(o):{str(p):sum(k[0]==o and k[1]==p for k in available)for p in [1,4]}for o in [1,2]},'eyes':entries})
    report={'kind':'conditional-source-history-among-equivalent-108-layouts','tests':tests()|{'actualTiedLayoutTransformAndOrderChecks':metamorphic},'frames':out,'immutableSourceBankCells':len(bank),'changesCanonicalForm':False,'newRGB':False,'productApplied':False,
      'limitations':['108 mass objective remains unadopted; history does not repair its fragmented lid.','Iris/white source-ID ranking uses actual4x source metadata; primary costs remain8x.','Native pigment curve cache is separate and not yet a full joint layout/history controller.','Captured states have frame gaps; no new runtime temporal-stability claim.','Current source/face eligibility is primary; external hair remains the original separate composition stage.']}
    (H/'HISTORY109.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    (H/'HISTORY_TIED_INPUTS109.json').write_text(json.dumps(fixture,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'tests':report['tests'],'sourceKeysUnresolved':sum(x['sourceKeyCheck']['unresolvedSourceKeys']for x in out),'bankRGB8Mismatch':sum(x['sourceKeyCheck']['bankRGB8Mismatch']for x in out),
      'tiedExamples':[{'frame':x['frame'],'eye':e}for x in out for e in x['eyes']if e.get('candidatesBefore',0)>1]}))
if __name__=='__main__':main()
