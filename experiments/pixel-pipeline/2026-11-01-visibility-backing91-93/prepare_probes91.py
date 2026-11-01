"""Emit reviewable new probe copies; never edits a product shader."""
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent;REPO=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game');SHADERS=REPO/'Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders'
def function(text,name):
 start=text.index('float '+name+'(');brace=text.index('{',start);level=1;i=brace+1
 while level:
  level+=(text[i]=='{')-(text[i]=='}');i+=1
 return text[start:i]
def main():
 original=(SHADERS/'EyeSurface348.shader').read_text(encoding='utf-8-sig');retarget=(SHADERS/'NativeSurface89.shader').read_text(encoding='utf-8-sig');skin=(SHADERS/'EyeSkin348.shader').read_text(encoding='utf-8-sig');light=(REPO/'Assets/EUnityValidation01/SkinPalette302/Shaders/FaceSceneLight335.hlsl').read_text()
 f=function(light,'ContinuousSurfaceLight335').replace('float ContinuousSurfaceLight335(const Varyings input,const MToonInput material)', 'float ProbeLight91(const Varyings input,const MToonInput material,float facing91,out float4 normal91,out float4 sh91,out float4 sum91)')
 f=f.replace('float ambient=Luminance335(SampleSH(normalWS));','float3 shRGB91=SampleSH(normalWS);float ambient=Luminance335(shRGB91);')
 f=f.replace('AccumulateSurfaceLight335(mainLight,normalWS,lit,available);','AccumulateSurfaceLight335(mainLight,normalWS,lit,available);float mainLit91=lit-ambient,mainAvailable91=available-ambient;')
 f=f.replace('return available>1e-6?', 'normal91=float4(normalWS,facing91);sh91=float4(shRGB91,ambient);sum91=float4(lit,available,mainLit91,mainAvailable91);return available>1e-6?')
 outputs={'ProbeLight91.hlsl':'// Same expression order as ContinuousSurfaceLight335; outputs only. No RGB correction.\n'+f+'\n'}
 for name,s in [('OriginalProducer91.shader',original),('RetargetProducer91.shader',retarget)]:
  s=s.replace(s[s.index('Shader "'):s.index('\n')],'Shader "EValidation/'+name[:-7]+'"',1)
  s=s.replace('float4 _ClipShift333,','#include "Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders/ProbeLight91.hlsl"\nfloat4 _ClipShift333,',1)
  s=s.replace('float4 shade:SV_Target4;','float4 shade:SV_Target4;float4 normal91:SV_Target5;float4 sh91:SV_Target6;float4 sum91:SV_Target7;')
  s=s.replace('O333 o;o.shade=0;','O333 o;o.shade=0;o.normal91=0;o.sh91=0;o.sum91=0;')
  s=s.replace('ContinuousSurfaceLight335(v,material)','ProbeLight91(v,material,f.facing,o.normal91,o.sh91,o.sum91)')
  if name.startswith('Original'):
   s=s.replace('Varyings Eye333Vertex(', 'float4x4 _ProbeGPUVP91;float _RasterScale91;\nVaryings Eye333Vertex(',1)
   s=s.replace('o.restHead348=v.texcoord1;return o;','o.restHead348=v.texcoord1;o.pos=mul(_ProbeGPUVP91,float4(o.positionWS,1));return o;')
   s=s.replace('input.pos.xy/4','input.pos.xy/_RasterScale91')
  assert 'SV_Target7'in s and 'ProbeLight91(v,'in s
  outputs[name]=s
 skin=skin.replace(skin[skin.index('Shader "'):skin.index('\n')],'Shader "EValidation/CurrentBacking91"',1)
 skin=skin.replace('Varyings Eye333Vertex(', 'float4x4 _ProbeGPUVP91;float _RasterScale91;\nVaryings Eye333Vertex(',1)
 # Native skin source has the same vertex rest/owner contract as EyeSurface348.
 assert 'o.restHead348=v.texcoord1;return o;'in skin
 skin=skin.replace('o.restHead348=v.texcoord1;return o;','o.restHead348=v.texcoord1;o.pos=mul(_ProbeGPUVP91,float4(o.positionWS,1));return o;').replace('input.pos.xy/4','input.pos.xy/_RasterScale91')
 outputs['CurrentBacking91.shader']=skin
 patch='*** Begin Patch\n'
 for name,text in outputs.items():patch+='*** Add File: '+(HERE/('shaders91/'+name)).relative_to(Path.cwd()).as_posix()+'\n'+''.join('+'+line+'\n'for line in text.splitlines())
 patch+='*** End Patch\n'
 if '--emit-patch'in sys.argv:print(patch,end='')
 else:print('Use apply_patch on --emit-patch output; no files imported.')
if __name__=='__main__':main()
