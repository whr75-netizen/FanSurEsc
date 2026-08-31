Shader "Hidden/FantasySurvival/LocalVolumetricLightFullscreen"
{
    SubShader
    {
        Tags
        {
            "RenderPipeline" = "UniversalPipeline"
            "RenderType" = "Transparent"
            "Queue" = "Transparent"
        }

        ZTest Always
        ZWrite Off
        Cull Off
        Blend One One
        ColorMask RGB

        Pass
        {
            Name "LocalVolumetricLightFullscreen"

            HLSLPROGRAM
            #pragma target 4.5
            #pragma vertex Vert
            #pragma fragment Frag

            #pragma multi_compile _ _ADDITIONAL_LIGHTS_VERTEX _ADDITIONAL_LIGHTS
            #pragma multi_compile_fragment _ _ADDITIONAL_LIGHT_SHADOWS
            #pragma multi_compile_fragment _ _SHADOWS_SOFT _SHADOWS_SOFT_LOW _SHADOWS_SOFT_MEDIUM _SHADOWS_SOFT_HIGH
            #pragma multi_compile_fragment _ _LIGHT_COOKIES
            #pragma multi_compile _ _CLUSTER_LIGHT_LOOP

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/DeclareDepthTexture.hlsl"

            #define LOCAL_VOLUME_MAXIMUM_LIGHTS 16
            #define LOCAL_VOLUME_MAXIMUM_SAMPLES 32

            int _LocalVolumeLightCount;
            float4 _LocalVolumeOriginsAndRanges[LOCAL_VOLUME_MAXIMUM_LIGHTS];
            float4 _LocalVolumeDirectionsAndRadii[LOCAL_VOLUME_MAXIMUM_LIGHTS];
            float4 _LocalVolumeMediumSettings[LOCAL_VOLUME_MAXIMUM_LIGHTS];
            float4 _LocalVolumeSamplingSettings;

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

            bool IsInsideFiniteCone(
                float3 relativePosition,
                float3 axis,
                float range,
                float radiusSlope)
            {
                float axial = dot(relativePosition, axis);
                if (axial < 0.0 || axial > range)
                {
                    return false;
                }

                float3 radialVector = relativePosition - axis * axial;
                float allowedRadius = axial * radiusSlope;
                return dot(radialVector, radialVector) <=
                    allowedRadius * allowedRadius + 0.00001;
            }

            void AddConeHit(
                float hitDistance,
                float axial,
                float range,
                inout float entry,
                inout float exit,
                inout int hitCount)
            {
                if (hitDistance < 0.0 || axial < -0.0001 || axial > range + 0.0001)
                {
                    return;
                }

                entry = min(entry, hitDistance);
                exit = max(exit, hitDistance);
                hitCount++;
            }

            bool IntersectFiniteCone(
                float3 rayOriginWS,
                float3 rayDirectionWS,
                float3 coneOriginWS,
                float3 coneAxisWS,
                float range,
                float endRadius,
                float sceneDistance,
                out float entry,
                out float exit)
            {
                float safeRange = max(range, 0.001);
                float radiusSlope = endRadius / safeRange;
                float slopeSquared = radiusSlope * radiusSlope;
                float3 relativeOrigin = rayOriginWS - coneOriginWS;
                float originAxial = dot(relativeOrigin, coneAxisWS);
                float directionAxial = dot(rayDirectionWS, coneAxisWS);
                float3 originRadial = relativeOrigin - coneAxisWS * originAxial;
                float3 directionRadial =
                    rayDirectionWS - coneAxisWS * directionAxial;

                float a = dot(directionRadial, directionRadial) -
                    slopeSquared * directionAxial * directionAxial;
                float b = 2.0 * (
                    dot(originRadial, directionRadial) -
                    slopeSquared * originAxial * directionAxial);
                float c = dot(originRadial, originRadial) -
                    slopeSquared * originAxial * originAxial;

                entry = 1e20;
                exit = -1e20;
                int hitCount = 0;

                if (IsInsideFiniteCone(
                    relativeOrigin,
                    coneAxisWS,
                    safeRange,
                    radiusSlope))
                {
                    entry = 0.0;
                    exit = 0.0;
                    hitCount = 1;
                }

                if (abs(a) <= 0.0000001)
                {
                    if (abs(b) > 0.0000001)
                    {
                        float sideHit = -c / b;
                        AddConeHit(
                            sideHit,
                            originAxial + sideHit * directionAxial,
                            safeRange,
                            entry,
                            exit,
                            hitCount);
                    }
                }
                else
                {
                    float discriminant = b * b - 4.0 * a * c;
                    if (discriminant >= 0.0)
                    {
                        float root = sqrt(discriminant);
                        float inverseDenominator = 0.5 / a;
                        float sideHit0 = (-b - root) * inverseDenominator;
                        float sideHit1 = (-b + root) * inverseDenominator;
                        AddConeHit(
                            sideHit0,
                            originAxial + sideHit0 * directionAxial,
                            safeRange,
                            entry,
                            exit,
                            hitCount);
                        AddConeHit(
                            sideHit1,
                            originAxial + sideHit1 * directionAxial,
                            safeRange,
                            entry,
                            exit,
                            hitCount);
                    }
                }

                if (abs(directionAxial) > 0.0000001)
                {
                    float capHit = (safeRange - originAxial) / directionAxial;
                    if (capHit >= 0.0)
                    {
                        float3 capPosition =
                            relativeOrigin + rayDirectionWS * capHit;
                        float3 capRadial =
                            capPosition - coneAxisWS * safeRange;
                        if (dot(capRadial, capRadial) <=
                            endRadius * endRadius + 0.00001)
                        {
                            AddConeHit(
                                capHit,
                                safeRange,
                                safeRange,
                                entry,
                                exit,
                                hitCount);
                        }
                    }
                }

                if (hitCount < 2)
                {
                    return false;
                }

                entry = max(entry, 0.0);
                exit = min(exit, sceneDistance + 0.005);
                return exit > entry + 0.0001;
            }

            float PhaseFunction(float anisotropy, float cosineTheta)
            {
                float g = clamp(anisotropy, -0.95, 0.95);
                float gSquared = g * g;
                float denominator = max(
                    1.0 + gSquared - 2.0 * g * cosineTheta,
                    0.0001);
                // Henyey-Greenstein without 1/(4*pi), so g=0 keeps a
                // convenient neutral multiplier of one.
                return (1.0 - gSquared) /
                    max(pow(denominator, 1.5), 0.0001);
            }

            float3 SampleSourceLight(
                int packedLightIndex,
                float3 samplePositionWS,
                float3 rayDirectionWS,
                float anisotropy)
            {
                Light sourceLight = GetAdditionalPerObjectLight(
                    packedLightIndex,
                    samplePositionWS);
                float shadow = AdditionalLightRealtimeShadow(
                    packedLightIndex,
                    samplePositionWS,
                    sourceLight.direction);
                float3 cookie = float3(1.0, 1.0, 1.0);
                #if defined(_LIGHT_COOKIES)
                    cookie = SampleAdditionalLightCookie(
                        packedLightIndex,
                        samplePositionWS);
                #endif

                float phase = PhaseFunction(
                    anisotropy,
                    dot(rayDirectionWS, sourceLight.direction));
                return sourceLight.color * cookie *
                    (sourceLight.distanceAttenuation * shadow * phase);
            }

            float3 IntegrateLightVolume(
                float3 rayOriginWS,
                float3 rayDirectionWS,
                float entry,
                float exit,
                float3 coneOriginWS,
                float3 coneAxisWS,
                float range,
                float scattering,
                float extinction,
                float anisotropy,
                int packedLightIndex,
                int sampleCount)
            {
                float pathLength = exit - entry;
                float stepLength = pathLength / max((float)sampleCount, 1.0);
                float transmittance = 1.0;
                float3 accumulated = float3(0.0, 0.0, 0.0);
                float safeExtinction = max(extinction, 0.0);
                float integratedStep = safeExtinction > 0.00001
                    ? (1.0 - exp(-safeExtinction * stepLength)) / safeExtinction
                    : stepLength;
                float stepTransmittance = exp(-safeExtinction * stepLength);

                [loop]
                for (int sampleIndex = 0;
                     sampleIndex < LOCAL_VOLUME_MAXIMUM_SAMPLES;
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
                    float sourceDistance = dot(
                        samplePositionWS - coneOriginWS,
                        coneAxisWS);
                    float sourcePathLength = length(
                        samplePositionWS - coneOriginWS);
                    float sourceFade = smoothstep(
                        0.015,
                        0.08,
                        sourceDistance / max(range, 0.001));
                    // Account for extinction on both halves of the single-
                    // scattering path: source -> sample and sample -> camera.
                    // The camera half is accumulated in transmittance below;
                    // the uniform source half is analytic and needs no nested
                    // lightmarch.
                    float sourceTransmittance = exp(
                        -safeExtinction * sourcePathLength);
                    float3 incidentLight = SampleSourceLight(
                        packedLightIndex,
                        samplePositionWS,
                        rayDirectionWS,
                        anisotropy);
                    accumulated += transmittance * incidentLight *
                        (scattering * sourceFade * sourceTransmittance *
                         integratedStep);
                    transmittance *= stepTransmittance;
                    if (transmittance < 0.001)
                    {
                        break;
                    }
                }

                return accumulated;
            }

            float4 Frag(Varyings input) : SV_Target0
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
                if (sceneDistance <= 0.0001)
                {
                    return float4(0.0, 0.0, 0.0, 0.0);
                }

                int sampleCount = clamp(
                    (int)round(_LocalVolumeSamplingSettings.x),
                    1,
                    LOCAL_VOLUME_MAXIMUM_SAMPLES);
                float3 accumulatedLight = float3(0.0, 0.0, 0.0);
                [loop]
                for (int lightIndex = 0;
                     lightIndex < LOCAL_VOLUME_MAXIMUM_LIGHTS;
                     lightIndex++)
                {
                    if (lightIndex >= _LocalVolumeLightCount)
                    {
                        break;
                    }

                    float4 originAndRange =
                        _LocalVolumeOriginsAndRanges[lightIndex];
                    float4 directionAndRadius =
                        _LocalVolumeDirectionsAndRadii[lightIndex];
                    float4 medium = _LocalVolumeMediumSettings[lightIndex];
                    float3 coneAxisWS = VolumeSafeNormalize(
                        directionAndRadius.xyz);
                    float entry;
                    float exit;
                    if (!IntersectFiniteCone(
                        rayOriginWS,
                        rayDirectionWS,
                        originAndRange.xyz,
                        coneAxisWS,
                        originAndRange.w,
                        directionAndRadius.w,
                        sceneDistance,
                        entry,
                        exit))
                    {
                        continue;
                    }

                    accumulatedLight += IntegrateLightVolume(
                        rayOriginWS,
                        rayDirectionWS,
                        entry,
                        exit,
                        originAndRange.xyz,
                        coneAxisWS,
                        originAndRange.w,
                        medium.x,
                        medium.y,
                        medium.z,
                        (int)round(medium.w),
                        sampleCount);
                }

                return float4(accumulatedLight, 0.0);
            }
            ENDHLSL
        }
    }

    FallBack Off
}
