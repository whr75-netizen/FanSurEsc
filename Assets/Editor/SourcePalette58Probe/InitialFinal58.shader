Shader "Hidden/SourcePalette58/InitialFinal" {
 SubShader { Pass {
  ZTest Always ZWrite Off Cull Off Blend Off
  HLSLPROGRAM
  #pragma target 4.5
  #pragma vertex Vert58
  #pragma fragment Frag58
  #include "SurfaceLayerOutput58.hlsl"
  struct Case58 {uint family;float g;uint corrected;uint bound;};
  StructuredBuffer<Case58> _Cases58;StructuredBuffer<uint4> _SourceRGB58;
  Texture2D<float4> _Final58;uint _Count58;int _Mode58;
  float4 Vert58(uint v:SV_VertexID):SV_POSITION {return float4(float2((v<<1)&2,v&2)*2-1,0,1);}
  float4 Frag58(float4 pos:SV_POSITION):SV_Target {
   uint i=min((uint)pos.x,_Count58-1);if(_Mode58==1)return _Final58.Load(int3((int)i,0,0));
   Case58 c=_Cases58[i];float3 native=SourceRGB8ToLinear54(_SourceRGB58[i].rgb);
   if(c.bound==0)return float4(native,(float)_SourceRGB58[i].a/255.0);
   float k=SourceShade54(c.family,c.g),count=_SourcePalette54Families[c.family].y;
   return float4(SurfaceLayerOutput335(native,float3(.17,.83,1.41),c.g,k/(count-1),c.family),1);
  }
  ENDHLSL
 } }
}
