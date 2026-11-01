from pathlib import Path
import json,hashlib,subprocess
H=Path(__file__).resolve().parent;R=H.parent;P=Path('C:/Users/15352/Documents/work/Fantasy Survival Escape Game')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*a):return subprocess.check_output(['git','-C',str(P),*a],encoding='utf-8').strip()
def main():
 a=json.loads((R/'live-curve106/ASSET106.json').read_text(encoding='utf-8'));base='bf6f9275bf588dfcc94f6928fc43c128470d181a'
 assert git('rev-parse','HEAD')==base and not git('diff','--cached','--name-only')
 assert git('diff','--name-only').splitlines()==a['modifiedBefore']and all(sha(P/x['path'])==x['sha']for x in a['protected32'])
 current=json.loads((H/'capture/CURRENT102.json').read_text());assert not any(current[x]for x in ['playing','transitioning','compiling','updating'])and len(current['dirty'])==31
 name='Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/ForwardEye107.compute';target=P/name;assert not target.exists()and not Path(str(target)+'.meta').exists()
 text=(H/'ForwardEye107.compute').read_bytes();assert b'ResolveCurve107'in text and b'Contributions107'in text
 target.write_bytes(text);report={'baselineCommit':base,'newAsset':name,'sha256':sha(target),'protected32':a['protected32'],'modifiedBefore':a['modifiedBefore'],'productDefault':77,'CSharpAssetsChanged':False}
 (H/'ASSET107.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({'newAsset':name,'sha256':report['sha256'],'newCSharpAssets':0}))
if __name__=='__main__':main()
