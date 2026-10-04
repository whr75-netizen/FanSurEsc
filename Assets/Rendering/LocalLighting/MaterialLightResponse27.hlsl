// Linear diffuse response shared by the N27 prototype and surface consumers.
#ifndef FANTASY_MATERIAL_LIGHT_RESPONSE_27_INCLUDED
#define FANTASY_MATERIAL_LIGHT_RESPONSE_27_INCLUDED

float3 Material27LightTint(float3 irradiance)
{
    irradiance = max(irradiance, 0.0);
    float peak = max(irradiance.r, max(irradiance.g, irradiance.b));
    return peak > 0.000001 ? irradiance / peak : 0.0;
}

float3 Material27Diffuse(float3 albedo, float3 irradiance)
{
    // Reflectance multiplies incident light. Never add light RGB to surface RGB.
    return albedo * max(irradiance, 0.0);
}

float3 Material27Readable(float3 albedo, float3 baseIrradiance, float3 steppedIrradiance)
{
    const float3 luminance = float3(0.2126729, 0.7151522, 0.0721750);
    float y = dot(max(baseIrradiance, 0.0), luminance);
    // Preserve the existing readable-night exposure, not a physical HDR curve.
    float brightness = y < 0.12 ? 0.55 : (y < 0.4 ? 0.78 : 1.0);
    float3 baseResponse = brightness * Material27LightTint(baseIrradiance);
    // Local source bands were already quantized. Classifying the sum again
    // would collapse distinct source levels and introduce a second quantizer.
    return Material27Diffuse(albedo, baseResponse + max(steppedIrradiance, 0.0));
}
#endif
