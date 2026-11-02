"""Evidence checks, not a claim that115 runtime rendering passed."""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent
R=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    before=load(H/'DISK_BEFORE115.json');protected={k:sha(R/k)==v for k,v in before['files'].items()}
    assert all(protected.values())
    c=load(H/'Compile115c_REPLY.json')['data'];assert c['isCompilationSuccessful']and c['isExecutionSuccessful']
    k=load(H/'KERNELS115.json');assert len(k['kernels'])==28 and not k['errors']and k['sameDomain']
    ref=load(H/'REFERENCE115.json');assert len(ref['rows'])==12
    cases=[e for r in ref['rows']for e in r['eyes']];assert len(cases)==24 and all(e['sourceFormSurvivors']==1 for e in cases)
    delta=load(H/'DELTA_CLASSIFICATION115.json');assert sum(delta['counts'].values())==len(delta['rows'])==22
    install=load(H/'INSTALL115.json');assert sha(R/install['asset'])==install['sha256']==sha(H/'ForwardEye115.compute')
    seq=H/'eye115-20261102T023401691Z-4f7e54be'
    complete=list(seq.rglob('RAW_COMPLETE*'));assert not complete
    states=sorted(H.glob('STATE115-*.json'));last=load(states[-1]);assert last['stage']=='probe-armed-on-live-head-next-normal-frame'
    assert not(H/'EXIT_COMMAND_RECEIVED115.json').exists()and not(H/'EXIT_API_RETURNED115.json').exists()
    assert load(H/'NormalExit115_ERROR.json')['uncertain']
    out={'schema':'evidence-check115/v1','sourceCompileSuccessful':True,'kernelMetadataChecked':28,'shaderErrors':k['errors'],'CPUReferenceActual113InputCases':len(cases),'CPUReferenceUniqueSourceFormSurvivorCases':len(cases),'CPUReferenceIsNotGPUResult':True,'pairedCounterfactualsClassified':22,'protectedDiskFiles':protected,'newShaderMatchesPreparedSource':True,'productDefault77Changed':False,'AssetsCSharpImported':0,'PlayEntries':1,'completeRuntimeFrames':len(complete),'lastObserverStage':last['stage'],'lastObserverUTC':last['utc'],'runtimeValidationPassed':False,'normalPlayExitOutcome':'uncertain; request dispatched, no command execution receipt','temporaryOptionsRestored':'unverified','dirtyAndInputAfterTrial':'unverified','curveFootprintEndpointRecoveryImplemented':False,'LibraryUpload':False}
    (H/'CHECK115.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in out.items()if k!='protectedDiskFiles'},ensure_ascii=False))
if __name__=='__main__':main()
