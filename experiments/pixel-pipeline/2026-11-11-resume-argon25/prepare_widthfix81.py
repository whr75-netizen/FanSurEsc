from pathlib import Path
import json,hashlib
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face81/width-fix/import'

def main():
 G.mkdir(parents=True,exist_ok=True);assert not(G/'REQUEST.json').exists();d=json.loads((H/'face81/import/COMPLETE.json').read_text());s=(H/'face75/import/RUN.cs.txt').read_text();s=s.replace('resume-20261111\\face75\\import','resume-20261111\\face81\\width-fix\\import').replace('resume-20261111\\face75\\shaders\\SourceNativeHull60.compute','resume-20261111\\FeatureCurve81.shader').replace('Assets/EUnityValidation01/SourceBoundary60/SourceNativeHull60.compute','Assets/EUnityValidation01/FeatureCurve81/FeatureCurve81.shader').replace('LoadAssetAtPath<ComputeShader>','LoadAssetAtPath<Shader>').replace('GetComputeShaderMessages','GetShaderMessages')
 start=s.index('cs.GetKernelThreadGroupSizes');end=s.index('\n',start);s=s[:start]+s[end:];s=s.replace('owned compute','owned raster shader').replace('compute missing','raster shader missing');(G/'RUN.cs.txt').write_text(s,encoding='utf-8',newline='\n');(G/'EXPECTED.json').write_text(json.dumps({'beforeSHA':d['shaderSHA256'],'afterSHA':hashlib.sha256((H/'FeatureCurve81.shader').read_bytes()).hexdigest(),'guid':d['guid']},indent=2));compile_unity_language(G/'RUN.cs.txt',H/'face81/build/widthfix81.dll');print('CPU compiled owned shader correction: original raw vertex width sampling, no render')
if __name__=='__main__':main()
