"""Isolated clones; original source material/lighting functions retained.

Only clip mapping and authored iris/white source pigment are replaced. Native
skin/eyeline still use their actual original material UV/alpha/light producer.
No Shader.SetGlobal/CommandBuffer.SetViewProjectionMatrices is needed.
"""
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
OUTPUT=Path(sys.argv[1])if len(sys.argv)>1 else HERE
R=Path(r'C:\Users\15352\Documents\work\Fantasy Survival Escape Game/Assets/EUnityValidation01/EyeBoundaryRestore348/Shaders')
uniform='''
float4 _NativeSourceX89,_NativeSourceY89,_CanonicalAnchor89;
float4 _SourcePhysicalROI89,_SourcePhysicalSize89,_PhysicalCamera89,_PhysicalForward89;
float4x4 _AuthoredToHead89,_CanonicalGPUProjection89,_PhysicalView89,_PhysicalCropGPUVP89;
int _Control89,_UseBank89,_SelectedOwner89;
float _ScreenSign89;
Texture2D<float4> _FeatureBankRGB89,_FeatureBankRole89;
float4 SourceClip89(float3 world){
 if(_Control89!=0)return mul(_PhysicalCropGPUVP89,float4(world,1));
 float4 rest=mul(_WorldToHead348,float4(world,1));
 float2 q=float2(dot(_NativeSourceX89,rest),dot(_NativeSourceY89,rest));
 float3 projected=mul(_AuthoredToHead89,float4(q,1,0)).xyz;
 float2 local=projected.xy/projected.z-_CanonicalAnchor89.xy;
 float depth=-mul(_PhysicalView89,float4(world,1)).z;
 return mul(_CanonicalGPUProjection89,float4(local.x,-local.y,-depth,1));
}
float2 SourceLogicalScreen89(float3 world){
 float4 p=mul(_PhysicalCropGPUVP89,float4(world,1));
 float2 sv=float2(p.x/p.w*.5+.5,.5+_ScreenSign89*p.y/p.w*.5)*_SourcePhysicalSize89.xy;
 return _SourcePhysicalROI89.xy+sv/4;
}
'''
vertex='''Varyings Eye333Vertex(const Attributes v){
 Varyings o=MToonVertex(v);o.e202Control=v.apertureControl.xy;
 o.e202Owner=v.e202SourceOwner.x;o.restHead348=v.texcoord1;
 o.viewDirWS=_PhysicalCamera89.w>.5?-_PhysicalForward89.xyz:_PhysicalCamera89.xyz-o.positionWS;
 o.pos=SourceClip89(o.positionWS);return o;
}'''
for kind,src in [('Surface','EyeSurface348.shader'),('Skin','EyeSkin348.shader')]:
 text=(R/src).read_text(encoding='utf-8-sig');text=text.replace('Shader "EValidation/Eye'+kind+'348"','Shader "EValidation/Native'+kind+'89"',1)
 old='Varyings Eye333Vertex(const Attributes v){Varyings o=MToonVertex(v);o.e202Control=v.apertureControl.xy;o.e202Owner=v.e202SourceOwner.x;o.restHead348=v.texcoord1;return o;}'
 assert text.count(old)==1;text=text.replace(old,uniform+vertex)
 old='v.pos.xy=_ROI348.xy+input.pos.xy/4;';assert text.count(old)==1;text=text.replace(old,'v.pos.xy=_Control89==3?_SourcePhysicalROI89.xy+input.pos.xy/4:SourceLogicalScreen89(v.positionWS);if(_SelectedOwner89>0&&round(v.e202Owner)!=_SelectedOwner89)discard;')
 text=text.replace('-TransformWorldToView(v.positionWS).z','-mul(_PhysicalView89,float4(v.positionWS,1)).z')
 if kind=='Surface':
  old='if(alpha<=1e-6)discard;int role=(int)round(_Auto245Role);';assert text.count(old)==1;text=text.replace(old,'int role=(int)round(_Auto245Role);bool bank=_UseBank89>0&&(role==1||role==4);if(!bank&&alpha<=1e-6)discard;')
  old='O333 o;o.shade=0;';assert text.count(old)==1;text=text.replace(old,'''O333 o;o.shade=0;
 if(bank){
  float4 rest=float4(v.restHead348,1);float2 q=float2(dot(_NativeSourceX89,rest),dot(_NativeSourceY89,rest));
  int2 k=(int2)floor(q);if(any(k<0)||any(k>=int2(480,272)))discard;
  float4 sourceRole=_FeatureBankRole89.Load(int3(k.x,271-k.y,0));
  if(round(sourceRole.x)!=role||round(sourceRole.y)!=round(v.e202Owner))discard;
  float4 colour=_FeatureBankRGB89.Load(int3(k.x,271-k.y,0));if(colour.a<=0)discard;
  o.rgba=colour;o.meta=float4(-mul(_PhysicalView89,float4(v.positionWS,1)).z,role+1,round(v.e202Owner),colour.a);
  o.restPosition=float4(v.restHead348,facing?1:-1);o.uv=float4(uv,primitiveID+1,_SupportKind348);return o;
 }
''')
 text='\n'.join(line.rstrip()for line in text.splitlines())+'\n'
 out=OUTPUT/f'Native{kind}89.shader';assert not out.exists();out.write_bytes(text.encode())
print('Prepared2 isolated shader clones; actual source UV/alpha/light functions retained; no existing product changed.')
