"""CPU compilation/replay only. Never calls Unity or a graphics compiler/device."""
from pathlib import Path
import hashlib,json,shutil,subprocess,tempfile,sys
import numpy as np

H=Path(__file__).resolve().parent
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(args):
    r=subprocess.run(args,capture_output=True,text=True,encoding='utf-8-sig',errors='replace',timeout=60)
    if r.returncode:raise RuntimeError(r.stdout+'\n'+r.stderr)
    return r.stdout
def freeze_inputs():
    old=H.parent;f=load(old/'SOURCE58.json');gpu=load(old/'GPU58.json')
    fixture={'scope':'Test-only confirmed region contracts over saved58 samples. These are NOT confirmed actual face segmentation labels.',
        'records':f['records'],'rows':gpu['rows'],'faceProbes':[]}
    src=old.parent/'source-regions103/part3/hierarchy.npz';labelsPath=old.parent/'source-regions104/part3/geodesic-labels.npz'
    with np.load(src) as data:rgba=data['rgba'].copy();mask=data['mask'].copy()
    with np.load(labelsPath) as data:labels=data['labels'].copy()
    # Actual source coordinates already used by104; no new classifier/threshold.
    for x,y in [(503,9),(461,760),(382,704),(380,704),(384,704)]:
        fixture['faceProbes'].append({'id':f'104/native-crop/{x},{y}','regionId':f'unconfirmed104/parent{int(labels[y,x])}',
            'rgba8':rgba[y,x].tolist(),'cropXY':[x,y]})
    # Read one existing uncertain-colour boundary from the saved partition; do not
    # claim its native texture transition is definitively AA rather than paint.
    edge=mask[:,1:]&mask[:,:-1]&(labels[:,1:]!=labels[:,:-1])&(labels[:,1:]>=0)&(labels[:,:-1]>=0)
    positions=np.argwhere(edge)
    y,x=map(int,positions[len(positions)//2]);
    for xx in [x,x+1]:fixture['faceProbes'].append({'id':f'104/existing-transition/{xx},{y}',
        'regionId':f'unconfirmed104/parent{int(labels[y,xx])}','rgba8':rgba[y,xx].tolist(),'cropXY':[xx,y]})
    (H/'FIXTURE58.json').write_text(json.dumps(fixture,ensure_ascii=False,indent=2),encoding='utf-8')
    origins={'source58SHA256':sha(old/'SOURCE58.json'),'actualGPU58SHA256':sha(old/'GPU58.json'),
        'sourceHierarchySHA256':sha(src),'savedLabelSHA256':sha(labelsPath),'fixtureSHA256':sha(H/'FIXTURE58.json'),
        'scope':'Reduced saved-input CPU fixture; not a new capture. Test-only confirmed bindings do not confirm actual face regions.'}
    (H/'INPUT_ORIGINS.json').write_text(json.dumps(origins,indent=2),encoding='utf-8')
def main():
    basis=load(H/'BASIS.json');repo=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
    if '--freeze-inputs' in sys.argv:freeze_inputs()
    fixture=load(H/'FIXTURE58.json');origins=load(H/'INPUT_ORIGINS.json')
    assert sha(H/'FIXTURE58.json')==origins['fixtureSHA256'],'Frozen source evidence changed'
    # The .ps1 launcher was blocked before execution by OS script policy.
    # Leave that policy untouched; use the installed ordinary C# compiler for
    # this standalone CPU program (no PowerShell script/Unity assemblies).
    csc=Path(r'C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe')
    with tempfile.TemporaryDirectory(prefix='face-lut-csharp-') as temp:
        exe=Path(temp)/'RegionBridgeCpu.exe'
        compiler=run([str(csc),'/nologo','/utf8output','/codepage:65001','/target:exe','/r:System.Core.dll','/r:System.Web.Extensions.dll',
            '/out:'+str(exe),str(H/'candidate/SourcePalette58.cs'),str(H/'ResolvedRegionInput.cs'),str(H/'CpuTests.cs')])
        cpu=json.loads(run([str(exe),str(H/'FIXTURE58.json')]).strip())
    # Run the EXISTING palette54 suite unchanged in a temporary copy: original
    # RESULTS/PACKET and all previous evidence stay untouched.
    suite=H/'reuse54'
    with tempfile.TemporaryDirectory(prefix='face-lut-cpu-') as temp:
        target=Path(temp)
        for name in ['test.cjs','source-palette.cjs','colour-math.cjs','adapter.cjs','fixtures.json']:shutil.copyfile(suite/name,target/name)
        run(['node',str(target/'test.cjs')]);oldTests=load(target/'RESULTS.json')
        oldSummary={k:oldTests[k] for k in ['cases','passed','paletteOutsideCount','sourceDomainsAutomaticallySegmented','regionShapeCorrected','UnityRun','HLSLCompiled','activeProductChanged']}
    initial=(H/'candidate/FaceSceneLight335.hlsl').read_text(encoding='utf-8')
    body=(H/'candidate/BodyPalette302.hlsl').read_text(encoding='utf-8')
    final=(H/'candidate/RestoreStyle335.compute').read_text(encoding='utf-8')
    start=final.index('[numthreads(8,8,1)]void ApplyShadeBoundary')
    branch=final[start:]
    assert initial.index('TryResolvedRegionPalette(stagePixel')<initial.index('return colour*factor;')
    assert 'SurfaceLayerOutput335(baseColour,factor,continuous,level,(uint2)input.pos.xy)' in body
    assert branch.index('TryResolvedRegionPalette')<branch.index('if(_ShadeApply335==0)')<branch.index('if(!ShadeRole335')<branch.index('if(abs(old-q)<.01)')
    assert 'colour.rgb=paletteRGB' in branch and 'factor.rgb=1;' in branch
    for name,digest in basis['reused'].items():
        path=H/name if name.startswith('reuse54/') else H/'candidate'/name
        assert sha(path)==digest,'Reused original changed: '+name
    for path,entry in basis['product'].items():assert sha(repo/path)==entry['sha256'],path+' product changed'
    for path,digest in basis['preservedTrackedChanges'].items():assert sha(repo/path)==digest,path+' existing change lost'
    # Flat-parent shortcut remains a failing actual-source counterexample.
    probes=fixture['faceProbes'][2:5]
    assert len({tuple(p['rgba8'][:3])for p in probes})==3 and len({p['regionId']for p in probes})==1
    report={'scope':'CPU-only candidate; no Unity/import/GPU/Play; product77 unchanged',
        'csharp':cpu,'compiler':{'path':str(csc),'output':compiler,'GPUDeviceUsed':False},
        'unusedPowerShellLauncher':'OS execution policy denied before script execution; policy unchanged; no retry',
        'existingPalette54Suite':oldSummary,
        'static':{'initialLUTBeforeLegacyRGBMultiply':True,'finalLUTBeforeApplyRoleAndOldEqualsQ':True,'candidateBodyCallUpdated':True,
            'existingMathByteIdentical':True,'currentProductFilesUnchanged':len(basis['product']),'preexistingTrackedChangesUnchanged':len(basis['preservedTrackedChanges'])},
        'actual104Counterexample':{'sameParent':probes[0]['regionId'],'sourceColours':[p['rgba8']for p in probes],
            'oneAnchorWouldEraseSourceContrast':True,'confirmedFaceBindingsAvailable':0,'probeCount':len(fixture['faceProbes']),
            'sourceHierarchySHA256':origins['sourceHierarchySHA256'],'savedLabelSHA256':origins['savedLabelSHA256'],'transitionMeaning':'not confirmed AA/paint; never promoted'},
        'limits':['No full-face confirmed source-region map or region-to-family mapping supplied.',
            '58 replay uses native primitive samples plus diagnostic g/k, not current live renderer face cells.',
            'AA/partial alpha, outlines, post-LUT RGB transforms and final frame palette membership require separate unimplemented contracts.',
            'No HLSL/Unity compilation or actual GPU candidate execution in this task.'],
        'files':{p.relative_to(H).as_posix():sha(p)for p in H.rglob('*')if p.is_file() and p.name not in ['RESULT.json','publish.py','COMMIT_RECEIPT.json']}}
    if '--check-only' not in sys.argv:(H/'RESULT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'csharpTests':cpu['tests'],'palette54Tests':oldSummary['cases'],'saved58Resolved':cpu['resolved'],
        'oldEqualsQ':cpu['oldEqualsQ'],'actualFaceBindings':0,'productModified':False,'GPUExecuted':False}))
if __name__=='__main__':main()
