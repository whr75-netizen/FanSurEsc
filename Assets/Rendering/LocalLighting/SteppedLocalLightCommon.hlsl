#ifndef FANTASY_SURVIVAL_STEPPED_LOCAL_LIGHT_COMMON_INCLUDED
#define FANTASY_SURVIVAL_STEPPED_LOCAL_LIGHT_COMMON_INCLUDED

#define STEPPED_LOCAL_LIGHT_MAXIMUM 16

int _SteppedLocalLightCount;
float4 _SteppedLocalLightPositionsAndRadii[STEPPED_LOCAL_LIGHT_MAXIMUM];
float4 _SteppedLocalLightColorsAndIntensities[STEPPED_LOCAL_LIGHT_MAXIMUM];
float4 _SteppedLocalLightQuantizationSettings[STEPPED_LOCAL_LIGHT_MAXIMUM];
float _SteppedLocalLightWorldCellSizes[STEPPED_LOCAL_LIGHT_MAXIMUM];
float _SteppedLocalLightHaloRadiusMultipliers[STEPPED_LOCAL_LIGHT_MAXIMUM];
float4x4 _SteppedLocalLightVolumeWorldToLocal[STEPPED_LOCAL_LIGHT_MAXIMUM];
float4 _SteppedLocalLightVolumeCenters[STEPPED_LOCAL_LIGHT_MAXIMUM];
float4 _SteppedLocalLightVolumeExtents[STEPPED_LOCAL_LIGHT_MAXIMUM];
float4x4 _SteppedLocalLightVolume2WorldToLocal[STEPPED_LOCAL_LIGHT_MAXIMUM];
float4 _SteppedLocalLightVolume2Centers[STEPPED_LOCAL_LIGHT_MAXIMUM];
float4 _SteppedLocalLightVolume2Extents[STEPPED_LOCAL_LIGHT_MAXIMUM];

bool IsInsideSteppedLightRoom(int index, float3 positionWS)
{
    float4 center = _SteppedLocalLightVolumeCenters[index];
    float4 center2 = _SteppedLocalLightVolume2Centers[index];
    if (center.w < 0.5 && center2.w < 0.5)
        return true;

    // The union describes an authored room, including L-shaped sales rooms.
    // It does not trace dynamic shadows through walls or furniture.
    if (center.w > 0.5)
    {
        float3 local = mul(_SteppedLocalLightVolumeWorldToLocal[index], float4(positionWS, 1.0)).xyz;
        if (all(abs(local - center.xyz) <= _SteppedLocalLightVolumeExtents[index].xyz))
            return true;
    }
    if (center2.w > 0.5)
    {
        float3 local = mul(_SteppedLocalLightVolume2WorldToLocal[index], float4(positionWS, 1.0)).xyz;
        if (all(abs(local - center2.xyz) <= _SteppedLocalLightVolume2Extents[index].xyz))
            return true;
    }
    return false;
}

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
    float normalInfluenceScale,
    out half3 nativeAdditiveLight)
{
    half3 accumulatedLight = half3(0.0, 0.0, 0.0);
    nativeAdditiveLight = half3(0.0, 0.0, 0.0);

    [loop]
    for (int index = 0; index < STEPPED_LOCAL_LIGHT_MAXIMUM; index++)
    {
        if (index >= _SteppedLocalLightCount)
        {
            break;
        }

        // Test the actual surface before light-grid rounding; rounding must
        // never move an outside surface into an illuminated room.
        if (!IsInsideSteppedLightRoom(index, positionWS))
            continue;

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
        float surfaceInput = surfaceAttenuation * lerp(1.0, normalTerm, normalInfluence);
        bool nativeAdditive = quantization.x < 0.0;
        // Three illuminated levels plus zero. The original round quantizer
        // includes zero in its count and remains unchanged for other lights.
        float positiveBands = max(round(abs(quantization.x)), 2.0);
        float surfaceLight = nativeAdditive ?
            ceil(saturate(surfaceInput) * positiveBands) / positiveBands :
            QuantizeSteppedLight01(surfaceInput, quantization.x);
        float haloLight = QuantizeSteppedLight01(
            haloAttenuation,
            quantization.y) * quantization.z;
        float contribution = surfaceLight + haloLight * (1.0 - surfaceLight);
        half3 lightColor =
            (half3)colorAndIntensity.rgb *
            (half)(colorAndIntensity.w * contribution);
        if (nativeAdditive)
            nativeAdditiveLight += lightColor;
        else
            accumulatedLight += lightColor;
    }

    return accumulatedLight;
}

// Existing fullscreen/character consumers retain the complete light field.
half3 EvaluateSteppedLocalLights(float3 positionWS, float3 normalWS, float normalInfluenceScale)
{
    half3 nativeAdditiveLight;
    half3 regularLight = EvaluateSteppedLocalLights(
        positionWS, normalWS, normalInfluenceScale, nativeAdditiveLight);
    return regularLight + nativeAdditiveLight;
}

#endif
