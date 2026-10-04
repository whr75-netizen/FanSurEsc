// Readable-night exposure with N27 linear material response (BUILDING16.md).
#ifndef FANTASY_NATIVE_READABLE_18_INCLUDED
#define FANTASY_NATIVE_READABLE_18_INCLUDED
#include "Assets/Rendering/LocalLighting/MaterialLightResponse27.hlsl"

float Native18Band(float luminance)
{
    return step(0.12, luminance) + step(0.4, luminance);
}

float Native18Brightness(float band)
{
    return band < 0.5 ? 0.55 : (band < 1.5 ? 0.78 : 1.0);
}

float3 Native18Color(float3 color, float3 irradiance, float band)
{
    // Compatibility for the old fixture API. The production readable branch
    // uses Material27Readable so local source bands are not classified twice.
    return Material27Diffuse(color, Material27LightTint(irradiance));
}
#endif
