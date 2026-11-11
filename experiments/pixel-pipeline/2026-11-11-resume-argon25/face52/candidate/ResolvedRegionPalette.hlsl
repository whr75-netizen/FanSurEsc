// Explicit, validated stage-raster input. No material ID -> colour region inference.
// Upload only after ResolvedRegionInput.Build; separate initial/final stage buffers.
// x=family ordinal, y=1 only for confirmed opaque interior. k is external Q/Qprime.
#ifndef RESOLVED_REGION_PALETTE_INCLUDED
#define RESOLVED_REGION_PALETTE_INCLUDED
#include "SourcePalette54.hlsl"
StructuredBuffer<uint2> _ResolvedRegionBinding;
StructuredBuffer<uint> _ResolvedRegionIndex;
uint2 _ResolvedRegionSize;
bool TryResolvedRegionPalette(uint2 pixel,out float3 rgb) {
 rgb=0;
 if(any(pixel>=_ResolvedRegionSize))return false;
 uint i=pixel.y*_ResolvedRegionSize.x+pixel.x;
 uint2 binding=_ResolvedRegionBinding[i];
 if(binding.y!=1)return false;
 rgb=SourceRGB8ToLinear54(SourceLookup54(binding.x,_ResolvedRegionIndex[i]).rgb);
 return true;
}
#endif
