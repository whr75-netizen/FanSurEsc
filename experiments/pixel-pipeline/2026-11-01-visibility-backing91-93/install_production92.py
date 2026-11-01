from pathlib import Path
import json,hashlib,shutil,uuid
HERE=Path(__file__).resolve().parent;REPO=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game')
def main():
 assert(HERE/'import92/BEFORE91.json').exists();source=HERE/'shaders91/ProductionTrace92.shader';target=REPO/'Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/ProductionTrace92.shader';assert not target.exists()and not Path(str(target)+'.meta').exists();shutil.copy2(source,target);meta=Path(str(target)+'.meta');meta.write_text('fileFormatVersion: 2\nguid: '+uuid.uuid4().hex+'\nShaderImporter:\n  externalObjects: {}\n  userData: \n  assetBundleName: \n  assetBundleVariant: \n',encoding='utf-8');(HERE/'INSTALLED_PRODUCTION92.json').write_text(json.dumps({'path':target.relative_to(REPO).as_posix(),'SHA256':hashlib.sha256(target.read_bytes()).hexdigest(),'newOnly':True,'runtimeProductionTraceNotDefault':True},indent=2)+'\n');print('One isolated source-metadata shader added; defaults unchanged.')
if __name__=='__main__':main()
