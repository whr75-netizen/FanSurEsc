from pathlib import Path
import hashlib,json,subprocess,uuid
H=Path(__file__).resolve().parent;P=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
before=json.loads((H.parent/'live-underlay98/ASSET_CREATE98.json').read_text(encoding='utf-8'))['protected32']
rows=[]
for r in before:
 if isinstance(r,str): p=P/r;rows.append({'path':r,'sha':sha(p)})
 else:
  key=next(k for k in ('path','file')if k in r);p=P/r[key];rows.append({'path':r[key],'sha':sha(p)})
modified=subprocess.check_output(['git','diff','--name-only'],cwd=P,encoding='utf-8').splitlines()
dest=P/'Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/ForwardEye102.compute'
assert not dest.exists() and not dest.with_suffix('.compute.meta').exists()
meta='fileFormatVersion: 2\nguid: '+uuid.uuid4().hex+'\nComputeShaderImporter:\n  externalObjects: {}\n  defaultTextures: []\n  nonModifiableTextures: []\n  userData:\n  assetBundleName:\n  assetBundleVariant:\n'
with dest.open('xb') as f:f.write((H/'ForwardEye102.compute').read_bytes())
with dest.with_suffix('.compute.meta').open('x',encoding='utf-8',newline='\n')as f:f.write(meta)
record={'protected32':rows,'modifiedBefore':modified,'newAsset':str(dest.relative_to(P)),'shaderSHA':sha(dest),'metaSHA':sha(dest.with_suffix('.compute.meta')),'existingFilesOverwritten':0}
(H/'ASSET102.json').write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'newFiles':2,'protected':len(rows),'modifiedBefore':len(modified),'shaderSHA':sha(dest)}))
