Shader "Hidden/FantasySurvival/CloudShadowFilter"
{
    Properties
    {
        _MainTex ("Cloud Density", 2D) = "white" {}
        _EvolutionPhase ("Evolution Phase", Float) = 0
        _Seed ("Seed", Float) = 1979
        _Coverage ("Coverage", Range(0, 1)) = 0.55
        _FormationPeriod ("Formation Cells Across Field", Vector) = (7, 7, 0, 0)
        _DensityResolution ("Density Resolution", Float) = 512
        _BillowStrength ("Billow Strength", Range(0, 1)) = 0.70
        _ErosionStrength ("Edge Erosion", Range(0, 1)) = 0.32
        _SoftnessMip ("Softness Mip", Range(0, 3)) = 0
        _Opacity ("Opacity", Range(0, 1)) = 1
        _MaximumAttenuation ("Maximum Attenuation", Range(0, 1)) = 0.72
        _OvercastCoverage ("Overcast Coverage", Range(0, 1)) = 0
        _ClearTransmissionScale ("Clear Transmission Scale", Range(0, 1)) = 1
        _OvercastTransmission ("Overcast Transmission", Range(0, 1)) = 1
    }

    SubShader
    {
        Tags { "RenderPipeline" = "UniversalPipeline" }
        Cull Off
        ZWrite Off
        ZTest Always

        Pass
        {
            Name "ProceduralCloudDensity"

            CGPROGRAM
            #pragma target 3.0
            #pragma vertex vert_img
            #pragma fragment GenerateDensity

            #include "UnityCG.cginc"

            float _EvolutionPhase;
            float _Seed;
            float _Coverage;
            float2 _FormationPeriod;
            float _DensityResolution;
            float _BillowStrength;
            float _ErosionStrength;

            float Hash13(float3 value)
            {
                value = frac(value * 0.1031);
                value += dot(value, value.yzx + 33.33);
                return frac((value.x + value.y) * value.z);
            }

            float2 Hash23(float3 value)
            {
                return float2(
                    Hash13(value),
                    Hash13(value + float3(19.19, 73.17, 41.73)));
            }

            float2 WrapCell(float2 cell, float2 period)
            {
                return cell - floor(cell / period) * period;
            }

            float LatticeValue(
                float2 cell,
                float height,
                float2 period,
                float seed)
            {
                return Hash13(float3(WrapCell(cell, period), height) + seed);
            }

            float PeriodicValueNoise2D(
                float2 position,
                float2 period,
                float height,
                float seed)
            {
                float2 cell = floor(position);
                float2 local = frac(position);
                float2 blend = local * local * local *
                    (local * (local * 6.0 - 15.0) + 10.0);

                float n00 = LatticeValue(cell, height, period, seed);
                float n10 = LatticeValue(
                    cell + float2(1.0, 0.0),
                    height,
                    period,
                    seed);
                float n01 = LatticeValue(
                    cell + float2(0.0, 1.0),
                    height,
                    period,
                    seed);
                float n11 = LatticeValue(
                    cell + float2(1.0, 1.0),
                    height,
                    period,
                    seed);

                return lerp(
                    lerp(n00, n10, blend.x),
                    lerp(n01, n11, blend.x),
                    blend.y);
            }

            float PeriodicWorley(float2 position, float2 period, float seed)
            {
                float2 cell = floor(position);
                float2 local = frac(position);
                float nearestDistanceSquared = 8.0;

                [unroll]
                for (int y = -1; y <= 1; y++)
                {
                    [unroll]
                    for (int x = -1; x <= 1; x++)
                    {
                        float2 neighbor = float2(x, y);
                        float2 wrappedCell = WrapCell(cell + neighbor, period);
                        float2 feature = Hash23(float3(wrappedCell, seed));
                        float2 delta = neighbor + feature - local;
                        nearestDistanceSquared = min(
                            nearestDistanceSquared,
                            dot(delta, delta));
                    }
                }

                return sqrt(nearestDistanceSquared);
            }

            float LargeScaleField(float2 uv, float phase, float seed)
            {
                float2 period = _FormationPeriod;
                float octave0 = PeriodicValueNoise2D(
                    uv * period + phase * float2(0.11, -0.07),
                    period,
                    0.0,
                    seed + 1.7);
                float octave1 = PeriodicValueNoise2D(
                    uv * (period * 2.0) + phase * float2(-0.17, 0.09),
                    period * 2.0,
                    11.0,
                    seed + 7.3);
                float octave2 = PeriodicValueNoise2D(
                    uv * (period * 4.0) + phase * float2(0.23, 0.13),
                    period * 4.0,
                    23.0,
                    seed + 17.9);
                return octave0 * 0.60 + octave1 * 0.27 + octave2 * 0.13;
            }

            fixed4 GenerateDensity(v2f_img input) : SV_Target
            {
                float2 uv = frac(input.uv);
                float2 warpPeriod = max(2.0, floor(_FormationPeriod * 1.5));
                float warpX = PeriodicValueNoise2D(
                    uv * warpPeriod +
                    _EvolutionPhase * float2(0.09, 0.05),
                    warpPeriod,
                    31.0,
                    _Seed + 29.1);
                float warpY = PeriodicValueNoise2D(
                    (uv + float2(0.37, 0.61)) * warpPeriod +
                    _EvolutionPhase * float2(-0.07, 0.11),
                    warpPeriod,
                    47.0,
                    _Seed + 43.7);
                float2 shapedUv =
                    uv + (float2(warpX, warpY) - 0.5) *
                    (0.15 / _FormationPeriod);

                float governingShape = LargeScaleField(
                    shapedUv,
                    _EvolutionPhase,
                    _Seed);
                float coverageThreshold = lerp(0.68, 0.40, saturate(_Coverage));

                float billowDistance = PeriodicWorley(
                    shapedUv * (_FormationPeriod * 4.0) +
                    _EvolutionPhase * float2(-0.31, 0.19),
                    _FormationPeriod * 4.0,
                    _Seed + 71.0);
                float billow = saturate(1.0 - billowDistance * 1.15);
                float governingGate = smoothstep(
                    coverageThreshold - 0.22,
                    coverageThreshold + 0.08,
                    governingShape);
                float shapedDensity =
                    governingShape +
                    (billow - 0.5) *
                    (0.16 * saturate(_BillowStrength)) *
                    governingGate;

                // At least four texels per detail cell avoid aliasing when the
                // profile requests a smaller render texture.
                float2 detailPeriod0 = min(_FormationPeriod * 8.0,
                    floor(_DensityResolution * 0.25));
                float2 detailPeriod1 = min(floor(_FormationPeriod * 14.5),
                    floor(_DensityResolution * 0.25));
                float detail0 = PeriodicValueNoise2D(
                    shapedUv * detailPeriod0 +
                    _EvolutionPhase * float2(0.73, -0.41),
                    detailPeriod0,
                    67.0,
                    _Seed + 113.0);
                float detail1 = PeriodicValueNoise2D(
                    shapedUv * detailPeriod1 +
                    _EvolutionPhase * float2(-0.53, 0.67),
                    detailPeriod1,
                    89.0,
                    _Seed + 151.0);
                float edgeDetail = detail0 * 0.65 + detail1 * 0.35;
                float edgeBand = 1.0 - smoothstep(
                    0.06,
                    0.20,
                    abs(shapedDensity - coverageThreshold));
                float erodedDensity =
                    shapedDensity -
                    (1.0 - edgeDetail) *
                    edgeBand *
                    (0.16 * saturate(_ErosionStrength));
                // Noise determines the silhouette, not nested interior tones.
                // Keep one shadow density inside each cloud and a short, smooth
                // boundary so slow evolution does not switch texels abruptly.
                float density = smoothstep(
                    coverageThreshold - 0.025,
                    coverageThreshold + 0.025,
                    erodedDensity);

                // R preserves the clear-weather silhouette exactly. G carries
                // the same continuous field for a moving threshold, without
                // changing its seed, world footprint or generating new noise.
                return fixed4(density, saturate((erodedDensity + 0.3) / 1.6), 0.0, 1.0);
            }
            ENDCG
        }

        Pass
        {
            Name "ComposeCloudShadowCookie"

            CGPROGRAM
            #pragma target 3.0
            #pragma vertex vert_img
            #pragma fragment ComposeCookie

            #include "UnityCG.cginc"

            sampler2D _MainTex;
            float _SoftnessMip;
            float _Opacity;
            float _MaximumAttenuation;
            float _Coverage;
            float _OvercastCoverage;
            float _ClearTransmissionScale;
            float _OvercastTransmission;

            fixed4 ComposeCookie(v2f_img input) : SV_Target
            {
                float2 density = tex2Dlod(
                    _MainTex,
                    float4(input.uv, 0.0, _SoftnessMip)).rg;
                float attenuation =
                    saturate(density.r) *
                    saturate(_Opacity) *
                    saturate(_MaximumAttenuation);
                float clearTransmission = (1.0 - attenuation) * _ClearTransmissionScale;
                float gathering = saturate(_OvercastCoverage);
                float threshold = lerp(lerp(0.68, 0.40, saturate(_Coverage)), -0.30, gathering);
                float field = density.g * 1.6 - 0.3;
                float overcastMask = smoothstep(0.0, 0.12, gathering) *
                    smoothstep(threshold - 0.025, threshold + 0.025, field);
                // Guarantee exact endpoints despite filtered/quantized density.
                if (gathering >= 1.0) overcastMask = 1.0;
                float transmission = lerp(clearTransmission, _OvercastTransmission, overcastMask);
                return fixed4(
                    transmission,
                    transmission,
                    transmission,
                    1.0);
            }
            ENDCG
        }
    }

    Fallback Off
}
