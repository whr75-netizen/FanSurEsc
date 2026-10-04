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

float3 Native18Color(float3 color, float3 irradiance, float band)
{
    float peak = max(irradiance.r, max(irradiance.g, irradiance.b));
    float3 tint = peak > 0.000001 ? floor(saturate(irradiance / peak) * 3.0 + 0.5) / 3.0 : 1.0;
    bool cool = irradiance.b > irradiance.r && irradiance.b > irradiance.g;
    if (!cool) return color * lerp(1.0, tint, 0.3);
    // Move shadow hue at constant luminance, preserving material ranks.
    const float3 luminance = float3(0.2126729, 0.7151522, 0.0721750);
    float3 target = dot(color, luminance) * tint / max(dot(tint, luminance), 0.000001);
    float3 delta = target - color;
    float3 gamutLimit = delta > 0.0 ? (1.0 - color) / max(delta, 0.000001) : 1.0;
    float strength = min(0.5 * (1.0 - band * 0.5), min(gamutLimit.r, min(gamutLimit.g, gamutLimit.b)));
    return color + delta * strength;
}
// Preserve the existing night response; only explicitly continuous local lights
// approach the same Point-sampled albedo. Lighting never blends palette columns.
float3 Native18SmoothLocalColor(float3 nightColor, float3 albedo, float3 incident)
{
    incident = max(incident, 0.0);
    float peak = max(incident.r, max(incident.g, incident.b));
    if (peak <= 0.000001) return nightColor;
    float energy = dot(incident, float3(0.2126729, 0.7151522, 0.0721750));
    float amount = 1.0 - exp2(-energy);
    float3 target = albedo * incident / peak;
    return lerp(nightColor, target, amount);
}
#endif
