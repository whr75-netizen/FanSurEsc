from pathlib import Path
import re,sys
HERE=Path(__file__).resolve().parent
mode=sys.argv[1]
base=HERE.parent/'source-palette58'
if not base.exists():base=HERE.parent/'2026-10-31-source-palette58'
files=[HERE/'Json58Linear66.cs']
if mode in ('Save66','Recovered66','Finish66'):files.append(HERE/'SerializedContent66.cs')
deps=HERE.parent/'uv-features64'
if not deps.exists():deps=HERE.parent/'2026-10-31-uv-features64'
if mode in ('Global66','Capture66','CaptureRetry66'):files.append(deps/'GlobalJournal64.cs')
if mode in ('Capture66','CaptureRetry66'):files.append(deps/'CpuSourceCapture64.cs')
files.append(HERE/(mode+'.cs'))
usings=[];body=[]
for p in files:
 s=p.read_text(encoding='utf-8-sig')
 for u in re.findall(r'(?m)^using [^;\n]+;',s):
  if u not in usings:usings.append(u)
 body.append(re.sub(r'(?m)^using [^;\n]+;\r?\n?','',s))
if mode=='ScopeCheck66':
 source=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game\Assets\EUnityValidation01\ClothRegion524\Runtime\ClothRegion524.cs').read_text(encoding='utf-8-sig')
 start=source.index('    sealed class BodyScopeResources551')
 end=source.index('    static readonly Dictionary<Full319View335',start)
 owner=source[start:end].rstrip()
 owner=owner.replace('public Mesh Mesh','public UnityEngine.Mesh Mesh').replace('public Transform Head','public UnityEngine.Transform Head').replace('Commit(Mesh mesh, Transform head','Commit(UnityEngine.Mesh mesh, UnityEngine.Transform head')
 body[-1]=body[-1].replace('// EXTRACT_OWNER65',owner)
(HERE/('RUN_'+mode+'.cs.txt')).write_text('\n'.join(usings)+'\n'+'\n'.join(body),encoding='utf-8')
print('Prepared outside Assets:',mode)
