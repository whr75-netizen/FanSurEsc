"""Focused evidence and policy conflict ledger; no display or Unity control."""
from pathlib import Path
import json,sys,hashlib,math
import numpy as np
from PIL import Image,ImageDraw
from export108 import load_fields,joint_arrays
from analyse108 import H,R,font,map_labels

COLOURS=['#202a35','#395ee8','#e9edf6','#d78745','#7148d4','#d6e6dc','#e35e56','#78919c']

def pixels(a):return Image.fromarray(np.array([[tuple(int(COLOURS[int(k)][t:t+2],16)for t in [1,3,5])for k in line]for line in a],np.uint8))

def main():
    rows=json.loads((H/'INPUT108.json').read_text());results=json.loads((H/'RESULTS108.json').read_text());row=next(r for r in rows if r['frame']==103)
    d=np.load(H/'fixtures'/ (row['name']+'.npz'));m,scale,ls,v=load_fields(Path(row['sourcePacket']));lo,hi,clo,chi,dom=joint_arrays(ls,v)
    y,x=4,12;sl=np.s_[y*scale:(y+1)*scale,x*scale:(x+1)*scale];fine=np.full((scale,scale),7,int)
    for p in range(3):fine[dom[p][sl]]=p+1
    canvas=clo[sl]>hi[:,sl[0],sl[1]].max(0);fine[canvas]=0
    counts=[int((fine==p).sum())for p in [1,2,3,0]];assert counts==[30,27,2,5]
    focus={'frame':103,'sourceId':row['sourceId'],'cellXY':[x,y],'sampleCountsIrisWhiteLidCanvas':counts,
      'visibleMassIrisWhiteLidCanvas':[float(d['lower'][k,y,x])for k in [1,2,3,0]],'allocations':{}}
    for policy in ['noCurve','arc4','arc8','relaxedCarrier4']:
        q=results[row['name']][policy]['1'];a=map_labels(d,1,q,'massFirst');focus['allocations'][policy]={'label':int(a[y,x]),'regionCounts':q['massFirst']['counts'],'massError':q['massFirst']['mass']}
    old=json.loads((R/'joint-lid107/FOCUS107.json').read_text())
    # Quantify the incompatible extra constraints, not an inherent impossibility
    # of strong eye-feature correction or a recommendation to keep strict area.
    conflicts=[];endpointFailures=[];relaxRecovered=[];equivalents=[]
    for name,rec in results.items():
        for owner in ['1','2']:
            for policy in ['arc4','arc8']:
                q=rec[policy][owner]
                if 'massFirst'in q:
                    a=q['sourceMassUpper'][2];n=q['minimumLidPathCells']
                    if n>math.ceil(a):conflicts.append({'fixture':name,'owner':int(owner),'policy':policy,'sourceLidMass':a,'naturalCeilMassBudget':math.ceil(a),'minimumCurvePathCells':n,
                        'contradiction':'N_lid >= path minimum AND N_lid <= ceil(source mass) is infeasible; neither bound is a universal artistic rule'})
            strict=rec['arc4'][owner];relaxed=rec['relaxedCarrier4'][owner]
            if strict['status']=='infeasible-curve-support':endpointFailures.append({'fixture':name,'owner':int(owner),'endpointsYX':strict['endpoints']})
            if strict['status']=='infeasible-curve-support'and'massFirst'in relaxed:relaxRecovered.append({'fixture':name,'owner':int(owner),'relocatedCells':relaxed['massFirst']['outsideSameCellCertainSupport'],
               'renderValid':False,'reason':'destination carrier depth/visibility and source-witness transport not defined by this mathematical relaxation'})
            for policy in ['noCurve','arc4','arc8','relaxedCarrier4']:
                q=rec[policy][owner]
                if q.get('massFirstIsUnique')is False:
                    a,b=q['massFirstDistinctWitnesses'][:2]
                    equivalents.append({'fixture':name,'owner':int(owner),'policy':policy,'costData':q['massFirst']['data'],'costMass':q['massFirst']['mass'],
                        'changedCellsXYLabelAandB':[[pt[1],pt[0],aa,bb]for pt,aa,bb in zip(q['points'],a,b)if aa!=bb]})
    report={'focus':focus,'curveMassConflictCases':conflicts,'strictCurveInfeasibleOwnerStates':endpointFailures,'recoveredByCoordinateRelaxation':relaxRecovered,'certifiedEquivalentMassFirstSolutions':equivalents,
       'sourceContrastsNotRGBChanged':True,'notAProofThatFeatureCorrectionIsImpossible':True,'candidateAccepted':False}
    (H/'EVIDENCE108.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    board=Image.new('RGB',(1280,850),'#111923');dr=ImageDraw.Draw(board)
    dr.text((20,15),'108: exact source support, conflicting constraints and equal-cost allocations',font=font(21),fill='white')
    dr.text((20,50),'Diagnostic label colours only. No new rendered RGB, palette, or artistic winner.',font=font(16),fill='#ffc97b')
    board.paste(pixels(fine).resize((176,176),Image.Resampling.NEAREST),(24,110));dr.text((24,85),'F103 cell (12,4)',font=font(16),fill='white')
    texts=['64 source samples:','iris 30 / white 27 / lid 2 / canvas 5','visible masses: .468750 / .421875 / .031127 / .078248','107: lid sample -> entire cell becomes lid','108 joint mass-first: cell stays iris; parts allocated jointly']
    for i,t in enumerate(texts):dr.text((230,112+i*29),t,font=font(16),fill='#b7dce9')
    yy=335;dr.text((24,yy),'Same source, different stated constraints (eye 1)',font=font(19),fill='white')
    for j,policy in enumerate(['noCurve','arc4','arc8','relaxedCarrier4']):
        q=results[row['name']][policy]['1'];a=map_labels(d,1,q,'massFirst');board.paste(pixels(a).resize((252,112),Image.Resampling.NEAREST),(24+j*309,yy+60))
        dr.text((24+j*309,yy+32),policy,font=font(16),fill='white');dr.text((24+j*309,yy+180),f"I/W/L = {q['massFirst']['counts']}",font=font(15),fill='#b7dce9')
    qq=results['actual107-frame105']['noCurve']['2'];a,b=qq['massFirstDistinctWitnesses'][:2];h,w=d['support'].shape[1:]
    dr.text((24,yy+235),'F105 / eye 2: two exactly equal mass AND data costs; no scan-order choice',font=font(18),fill='#ffc97b')
    for j,lab in enumerate([a,b]):
        arr=np.zeros((h,w),int)
        for(y,x),p in zip(qq['points'],lab):arr[y,x]=p+3 if p else 0
        board.paste(pixels(arr).resize((324,144),Image.Resampling.NEAREST),(24+j*380,yy+275))
    dr.text((790,yy+282),'Different iris cells (4,5) versus (5,5)',font=font(16),fill='white')
    dr.text((790,yy+317),f"mass L1 = {qq['massFirst']['mass']:.9f}",font=font(16),fill='#b7dce9')
    dr.text((790,yy+350),f"data = {qq['massFirst']['data']:.9f}",font=font(16),fill='#b7dce9')
    dr.text((24,810),'Same-cell locking causes 32 additional infeasible cases; relaxing it is NOT a verified occlusion/render solution.',font=font(16),fill='#ffb678')
    board.save(H/'MINIMUM_CONFLICTS108.png')
    print(json.dumps({'focus':focus,'massCurveConflictCases':len(conflicts),'strictInfeasible':len(endpointFailures),'relaxationRecovered':len(relaxRecovered),'equalCostCases':len(equivalents)}))
if __name__=='__main__':main()
