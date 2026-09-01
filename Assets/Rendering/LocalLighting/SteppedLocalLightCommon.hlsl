#ifndef FANTASY_SURVIVAL_STEPPED_LOCAL_LIGHT_COMMON_INCLUDED
#define FANTASY_SURVIVAL_STEPPED_LOCAL_LIGHT_COMMON_INCLUDED

#define STEPPED_LOCAL_LIGHT_MAXIMUM 16

int _SteppedLocalLightCount;
float4 _SteppedLocalLightPositionsAndRadii[STEPPED_LOCAL_LIGHT_MAXIMUM];
float4 _SteppedLocalLightColorsAndIntensities[STEPPED_LOCAL_LIGHT_MAXIMUM];
float4 _SteppedLocalLightQuantizationSettings[STEPPED_LOCAL_LIGHT_MAXIMUM];
float _SteppedLocalLightWorldCellSizes[STEPPED_LOCAL_LIGHT_MAXIMUM];
float _SteppedLocalLightHaloRadiusMultipliers[STEPPED_LOCAL_LIGHT_MAXIMUM];

float3 SteppedSafeNormalize(float3 value)
{
    return value * rsqrt(max(dot(value, value), 0.000001));
}

float3 SnapSteppedLightWorldPosition(float3 positionWS, float cellSize)
{
    float safeCellSize = max(cellSize, 0.0001);
    return floor(positionWS / safeCellSize + 0.5) * safeCellSize;
}

float QuantizeSteppedLight01(float value, float bands)
{
    float intervals = max(round(bands) - 1.0, 1.0);
    return floor(saturate(value) * intervals + 0.5) / intervals;
}

half3 EvaluateSteppedLocalLights(
    float3 positionWS,
    float3 normalWS,
    float normalInfluenceScale)
{
    half3 accumulatedLight = half3(0.0, 0.0, 0.0);

    [loop]
    for (int index = 0; index < STEPPED_LOCAL_LIGHT_MAXIMUM; index++)
    {
        if (index >= _SteppedLocalLightCount)
        {
            break;
        }

        float4 positionAndRadius = _SteppedLocalLightPositionsAndRadii[index];
        float4 colorAndIntensity =
            _SteppedLocalLightColorsAndIntensities[index];
        float4 quantization = _SteppedLocalLightQuantizationSettings[index];
        float3 snappedPositionWS = SnapSteppedLightWorldPosition(
            positionWS,
            _SteppedLocalLightWorldCellSizes[index]);
        float3 toLight = positionAndRadius.xyz - snappedPositionWS;
        float distanceToLight = length(toLight);
        float surfaceRadial = saturate(
            1.0 - distanceToLight / max(positionAndRadius.w, 0.01));
        float haloRadius = positionAndRadius.w *
            max(_SteppedLocalLightHaloRadiusMultipliers[index], 1.0);
        float haloRadial = saturate(
            1.0 - distanceToLight / max(haloRadius, 0.01));
        float surfaceAttenuation = surfaceRadial * surfaceRadial;
        float haloAttenuation = haloRadial * haloRadial;
        if (haloAttenuation <= 0.0)
        {
            continue;
        }

        float normalTerm = saturate(dot(
            normalWS,
            SteppedSafeNormalize(toLight)));
        float normalInfluence =
            saturate(quantization.w * normalInfluenceScale);
        float surfaceLight = QuantizeSteppedLight01(
            surfaceAttenuation * lerp(1.0, normalTerm, normalInfluence),
            quantization.x);
        float haloLight = QuantizeSteppedLight01(
            haloAttenuation,
            quantization.y) * quantization.z;
        float contribution = surfaceLight + haloLight * (1.0 - surfaceLight);
        accumulatedLight +=
            (half3)colorAndIntensity.rgb *
            (half)(colorAndIntensity.w * contribution);
    }

    return accumulatedLight;
}

#endif
