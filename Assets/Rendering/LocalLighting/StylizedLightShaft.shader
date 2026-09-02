Shader "Hidden/FantasySurvival/StylizedLightShaft"
{
    Properties
    {
        [HideInInspector][HDR] _ShaftColor("Shaft Color", Color) = (1, 1, 1, 1)
        [HideInInspector] _ShaftIntensity("Shaft Intensity", Float) = 0
        [HideInInspector] _ShadowThreshold("Shadow Contrast Threshold", Range(0, 1)) = 0.08
        [HideInInspector] _SurfaceFadeDistance("Surface Fade Distance", Float) = 0.45
        [HideInInspector] _DirectionalVolumeBounds("Volume Bounds", Vector) = (0.02, 6, 0.75, 0)
        [HideInInspector] _DirectionalMediumSettings("Medium Settings", Vector) = (0.16, 0.22, 0, 0)
        [HideInInspector] _DirectionalSampleCount("Sample Count", Float) = 8
        [HideInInspector] _DirectionalVolumeTexture("Directional Volume", 2D) = "black" {}
    }

    SubShader
    {
        Tags
        {
            "RenderPipeline" = "UniversalPipeline"
            "RenderType" = "Transparent"
            "Queue" = "Transparent+20"
        }

        ZTest Always
        ZWrite Off
        Cull Off
        ColorMask RGB

        Pass
        {
            Name "DirectionalVolumeIntegration"
            Blend One Zero

            HLSLPROGRAM
            #pragma target 4.5
            #pragma vertex Vert
            #pragma fragment Frag
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/DeclareDepthTexture.hlsl"

            #define DIRECTIONAL_VOLUME_MAXIMUM_SAMPLES 16

            CBUFFER_START(UnityPerMaterial)
                half4 _ShaftColor;
                float _ShaftIntensity;
                float _ShadowThreshold;
                float _SurfaceFadeDistance;
                float4 _DirectionalVolumeBounds;
                float4 _DirectionalMediumSettings;
                float _DirectionalSampleCount;
            CBUFFER_END

            struct Attributes
            {
                uint vertexID : SV_VertexID;
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float2 uv : TEXCOORD0;
                UNITY_VERTEX_OUTPUT_STEREO
            };

            Varyings Vert(Attributes input)
            {
                Varyings output;
                UNITY_SETUP_INSTANCE_ID(input);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(output);
                output.positionCS = GetFullScreenTriangleVertexPosition(input.vertexID);
                output.uv = GetFullScreenTriangleTexCoord(input.vertexID);
                return output;
            }

            float3 VolumeSafeNormalize(float3 value)
            {
                return value * rsqrt(max(dot(value, value), 0.0000001));
            }

            float ToDeviceDepth(float rawDepth)
            {
                #if UNITY_REVERSED_Z
                    return rawDepth;
                #else
                    return lerp(UNITY_NEAR_CLIP_VALUE, 1.0, rawDepth);
                #endif
            }

            void ReconstructCameraRay(
                float2 uv,
                out float3 rayOriginWS,
                out float3 rayDirectionWS,
                out float sceneDistance)
            {
                #if UNITY_REVERSED_Z
                    const float nearDeviceDepth = 1.0;
                    const float farDeviceDepth = 0.0;
                #else
                    const float nearDeviceDepth = UNITY_NEAR_CLIP_VALUE;
                    const float farDeviceDepth = 1.0;
                #endif

                float3 nearWS = ComputeWorldSpacePosition(
                    uv,
                    nearDeviceDepth,
                    UNITY_MATRIX_I_VP);
                float3 farWS = ComputeWorldSpacePosition(
                    uv,
                    farDeviceDepth,
                    UNITY_MATRIX_I_VP);
                rayOriginWS = nearWS;
                rayDirectionWS = VolumeSafeNormalize(farWS - nearWS);

                float rawSceneDepth = SampleSceneDepth(uv, sampler_PointClamp);
                float3 sceneWS = ComputeWorldSpacePosition(
                    uv,
                    ToDeviceDepth(rawSceneDepth),
                    UNITY_MATRIX_I_VP);
                sceneDistance = max(
                    dot(sceneWS - rayOriginWS, rayDirectionWS),
                    0.0);
            }

            bool IntersectHeightVolume(
                float3 rayOriginWS,
                float3 rayDirectionWS,
                float sceneDistance,
                out float entry,
                out float exit)
            {
                if (abs(rayDirectionWS.y) <= 0.00001)
                {
                    entry = 0.0;
                    exit = 0.0;
                    return false;
                }

                float baseHeight = _DirectionalVolumeBounds.x;
                float topHeight = baseHeight + max(_DirectionalVolumeBounds.y, 0.001);
                float baseHit = (baseHeight - rayOriginWS.y) / rayDirectionWS.y;
                float topHit = (topHeight - rayOriginWS.y) / rayDirectionWS.y;
                entry = max(min(baseHit, topHit), 0.0);
                exit = min(max(baseHit, topHit), sceneDistance);
                return exit > entry + 0.0001;
            }

            float SampleMainShadow(float3 positionWS)
            {
                #if defined(MAIN_LIGHT_CALCULATE_SHADOWS)
                float4 shadowCoord = TransformWorldToShadowCoord(positionWS);
                half4 shadowParams = GetMainLightShadowParams();
                // The atmosphere needs a visibility classification, not the full
                // surface-shadow PCF kernel. One comparison keeps the cost bounded
                // at sampleCount * five probes; half-resolution bilinear composite
                // softens the presentation without multiplying shadow taps.
                real attenuation = SAMPLE_TEXTURE2D_SHADOW(
                    _MainLightShadowmapTexture,
                    sampler_LinearClampCompare,
                    shadowCoord.xyz);
                attenuation = LerpWhiteTo(attenuation, shadowParams.x);
                return lerp(
                    attenuation,
                    1.0,
                    GetMainLightShadowFade(positionWS));
                #else
                return 1.0;
                #endif
            }

            float PhaseFunction(float anisotropy, float cosineTheta)
            {
                float g = clamp(anisotropy, -0.85, 0.85);
                float gSquared = g * g;
                float denominator = max(
                    1.0 + gSquared - 2.0 * g * cosineTheta,
                    0.0001);
                return (1.0 - gSquared) /
                    max(pow(denominator, 1.5), 0.0001);
            }

            float IntegrateDirectionalVolume(
                float3 rayOriginWS,
                float3 rayDirectionWS,
                float sceneDistance,
                float entry,
                float exit)
            {
                int sampleCount = clamp(
                    (int)round(_DirectionalSampleCount),
                    1,
                    DIRECTIONAL_VOLUME_MAXIMUM_SAMPLES);
                float pathLength = exit - entry;
                float stepLength = pathLength / max((float)sampleCount, 1.0);
                float safeExtinction = max(_DirectionalMediumSettings.x, 0.0);
                float integratedStep = safeExtinction > 0.00001
                    ? (1.0 - exp(-safeExtinction * stepLength)) / safeExtinction
                    : stepLength;
                float stepTransmittance = exp(-safeExtinction * stepLength);
                float transmittance = 1.0;
                float accumulated = 0.0;

                Light mainLight = GetMainLight();
                float3 lightDirection = VolumeSafeNormalize(mainLight.direction);
                float3 contrastAxisA = cross(float3(0.0, 1.0, 0.0), lightDirection);
                if (dot(contrastAxisA, contrastAxisA) <= 0.0001)
                {
                    contrastAxisA = cross(float3(1.0, 0.0, 0.0), lightDirection);
                }
                contrastAxisA = VolumeSafeNormalize(contrastAxisA);
                float3 contrastAxisB = VolumeSafeNormalize(
                    cross(lightDirection, contrastAxisA));

                float probeDistance = max(_DirectionalVolumeBounds.z, 0.01);
                float contrastThreshold = clamp(_ShadowThreshold, 0.001, 1.0);
                float contrastStart = contrastThreshold * 0.35;
                float phase = PhaseFunction(
                    _DirectionalMediumSettings.y,
                    dot(rayDirectionWS, lightDirection));
                float baseHeight = _DirectionalVolumeBounds.x;
                float volumeHeight = max(_DirectionalVolumeBounds.y, 0.001);

                [loop]
                for (int sampleIndex = 0;
                     sampleIndex < DIRECTIONAL_VOLUME_MAXIMUM_SAMPLES;
                     sampleIndex++)
                {
                    if (sampleIndex >= sampleCount)
                    {
                        break;
                    }

                    float distanceAlongRay =
                        entry + ((float)sampleIndex + 0.5) * stepLength;
                    float3 samplePositionWS =
                        rayOriginWS + rayDirectionWS * distanceAlongRay;
                    float centerVisibility = SampleMainShadow(samplePositionWS);
                    float negativeVisibilityA = SampleMainShadow(
                        samplePositionWS - contrastAxisA * probeDistance);
                    float positiveVisibilityA = SampleMainShadow(
                        samplePositionWS + contrastAxisA * probeDistance);
                    float negativeVisibilityB = SampleMainShadow(
                        samplePositionWS - contrastAxisB * probeDistance);
                    float positiveVisibilityB = SampleMainShadow(
                        samplePositionWS + contrastAxisB * probeDistance);
                    float surroundingVisibility =
                        (negativeVisibilityA + positiveVisibilityA +
                         negativeVisibilityB + positiveVisibilityB) * 0.25;
                    float positiveContrast = max(
                        centerVisibility - surroundingVisibility,
                        0.0);
                    float contrastVisibility = smoothstep(
                        contrastStart,
                        contrastThreshold,
                        positiveContrast);

                    float normalizedHeight = saturate(
                        (samplePositionWS.y - baseHeight) / volumeHeight);
                    float volumeEdgeFade =
                        smoothstep(0.0, 0.04, normalizedHeight) *
                        (1.0 - smoothstep(0.94, 1.0, normalizedHeight));
                    float surfaceFade = smoothstep(
                        0.0,
                        max(_SurfaceFadeDistance, 0.001),
                        sceneDistance - distanceAlongRay);

                    accumulated += transmittance * centerVisibility *
                        contrastVisibility * phase * volumeEdgeFade *
                        surfaceFade * integratedStep;
                    transmittance *= stepTransmittance;
                    if (transmittance < 0.001)
                    {
                        break;
                    }
                }

                return accumulated;
            }

            half4 Frag(Varyings input) : SV_Target0
            {
                UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(input);

                float2 uv = saturate(input.uv);
                float3 rayOriginWS;
                float3 rayDirectionWS;
                float sceneDistance;
                ReconstructCameraRay(
                    uv,
                    rayOriginWS,
                    rayDirectionWS,
                    sceneDistance);

                float entry;
                float exit;
                if (sceneDistance <= 0.0001 ||
                    !IntersectHeightVolume(
                        rayOriginWS,
                        rayDirectionWS,
                        sceneDistance,
                        entry,
                        exit))
                {
                    return half4(0.0, 0.0, 0.0, 0.0);
                }

                float scattering = IntegrateDirectionalVolume(
                    rayOriginWS,
                    rayDirectionWS,
                    sceneDistance,
                    entry,
                    exit);
                return half4(
                    _ShaftColor.rgb * (_ShaftIntensity * scattering),
                    0.0);
            }
            ENDHLSL
        }

        Pass
        {
            Name "DirectionalVolumeComposite"
            Blend One One

            HLSLPROGRAM
            #pragma target 4.5
            #pragma vertex Vert
            #pragma fragment Frag

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

            TEXTURE2D_X(_DirectionalVolumeTexture);

            struct Attributes
            {
                uint vertexID : SV_VertexID;
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float2 uv : TEXCOORD0;
                UNITY_VERTEX_OUTPUT_STEREO
            };

            Varyings Vert(Attributes input)
            {
                Varyings output;
                UNITY_SETUP_INSTANCE_ID(input);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(output);
                output.positionCS = GetFullScreenTriangleVertexPosition(input.vertexID);
                output.uv = GetFullScreenTriangleTexCoord(input.vertexID);
                return output;
            }

            half4 Frag(Varyings input) : SV_Target0
            {
                UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(input);
                half3 volume = SAMPLE_TEXTURE2D_X(
                    _DirectionalVolumeTexture,
                    sampler_LinearClamp,
                    saturate(input.uv)).rgb;
                return half4(volume, 0.0);
            }
            ENDHLSL
        }
    }

    FallBack Off
}
