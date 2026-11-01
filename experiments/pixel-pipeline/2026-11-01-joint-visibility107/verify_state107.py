"""Consolidate exact restoration and observed ON/restored colour differences."""
from pathlib import Path
import sys,json,hashlib,collections
import numpy as np
H=Path(__file__).resolve().parent;R=H.parent
sys.path.insert(0,str(R/'forward-eye102'));from analyse102 import load,buffer
from analyse_capture68 import plane,rgb8
def main():
    cap=H/'capture-final';s=load(sorted(cap.glob('STATE107-*'))[-1]);before=load(cap/'CURRENT102.json');after=load(cap/'POST102.json')
    assert not s.get('error')and not s.get('restorationError')and s['PlayExited']and s['observerRemoved']and s['motionRestoration82']['allRestored']
    assert before['dirty']==after['dirty']and before['input']==after['input']and before['scenes']==after['scenes']and not after['playing']and not after['compiling']
    keys=['options','optionsEnabled','paused','timeScale','captureDeltaTime','runInBackground','playerRunInBackground','graphicsPipelinePath','qualityPipelinePath','buildScenes','domain'];assert all(before[k]==after[k]for k in keys)
    assert not any(x['equal']is False for x in s['nativeComparisons72'])and not s['globalRestoreErrors']
    asset=load(H/'ASSET107_FINAL.json');repo=Path('C:/Users/15352/Documents/work/Fantasy Survival Escape Game')
    assert all(hashlib.sha256((repo/r['path']).read_bytes()).hexdigest()==r['sha']for r in asset['protected32'])and hashlib.sha256((repo/asset['newAsset']).read_bytes()).hexdigest()==asset['sha256']
    hs=[e for e in s['sequencePackets']if e['testStage82'].startswith('partial-hair-')];assert len(hs)==3;p0=Path(hs[0]['output']);p2=Path(hs[2]['output']);differences={}
    for key in ['F-EyeRGBA','F-FinalRGBA','F-EyeOwner','F-FinalOwner','L0-RGBA','L0-UV','L0-LIGHT','S4-rgba','S4-meta']:
        a=plane(p0/(key+'.plane'))[1];b=plane(p2/(key+'.plane'))[1];delta=np.abs(a-b);rows=[]
        for y,x in np.argwhere(np.any(a!=b,axis=-1)):
            rows.append({'xyROIbottom':[int(x),int(y)],'before':a[y,x].tolist(),'after':b[y,x].tolist(),'beforeSRGB8':rgb8(a[y,x,:3]).tolist()if'RGBA'in key or'rgba'in key else None,'afterSRGB8':rgb8(b[y,x,:3]).tolist()if'RGBA'in key or'rgba'in key else None})
        differences[key]={'rawChangedPixels':len(rows),'maxRawDifference':float(delta.max()),'rgb8ChangedPixels':int(np.any(rgb8(a[...,:3])!=rgb8(b[...,:3]),axis=-1).sum())if'RGBA'in key or'rgba'in key else None,'examples':rows[:12]}
    observations=[]
    for p in sorted(cap.glob('eye107-*/partial-hair107/HAIR_OBSERVATION107*')):
        v=load(p);observations.append({'frame':v['frame'],'stage':v['stage'],'rangeDifferences':sum(not x['drawEqual']for x in v['descriptors']),'boundsDifferences':sum(not x['boundsEqual']for x in v['descriptors']),'rendererStates':v['renderers']})
    console=load(H/'capture/PostFinal107_CONSOLE_AFTER.json')['data'];oldConsole=load(H/'capture/CaptureFinal107_CONSOLE_BEFORE.json')['data']
    logkey=lambda x:(x['message'],x['timestamp']);beforeErrors=collections.Counter(logkey(x)for x in oldConsole['logs']if x['type']=='Error');afterErrors=collections.Counter(logkey(x)for x in console['logs']if x['type']=='Error');newErrors=list((afterErrors-beforeErrors).elements());assert not newErrors
    final={'EditUTC':after['utc'],'playing':after['playing'],'compiling':after['compiling'],'dirtyExact':len(after['dirty']),'nativeExact':sum(x['equal']is True for x in s['nativeComparisons72']),'nativeUnavailable':[x for x in s['nativeComparisons72']if x['equal']is None],
      'inputSameObject22ValuesDevicesExact':True,'optionsTimePipelineSceneExact':True,'globalsExact':not s['globalRestoreErrors'],'protectedFilesExact':len(asset['protected32']),'RTBeforeAfter':[s['beforeMemory']['renderTextureCount'],s['afterMemory']['renderTextureCount']],
      'GetTotalAllocatedMemoryLongBeforeAfter':[s['beforeMemory']['allocated'],s['afterMemory']['allocated']],'allocatedTimesUTC':[s['beforeMemory']['utc'],s['afterMemory']['utc']],'allocatedDeltaBytes':s['afterMemory']['allocated']-s['beforeMemory']['allocated'],'allocatedIsNotPhysicalWorkingSet':True,
      'motionRestoration':s['motionRestoration82'],'hairDrawObservations':observations,'hairOnRestoredDifferences':differences,'latestConsoleCounts':{k:console[k]for k in ['errorCount','warningCount','totalCount']},'latestConsoleErrors':[x for x in console['logs']if x['type']=='Error'],'newConsoleErrors':newErrors,'productDefault':77,'newCSharpAssets':0}
    (H/'PRESERVATION107.json').write_text(json.dumps(final,indent=2,ensure_ascii=False)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in final.items()if k not in ['motionRestoration','hairDrawObservations','latestConsoleErrors','hairOnRestoredDifferences']},ensure_ascii=False));print('HAIR COLOUR',json.dumps(differences,ensure_ascii=False)[:2400])
if __name__=='__main__':main()
