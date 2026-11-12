"""Connect the already-selected main-view source after MainToHead transport.
Strict source identities, UV, shade and exact depth transport are required.
No geometry, palette entries, ownership, thresholds or product defaults change.
"""
from pathlib import Path
import json,hashlib
from prepare_final41 import compile_unity_language
H=Path(__file__).resolve().parent;G=H/'face101'

def source101():
 s=(H/'SourceValue91.shader').read_text().replace('EValidation/SourceValue91','EValidation/SourceValue101')
 marker=' int _Role89;';assert s.count(marker)==1;s=s.replace(marker,' Texture2D<float4> _MainMap101,_MainClass480101,_MainClass960101,_MainMeta480101,_MainMeta960101,_MainRawUV480101,_MainRawUV960101,_MainNormal480101,_MainNormal960101,_MainMask480101,_MainMask960101;float _HeadDepthOffset101;\n'+marker)
 start=s.index('  if(plane==8)return cls;');stop=s.index('  if(plane==12)return',start);old=s[start:stop];at=old.index('  float4 hu=')
 # Retain the original conditions verbatim. Move the old debug returns after
 # the strict alternative has chosen which camera actually produced this cell.
 mainDecl=old[at:old.index('  bool ordinary=')];ordinary=old[old.index('  bool ordinary='):old.index('  // Exact UV/address identity')];known=old[old.index('  bool known='):]
 replacement=mainDecl+ordinary+known+'''  int sourceKind101=added?1:0;bool mainAdded101=false;
  if(!known&&ordinary){float4 mainMap101=_MainMap101.Load(int3(mp,0));mainAdded101=mainMap101.r>.5&&mainMap101.a>.5;int2 mainN101=mainAdded101?(int2)round(mainMap101.gb):mp;
   if(all(mainN101>=0)&&all(mainN101<(mainAdded101?int2(960,544):int2(480,272)))){
    float4 mc101=mainAdded101?_MainClass960101.Load(int3(mainN101,0)):_MainClass480101.Load(int3(mainN101,0)),mm101=mainAdded101?_MainMeta960101.Load(int3(mainN101,0)):_MainMeta480101.Load(int3(mainN101,0)),mu101=mainAdded101?_MainRawUV960101.Load(int3(mainN101,0)):_MainRawUV480101.Load(int3(mainN101,0));
    bool exact101=mc101.a>.5&&mm101.y==_Role89&&all(mu101.xy==mu.xy)&&all(hu.xy==mu.xy)&&mu.z==mc101.x&&hu.z==mc101.x&&all(mm101.yzw==ms.yzw)&&all(mm101.yzw==hm.yzw)&&mm101.x==ms.x&&mm101.x-_HeadDepthOffset101==hm.x;
    if(exact101){cls=mc101;cls.z-=_HeadDepthOffset101;meta=mm101;meta.x=hm.x;uv=mu101;n=mainN101;known=true;sourceKind101=mainAdded101?3:2;}
   }
  }
  if(plane==8)return cls;if(plane==9)return meta;if(plane==10)return sourceKind101>=2?(mainAdded101?_MainNormal960101.Load(int3(n,0)):_MainNormal480101.Load(int3(n,0))):(added?_Normal96084.Load(int3(n,0)):_Normal48084.Load(int3(n,0)));if(plane==11)return uv;
'''
 s=s[:start]+replacement+s[stop:];s=s.replace('float4(n,added?1:0,known?1:0)','float4(n,sourceKind101,known?1:0)').replace('if(plane==15)return added?_Mask96084.Load(int3(n,0)):_Mask48084.Load(int3(n,0));','if(plane==15)return sourceKind101>=2?(mainAdded101?_MainMask960101.Load(int3(n,0)):_MainMask480101.Load(int3(n,0))):(added?_Mask96084.Load(int3(n,0)):_Mask48084.Load(int3(n,0)));')
 assert s.count('sourceKind101>=2')==2 and s.count('if(exact101)')==1;return s

def main():
 (G/'build').mkdir(parents=True,exist_ok=True);s=source101();(H/'SourceValue101.shader').write_text(s,encoding='utf-8',newline='\n');p=(H/'SourceFootprint100.shader').read_text().replace('SourceFootprint100','SourceFootprint101B').replace('return float4(flags,domain.x,map.w,history.w);','return float4(flags+512*(uint)map.z,domain.x,map.w,owner.x);');(H/'SourceFootprint101B.shader').write_text(p,encoding='utf-8',newline='\n')
 old=H/'face100/reasons32';root=G/'source32'
 for folder in ['capture','preflight/final','post/final']:(root/folder).mkdir(parents=True,exist_ok=True)
 assert not(root/'capture/REQUEST.json').exists();s=(old/'capture/RUN.cs.txt').read_text().replace(str(old),str(root)).replace('face100-reasons-','face101-main-source-').replace('SourceFootprint100/SourceFootprint100.shader','SourceFootprint101B/SourceFootprint101B.shader');oldShader='SourceValue91/SourceValue91.shader';assert s.count(oldShader)==1;s=s.replace(oldShader,'SourceValue101/SourceValue101.shader')
 a='p.SetInt("_Role89",sourceFlat67.MappedRole72);';assert s.count(a)==1;extra='T("_MainClass480101",main41.style480[3]);T("_MainClass960101",main41.style960[3]);T("_MainMeta480101",main41.motion.raw[5]);T("_MainMeta960101",main41.native[5]);T("_MainRawUV480101",main41.motion.raw[6]);T("_MainRawUV960101",main41.native[6]);T("_MainNormal480101",main41.motion.raw[2]);T("_MainNormal960101",main41.native[2]);T("_MainMask480101",main41.shadeMask480);T("_MainMask960101",main41.shadeMask960);p.SetTexture("_MainMap101",main41.actionMap);p.SetFloat("_HeadDepthOffset101",depth41);';s=s.replace(a,extra+a);s=s.replace('FrameInfo40["rawSourcePlaneCount100"]=15;','FrameInfo40["sourceColourProducer101"]="main-or-head exact current source, metadata depth transported to head";FrameInfo40["rawSourcePlaneCount100"]=15;');p=root/'capture/RUN.cs.txt';p.write_text(s,encoding='utf-8');compile_unity_language(p,G/'build/source32.dll')
 for mode in ['preflight','post']:
  s=(old/mode/'final/RUN.cs.txt').read_text().replace('const string Root=@"'+str(old/mode)+'";','const string Root=@"'+str(root/mode)+'";')
  if mode=='post':s=s.replace(str(old/'capture/INPUT_BEFORE.json'),str(root/'capture/INPUT_BEFORE.json'))
  p=root/mode/'final/RUN.cs.txt'
  if(p.parent/'REQUEST.json').exists():assert p.read_text()==s,'immutable executed state command changed'
  else:p.write_text(s,encoding='utf-8')
  compile_unity_language(p,G/'build'/(mode+'.dll'))
 for shader in ['SourceValue101','SourceFootprint101B']:
  out=G/('import-'+shader)/'import';out.mkdir(parents=True,exist_ok=True)
  if(out/'REQUEST.json').exists():
   assert(out/'COMPLETE.json').exists()and json.loads((out/'EXPECTED.json').read_text())['shaderSHA256']==hashlib.sha256((H/(shader+'.shader')).read_bytes()).hexdigest();continue
  s=(H/'face96/import/RUN.cs.txt').read_text().replace(str(H/'face96/import'),str(out)).replace('SourceFootprint96',shader);p=out/'RUN.cs.txt';p.write_text(s,encoding='utf-8');compile_unity_language(p,G/'build'/('import-'+shader+'.dll'));(out/'EXPECTED.json').write_text(json.dumps({'shaderSHA256':hashlib.sha256((H/(shader+'.shader')).read_bytes()).hexdigest(),'UnityGeneratesMeta':True},indent=2))
 print('101 external runner compiled; actual91 known gate retained, main source requires exact identity/depth/UV/Q; no Unity/GPU executed')
if __name__=='__main__':main()
