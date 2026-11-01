from pathlib import Path
import hashlib,json,shutil,uuid
HERE=Path(__file__).resolve().parent;REPO=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');DEST=REPO/'Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders'
def main():
 root=HERE/'import91';before=json.loads((root/'BEFORE91.json').read_text());assert not before['playing']and not before['compiling'];native=json.loads((root/'NATIVE_BEFORE73.json').read_text());assert len(native)>=47
 rows=[]
 for p in sorted((HERE/'shaders91').iterdir()):
  assert p.suffix in ['.hlsl','.shader'];target=DEST/p.name;assert not target.exists()and not Path(str(target)+'.meta').exists()
 for p in sorted((HERE/'shaders91').iterdir()):
  target=DEST/p.name;shutil.copy2(p,target);guid=uuid.uuid4().hex;kind='ShaderImporter'if p.suffix=='.shader'else'ShaderIncludeImporter';meta=f'fileFormatVersion: 2\nguid: {guid}\n{kind}:\n  externalObjects: {{}}\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n';Path(str(target)+'.meta').write_text(meta,encoding='utf-8');rows.append({'path':target.relative_to(REPO).as_posix(),'SHA256':hashlib.sha256(target.read_bytes()).hexdigest(),'metaGUID':guid})
 report={'files':rows,'newOnly':True,'productFilesChanged':False,'nativeBackupEntries':len(native),'CSharpAssets':0};(HERE/'INSTALLED_PROBES91.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
