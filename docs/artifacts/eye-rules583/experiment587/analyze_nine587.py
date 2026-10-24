from pathlib import Path
import json,csv
R=Path(__file__).parent
def cells(p,old=False):
    return {(int(q['cellX' if old else 'x']),int(q['cellY' if old else 'y']),q['buffer']):tuple(float(q[k]) for k in ['r','g','b','a']) for q in csv.DictReader(p.open(),delimiter='\t')}
mapping=[(2,0,'Eight587',0),(2,1,'Eight587',1),(2,2,'Eight587',2),(5,0,'Eight587',3),(5,1,'First587B',0),(5,2,'Eight587',4),(16,0,'Eight587',5),(16,1,'Eight587',6),(16,2,'Eight587',7)]
ref=json.loads((R.with_name('EyeFilter586')/'Stage586/FILTER586.json').read_text())['records']
results=[]
for case,frame,run,index in mapping:
    root=R/'Runtime587'/run;p=root/f'{index:03}'
    off=cells(Path(str(p)+'_OFF_CELLS587.tsv'));on=cells(Path(str(p)+'_ON_CELLS587.tsv'))
    oldroot=R.with_name('EyeFollow584')/'Runtime584'/{2:'OneCase2',5:'OneCase5B',16:'OneCase16'}[case]
    baseline=cells(oldroot/f'{frame:03}_ON_CELLS582.tsv',True)
    keys=[k for k in off if k[2] in ['EyeVisible','EyeIntrinsic']]
    parity=[k for k in keys if off[k]!=baseline[k]]
    changes=[dict(cell=list(k[:2]),buffer=k[2],before=off[k],after=on[k]) for k in off if off[k]!=on[k]]
    intrinsic=[q for q in changes if q['buffer']=='EyeIntrinsic']
    iriswhite=[q for q in changes if q['buffer']=='EyeVisible' and (1<=q['before'][0]<=4 or 1<=q['after'][0]<=4)]
    area=next(q for q in csv.DictReader(Path(str(p)+'_ON_AREA587.tsv').open(),delimiter='\t') if q['eyeID']=='2')
    reference=next(q for q in ref if q['case']==case and q['frame']==frame)
    visible={}
    for name,cs in [('OFF',off),('ON',on)]:
        visible[name]=[list(k[:2]) for k,v in cs.items() if k[2]=='EyeVisible' and v[1]==2 and v[0] in [5,7]]
    a=float(area['area']);err=float(area['errorEstimate'])
    results.append(dict(case=case,frame=frame,run=run,index=index,baselineParityChanges=len(parity),
        intrinsicChanges=intrinsic,irisWhiteFeatureChanges=iriswhite,area=a,areaReference=reference['area128'],
        referenceDelta=a-reference['area128'],interlacedErrorEstimate=err,budget=int(a+.5),
        thresholdIntervalSeparated=abs(a-.5)>err,visible=visible,changes=changes,textureBytes=int(area['textureBytes'])))
summary=dict(poses=9,records=results,baselineVisibleIntrinsicChanges=sum(q['baselineParityChanges'] for q in results),
    intrinsicChanges=sum(len(q['intrinsicChanges']) for q in results),irisWhiteFeatureChanges=sum(len(q['irisWhiteFeatureChanges']) for q in results),
    maxAreaReferenceDelta=max(abs(q['referenceDelta']) for q in results),maxInterlacedErrorEstimate=max(q['interlacedErrorEstimate'] for q in results),
    budgetByCase={str(case):[q['budget'] for q in results if q['case']==case] for case in [2,5,16]},
    newActualRotationFrames=0,allFrozenRunsRestored=all(json.loads((R/'Runtime587'/run/'status.json').read_text())['restored'] for run in ['Eight587','First587B']))
(R/'NINE_RESULT587.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k!='records'},indent=2))
for q in results:print(json.dumps({k:q[k] for k in ['case','frame','area','referenceDelta','interlacedErrorEstimate','visible','irisWhiteFeatureChanges']}))
