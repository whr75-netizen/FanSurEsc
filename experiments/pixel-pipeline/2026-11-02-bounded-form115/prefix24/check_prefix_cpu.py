"""Check prepared source/evidence only. Never load Unity/host DLLs or a GPU API."""
from pathlib import Path
import hashlib,json,re

H=Path(__file__).resolve().parent
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(name):return json.loads((H/name).read_text(encoding='utf-8'))

def main():
    module=read('MODULE.json');hlsl=read('HLSL_COMPILE.json');case=read('CASE.json')
    host=(H/'Prefix24Host.cs').read_text(encoding='utf-8')
    protocol=(H/'Prefix24Protocol.cs').read_text(encoding='utf-8')
    shader=(H/'Prefix24.compute').read_text(encoding='utf-8')
    expected=['BuildSubsets113','Enumerate113','Reduce113','Write113']
    assert re.findall(r'^#pragma kernel (\w+)',shader,re.M)==expected==module['entrypoints']
    assert module['functionBodiesExactlyPreserved'] and module['privateSourceArrays']==0
    assert sha(H/'Prefix24.compute')==module['sourceSHA256']==hlsl['sourceSHA256']==case['ShaderSha256']
    assert not hlsl['GPUDeviceCreated'] and hlsl['GPUDispatches']==0 and hlsl['UnityCalls']==0
    assert not hlsl['GPUDriverOrDeviceDLLsLoaded']
    strides={'_Cells113':16,'_CellTags113':16,'_Frame113':16,'_Points113':16,'_Subsets113':32,'_Groups113':48,'_Best113':48,'_CurveColour106':16,'_CurveIdentity106':16,'_CurveDecision106':16,'_CurveAudit106':16}
    rows=[]
    for i,k in enumerate(hlsl['kernels']):
        assert k['entry']==expected[i] and not k['audit']['privateArrayDeclarations']
        assert k['audit']['threads']==([8,8,1]if i==3 else[64,1,1])
        bindings=[b for b in k['bindings']if b['Type']==6]
        assert len(bindings)==[5,3,2,8][i]
        for b in bindings:
            assert b['BindCount']==1 and b['NumSamples']==strides[b['Name']]
            assert k['audit']['structuredStridesBySlot']['u'+str(b['BindPoint'])]==strides[b['Name']]
        rows.append({'stage':i+1,'kernel':k['entry'],'dispatch':[[1,2,1],[32,1,1],[1,1,1],[1,1,1]][i],
          'uavs':len(bindings),'allocatedStructuredBytes':[591616,3671040,3145824,68448][i],
          'readbackBytes':[4096,1536,48,9216][i],'privateArrays':0})
    commands=read('COMMANDS.json')
    for name,digest in commands['dependencies'].items():assert sha(H/name)==digest,name
    assert host.count('shader.Dispatch(')==1 and host.count('AsyncGPUReadback.Request(')==1
    for c in commands['commands']:
        text=(H/c['file']).read_text(encoding='utf-8')
        assert sha(H/c['file'])==c['SHA256'] and not c['submitted'] and not c['autoNextStage']
        assert 'Protocol24.Decode=PrefixMetadata24.Decode;'in text and 'value is Receipt24?PrefixMetadata24.ReceiptBytes'in text
        assert 'JsonUtility.FromJson('not in text
        assert 'Prefix24Host.Start('+str(c['stage'])+','in text
        assert re.search(r'namespace\s+([\w.]+)',text)[1]=='Unity.AI.Assistant.Agent.Dynamic.Extension.Editor'
        for bad in ['EvaluateForm115','BoundRun115','Forward115','RegionDriver115','AfterCanvas','EditorApplication.update','EditorApplication.delayCall','Shader.SetGlobal','WaitForCompletion','EnterPlaymode','ExitPlaymode','SaveAssets','ImportAsset','InputSystem.settings =','File.Move','File.Delete','System.Reflection','System.Runtime.InteropServices','using System.Runtime.Serialization','DataContractJsonSerializer','System.Diagnostics','System.Net']:
            assert bad not in text,bad
    for part in ['void Received(', 'void MaybeFinish(', 'void Finish(']:
        body=host[host.index(part):]
        assert 'shader.Dispatch('not in body and 'Begin();'not in body and 'Prepare();'not in body
    cs=read('CS_COMPILE.json')
    assert cs['GPUOrUnityCalls']==0 and not cs['hostAssemblyExecuted'] and len(cs['compilations'])==7
    assert any(x['name']=='Stage1MonoReferences'for x in cs['compilations'])
    for c in cs['compilations']:
        assert not c['warnings'].strip() and not c['executedOutput']
        for name,digest in c['sources'].items():
            paths=[Path(x)for x in c['arguments']if not x.startswith('/')and Path(x).name==name]
            assert len(paths)==1 and sha(paths[0])==digest,(c['name'],name)
    tests=read('CPU_TEST_LATEST.json')['summary']
    assert tests['Passed']==28 and not tests['ProductionRunRootCreated'] and tests['ProductionRunBytesPreserved'] and tests['ActualGpuPredecessorValidated'] and not tests['HostAssemblyExecuted'] and not tests['GPUDeviceCreated'] and not tests['GPUDriverModules']
    for f in case['InputFiles']:
        p=H/'fixture'/f['File'];assert p.stat().st_size==f['Bytes'] and sha(p)==f['Sha256']
    lock=(H/'CaseLock24.cs').read_text(encoding='utf-8')
    assert sha(H/'CASE.json')in lock and case['RunId']in lock
    prior_stages=[]
    for stage in [1,2]:
        directory=H/'runs'/case['RunId']/('stage-'+str(stage).zfill(2))
        if not directory.exists():continue
        receipt=json.loads((directory/'COMPLETE.json').read_text())
        assert receipt['Success']and receipt['ExecutionKind']=='gpu-prefix'and receipt['StateEqual']and receipt['ResourcesReleased']and receipt['DispatchCalls']==1
        assert receipt['SourceId']==case['SourceId']and receipt['CaseSha256']==sha(H/'CASE.json')and not(directory/'FAILED.json').exists()and not list(directory.glob('PENDING-*.json'))
        for output in receipt['Outputs']:
            assert output['File']==output['Name']+'.bin'and sha(directory/output['File'])==output['Sha256']
            spec=next(x for x in case['InputFiles']if x['Name']==output['Name']and x['Stage']==stage);assert output['Sha256']==spec['Sha256']
        prior_stages.append(stage)
    assert prior_stages==[1,2] and not(H/'runs'/case['RunId']/'stage-03').exists()
    request=json.loads((H/'enumerate24/Stage2Prefix24_REQUEST.json').read_text());assert request['sourceSHA256']==commands['commands'][1]['SHA256']
    result={'scope':'Current command-source CPU validation; existing actual GPU stages1/2 evidence read only','sourcePreparationComplete':True,'GPUOrUnityCalls':0,'GPUHostExecutedThisCheck':False,'AssetsImportedThisCheck':False,'currentCommandVersionsSubmitted':[2],'priorActualGpuStagesValidated':prior_stages,
      'CPUCompilations':{'HLSLPreviouslyCompiledSameSource':4,'CSharp':7,'CSharpWarnings':0,'existingHlslSignedUnsignedWarning':'X3203 (original Enumerate expression; fixed eye0 fixture)'},
      'CPUTestGroups':tests['Passed'],'stages':rows,
      'lifetime':'One stage owns clone/buffers. No auto-next. All issued readbacks settled before release. Unknown submission/request retains ownership and blocks completion/replay.',
      'state':'Read-only before/after public Editor/options/scene/pipeline/time/input/devices/dirty/global summary; this host changes none of those. Any mismatch blocks completion; no guessed restoration.',
      'notIntegrated':['16-subsample depth transport','socket-diameter normalization','curve midpoint recovery','renderer final composition','product77'],
      'remainingConditions':['Reduce/Write have not been approved or run; no Unity/GPU calls in this check','The existing shader was imported in f919290b; its source remains unchanged','Fresh Editor/process/project/native/input preflight before any future Unity action','Completed stages1/2 cannot be replayed; a future stage3 must validate actual stage2 complete receipt/output bytes and absence of FAILED/PENDING','Prior D3D11 reset root cause remains unresolved; CPU compilation is not device/driver safety evidence'],
      'caseSHA256':sha(H/'CASE.json'),'shaderSHA256':sha(H/'Prefix24.compute')}
    (H/'PREFIX24_CHECK.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
