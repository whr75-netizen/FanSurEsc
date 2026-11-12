"""Prepare a32-frame read-only GPU reason packet; unchanged99C/98B output."""
from pathlib import Path
import json,hashlib,sys
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face100'

def main():
 name='reasons32';root=G/name;old=H/'face99/fine64';(G/'build').mkdir(parents=True,exist_ok=True)
 for folder in ['capture','preflight/final','post/final','console']:(root/folder).mkdir(parents=True,exist_ok=True)
 assert not(root/'capture/REQUEST.json').exists();s=(old/'capture/RUN.cs.txt').read_text().replace(str(old),str(root)).replace('face99-fine-','face100-reasons-')
 def once(a,b):
  nonlocal s
  assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
 once('id="face99-fine64-"','id="face100-reasons-"')
 once('motion40.FirstTarget,64,24,motion40.Snapshot','motion40.FirstTarget,32,24,motion40.Snapshot');once('["plannedSourceFrames"]=64','["plannedSourceFrames"]=32');once('SourceFootprint98/SourceFootprint98.shader','SourceFootprint100/SourceFootprint100.shader')
 once('T("_RawWorld95",native42.world);','T("_MainUV100",main41.resolvedUV);T("_MainSource100",main41.preparedMeta);T("_MainDomain100",main41.domain);T("_Owner100",native42.owner);p.SetInt("_Role100",sourceFlat67.MappedRole72);T("_RawWorld95",native42.world);')
 once('FrameInfo40["sourceFootprint95"]=new Obj40{','FrameInfo40["rawSourcePlaneCount100"]=15;FrameInfo40["mappedRole100"]=sourceFlat67.MappedRole72;FrameInfo40["sourceFootprint95"]=new Obj40{');once('14 source planes+zero padding','15 source planes including100 reasons+zero padding')
 assert s.count('cmd.RequestAsyncReadback(readbackPack93.rt')==1 and'EvaluateForm115'not in s and'BoundRun115'not in s
 p=root/'capture/RUN.cs.txt';p.write_text(s,encoding='utf-8',newline='\n');compile_unity_language(p,G/'build/reasons32.dll')
 for mode in ['preflight','post']:
  src=(old/'post/final/RUN.cs.txt').read_text();src=src.replace('const string Root=@"'+str(old/'post')+'";','const string Root=@"'+str(root/mode)+'";')
  if mode=='post':src=src.replace(str(old/'capture/INPUT_BEFORE.json'),str(root/'capture/INPUT_BEFORE.json'))
  assert ('const string Root=@"'+str(root/mode)+'";')in src;p=root/mode/'final/RUN.cs.txt';p.write_text(src,encoding='utf-8');compile_unity_language(p,G/'build'/(mode+'.dll'))
 shader='SourceFootprint100';out=G/'import'/ 'import';out.mkdir(parents=True,exist_ok=True);assert not(out/'REQUEST.json').exists();s=(H/'face96/import/RUN.cs.txt').read_text().replace(str(H/'face96/import'),str(out)).replace('SourceFootprint96',shader);p=out/'RUN.cs.txt';p.write_text(s,encoding='utf-8');compile_unity_language(p,G/'build/import.dll');(out/'EXPECTED.json').write_text(json.dumps({'shaderSHA256':hashlib.sha256((H/(shader+'.shader')).read_bytes()).hexdigest(),'UnityGeneratesMeta':True},indent=2))
 print('100 external runner CPU compilation complete; no Unity/import/GPU executed')
if __name__=='__main__':main()
