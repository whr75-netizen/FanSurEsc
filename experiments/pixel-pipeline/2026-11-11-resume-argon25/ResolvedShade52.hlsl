// Upload all buffers from one ResolvedShade52.Build result, scoped to this pass.
// Same-stage metadata only; no resized mask, RGB multiplication or inferred label.
#ifndef RESOLVED_SHADE_52_INCLUDED
#define RESOLVED_SHADE_52_INCLUDED
#include "ResolvedRegionPalette.hlsl"
StructuredBuffer<float> _ResolvedRegionAppliedQ;
bool TryResolvedShade52(uint2 pixel,out float3 rgb,out float appliedQ) {
 appliedQ=0;
 if(!TryResolvedRegionPalette(pixel,rgb))return false;
 appliedQ=_ResolvedRegionAppliedQ[pixel.y*_ResolvedRegionSize.x+pixel.x];
 return true;
}
#endif
