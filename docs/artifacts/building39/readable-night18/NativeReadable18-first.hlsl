// N18 presentation contract: BUILDING16.md, readable night.
#ifndef FANTASY_NATIVE_READABLE_18_INCLUDED
#define FANTASY_NATIVE_READABLE_18_INCLUDED

float Native18Band(float luminance)
{
    return step(0.12, luminance) + step(0.4, luminance);
}

float Native18Brightness(float band)
{
    return band < 0.5 ? 0.55 : (band < 1.5 ? 0.78 : 1.0);
}

float3 Native18Tint(float3 irradiance, float band)
{
    float peak = max(irradiance.r, max(irradiance.g, irradiance.b));
    float3 tint = peak > 0.000001 ? floor(saturate(irradiance / peak) * 3.0 + 0.5) / 3.0 : 1.0;
    bool cool = irradiance.b > irradiance.r && irradiance.b > irradiance.g;
    float strength = cool ? 0.3 * (1.0 - band * 0.5) : 0.3;
    return lerp(1.0, tint, strength);
}
#endif
