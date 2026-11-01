from pathlib import Path
import json,hashlib,shutil,uuid
HERE=Path(__file__).resolve().parent;REPO=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');DEST=REPO/'Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assert(HERE/'import91b/BEFORE91.json').exists();native=json.loads((HERE/'import91b/NATIVE_BEFORE73.json').read_text());assert len(native)>=47;previous=json.loads((HERE/'INSTALLED_PROBES91.json').read_text())
 for row in previous['files']:assert sha(REPO/row['path'])==row['SHA256'],'Concurrent source edit: '+row['path']
 files=[]
 for name in ['OriginalProducer91.shader','RetargetProducer91.shader','CurrentBacking91.shader','OwnedAmbient91.hlsl']:
  source=HERE/'shaders91'/name;target=DEST/name
  if target.exists():
   old=HERE/'import91b'/('DISK_BEFORE-'+name);assert not old.exists();shutil.copy2(target,old)
  else:
   assert not Path(str(target)+'.meta').exists();Path(str(target)+'.meta').write_text('fileFormatVersion: 2\nguid: '+uuid.uuid4().hex+'\nShaderIncludeImporter:\n  externalObjects: {}\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n',encoding='utf-8')
  shutil.copy2(source,target);files.append({'path':target.relative_to(REPO).as_posix(),'SHA256':sha(target)})
 (HERE/'INSTALLED_BOUND91.json').write_text(json.dumps({'files':files,'onlyOwn91ShadersUpdated':True,'userOrProductSourceModified':False},indent=2)+'\n');print('Owned SH-input variant installed; C# Assets unchanged.')
if __name__=='__main__':main()
