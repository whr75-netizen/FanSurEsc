Shader "Hidden/FantasySurvival/SteppedLocalLightFullscreen"
{
    SubShader
    {
        Tags
        {
            "RenderPipeline" = "UniversalPipeline"
            "RenderType" = "Transparent"
        }

        ZTest Always
        ZWrite Off
        Cull Off
        Blend One One
        ColorMask RGB

        Pass
        {
            Name "SteppedLocalLightFullscreen"

            HLSLPROGRAM
            #pragma target 4.5
            #pragma vertex Vert
            #pragma fragment Frag

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.core/Runtime/Utilities/Blit.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/DeclareDepthTexture.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/DeclareNormalsTexture.hlsl"

            #define STEPPED_LOCAL_LIGHT_MAXIMUM 16

            int _SteppedLocalLightCount;
            float4 _SteppedLocalLightPositionsAndRadii[STEPPED_LOCAL_LIGHT_MAXIMUM];
            float4 _SteppedLocalLightColorsAndIntensities[STEPPED_LOCAL_LIGHT_MAXIMUM];
            float4 _SteppedLocalLightQuantizationSettings[STEPPED_LOCAL_LIGHT_MAXIMUM];
            float _SteppedLocalLightWorldCellSizes[STEPPED_LOCAL_LIGHT_MAXIMUM];
            float _SteppedLocalLightHaloRadiusMultipliers[STEPPED_LOCAL_LIGHT_MAXIMUM];

            float GeometryMask(float rawDepth)
            {
                #if UNITY_REVERSED_Z
                    return step(0.000001, rawDepth);
                #else
                    return 1.0 - step(0.999999, rawDepth);
                #endif
            }

            float3 SteppedSafeNormalize(float3 value)
            {
                return value * rsqrt(max(dot(value, value), 0.000001));
            }

            float3 ReconstructWorldPosition(float2 uv, float rawDepth)
            {
                #if UNITY_REVERSED_Z
                    float deviceDepth = rawDepth;
                #else
                    float deviceDepth = lerp(UNITY_NEAR_CLIP_VALUE, 1.0, rawDepth);
                #endif

                return ComputeWorldSpacePosition(uv, deviceDepth, UNITY_MATRIX_I_VP);
            }

            float3 SnapWorldPosition(float3 positionWS, float cellSize)
            {
                float safeCellSize = max(cellSize, 0.0001);
                return floor(positionWS / safeCellSize + 0.5) * safeCellSize;
            }

            float Quantize01(float value, float bands)
            {
                float intervals = max(round(bands) - 1.0, 1.0);
                return floor(saturate(value) * intervals + 0.5) / intervals;
            }

            half4 Frag(Varyings input) : SV_Target0
            {
                UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(input);

                float2 uv = saturate(input.texcoord.xy);
                float rawDepth = SampleSceneDepth(uv, sampler_PointClamp);
                if (GeometryMask(rawDepth) <= 0.0)
                {
                    return half4(0.0, 0.0, 0.0, 0.0);
                }

                float3 positionWS = ReconstructWorldPosition(uv, rawDepth);
                float3 normalWS = SteppedSafeNormalize(
                    SampleSceneNormals(uv, sampler_PointClamp));
                half3 accumulatedLight = half3(0.0, 0.0, 0.0);

                [loop]
                for (int index = 0; index < STEPPED_LOCAL_LIGHT_MAXIMUM; index++)
                {
                    if (index >= _SteppedLocalLightCount)
                    {
                        break;
                    }

                    float4 positionAndRadius =
                        _SteppedLocalLightPositionsAndRadii[index];
                    float4 colorAndIntensity =
                        _SteppedLocalLightColorsAndIntensities[index];
                    float4 quantization =
                        _SteppedLocalLightQuantizationSettings[index];
                    float3 snappedPositionWS = SnapWorldPosition(
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
                    float surfaceLight = Quantize01(
                        surfaceAttenuation * lerp(1.0, normalTerm, quantization.w),
                        quantization.x);
                    float haloLight = Quantize01(
                        haloAttenuation,
                        quantization.y) * quantization.z;
                    float contribution =
                        surfaceLight + haloLight * (1.0 - surfaceLight);
                    accumulatedLight +=
                        (half3)colorAndIntensity.rgb *
                        (half)(colorAndIntensity.w * contribution);
                }

                return half4(accumulatedLight, 0.0);
            }
            ENDHLSL
        }
    }

    FallBack Off
}
