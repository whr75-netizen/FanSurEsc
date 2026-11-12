"""Reuse existing91 shader/raster, only source table and CPU palette preparation.

No Assets import, new shader, compute dispatch, default switch or GPU expected
RGB upload. Runtime C# builds its own LUT from native source references.
"""
from pathlib import Path
import json,hashlib,numpy as np
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face92/gpu'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 for d in ['capture','build','final','post/final','console']:(G/d).mkdir(parents=True,exist_ok=True)
 assert not any((G/d/'REQUEST.json').exists()for d in ['capture','final']);assert json.loads((H/'face92/CPU_PALETTE_PORT92.json').read_text())['PythonCSharpExact'];info=json.loads((H/'face28/SOURCE_INPUT28.json').read_text());z=np.load(H/'face92/SOURCE_VALUE92.npz');a=np.zeros((1024,1024),'<f4');ox,oy=info['cropOffset'];h,w=z['mask'].shape;a[oy:oy+h,ox:ox+w]=np.where(z['mask'],z['labels']+1,0);a[::-1].copy().tofile(H/'face92/ADDRESS92.r32');table=json.loads((H/'face88/TABLE89.json').read_text());table.update({'sourceValueCount':len(z['referenceIndices']),'sourceValueVersion':92,'nativeContrasts':3822,'addressSHA':sha(H/'face92/ADDRESS92.r32'),'referenceSHA':sha(H/'face92/REFERENCES92.rgb'),'ordersSHA':sha(H/'face92/ORDERS92.i32'),'contrastSHA':sha(H/'face92/CONTRAST92.i32'),'controlSHA':sha(H/'face92/PALETTE92.rgb'),'controlMeaning':'unconstrained-source92/Y-only floor-ceil, not old-unit88'});(H/'face92/TABLE92.json').write_text(json.dumps(table,indent=2))
 s=(H/'face91/capture/RUN.cs.txt').read_text();pos=s.index('// Pure CPU construction. Final runtime RGB');s=s[:pos];s+='\n'+(H/'PaletteRuntime89.cs').read_text()+'\n'+(H/'PaletteConstraints92.cs').read_text()+'\n'+(H/'SourceField89.cs.txt').read_text();s=s.replace('resume-20261111\\face91\\capture','resume-20261111\\face92\\gpu\\capture').replace('face91-current-independent-history-','face92-native-contrast-palette-').replace('motion40.FirstTarget,64,16,motion40.Snapshot','motion40.FirstTarget,6,1,motion40.Snapshot').replace('["plannedSourceFrames"]=64','["plannedSourceFrames"]=6')
 old='field89=new SourceField89(Path.GetFullPath(Path.Combine(root,"..","face88")),eye,width,height,evidence89);';assert s.count(old)==1;s=s.replace(old,'field89=new SourceField89(Path.GetFullPath(Path.Combine(root,"..","face92")),eye,width,height,evidence89,new SourceFiles89{table="TABLE92.json",reference="REFERENCES92.rgb",order="ORDERS92.i32",address="ADDRESS92.r32",control="PALETTE92.rgb",contrast="CONTRAST92.i32"});');assert 'EvaluateForm115'not in s and 'BoundRun115'not in s and s.count('motion40.FirstTarget,6,1,motion40.Snapshot')==1
 (G/'capture/RUN.cs.txt').write_text(s,encoding='utf-8',newline='\n');compile_unity_language(G/'capture/RUN.cs.txt',G/'build/capture92.dll')
 for mode in ['final','post/final']:
  t=(H/'face91'/mode/'RUN.cs.txt').read_text().replace('resume-20261111\\face91','resume-20261111\\face92\\gpu');(G/mode/'RUN.cs.txt').write_text(t,encoding='utf-8',newline='\n');compile_unity_language(G/mode/'RUN.cs.txt',G/'build'/(mode.replace('/','-')+'92.dll'))
 (G/'console/ARGS.json').write_text((H/'face91/console/ARGS.json').read_text());result={'externalCSharp9Compiled':True,'plannedFrames':6,'existingShader91SHA':sha(H/'SourceValue91.shader'),'computeDispatches':0,'newShaderOrAssetsImport':False,'originalSupportIdentityUnchanged':True,'tableOnlySource92AndNativeContrastConstraints':True,'actualGPUExecuted':False};(G/'CPU_PREPARED92.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
if __name__=='__main__':main()
