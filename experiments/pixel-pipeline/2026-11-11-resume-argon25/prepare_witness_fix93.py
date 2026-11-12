"""Reimport only the owned shader; explicit if preserves geometric witness.

The prior failed/valid-input packets and original shader bytes remain intact.
"""
from pathlib import Path
import json,hashlib
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face93/witness-fix'
def main():
 for d in ['build','capture','import','final','post/final','console']:(G/d).mkdir(parents=True,exist_ok=True)
 assert not any((G/d/'REQUEST.json').exists()for d in ['capture','import','final']);before=json.loads((G/'BEFORE_PATCH93.json').read_text());new=json.loads((G/'CPU_SHADER93.json').read_text());assert new['shaderSHA256']==hashlib.sha256((H/'ProjectedRibbon93.shader').read_bytes()).hexdigest()
 t=(H/'face93/import/RUN.cs.txt').read_text().replace('resume-20261111\\face93\\import','resume-20261111\\face93\\witness-fix\\import');lines=t.splitlines();old=next(x for x in lines if 'create-only destination already exists'in x);t=t.replace(old,' if(!File.Exists(Target)||!File.Exists(Target+".meta")||!AssetDatabase.IsValidFolder("Assets/EUnityValidation01/ProjectedRibbon93"))throw new InvalidOperationException("93 owned shader destination missing");');old=next(x for x in lines if 'string folder=AssetDatabase.CreateFolder'in x);t=t.replace(old,' if(hash(File.ReadAllBytes(Target))!=hash(bytes)||hash(File.ReadAllBytes(Target+".meta"))!=(string)expected["metaSHA256"]||AssetDatabase.AssetPathToGUID(Target)!=(string)expected["guid"])throw new InvalidOperationException("93 owned shader/meta/GUID changed; no import");AssetDatabase.ImportAsset(Target,ImportAssetOptions.ForceSynchronousImport);');t=t.replace('81 create-only tiny raster shader imported; existing native/input/options preserved; no Play/GPU submission','93 owned shader witness fix imported; existing native/input/options preserved; no CSharp/default/Play/GPU submission');(G/'import/RUN.cs.txt').write_text(t,encoding='utf-8',newline='\n');compile_unity_language(G/'import/RUN.cs.txt',G/'build/import93.dll');(G/'import/EXPECTED.json').write_text(json.dumps({'shaderSHA256':new['shaderSHA256'],'guid':before['guid'],'metaSHA256':before['metaSHA256']},indent=2))
 s=(H/'face93/packed1/capture/RUN.cs.txt').read_text().replace('resume-20261111\\face93\\packed1\\capture','resume-20261111\\face93\\witness-fix\\capture').replace('face93-packed-native-ribbon-','face93-guarded-witness-ribbon-');assert 'bytes.Length>262144'in s and 'EvaluateForm115'not in s;(G/'capture/RUN.cs.txt').write_text(s,encoding='utf-8',newline='\n');compile_unity_language(G/'capture/RUN.cs.txt',G/'build/fixed93.dll')
 for mode in ['final','post/final']:
  s=(H/'face93/packed1'/mode/'RUN.cs.txt').read_text().replace('resume-20261111\\face93\\packed1','resume-20261111\\face93\\witness-fix');(G/mode/'RUN.cs.txt').write_text(s,encoding='utf-8',newline='\n');compile_unity_language(G/mode/'RUN.cs.txt',G/'build'/(mode.replace('/','-')+'93.dll'))
 (G/'console/ARGS.json').write_text((H/'face93/console/ARGS.json').read_text());d={'externalCSharp9Compiled':True,'shaderChangeOnlyExplicitOutParameterGuards':True,'originalShaderSHA':before['beforeSHA256'],'correctedShaderSHA':new['shaderSHA256'],'readbackBytes':259584,'old262144ByteCapUnchanged':True,'initialFrames':1,'newGPUExecuted':False};(G/'CPU_PREPARED93.json').write_text(json.dumps(d,indent=2));print(json.dumps(d))
if __name__=='__main__':main()
