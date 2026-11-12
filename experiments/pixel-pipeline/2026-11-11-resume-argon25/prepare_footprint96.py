from pathlib import Path
import json,sys
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face96'
def main():
 for d in ['build','import','geometry64/capture','geometry64/final','geometry64/post/final','geometry64/console']:(G/d).mkdir(parents=True,exist_ok=True)
 assert not(G/'geometry64/capture/REQUEST.json').exists()and not(G/'import/REQUEST.json').exists()
 s=(H/'face95/motion64/capture/RUN.cs.txt').read_text().replace('resume-20261111\\face95\\motion64','resume-20261111\\face96\\geometry64').replace('face95-raw2x-motion64-','face96-halo-geometry-')
 def once(a,b):
  nonlocal s
  assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
 once('SourceFootprint95/SourceFootprint95.shader','SourceFootprint96/SourceFootprint96.shader')
 once('PrepareCurve81();PrepareRibbon93();lock(sync77)','PrepareCurve81();PrepareRibbon93();ExportActor96();lock(sync77)')
 s+='\n'+(H/'ActorSource96.cs.txt').read_text()+'\n'+(H/'AlphaChannel96.cs.txt').read_text()
 once('T("_RawWorld95",native42.world);','T("_RawWorld95",native42.world);T("_NativeCell96",native42.cellID);')
 once('var lo=native42.origin+2*(origin+join41+delta42)-Vector2.one*.5f;','var lo=native42.origin+2*(origin+join41+delta42);')
 once('var first=new Vector2Int((int)Math.Ceiling(lo.x),(int)Math.Ceiling(lo.y));','var first=new Vector2Int((int)Math.Floor(lo.x),(int)Math.Floor(lo.y));')
 s=s.replace('first.x+2*W77>960||first.y+2*W77>544','first.x+2*W77+1>960||first.y+2*W77+1>544')
 once('["sampleFootprint"]= "four existing native pixel centres, not continuous alpha between samples"','["sampleFootprint"]="world halo covers the entire cell footprint as native pixel tiles; actor geometry exported separately",["haloSize"]=2*W77+1')
 once('RGBAFloat32 bottom-left24layers SourceFootprint95 rawWORLD4+DEPTH4+META4+UV4+RECEIPTS8','RGBAFloat32 flat96 worldHaloRGBA+worldHaloDepth+14 source planes+zero padding')
 a=s.index('int actorCount77=0,faceCount77=0;');b=s.index('for(int yy=0;',a)
 s=s[:a]+'int actorCount77=0,faceCount77=0;int halo96=2*W77+1,base96=2*halo96*halo96;for(int y77=0;y77<W77;y77++)for(int x77=0;x77<W77;x77++){int local96=y77*W77+x77;int cell96=16*(base96+13*W77*W77+local96);if(BitConverter.ToSingle(bytes,cell96+8)==1)actorCount77++;int address96=16*(base96+4*W77*W77+local96);if(BitConverter.ToSingle(bytes,address96+12)==1&&BitConverter.ToSingle(bytes,address96)>0)faceCount77++;}'+s[b:]
 once('int b89=16*(yy*W77*24+17*W77+xx);','int b89=16*(base96+4*W77*W77+yy*W77+xx);')
 assert 'EvaluateForm115'not in s and 'BoundRun115'not in s and s.count('cmd.RequestAsyncReadback(readbackPack93.rt')==1
 (G/'geometry64/capture/RUN.cs.txt').write_text(s,encoding='utf-8',newline='\n');compile_unity_language(G/'geometry64/capture/RUN.cs.txt',G/'build/geometry96.dll')
 for d in ['final','post/final']:
  s=(H/'face95/motion64'/d/'RUN.cs.txt').read_text().replace('resume-20261111\\face95\\motion64','resume-20261111\\face96\\geometry64');(G/'geometry64'/d/'RUN.cs.txt').write_text(s,encoding='utf-8',newline='\n');compile_unity_language(G/'geometry64'/d/'RUN.cs.txt',G/'build'/(d.replace('/','-')+'96.dll'))
 (G/'geometry64/console/ARGS.json').write_bytes((H/'face95/motion64/console/ARGS.json').read_bytes())
 s=(H/'face95/import/RUN.cs.txt').read_text().replace('resume-20261111\\face95\\import','resume-20261111\\face96\\import').replace('SourceFootprint95','SourceFootprint96');(G/'import/RUN.cs.txt').write_text(s,encoding='utf-8',newline='\n');compile_unity_language(G/'import/RUN.cs.txt',G/'build/import96.dll')
 import hashlib
 (G/'import/EXPECTED.json').write_text(json.dumps({'shaderSHA256':hashlib.sha256((H/'SourceFootprint96.shader').read_bytes()).hexdigest(),'UnityGeneratesMeta':True},indent=2));print('96 external commands compiled; no Unity/GPU execution')
if __name__=='__main__':main()
