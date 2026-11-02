"""Roslyn direct compilation only: no MSBuild/project/analyzer/Unity execution."""
from pathlib import Path
import hashlib,json,subprocess,sys
H=Path(__file__).resolve().parent;OUT=H/'build';OUT.mkdir(exist_ok=True)
DOT=Path(r'C:\Program Files\dotnet\dotnet.exe');CSC=Path(r'C:\Program Files\dotnet\sdk\10.0.402\Roslyn\bincore\csc.dll')
EDITOR=Path(r'C:\Users\15352\Documents\work\6000.5.9f1\Editor\Data')
REF=EDITOR/'NetStandard/ref/2.1.0/netstandard.dll'
def compile_one(name,sources,refs,target='library'):
    args=[str(DOT),'exec',str(CSC),'/nologo','/noconfig','/nostdlib+','/utf8output','/preferreduilang:en-US','/langversion:latest','/nullable:disable','/target:'+target,'/out:'+str(OUT/(name+'.dll'))]
    args+=['/reference:'+str(p)for p in refs];args+=[str(p)for p in sources]
    assert all('/analyzer:'not in x for x in args)
    p=subprocess.run(args,capture_output=True,text=True,encoding='utf-8');(OUT/(name+'.compile.txt')).write_text(p.stdout+p.stderr,encoding='utf-8')
    print(name+': '+(p.stdout+p.stderr).strip());assert p.returncode==0
    return {'name':name,'arguments':args,'sources':{p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in sources},'referenceSHA256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest()for p in refs},'warnings':p.stdout,'executedOutput':False,'GPUOrUnityCalls':0}

def main():
    rows=[compile_one('Prefix24Protocol',[H/'Prefix24Protocol.cs'],[REF])]
    if(H/'Prefix24Host.cs').exists():
        managed=EDITOR/'Managed/UnityEngine';scripts=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game\Library\ScriptAssemblies')
        refs=[REF,EDITOR/'NetStandard/compat/2.1.0/shims/netfx/mscorlib.dll',OUT/'Prefix24Protocol.dll',managed/'UnityEngine.CoreModule.dll',managed/'UnityEditor.CoreModule.dll',managed/'UnityEngine.JSONSerializeModule.dll',scripts/'Unity.InputSystem.dll']
        if(H/'Entry24.cs').exists():refs+=[scripts/'Unity.AI.Assistant.Agent.Dynamic.Extension.Editor.dll']
        sources=[H/'Prefix24Host.cs',H/'CaseLock24.cs']+([H/'Entry24.cs']if(H/'Entry24.cs').exists()else[])
        rows.append(compile_one('Prefix24Host',sources,refs))
        if(H/'COMMANDS.json').exists():
            # Exact future command units compile as ONE assembly; they do not
            # depend on installing Protocol.dll inside the Unity project.
            inline_refs=[p for p in refs if p!=OUT/'Prefix24Protocol.dll']
            for c in json.loads((H/'COMMANDS.json').read_text())['commands']:
                rows.append(compile_one('Stage'+str(c['stage'])+'Command',[H/c['file']],inline_refs))
            # Installed DynamicAssemblyBuilder curates Unity*/netstandard plus
            # object/Enumerable metadata; it does NOT curate arbitrary System.*.
            # Match that narrower runtime-reference regime without loading it.
            mono=EDITOR/'MonoBleedingEdge/lib/mono/unityjit-win32'
            runtime_refs=[mono/'mscorlib.dll',mono/'System.dll',mono/'System.Core.dll',mono/'Facades/netstandard.dll']
            runtime_refs += [p for p in inline_refs if p.name not in {'netstandard.dll','mscorlib.dll'}]
            rows.append(compile_one('Stage1MonoReferences',[H/'STAGE1.command.cs.txt'],runtime_refs))
    (H/'CS_COMPILE.json').write_text(json.dumps({'compiler':str(CSC),'GPUOrUnityCalls':0,'hostAssemblyExecuted':False,'compilations':rows},indent=2)+'\n')
if __name__=='__main__':main()
