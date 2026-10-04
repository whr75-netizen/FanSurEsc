// Native-only readable exposure: preserve actual direct shadow loss.
#ifndef FANTASY_NATIVE_LIGHT_31_INCLUDED
#define FANTASY_NATIVE_LIGHT_31_INCLUDED

float3 Native31Readable(float3 albedo, float3 shadowedIrradiance,
    float3 shadowLoss, float3 steppedIrradiance)
{
    const float3 luminance = float3(0.2126729, 0.7151522, 0.0721750);
    float3 shadowed = max(shadowedIrradiance, 0.0);
    float3 opened = shadowed + max(shadowLoss, 0.0);
    float peak = max(opened.r, max(opened.g, opened.b));
    float y = dot(opened, luminance);
    float brightness = y < 0.12 ? 0.55 : (y < 0.4 ? 0.78 : 1.0);
    // Exposure comes from the same incident lights before occlusion. Only
    // their real shadow loss reduces the diffuse response. Ambient survives.
    float3 baseResponse = peak > 0.000001 ? brightness * shadowed / peak : 0.0;
    // Moving source is already quantized. Specular is shadowed separately.
    return Material27Diffuse(albedo, baseResponse + max(steppedIrradiance, 0.0));
}
#endif
