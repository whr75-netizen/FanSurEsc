from pathlib import Path
import json,hashlib,re,subprocess
H=Path(__file__).resolve().parent;F=H.parent/'gpu-form115'
if not F.exists():F=H.parent/'2026-11-02-gpu-form115'
R=next((p for p in H.parents if(p/'.git').exists()),Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    cache=F if(F/'NATIVE_BEFORE73.json').exists()else H/'recovery'
    rec=F/'recovery-read'if(F/'recovery-read/RECOVERY_FINDINGS115.json').exists()else H/'recovery'
    before=json.loads((cache/'NATIVE_BEFORE73.json').read_text());protected=json.loads((F/'DISK_BEFORE115.json').read_text());summary=json.loads((rec/'RECOVERY_FINDINGS115.json').read_text());rows=[]
    for unavailable in summary['nativeUnavailable']:
        path=unavailable['path'];p=R/path;meta=Path(str(p)+'.meta');old=next(x for x in before if x['path']==path and x['type']==unavailable['type']);native=json.loads((cache/old['snapshot']).read_text());root=next(iter(native.values()));parsed=root.get('m_ParsedForm',{});name=parsed.get('m_Name');declared=re.search(r'\bShader\s+"([^"]+)"',p.read_text(encoding='utf-8-sig'));guid=re.search(r'^guid:\s*(\w+)',meta.read_text(encoding='utf-8-sig'),re.M).group(1)
        show=subprocess.run(['git','-C',str(R),'show',protected['HEAD']+':'+path],capture_output=True)
        rows.append({'path':path,'sourceExists':p.exists(),'metaExists':meta.exists(),'metaGUID':guid,'sourceSHA256':sha(p),'sourceLogicalShaderName':declared.group(1)if declared else None,'beforeNativeLogicalShaderName':name,'logicalNameMatchesBeforeNative':bool(declared and name==declared.group(1)),'protectedBeforeTrial':path in protected['files'],'beforeTrialProtectedHashMatches':sha(p)==protected['files'][path]if path in protected['files']else None,'trackedAtBeforeCommit':show.returncode==0,'matchesBeforeCommitBlob':show.stdout==p.read_bytes()if show.returncode==0 else None,'matchesBeforeCommitIgnoringCRLF':show.stdout.replace(b'\r\n',b'\n')==p.read_bytes().replace(b'\r\n',b'\n')if show.returncode==0 else None,'nativeObjectCurrentlyLoaded':False,'compiledNativeEquivalenceEstablished':False,'assetDatabaseRegistrationQueried':False,'importOrCompileRequested':False})
    out={'schema':'unloaded-shader-disk115/v1','rows':rows,'note':'Disk declarations/meta can be read without importing. GUID metadata alone is not a fresh AssetDatabase/compiled-native confirmation.'}
    (H/'UNLOADED_SHADER_DISK115.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(out,ensure_ascii=False))
if __name__=='__main__':main()
