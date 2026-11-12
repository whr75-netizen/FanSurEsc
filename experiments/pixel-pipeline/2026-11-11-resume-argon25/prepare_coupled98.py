from pathlib import Path
import json,sys,hashlib,re
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face98'

def main():
 name=sys.argv[1]if len(sys.argv)>1 else'one';count=1 if name.startswith('one')else 64;root=G/name
 for d in['capture','final','post/final','console']:(root/d).mkdir(parents=True,exist_ok=True)
 (G/'build').mkdir(exist_ok=True);assert not(root/'capture/REQUEST.json').exists()
 s=(H/'face96/geometry64/capture/RUN.cs.txt').read_text().replace('resume-20261111\\face96\\geometry64','resume-20261111\\face98\\'+name).replace('face96-halo-geometry-','face98-coupled-source-'+name+'-')
 def once(a,b):
  nonlocal s
  assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
 once('SourceFootprint96/SourceFootprint96.shader','SourceFootprint98/SourceFootprint98.shader')
 once('InitRibbon93();InitFootprint95();','InitRibbon93();InitJoint97();InitCoupled98();InitFootprint95();')
 once('RecordRibbon93(graph);RecordFootprint95(graph);','RecordRibbon93(graph);RecordJoint97(graph);RecordCoupled98(graph);RecordFootprint95(graph);')
 once('ReleaseRibbon93();if(inkStyle39)','ReleaseCoupled98();ReleaseJoint97();ReleaseRibbon93();if(inkStyle39)')
 once('["file"]="ribbon-frame"+frame+".bin"};','["file"]="ribbon-frame"+frame+".bin"};PrepareJoint97(input);')
 once('T("_RawWorld95",native42.world);','T("_RawWorld95",native42.world);T("_JointFinal97",jointFields97[0]);T("_JointReceipt97",jointFields97[1]);T("_CoupledFinal98",coupledFields98[0]);T("_CoupledReceipt98",coupledFields98[1]);')
 once('readonly SourceOutline40[] slots;readonly EyeFeature348 eye;','readonly SourceOutline40[] slots;readonly SourceOpacity97Cache opacity97;readonly EyeFeature348 eye;')
 once('slots[i].Received77=Receipt;}}catch{foreach(var s in slots)','slots[i].Received77=Receipt;}opacity97=slots[0].NewOpacity97();foreach(var s97 in slots)s97.SetOpacity97(opacity97);}catch{opacity97?.Dispose();foreach(var s in slots)')
 once('throw new InvalidOperationException("77 resource release incomplete");},afterEdit);','throw new InvalidOperationException("77 resource release incomplete");opacity97.Dispose();},afterEdit);')
 once('["noRGBHistory"]=true,["GPUCPUReadbackForSelection"]=false','["sourceAlpha97ManagedBytesAfterRelease"]=opacity97.Bytes,["noRGBHistory"]=true,["GPUCPUReadbackForSelection"]=false')
 once('motion40.FirstTarget,64,24,motion40.Snapshot','motion40.FirstTarget,'+str(count)+','+('1'if count==1 else'24')+',motion40.Snapshot')
 once('["plannedSourceFrames"]=64','["plannedSourceFrames"]='+str(count))
 # Preserve the immutable96 RUN; only replace its embedded calibration in
 # this newly generated97 command. No per-pixel LINQ allocation in97.
 at=s.index('namespace Unity.AI.Assistant.Agent.Dynamic.Extension.Editor {\npublic static class AlphaChannel96 {');s=s[:at]+(H/'AlphaChannel96.cs.txt').read_text()
 s+='\n'+(H/'JointLine97.cs').read_text().split('namespace LineGeometry97',1)[0].replace('using System;','').replace('using System.Collections.Generic;','')+'namespace LineGeometry97'+(H/'JointLine97.cs').read_text().split('namespace LineGeometry97',1)[1]+'\n'+(H/'JointRibbon97.cs.txt').read_text().replace('var greens=new Arr40();','var greens=new Arr40();var collector98=new LineGeometry97.CurveOpacity98(scene,raster);').replace('int edge=(int)row[0];raster.Add','int edge=(int)row[0];collector98.Register(edge,(xy[0]+xy[2])*.5,(xy[1]+xy[3])*.5,Math.Max((xy[0]-xy[2]).Length,(xy[1]-xy[3]).Length));raster.Add').replace('jointProof97.SetPixelData(jointData97,0);','PrepareCoupled98(collector98,clock);jointProof97.SetPixelData(jointData97,0);')+'\nnamespace LineGeometry97'+(H/'CurveOpacity98B.cs').read_text().split('namespace LineGeometry97',1)[1]+'\n'+(H/'CoupledRibbon98.cs.txt').read_text().replace('CoupledRibbon98/CoupledRibbon98.shader','CoupledRibbon98B/CoupledRibbon98B.shader')
 assert 'EvaluateForm115'not in s and 'BoundRun115'not in s and s.count('cmd.RequestAsyncReadback(readbackPack93.rt')==1
 p=root/'capture/RUN.cs.txt';p.write_text(s,encoding='utf-8',newline='\n');compile_unity_language(p,G/'build'/('capture-'+name+'97.dll'))
 for d in['final','post/final']:
  s=(H/'face96/geometry64'/d/'RUN.cs.txt').read_text().replace('resume-20261111\\face96\\geometry64','resume-20261111\\face98\\'+name);p=root/d/'RUN.cs.txt';p.write_text(s,encoding='utf-8',newline='\n');compile_unity_language(p,G/'build'/(d.replace('/','-')+'-'+name+'97.dll'))
 (root/'console/ARGS.json').write_bytes((H/'face96/geometry64/console/ARGS.json').read_bytes())
 pack=(H/'SourceFootprint96.shader').read_text().replace('SourceFootprint96','SourceFootprint97').replace('_NativeCell96;','_NativeCell96,_JointFinal97,_JointReceipt97;').replace('if(plane==3)return _Atlas95.Load(int3(p+int2(16*_Width95,0),0));','if(plane==3)return _JointReceipt97.Load(int3(p,0));').replace('if(plane==12)return _Atlas95.Load(int3(p+int2(_Width95,0),0));','if(plane==12)return _JointFinal97.Load(int3(p,0));')
 pack=pack.replace('SourceFootprint97','SourceFootprint98').replace('_JointReceipt97;','_JointReceipt97,_CoupledFinal98,_CoupledReceipt98;').replace('if(plane==7)return _LineProjection95.Load(int3(p,0));','if(plane==7)return _CoupledFinal98.Load(int3(p,0));').replace('if(plane==8)return _LineFootprint95.Load(int3(p,0));','if(plane==8)return _CoupledReceipt98.Load(int3(p,0));')
 (H/'SourceFootprint98.shader').write_text(pack,encoding='utf-8',newline='\n')
 for shader in['CoupledRibbon98B','SourceFootprint98']:
  out=G/('import-'+shader)/'import';out.mkdir(parents=True,exist_ok=True)
  if(out/'REQUEST.json').exists():
   assert(out/'COMPLETE.json').exists()and json.loads((out/'EXPECTED.json').read_text())['shaderSHA256']==hashlib.sha256((H/(shader+'.shader')).read_bytes()).hexdigest();continue
  s=(H/'face96/import/RUN.cs.txt').read_text().replace('resume-20261111\\face96\\import','resume-20261111\\face98\\import-'+shader+'\\import').replace('SourceFootprint96',shader);p=out/'RUN.cs.txt';p.write_text(s,encoding='utf-8',newline='\n');compile_unity_language(p,G/'build'/('import-'+shader+'.dll'));(out/'EXPECTED.json').write_text(json.dumps({'shaderSHA256':hashlib.sha256((H/(shader+'.shader')).read_bytes()).hexdigest(),'UnityGeneratesMeta':True},indent=2))
 (root/'CPU_PREPARED98.json').write_text(json.dumps({'externalCSharpCompiled':True,'newGPUComputeKernels':0,'newRasterPasses':2,'maxMRT':2,'readbackBytes':259584,'sourceAlphaCacheOuterOwner':True,'frames':count,'GPUExecuted':False,'finalGeneralOpacitySolved':False},indent=2));print('98 current CPU/managed compilation complete; Unity/GPU not executed')
if __name__=='__main__':main()
