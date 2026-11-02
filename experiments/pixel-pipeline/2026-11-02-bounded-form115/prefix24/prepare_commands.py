"""Create four standalone official command source units. Do not submit them."""
from pathlib import Path
import hashlib,json,re
H=Path(__file__).resolve().parent
NS='Unity.AI.Assistant.Agent.Dynamic.Extension.Editor'
def main():
    uses=[];bodies=[]
    dependencies=['Prefix24Protocol.cs','CaseLock24.cs','Prefix24Host.cs','metadata24/Json58Linear24.cs','PrefixMetadata24.cs']
    for name in dependencies:
        s=(H/name).read_text(encoding='utf-8')
        for line in re.findall(r'(?m)^using [^;\n]+;',s):
            if line not in uses:uses.append(line)
        bodies.append(re.sub(r'(?m)^using [^;\n]+;\r?\n?','',s))
    rows=[]
    for stage in range(1,5):
        entry='namespace '+NS+' { public sealed class CommandScript : IRunCommand { public void Execute(ExecutionResult result) { global::Prefix24.Prefix24Host.Start('+str(stage)+',message=>result.Log(message)); } } }\n'
        # Installed MoveToNamespace preserves code whose FIRST namespace already
        # matches the command namespace. Other Prefix24 namespaces remain global.
        source='\n'.join(uses)+'\n'+entry+'\n'.join(bodies)
        assert re.search(r'namespace\s+([\w.]+)',source)[1]==NS
        for bad in ['System.Runtime.InteropServices','System.Reflection','System.Diagnostics','System.Net','EnterPlaymode','EditorApplication.update','Shader.SetGlobal','AssetDatabase.ImportAsset','WaitForCompletion','EvaluateForm115','BoundRun115']:
            assert bad not in source,bad
        assert source.count('shader.Dispatch(')==1 and source.count('AsyncGPUReadback.Request(')==1
        assert 'Protocol24.Decode=PrefixMetadata24.Decode;'in source
        assert 'value is Receipt24?PrefixMetadata24.ReceiptBytes'in source
        assert 'JsonUtility.FromJson('not in source
        file=H/('STAGE'+str(stage)+'.command.cs.txt');file.write_bytes(source.encode())
        rows.append({'stage':stage,'file':file.name,'SHA256':hashlib.sha256(file.read_bytes()).hexdigest(),'dispatchSites':1,'autoNextStage':False,'submitted':False})
    (H/'COMMANDS.json').write_text(json.dumps({'firstNamespaceCompatibleWithInstalledBuilder':True,'noUnauthorizedNamespaceUsageInLiveCommand':True,'interopOnlyInExternalCpuAbiTest':True,'UnityCalls':0,'nestedMetadataBoundary':'PrefixMetadata24.Decode/ReceiptBytes + bounded Json58Linear66','dependencies':{p:hashlib.sha256((H/p).read_bytes()).hexdigest()for p in dependencies},'commands':rows,'existingActualStage1Evidence':'runs/'+json.loads((H/'CASE.json').read_text())['RunId']+'/stage-01/COMPLETE.json','newSourcesSubmitted':False},indent=2)+'\n')
    print(json.dumps(rows))
if __name__=='__main__':main()
