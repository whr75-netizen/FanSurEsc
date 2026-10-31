// Isolated candidate include OUTSIDE Assets. Not imported/compiled/activated.
// Caller supplies source-family ordinal already bound from material/UV domain.
// This code does not identify eyes/hair, sample albedo or generate regions.
#ifndef SOURCE_PALETTE54_INCLUDED
#define SOURCE_PALETTE54_INCLUDED
StructuredBuffer<uint4> _SourcePalette54RGB8;
StructuredBuffer<float> _SourcePalette54Thresholds;
// x=palette offset, y=count, z=threshold offset, w=threshold count.
StructuredBuffer<uint4> _SourcePalette54Families;
uint SourceShade54(uint family, float g) {
 uint4 f=_SourcePalette54Families[family];uint k=0;
 for(uint i=0;i<f.w;i++)k+=(g>=_SourcePalette54Thresholds[f.z+i])?1:0;
 return k;
}
uint4 SourceLookup54(uint family,uint k) {
 return _SourcePalette54RGB8[_SourcePalette54Families[family].x+k];
}
float3 SourceRGB8ToLinear54(uint3 rgb8) {
 float3 c=(float3)rgb8/255.0;
 return float3(c.r<=.04045?c.r/12.92:pow((c.r+.055)/1.055,2.4),
  c.g<=.04045?c.g/12.92:pow((c.g+.055)/1.055,2.4),
  c.b<=.04045?c.b/12.92:pow((c.b+.055)/1.055,2.4));
}
// Linear RT consumers decode once; final sRGB encoding is the sole inverse.
// Legacy HairFinal/G/LineTone/AA/tone mapping after this breaks the contract.
#endif
